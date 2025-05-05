import imageio_ffmpeg
import json
import os
import redis
import shutil
import subprocess
import time
import torch
import torchaudio
from bson import ObjectId
from datetime import timedelta as td
from datetime import datetime
from faster_whisper import WhisperModel
from minio import Minio
from pydub import AudioSegment
from pymongo import MongoClient
from tempfile import mkdtemp

# ========= CONFIG =========
use_cuda = torch.cuda.is_available()

# Whisper
model_size = "turbo"
compute_type = "float32"

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

try:
    mongo_client = MongoClient(mongo_uri)
    mongo_db = mongo_client[MONGO_DB]
    files_collection = mongo_db["file"]
    queue_collection = mongo_db["queue"]
    print(f"Succesfully connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}")
    queue_collection = mongo_client[MONGO_DB][MONGO_QUEUE_COLLECTION]
    file_collection = mongo_client[MONGO_DB][MONGO_FILE_COLLECTION]
    print(f"Succesfully obtained collections: {MONGO_QUEUE_COLLECTION} and {MONGO_FILE_COLLECTION}")
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

print("Connecting to minio...")
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# Redis config
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    print(f"Succesfully connected to Redis: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    exit(1)

# ========= MODELS =========
print("Loading models...")

print("Loading whisper model...")
model = WhisperModel(
    model_size,
    device="cuda" if use_cuda else "cpu",
    compute_type=compute_type
)

print("Loading silero-vad model...")
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

# ========= FUNCTIONS =========
def get_timestamp(seconds):
    t = str(td(seconds=seconds)).split(".")
    return f"{t[0]},{t[1][:3] if len(t) > 1 else '000'}"

def write_wav(segment, path):
    segment.export(path, format="wav")

# ========= GET TASK =========
def get_task():

    job = queue_collection.find_one_and_update(
        {"status": "waiting"},
        {"$set": {"status": "processing"}},
        sort=[("_id", 1)]  # Opcional: garantiza orden FIFO si usas MongoDB
    )

    if not job:
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

def fail_task(job, fail_reason):
    queue_collection.update_one(
        {"_id": job["_id"]},
        {"$set": {
            "status": "failed",
            "detailed_status": fail_reason,
            "completed_at": datetime.now(),
            "updated_at": datetime.now()}
        }
    )

def store_transcription(job, transcription):
    queue_collection.update_one(
        {"_id": ObjectId(job["_id"])},
        {"$set": {"transcription": transcription}}
    )

def store_transcription_segment(job, transcription_segment):
    queue_collection.update_one(
        {"_id": ObjectId(job["_id"])},
        {"$push": {"transcription": transcription_segment}}
    )

# ========= DOWNLOAD FROM MINIO =========
def download_file_from_minio(filename, temp_dir):
    mp3_path = os.path.join(temp_dir, filename)

    minio_client.fget_object(
        MINIO_BUCKET_NAME,
        filename,
        mp3_path
    )

    return mp3_path

# ========= PREPARE AUDIO =========
def prepare_audio_old(filename, temp_dir):
    wav_path = os.path.join(temp_dir, "converted.wav")

    audio = AudioSegment.from_file(filename)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(wav_path, format="wav")

    waveform, sr = torchaudio.load(wav_path)
    if use_cuda:
        waveform = waveform.to("cuda")
    
    return {"audio": audio, "waveform": waveform, "sr": sr}

def prepare_audio(file_path, temp_dir):
    wav_path = os.path.join(temp_dir, "converted.wav")

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg_path,
        "-i", file_path,
        "-ac", "1",
        "-ar", "16000",
        "-y",
        wav_path
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error converting file {file_path} to audio using ffmpeg: {e}")
    
    audio_segments = AudioSegment.from_wav(wav_path)
    
    waveform, sr = torchaudio.load(wav_path)
    if use_cuda:
        waveform = waveform.to("cuda")

    return {"audio": audio_segments, "audio_path": wav_path, "waveform": waveform, "sr": sr}

# ========= VOICE DETECTION =========
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

# ========= EXTRACT AND STORE SEGMENTS =========
def extract_segments(audio, speech_timestamps, sr):
    segments = []
    for i, ts in enumerate(speech_timestamps):
        start_sec = ts['start'] / sr
        end_sec = ts['end'] / sr
        duration = end_sec - start_sec

        segment_audio = audio[start_sec * 1000:end_sec * 1000]
        seg_path = os.path.join(temp_dir, f"segment_{i}.wav")
        write_wav(segment_audio, seg_path)
        segments.append((seg_path, start_sec, end_sec))
    return segments

# ========= TRANSCRIBE USING FASTER-WHISPER =========
def transcribe_segments(segments, job):
    results = []
    for i, (seg_path, start, end) in enumerate(segments):
        segs, info = model.transcribe(seg_path, beam_size=5)
        full_text = "".join([s.text for s in segs])
        print(f"[{get_timestamp(start)} --> {get_timestamp(end)}] ({info.language}) {full_text.strip()}")
        result = {
            "seg": i+1,
            "start": start,
            "end": end,
            "language": info.language,
            "text": full_text.strip()
        }
        results.append(result)
        os.remove(seg_path)

        # send segment to redis
        r.publish(job["object_etag"], json.dumps(result))
        # store segment transcription to mongo
        store_transcription_segment(job, result)

    # send closed event
    r.publish(job["object_etag"], json.dumps({"state": "closed"}))
    return results

if __name__ == "__main__":
    while True:
        # Get job, if none, wait 1 seconds and try again
        job = get_task()
        if not job:
            time.sleep(1)
            continue
        print(job)
        print(f"[INFO] Processing job for file: {job["object_name"]} (etag: {job['object_etag']})")

        
        temp_dir = mkdtemp()
        file_path = download_file_from_minio(job["object_name"], temp_dir)
        
        # try to convert file to audio in mono 16khz
        try:
            audio = prepare_audio(file_path, temp_dir)
        except Exception as e:
            # in case we fail, we mark the job as failed and continue
            fail_task(job, str(e))
            continue

        speech_timestamps = voice_detection(audio["waveform"], audio["sr"])
        print(f"[INFO] Detectados {len(speech_timestamps)} segmentos con voz")

        segments = extract_segments(audio["audio"], speech_timestamps, audio["sr"])
        print(f"[INFO] Extraídos {len(segments)} segmentos de audio")
        store_transcription(job, [])
        results = transcribe_segments(segments, job)
        print(f"[INFO] Transcripción completa")
        # Save results to mongo
        # find existing file and set results
        # in "transcription" field

        complete_task(job)
        # store_file_transcription(job, results)
        print(f"[INFO] Tarea completada")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("[DEBUG] Job: ", job)
        print("[DEBUG] Results: ", results)



