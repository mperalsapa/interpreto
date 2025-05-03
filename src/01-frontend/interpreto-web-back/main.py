import asyncio
import hashlib
import io
import os
import uvicorn
import redis.asyncio as redis
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from minio import Minio
from pymongo import MongoClient

app = FastAPI()

# MongoDB Config
MONGO_HOST = os.environ.get("MONGO_HOST", "192.168.1.10")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_USER = os.environ.get("MONGO_USER", "frontend-service")
MONGO_PASS = os.environ.get("MONGO_PASS", "frontend-service")
MONGO_DB   = os.environ.get("MONGO_DB", "media_service")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

try:
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[MONGO_DB]
    files_collection = mongo_db["file"]
    queue_collection = mongo_db["queue"]
    print(f"Succesfully connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit(1)


# MinIO Config
MINIO_HOST = os.environ.get("MINIO_HOST", "localhost")
MINIO_PORT = int(os.environ.get("MINIO_PORT", "9000"))
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "False").lower().capitalize() == "True"
MINIO_BUCKET_NAME = "media-files"

try:
    minio_client = Minio(
        f"{MINIO_HOST}:{MINIO_PORT}",
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE
    )
    print(f"Succesfully connected to MinIO: {MINIO_HOST}:{MINIO_PORT}")
except Exception as e:
    print(f"Error connecting to MinIO: {e}")
    exit(1)

# Redis config
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    print(f"Succesfully connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    exit(1)

# Making sure MinIO bucket exists
try:
    if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
        print(f"Creating MinIO bucket: {MINIO_BUCKET_NAME}")
        minio_client.make_bucket(MINIO_BUCKET_NAME)
    else:
        print(f"Using existing MinIO bucket: {MINIO_BUCKET_NAME}")
except Exception as e:
    print(f"Error creating MinIO bucket: {e}")
    exit(1)

# Middleware CORS
# TODO: Change this to a more secure way
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def store_file_minio(file, object_name, content_type):
    stored_object = minio_client.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            file,
            length=len(file.getvalue()),
            content_type=content_type
        )

    return stored_object

def store_file_mongo(file, object_result, file_hash):
    inserted_file = files_collection.insert_one({
        "filename": file.filename,
        "object_name": object_result.object_name,
        "object_etag": object_result.etag,
        "hash": file_hash,
        "uploaded_at": datetime.utcnow()
    })
    
    return inserted_file

def store_queue_mongo(inserted_file, object_response):
    queue_collection.insert_one({
        "file_id": str(inserted_file.inserted_id),
        "status": "waiting",
        "object_name": object_response.object_name,
        "object_etag": object_response.etag,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        content_hash = hashlib.sha256(contents).hexdigest()

        # Verificar si ya existe en MongoDB por hash
        # Check if file already exists in mongo by filehash
        if files_collection is not None and files_collection.find_one({"hash": content_hash}):
            async def duplicate_stream():
                yield f"data: El archivo ya existe, no se sube de nuevo.\n\n"
            return StreamingResponse(duplicate_stream(), media_type="text/event-stream")
        
        # If not exists, generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        object_name = f"{timestamp}{file_extension}"
        file_stream = io.BytesIO(contents)

        # Store file in MinIO
        stored_object = store_file_minio(file_stream, object_name, file.content_type)

        # Store file in MongoDB
        inserted_file = store_file_mongo(file, stored_object, content_hash)

        # Store file in MongoDB queue
        store_queue_mongo(inserted_file, stored_object)

        # Response to client using SSE
        async def event_stream():
            # Subscribe to redis for realtime response
            pubsub = r.pubsub()
            await pubsub.subscribe(stored_object.etag)

            # Force timeout in case of no response
            # If a worker gets the job, it will send a message to redis
            # If no worker or worker dies, we will stop waiting for a response
            timeout_seconds = 30
            deadline = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            closed = False

            try:
                while datetime.utcnow() < deadline and not closed:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)  # Gets message from redis (client) pubsub buffer
                    if not message: # if there is no message, wait 1 sec and try again (until timeout)
                        await asyncio.sleep(1)
                        continue

                    # If we have a message, get the data, yield it and check if it's "closed"
                    # If it's "closed", we stop waiting for more responses
                    data = message['data'].decode()
                    yield f"data: {data}\n\n"
                    if data.strip().lower() == "closed":
                        closed = True

                    # If we have a message, we reset the timeout
                    deadline = datetime.utcnow() + timedelta(seconds=timeout_seconds)

            finally:
                # Unsubscribe from redis, so we don't get more messages
                await pubsub.unsubscribe(stored_object.etag)
                await pubsub.close()

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        error_message = str(e)
        async def error_stream():
            errorString = f"data: Error processing file: {error_message}\n\n"
            print(errorString)
            yield errorString
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    finally:
        await file.close()

# Absolute path to frontend build directory
frontend_dist_path = os.path.join(os.path.dirname(__file__), "./front-dist")
frontend_dist_path = os.path.abspath(frontend_dist_path)

# Mount static files
app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
