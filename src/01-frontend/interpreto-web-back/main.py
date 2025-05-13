import asyncio
import hashlib
import io
import json
import mimetypes
import os
import uvicorn
import redis.asyncio as redis
from bson import ObjectId
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from io import BytesIO
from minio import Minio
from pymongo import MongoClient

app = FastAPI()

# MongoDB Config
MONGO_HOST = os.environ.get("MONGO_HOST", "192.168.1.10")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_USER = os.environ.get("MONGO_USER", "frontend-service")
MONGO_PASS = os.environ.get("MONGO_PASS", "frontend-service")
MONGO_DB   = os.environ.get("MONGO_DB", "media_service")
MONGO_FILE_COLLECTION = os.environ.get("MONGO_FILE_COLLECTION", "file")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

try:
    mongo_client = MongoClient(mongo_uri)
    print(f"Succesfully connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}")
    files_collection = mongo_client[MONGO_DB][MONGO_FILE_COLLECTION]
    print(f"Succesfully obtained collection: {MONGO_FILE_COLLECTION}")
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
        "content_type": file.content_type,
        "object_name": object_result.object_name,
        "object_etag": object_result.etag,
        "hash": file_hash,
        "status": "waiting",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
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
        existing_file = files_collection.find_one({"hash": content_hash})
        if existing_file:
            return JSONResponse(status_code=200, content={"state": "existing", "file_id": str(existing_file["_id"])})

        # If not exists, generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        object_name = f"{timestamp}{file_extension}"
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
    file = files_collection.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    allowed_fields = ["filename", "content_type", "status", "created_at", "completed_at"]
    file_info = {field: file[field] for field in allowed_fields if field in file}
    print(file_info)
    return JSONResponse(status_code=200, content=jsonable_encoder(file_info)) # using jsonable_encoder to ensure proper timestamp serialization



@app.get("/api/file/{file_id}/transcription/stream")
async def get_file(file_id: str):
    file = files_collection.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file job is completed
    if file["status"] == "completed":
        async def event_stream():
            for i, seg in enumerate(file["transcription"]):
                response = {"state": "transcribed_segment", "message": seg}
                yield f"data: {json.dumps(response)}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    

    pubsub = r.pubsub()
    await pubsub.subscribe(file["object_etag"])

    # Obtención de la transcripción actual
    transcription = file.get("transcription", [])
    last_transcription = int(transcription[-1]["seg"]) if transcription else 0
    last_transcription_sent = 0  # Variable para controlar el último segmento enviado
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

            # Bucle que escuchará los mensajes de Redis
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if not message:
                    if last_transcription_sent:
                        print(f"No message, waiting. Last transcription sent was {last_transcription_sent}.")
                    await asyncio.sleep(1)  # Espera si no hay nuevos mensajes
                    continue
                data = message['data'].decode()
                print(f"New message: {data}")

                try:
                    # Intentamos cargar el JSON desde el mensaje
                    data = json.loads(data)
                    if data.get("state") == "closed":
                        break
                    seg = int(data.get("seg"))
                    print(f"Processing message. Mesage seg is: {seg}")
                    if seg == last_transcription + 1:
                        print("New message is the following to the last message")
                        # Si el segmento recibido es el siguiente en la secuencia
                        transcription.append(data)
                        last_transcription += 1
                        yield f"data: {json.dumps({'state': 'transcribed_segment', 'message': data})}\n\n"
                    else:
                        # Si hay un gap en la secuencia, actualizamos la transcripción desde Mongo
                        file = files_collection.find_one({"_id": ObjectId(file_id)})
                        transcription = file["transcription"]
                        last_transcription = int(transcription[-1]["seg"]) if transcription else 0

                        # Volver a intentar enviar los mensajes faltantes
                        for item in transcription:
                            if item["seg"] > last_transcription_sent:
                                yield f"data: {json.dumps({'state': 'transcribed_segment', 'seg': item['seg'], 'text': item['text']})}\n\n"
                                last_transcription_sent = item["seg"]
                        # Continuar con el nuevo mensaje
                        if seg == last_transcription + 1:
                            transcription.append(data)
                            last_transcription += 1
                            yield f"data: {json.dumps({'state': 'transcribed_segment', 'seg': seg, 'text': data['text']})}\n\n"

                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    # Si el mensaje no es válido, ignorarlo
                    print(e)
                    continue
        finally:            
            if file:
                await pubsub.unsubscribe(file["object_etag"])
            await pubsub.close()
    
    return StreamingResponse(event_stream(file, transcription_state), media_type="text/event-stream") 

@app.get("/api/file/{file_id}/transcription")
async def get_file_transcription(file_id: str):
    file = files_collection.find_one({"_id": ObjectId(file_id)})
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file job is completed
    if file["status"] == "completed":
        return JSONResponse(status_code=200, content=jsonable_encoder(file["transcription"]))
    
    return JSONResponse(status_code=200, content={"state": "waiting", "message": "Transcription is still in progress."})

@app.get("/media/{file_id}")
async def get_media_file(file_id: str, request: Request):


    # 3. Buscar archivo en la colección de archivos para obtener filename y mime
    file_doc = files_collection.find_one({"_id": ObjectId(file_id)})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found for this ETag")

    object_name = file_doc["object_name"]
    mime_type = file_doc.get("content_type") or mimetypes.guess_type(object_name)[0] or "application/octet-stream"

    # 4. Obtener encabezado Range (si existe)
    range_header = request.headers.get('Range')

    # 5. Obtener tamaño completo del archivo
    stat = minio_client.stat_object("media-files", object_name)
    file_size = stat.size

    if range_header:
        # 6. Parsear rango
        range_start, range_end = parse_range_header(range_header, file_size)

        # 7. Obtener solo el fragmento necesario desde MinIO
        try:
            partial_file_data = minio_client.get_object(
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

    # 8. Si no se especificó un rango, devolver el archivo completo
    try:
        file_data = minio_client.get_object("media-files", object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve full file: {str(e)}")

    return StreamingResponse(file_data, media_type=mime_type)




def parse_range_header(range_header, file_size):
    # El encabezado de rango puede tener el formato 'bytes=start-end'
    range_values = range_header.replace('bytes=', '').split('-')
    range_start = int(range_values[0])
    range_end = int(range_values[1]) if range_values[1] else file_size - 1

    # Validar que el rango sea válido
    if range_start >= file_size or range_end >= file_size:
        raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

    return range_start, range_end


def chunked_file(file_data, range_start, range_end, chunk_size=1024*1024):
    """Genera los fragmentos del archivo en partes (chunks)"""
    # Creamos un buffer que lea en el rango deseado
    bytes_read = 0
    while bytes_read < range_end - range_start + 1:
        # Lee el siguiente chunk (mínimo entre el tamaño del chunk y el resto del rango)
        chunk = file_data.read(min(chunk_size, range_end - range_start + 1 - bytes_read))
        if not chunk:
            break
        yield chunk
        bytes_read += len(chunk)

# Absolute path to frontend build directory
frontend_dist_path = os.path.join(os.path.dirname(__file__), "./front-dist")
frontend_dist_path = os.path.abspath(frontend_dist_path)

# Mount static files
# app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
# 2) Montamos sólo los archivos estáticos (los de assets) en /static
app.mount(
    "/assets",
    StaticFiles(directory=os.path.join(frontend_dist_path, "assets")),
    name="assets"
)

# 4) Ruta para la raíz “/” — devuelve index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(open(os.path.join(frontend_dist_path, "index.html"), "r").read())

# 5) Catch-all para cualquier otra ruta no API: devuelve también index.html
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def catch_all(full_path: str):
    return HTMLResponse(open(os.path.join(frontend_dist_path, "index.html"), "r").read())


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
