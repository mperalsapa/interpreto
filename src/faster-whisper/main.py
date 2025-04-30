from faster_whisper import WhisperModel
import os
from datetime import timedelta as td

model_size = "turbo"

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")
model = WhisperModel(model_size, device="cuda", compute_type="float32")
# model = WhisperModel(model_size, device="cpu", compute_type="float32")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
#model = WhisperModel(model_size, device="cpu", compute_type="float32")

# FileName = "/mnt/d/Users/Marc/Documents/REPO/SAPA/IABD/M06-Projecte/references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3"
# FileName = "../../references/audio/Kung_Fu_Panda_4_(2024)_[tmdbid-1011985]_Cast.mp3"
# FileName = "/mnt/d/Users/Marc/Downloads/dung_and_drag.mp3"
# FileName = "/mnt/d/Users/Marc/Downloads/kraven.mp3"
# FileName = "/mnt/d/Users/Marc/Downloads/kraven-full.mp3"
FileName = "/mnt/d/Users/Marc/Downloads/Malditos_bastardos_(2009).mp3"

segments, info = model.transcribe(FileName, beam_size=2)

print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

transcription = []

for segment in segments:
    line = {
        "start": segment.start,
        "end": segment.end,
        "text": segment.text
    }
    transcription.append(line)
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

filestring = ""
elapsedTime = 0
def getTimestamp(seconds):
    # Get timestamp from time delta
    timestamp = str(td(seconds=seconds)).split(".")
    
    # If time delta has no milis, we append 000 for consistency
    if len(timestamp) < 2:
        timestamp.append("000")
    else:
        # if have milis, we grab only first 3 digits
        timestamp[1] = timestamp[1][0:3]

    return ",".join(timestamp)

for i, line in enumerate(transcription):
    startTime = line["start"]
    endTime = line["end"]
    text = line["text"]
    
    filestring += f"{ i }\n{ getTimestamp(startTime) } --> { getTimestamp(endTime) }\n{ text.strip() }\n\n"


SRT = True
os.makedirs("output", exist_ok=True)
with open("output/{}.{}".format(os.path.splitext(os.path.basename(FileName))[0], ('srt' if SRT else 'txt')), "w") as file:
    file.write(filestring)