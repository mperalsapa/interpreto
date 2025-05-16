import asyncio
import hashlib
import io
import json
import mimetypes
import os
import uvicorn
import redis.asyncio as redis
from bson import ObjectId
from datetime import datetime as dt
from datetime import timezone as tz
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from io import BytesIO
from minio import Minio
from pymongo import MongoClient

app = FastAPI()

# Global variables
MONGO_CLIENT = None
FILES_COLLECTION = None
MINIO_CLIENT = None
REDIS_CLIENT = None
MINIO_BUCKET_NAME = None

@app.on_event("startup")
def startup_event():
    global MONGO_CLIENT, FILES_COLLECTION, MINIO_CLIENT, REDIS_CLIENT, MINIO_BUCKET_NAME

    # MongoDB Config
    try:
        MONGO_HOST = os.environ.get("MONGO_HOST", "192.168.1.10")
        MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
        MONGO_USER = os.environ.get("MONGO_USER", "frontend-service")
        MONGO_PASS = os.environ.get("MONGO_PASS", "frontend-service")
        MONGO_DB   = os.environ.get("MONGO_DB", "media_service")
        MONGO_FILE_COLLECTION = os.environ.get("MONGO_FILE_COLLECTION", "file")

        mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

        MONGO_CLIENT = MongoClient(mongo_uri)
        print(f"Succesfully connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}")
        FILES_COLLECTION = MONGO_CLIENT[MONGO_DB][MONGO_FILE_COLLECTION]
        print(f"Succesfully obtained collection: {MONGO_FILE_COLLECTION}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        exit(1)


    # MinIO Config
    try:
        MINIO_HOST = os.environ.get("MINIO_HOST", "localhost")
        MINIO_PORT = int(os.environ.get("MINIO_PORT", "9000"))
        MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        MINIO_SECURE = os.environ.get("MINIO_SECURE", "False").lower().capitalize() == "True"
        MINIO_BUCKET_NAME = "media-files"

        MINIO_CLIENT = Minio(
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
    try:
        REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
        REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
        
        REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        print(f"Succesfully connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        exit(1)

    # Making sure MinIO bucket exists
    try:
        if not MINIO_CLIENT.bucket_exists(MINIO_BUCKET_NAME):
            print(f"Creating MinIO bucket: {MINIO_BUCKET_NAME}")
            MINIO_CLIENT.make_bucket(MINIO_BUCKET_NAME)
        else:
            print(f"Using existing MinIO bucket: {MINIO_BUCKET_NAME}")
    except Exception as e:
        print(f"Error creating MinIO bucket: {e}")
        exit(1)

    # Store in app state
    app.state.MONGO_CLIENT = MONGO_CLIENT
    app.state.FILES_COLLECTION = FILES_COLLECTION
    app.state.MINIO_CLIENT = MINIO_CLIENT
    app.state.REDIS_CLIENT = REDIS_CLIENT
    app.state.minio_bucket = MINIO_BUCKET_NAME

@app.on_event("shutdown")
def shutdown_event():
    if MONGO_CLIENT:
        MONGO_CLIENT.close()
        print("🔌 MongoDB connection closed.")

# Middleware CORS
# TODO: Change this to a more secure way
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def store_file_minio(file, object_name, content_type):
    stored_object = MINIO_CLIENT.put_object(
            MINIO_BUCKET_NAME,
            object_name,
            file,
            length=len(file.getvalue()),
            content_type=content_type
        )

    return stored_object

def store_file_mongo(file, object_result, file_hash):
    inserted_file = FILES_COLLECTION.insert_one({
        "filename": file.filename,
        "content_type": file.content_type,
        "object_name": object_result.object_name,
        "object_etag": object_result.etag,
        "hash": file_hash,
        "status": "waiting",
        "created_at": dt.now(tz.utc),
        "updated_at": dt.now(tz.utc),
    })
    
    return inserted_file

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Check if given file has a audio/* o video/* content type
        if not file.content_type.startswith("audio/") and not file.content_type.startswith("video/"):
            return JSONResponse(status_code=400, content={"state": "error", "message": "El archivo debe ser de tipo audio o video."})

        contents = await file.read()
        content_hash = hashlib.sha256(contents).hexdigest()

        # Check if file already exists in mongo by filehash
        existing_file = FILES_COLLECTION.find_one({"hash": content_hash})
        if existing_file:
            return JSONResponse(status_code=200, content={"state": "existing", "file_id": str(existing_file["_id"])})

        # If not exists, generate filename
        object_name = content_hash
        file_stream = io.BytesIO(contents)

        # Store file in MinIO
        stored_object = store_file_minio(file_stream, object_name, file.content_type)

        # Store file in MongoDB
        inserted_file = store_file_mongo(file, stored_object, content_hash)

        return JSONResponse(status_code=200, content={"state": "uploaded", "file_id": str(inserted_file.inserted_id)})

    except Exception as e:
        error_message = str(e)
        return JSONResponse(status_code=500, content={"state": "error", "message": f"Error processing file: {error_message}"})
    finally:
        await file.close()

@app.get("/api/file/{file_id}")
async def get_file(file_id: str):
    file = FILES_COLLECTION.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    allowed_fields = ["filename", "content_type", "status", "created_at", "completed_at"]
    file_info = {field: file[field] for field in allowed_fields if field in file}
    print(file_info)
    return JSONResponse(status_code=200, content=jsonable_encoder(file_info)) # using jsonable_encoder to ensure proper timestamp serialization



@app.get("/api/file/{file_id}/transcription/stream")
async def get_file(file_id: str):
    file = FILES_COLLECTION.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file job is completed
    if file["status"] == "completed":
        async def event_stream():
            for i, seg in enumerate(file["transcription"]):
                response = {"state": "transcribed_segment", "message": seg}
                yield f"data: {json.dumps(response)}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    pubsub = REDIS_CLIENT.pubsub()
    await pubsub.subscribe(file["object_etag"])

    # get the last transcription segment
    transcription = file.get("transcription", [])
    last_transcription = int(transcription[-1]["seg"]) if transcription else 0
    last_transcription_sent = 0  # Variable to keep track of the last sent transcription segment
    transcription_state = {
        "transcription" : transcription,
        "last_transcription" : last_transcription,
        "last_transcription_sent" : last_transcription_sent
    }

    async def event_stream(file = None, transcription_state = {}):
        transcription = transcription_state["transcription"]
        last_transcription = transcription_state["last_transcription"]
        last_transcription_sent = transcription_state["last_transcription_sent"]

        try:
            if not file:
                yield "data: No file queued\n\n"
                return
            
            for i, t in enumerate(transcription):
                last_transcription = t["seg"]
                response = {"state": "transcribed_segment", "message": t}
                yield f"data: {json.dumps(response)}\n\n"
                last_transcription_sent = i

            # Loop that will listen to Redis messages
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if not message:
                    if last_transcription_sent:
                        print(f"No message, waiting. Last transcription sent was {last_transcription_sent}.")
                    await asyncio.sleep(1)  # wait for a second before checking again
                    continue
                data = message['data'].decode()
                print(f"New message: {data}")

                try:
                    # Tries to load the JSON from the message
                    data = json.loads(data)
                    if data.get("state") == "closed":
                        break
                    seg = int(data.get("seg"))
                    print(f"Processing message. Mesage seg is: {seg}")
                    if seg == last_transcription + 1:
                        print("New message is the following to the last message")
                        # if the segment is the next in the sequence
                        transcription.append(data)
                        last_transcription += 1
                        yield f"data: {json.dumps({'state': 'transcribed_segment', 'message': data})}\n\n"
                    else:
                        # If the segment is not the next in the sequence, we need to get the last transcription from Mongo
                        file = FILES_COLLECTION.find_one({"_id": ObjectId(file_id)})
                        transcription = file["transcription"]
                        last_transcription = int(transcription[-1]["seg"]) if transcription else 0

                        # Try to send the missing messages
                        for item in transcription:
                            if item["seg"] > last_transcription_sent:
                                yield f"data: {json.dumps({'state': 'transcribed_segment', 'seg': item['seg'], 'text': item['text']})}\n\n"
                                last_transcription_sent = item["seg"]
                        # Continue with the new message
                        if seg == last_transcription + 1:
                            transcription.append(data)
                            last_transcription += 1
                            yield f"data: {json.dumps({'state': 'transcribed_segment', 'seg': seg, 'text': data['text']})}\n\n"

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Ignore invalid messages
                    print(e)
                    continue
        finally:            
            if file:
                await pubsub.unsubscribe(file["object_etag"])
            await pubsub.close()
    
    return StreamingResponse(event_stream(file, transcription_state), media_type="text/event-stream") 

@app.get("/api/file/{file_id}/transcription")
async def get_file_transcription(file_id: str):
    file = FILES_COLLECTION.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file job is completed
    if file["status"] == "completed":
        return JSONResponse(status_code=200, content=jsonable_encoder(file["transcription"]))
    
    return JSONResponse(status_code=200, content={"state": "waiting", "message": "Transcription is still in progress."})

@app.get("/api/admin/files")
async def get_files(request: Request):
    # check if user is admin, reading bearertoken and checking if matches "sapa2025" in sha1
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.split(" ")[1]
    if token != "fa5ef3f3f833d4a8e756935f4c6ab298f7a738ed":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Get all files from MongoDB
    files = FILES_COLLECTION.find()
    files_list = []
    for file in files:
        file["_id"] = str(file["_id"])
        file["created_at"] = file["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        if "completed_at" in file:
            file["completed_at"] = file["completed_at"].strftime("%Y-%m-%d %H:%M:%S")
        files_list.append(file)
    
    return JSONResponse(status_code=200, content=jsonable_encoder(files_list))

@app.get("/media/{file_id}")
async def get_media_file(file_id: str, request: Request):
    # Search for file in MongoDB
    file_doc = FILES_COLLECTION.find_one({"_id": ObjectId(file_id)})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found for this ETag")

    object_name = file_doc["object_name"]
    mime_type = file_doc.get("content_type") or mimetypes.guess_type(object_name)[0] or "application/octet-stream"

    # Get the Range header from the request
    range_header = request.headers.get('Range')

    # Get the file size from MinIO
    stat = MINIO_CLIENT.stat_object("media-files", object_name)
    file_size = stat.size

    if range_header:
        # Parse the range header to get the start and end bytes
        range_start, range_end = parse_range_header(range_header, file_size)

        # Obtain the file range from MinIO
        try:
            partial_file_data = MINIO_CLIENT.get_object(
                "media-files",
                object_name,
                offset=range_start,
                length=range_end - range_start + 1
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve file range: {str(e)}")

        headers = {
            "Content-Range": f"bytes {range_start}-{range_end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(range_end - range_start + 1),
        }

        return StreamingResponse(partial_file_data, media_type=mime_type, headers=headers, status_code=206)

    # Get the full file from MinIO
    try:
        file_data = MINIO_CLIENT.get_object("media-files", object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve full file: {str(e)}")

    return StreamingResponse(file_data, media_type=mime_type)

def parse_range_header(range_header, file_size):
    # The range header can have the format 'bytes=start-end'
    range_values = range_header.replace('bytes=', '').split('-')
    range_start = int(range_values[0])
    range_end = int(range_values[1]) if range_values[1] else file_size - 1

    # Validate that the range is valid
    if range_start >= file_size or range_end >= file_size:
        raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    return range_start, range_end

def chunked_file(file_data, range_start, range_end, chunk_size=1024*1024):
    # We create a buffer that reads in the desired range
    bytes_read = 0
    while bytes_read < range_end - range_start + 1:
        # Reads the next chunk (minimum between the chunk size and the rest of the range)
        chunk = file_data.read(min(chunk_size, range_end - range_start + 1 - bytes_read))
        if not chunk:
            break
        yield chunk
        bytes_read += len(chunk)

# Absolute path to frontend build directory
frontend_dist_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "front-dist")
)

# Mount static files for assets
app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(frontend_dist_path, "assets")),
    name="assets"
)

# / route, returns intex.html
@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(open(os.path.join(frontend_dist_path, "index.html"), "r").read())

# Catch-all for any other non api route
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str):
    file_path = os.path.join(frontend_dist_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_dist_path, "index.html"))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
