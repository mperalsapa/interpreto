from faster_whisper import WhisperModel

model_size = "turbo"

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")
# model = WhisperModel(model_size, device="cuda", compute_type="float32")
model = WhisperModel(model_size, device="cpu", compute_type="float32")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
#model = WhisperModel(model_size, device="cpu", compute_type="float32")

# segments, info = model.transcribe("/mnt/d/Users/Marc/Documents/REPO/SAPA/IABD/M06-Projecte/references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3", beam_size=5)

segments, info = model.transcribe("../../references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3", beam_size=5)


print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
