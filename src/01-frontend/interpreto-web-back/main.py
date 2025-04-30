# main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import uvicorn  # <- Esto es importante

app = FastAPI()

# Middleware CORS para permitir peticiones del frontend (React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza con dominios reales en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generador SSE que emite frases poco a poco
def sse_response(filename: str):
    yield f"data: Recibí el archivo de audio: {filename} \n\n"
    time.sleep(1)
    yield "data: Procesando el archivo... \n\n"
    time.sleep(1)
    yield "data: He terminado de procesar el archivo. Gracias. \n\n"

# Endpoint que recibe el archivo y devuelve SSE
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    return StreamingResponse(sse_response(file.filename), media_type="text/event-stream")

# ¡Esto arranca el servidor!
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
