import webrtcvad
import whisper
import wave
import contextlib
import collections
import subprocess
import os
import sys
from pydub import AudioSegment

# --- CONFIGURACIÓN ---
FRAME_DURATION = 30  # ms
SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2

# Inicializar VAD
vad = webrtcvad.Vad(3)

# Cargar modelo Whisper
model = whisper.load_model("large-v3-turbo")  # Cambia a "medium", "large", etc. si querés

def convert_to_wav(input_path, output_path="converted.wav"):
    # Convertir a WAV 16kHz mono PCM
    print(f"Convirtiendo {input_path} a WAV compatible...")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(CHANNELS).set_sample_width(BYTES_PER_SAMPLE)
    audio.export(output_path, format="wav")
    return output_path

def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        assert wf.getnchannels() == CHANNELS
        assert wf.getsampwidth() == BYTES_PER_SAMPLE
        assert wf.getframerate() == SAMPLE_RATE
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data

def frame_generator(frame_duration_ms, audio, sample_rate):
    n = int(sample_rate * (frame_duration_ms / 1000.0) * BYTES_PER_SAMPLE)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / BYTES_PER_SAMPLE) / sample_rate
    while offset + n <= len(audio):
        yield audio[offset:offset + n], timestamp, duration
        timestamp += duration
        offset += n

def vad_collector(sample_rate, frame_duration_ms, padding_duration_ms, frames):
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    triggered = False

    voiced_frames = []
    segments = []

    for frame, timestamp, duration in frames:
        is_speech = vad.is_speech(frame, sample_rate)

        if not triggered:
            ring_buffer.append((frame, timestamp, duration))
            num_voiced = len([f for f, t, d in ring_buffer if vad.is_speech(f, sample_rate)])
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                start_time = ring_buffer[0][1]
                voiced_frames.extend([f for f, t, d in ring_buffer])
                ring_buffer.clear()
        else:
            voiced_frames.append(frame)
            ring_buffer.append((frame, timestamp, duration))
            num_unvoiced = len([f for f, t, d in ring_buffer if not vad.is_speech(f, sample_rate)])
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                end_time = timestamp + duration
                segment = b''.join(voiced_frames)
                segments.append((segment, start_time, end_time))
                ring_buffer.clear()
                voiced_frames = []
                triggered = False

    if voiced_frames:
        end_time = timestamp + duration
        segment = b''.join(voiced_frames)
        segments.append((segment, start_time, end_time))

    return segments

def transcribe_segments(segments):
    results = []
    for i, (segment, start, end) in enumerate(segments):
        segment_path = f"segment_{i}.wav"
        with wave.open(segment_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BYTES_PER_SAMPLE)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(segment)

        result = model.transcribe(segment_path, task="transcribe", language=None)
        os.remove(segment_path)

        results.append({
            "start": start,
            "end": end,
            "language": result.get("language", "unknown"),
            "text": result["text"].strip()
        })
    return results

def main(audio_path):
    # Convertir si es necesario
    if not audio_path.endswith(".wav"):
        audio_path = convert_to_wav(audio_path)

    audio = read_wave(audio_path)
    frames = frame_generator(FRAME_DURATION, audio, SAMPLE_RATE)
    segments = vad_collector(SAMPLE_RATE, FRAME_DURATION, 300, frames)
    transcriptions = transcribe_segments(segments)

    for t in transcriptions:
        print(f"[{t['start']:.2f}s - {t['end']:.2f}s] ({t['language']}): {t['text']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python script.py archivo.mp3")
        sys.exit(1)
    main(sys.argv[1])
