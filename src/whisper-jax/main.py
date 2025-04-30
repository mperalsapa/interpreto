from whisper_jax import FlaxWhisperPipline

# instantiate pipeline
pipeline = FlaxWhisperPipline("openai/whisper-large-v2")

# JIT compile the forward call - slow, but we only do once
text = pipeline("../../references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3")

# used cached function thereafter - super fast!!
text = pipeline("../../references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3")

print(text)
