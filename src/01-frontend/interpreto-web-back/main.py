from pymongo import MongoClient
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from minio import Minio
import os
from datetime import datetime
import io

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
    print(f"Conectado a MongoDB en {MONGO_HOST}:{MONGO_PORT}")
except Exception as e:
    print(f"Error conectando a MongoDB: {e}")
    exit(1)


# MinIO Config
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Asegurarse de que el bucket existe
BUCKET_NAME = "media-files"
try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
except Exception as e:
    print(f"Error al crear el bucket: {e}")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import StreamingResponse
from datetime import datetime
import hashlib
import io
import os

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print("Entrando a la función upload_file")
    try:
        contents = await file.read()
        hash_value = hashlib.sha256(contents).hexdigest()

        # # Verificar si ya existe en MongoDB por hash
        if files_collection is not None and files_collection.find_one({"hash": hash_value}):
            async def duplicate_stream():
                yield f"data: El archivo ya existe, no se sube de nuevo.\n\n"
            return StreamingResponse(duplicate_stream(), media_type="text/event-stream")

        # Si no existe, generar nombre y subir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1]
        object_name = f"{timestamp}{file_extension}"
        file_stream = io.BytesIO(contents)

        # Subir a MinIO
        object_result = minio_client.put_object(
            BUCKET_NAME,
            object_name,
            file_stream,
            length=len(contents),
            content_type=file.content_type
        )

        # Guardar metadata en MongoDB
        inserted_file = files_collection.insert_one({
            "filename": file.filename,
            "object_name": object_name,
            "object_etag": object_result.etag,
            "hash": hash_value,
            "uploaded_at": datetime.utcnow()
        })

        # añadir a la cola
        queue_collection.insert_one({
            "file_id": str(inserted_file.inserted_id),
            "status": "waiting",
            "object_name": object_name,
            "object_etag": object_result.etag,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        async def event_stream():
            yield f"data: Archivo recibido: {file.filename}\n\n"
            yield "data: Subiendo archivo a MinIO...\n\n"
            yield f"data: File hash: {hash_value}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    except Exception as e:
        error_message = str(e)
        async def error_stream():
            yield f"data: Error al procesar el archivo: {error_message}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    finally:
        await file.close()



if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
