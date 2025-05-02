import os
import torch
import torchaudio
import time
import shutil
from faster_whisper import WhisperModel
from datetime import timedelta as td
from datetime import datetime
from pydub import AudioSegment
from tempfile import mkdtemp
from pymongo import MongoClient
from minio import Minio
from bson import ObjectId

# ========= CONFIG =========
model_size = "turbo"
use_cuda = torch.cuda.is_available()
compute_type = "float32"
min_speech_duration = 0.3  # segundos

# Mongo
# MongoDB Config
MONGO_HOST = os.environ.get("MONGO_HOST", "192.168.1.10")
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))
MONGO_USER = os.environ.get("MONGO_USER", "frontend-service")
MONGO_PASS = os.environ.get("MONGO_PASS", "frontend-service")
MONGO_DB   = os.environ.get("MONGO_DB", "media_service")
MONGO_QUEUE_COLLECTION = os.environ.get("MONGO_QUEUE_COLLECTION", "queue")
MONGO_FILE_COLLECTION = os.environ.get("MONGO_FILE_COLLECTION", "file")

mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}?authSource=admin"

# Minio
minio_endpoint = "localhost:9000"
minio_access_key = "minioadmin"
minio_secret_key = "minioadmin"
minio_bucket = "media-files"

# ========= CLIENTES =========
mongo_client = MongoClient(mongo_uri)
queue_collection = mongo_client[MONGO_DB][MONGO_QUEUE_COLLECTION]
file_collection = mongo_client[MONGO_DB][MONGO_FILE_COLLECTION]

minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# DEBUG TEST TEMP
# Load mongo queue and list it all
# print("[DEBUG] Jobs: ", queue_collection.count_documents({}))
# exit()

# ========= MODELOS =========
model = WhisperModel(
    model_size,
    device="cuda" if use_cuda else "cpu",
    compute_type=compute_type
)

vad = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False
)

vad_model = vad[0].to("cuda" if use_cuda else "cpu")
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = vad[1]

# if use_cuda:
#     vad_model = vad_model.to("cuda")

# ========= FUNCIONES =========
def get_timestamp(seconds):
    t = str(td(seconds=seconds)).split(".")
    return f"{t[0]},{t[1][:3] if len(t) > 1 else '000'}"

def write_wav(segment: AudioSegment, path: str):
    segment.export(path, format="wav")

# ========= OBTENER TAREA =========
def get_task():
    print("[INFO] Obteniendo tarea de la cola...")

    job = queue_collection.find_one_and_update(
        {"status": "waiting"},
        {"$set": {"status": "processing"}},
        sort=[("_id", 1)]  # Opcional: garantiza orden FIFO si usas MongoDB
    )

    if not job:
        print("[INFO] No hay tareas en la cola")
        return None

    return job

def complete_task(job):
    queue_collection.update_one(
        {"_id": job["_id"]},
        {"$set": {
            "status": "completed",
            "completed_at": datetime.now(),
            "updated_at": datetime.now()}
        }
    )

def store_file_transcription(job, transcription):
    file_collection.update_one(
        {"_id": ObjectId(job["file_id"])},
        {"$set": {"transcription": transcription}}
    )

# ========= DESCARGAR DE MINIO =========
def download_file_from_minio(filename, temp_dir):
    mp3_path = os.path.join(temp_dir, filename)

    minio_client.fget_object(
        minio_bucket,
        filename,
        mp3_path
    )

    return mp3_path

# ========= PREPARAR AUDIO =========
def prepare_audio(filename, temp_dir):
    wav_path = os.path.join(temp_dir, "converted.wav")

    audio = AudioSegment.from_file(filename)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    waveform, sr = torchaudio.load(wav_path)
    if use_cuda:
        waveform = waveform.to("cuda")
    
    return {"audio": audio, "waveform": waveform, "sr": sr}

# ========= DETECCIÓN DE VOZ =========
def voice_detection(waveform, sr):
    speech_timestamps = get_speech_timestamps(
        waveform,
        vad_model,
        sampling_rate=sr,
        threshold=0.5,
        min_speech_duration_ms=300,
        max_speech_duration_s=30,
        min_silence_duration_ms=1500,
        speech_pad_ms=100
    )
    return speech_timestamps

# ========= EXTRAER Y GUARDAR SEGMENTOS =========
def extract_segments(audio, speech_timestamps, sr):
    segments = []
    for i, ts in enumerate(speech_timestamps):
        start_sec = ts['start'] / sr
        end_sec = ts['end'] / sr
        duration = end_sec - start_sec
        # if duration < min_speech_duration:
        #     continue

        segment_audio = audio[start_sec * 1000:end_sec * 1000]
        seg_path = os.path.join(temp_dir, f"segment_{i}.wav")
        write_wav(segment_audio, seg_path)
        segments.append((seg_path, start_sec, end_sec))
    return segments

# ========= TRANSCRIBIR CON FASTER-WHISPER =========
def transcribe_segments(segments):
    results = []
    for i, (seg_path, start, end) in enumerate(segments):
        segs, info = model.transcribe(seg_path, beam_size=5)
        full_text = "".join([s.text for s in segs])
        print(f"[{get_timestamp(start)} --> {get_timestamp(end)}] ({info.language}) {full_text.strip()}")
        results.append({
            "start": start,
            "end": end,
            "language": info.language,
            "text": full_text.strip()
        })
        os.remove(seg_path)
    return results

if __name__ == "__main__":
    while True:
        # Get job, if none, wait 1 seconds and try again
        job = get_task()
        if not job:
            time.sleep(1)
            continue
        print(job)
        print(f"[INFO] Procesando archivo: {job["object_name"]}")

        
        temp_dir = mkdtemp()
        mp3_path = download_file_from_minio(job["object_name"], temp_dir)
        audio = prepare_audio(mp3_path, temp_dir)
        speech_timestamps = voice_detection(audio["waveform"], audio["sr"])
        print(f"[INFO] Detectados {len(speech_timestamps)} segmentos con voz")

        segments = extract_segments(audio["audio"], speech_timestamps, audio["sr"])
        print(f"[INFO] Extraídos {len(segments)} segmentos de audio")
        results = transcribe_segments(segments)
        print(f"[INFO] Transcripción completa")
        # Save results to mongo
        # find existing file by new_name
        # and set field "transcription" to results

        complete_task(job)
        store_file_transcription(job, results)
        print(f"[INFO] Tarea completada")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[DEBUG] Job: ", job)
        print("[DEBUG] Results: ", results)

        exit()



