import os
import torch
import torchaudio
from datetime import timedelta as td
from faster_whisper import WhisperModel
from pydub import AudioSegment
from tempfile import mkdtemp

# ========= CONFIG =========
model_size = "turbo"
use_cuda = torch.cuda.is_available()
compute_type = "float32"
# filename = "/mnt/d/Users/Marc/Downloads/kraven.mp3"
filename = "/mnt/d/Users/Marc/Downloads/Malditos_bastardos_(2009).mp3"
min_speech_duration = 0.3  # segundos

# ========= MODELOS =========
# Load faster-whisper
model = WhisperModel(
    model_size,
    device="cuda" if use_cuda else "cpu",
    compute_type=compute_type
)

# Load Silero VAD
vad = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=False
)

vad_model = vad[0]
(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = vad[1]


# ========= FUNCIONES =========
def get_timestamp(seconds):
    t = str(td(seconds=seconds)).split(".")
    return f"{t[0]},{t[1][:3] if len(t) > 1 else '000'}"

def write_wav(segment: AudioSegment, path: str):
    segment.export(path, format="wav")

# ========= PREPARAR AUDIO =========
# Convertir a mono 16kHz WAV (requerido por Silero)
temp_dir = mkdtemp()
wav_path = os.path.join(temp_dir, "converted.wav")

audio = AudioSegment.from_file(filename)
audio = audio.set_channels(1).set_frame_rate(16000)
audio.export(wav_path, format="wav")

# Cargar como tensor con torchaudio
waveform, sr = torchaudio.load(wav_path)
if use_cuda:
    vad_model = vad_model.to("cuda")
    waveform = waveform.to("cuda")

# ========= DETECCIÓN DE VOZ =========
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

print(f"[INFO] Detectados {len(speech_timestamps)} segmentos con voz")

# ========= EXTRAER Y GUARDAR SEGMENTOS =========
segments = []
for i, ts in enumerate(speech_timestamps):
    start_sec = ts['start'] / sr
    end_sec = ts['end'] / sr
    duration = end_sec - start_sec
    if duration < min_speech_duration:
        continue

    segment_audio = audio[start_sec * 1000:end_sec * 1000]  # Pydub usa milisegundos
    seg_path = os.path.join(temp_dir, f"segment_{i}.wav")
    write_wav(segment_audio, seg_path)

    segments.append((seg_path, start_sec, end_sec))

# ========= TRANSCRIBIR CON FASTER-WHISPER =========
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

# ========= EXPORTAR SRT =========
os.makedirs("output", exist_ok=True)
base = os.path.splitext(os.path.basename(filename))[0]
outpath = f"output/{base}.srt"

with open(outpath, "w", encoding="utf-8") as f:
    for i, r in enumerate(results):
        index = i+1
        start = get_timestamp(r['start'])
        end = get_timestamp(r['end'])
        text = r['text']

        f.write(f"{index}\n{start} --> {end}\n{text}\n\n")
        # f.write(f"{i + 1}\n{get_timestamp(r['start'])} --> {get_timestamp(r['end'])}\n{r['text']}\n\n")

print(f"Transcripción exportada a: {outpath}")
