import webrtcvad
import wave
import contextlib
import collections
import os
import sys
from pydub import AudioSegment
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

# --- CONFIGURACIÓN ---
FRAME_DURATION = 30  # ms
SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2


def convert_to_wav(input_path, output_path="converted.wav"):
    print(f"[INFO] Convirtiendo {input_path} a WAV compatible...")
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

def transcribe_segments(segments, min_duration=1):
    results = []
    for i, (segment, start, end) in enumerate(segments):
        duration = end - start
        if duration < min_duration:
            continue  # ⛔️ Ignorar segmentos muy cortos

        segment_path = f"segment_{i}.wav"
        with wave.open(segment_path, 'wb') as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(BYTES_PER_SAMPLE)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(segment)

        result = pipe(segment_path, return_timestamps="word")
        os.remove(segment_path)

        language = result.get("language", "und")
        text = result["text"].strip()
        results.append({
            "start": start,
            "end": end,
            "language": language,
            "text": text
        })
    return results


def main(audio_path):
    if not audio_path.endswith(".wav"):
        audio_path = convert_to_wav(audio_path)

    audio = read_wave(audio_path)
    frames = frame_generator(FRAME_DURATION, audio, SAMPLE_RATE)
    segments = vad_collector(SAMPLE_RATE, FRAME_DURATION, 300, frames)
    print(f"[INFO] Se detectaron {len(segments)} segmentos de voz.")
    transcriptions = transcribe_segments(segments)

    print("\n📋 Resultados:")
    for t in transcriptions:
        print(f"[{t['start']:.2f}s - {t['end']:.2f}s] ({t['language']}): {t['text']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python script.py archivo.mp3")
        sys.exit(1)

    # Inicializar VAD
    vad = webrtcvad.Vad(3)

    # Dispositivo
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # Cargar modelo HuggingFace
    model_id = "openai/whisper-large-v3-turbo"

    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    ).to(device)

    processor = AutoProcessor.from_pretrained(model_id)

    pipe = pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        torch_dtype=torch_dtype,
        device=device,
        chunk_length_s=30,
    )

    print(f"[INFO] Usando modelo {model_id} en {device}")

    main(sys.argv[1])
