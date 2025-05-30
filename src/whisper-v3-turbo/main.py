import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
# from datasets import load_dataset
import sys
from datetime import timedelta as td
import os

SRT = False
FileName = ""

if len(sys.argv) > 1: 
    for arg in sys.argv[1:]:
        if arg == "--srt":
            SRT = True
        else:
            FileName = arg

if SRT:
    print("Output format will be SRT")
if FileName:
    print(f"File to process: {FileName}")
else:
    print("No filename was given. Example: python main.py audio-file.mp3 --srt")
    quit(1)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
# device = "cpu"
# torch_dtype = torch.float32

model_id = "openai/whisper-large-v3-turbo"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    torch_dtype=torch_dtype,
    device=device,
    chunk_length_s=30,
    generate_kwargs={"language": "en"}
)

# dataset = load_dataset("distil-whisper/librispeech_long", "clean", split="validation")
# sample = dataset[0]["audio"]
# filename = "harry_potter_first_5_min"
# sample = f"../references/{FileName}.mp3"

print(f"Pipeline is using device: {pipe.device}")

result = pipe(FileName, return_timestamps=True)
# print(result["text"])
print(result)

filestring = result["text"]
# write text to file
if SRT:
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
    
    for i, chunk in enumerate(result["chunks"]):
        startTime = chunk["timestamp"][0]
        endTime = chunk["timestamp"][1] if chunk["timestamp"][1] != None else startTime + 1
        text = chunk["text"]
        if startTime < elapsedTime:
            startTime += elapsedTime
            endTime += elapsedTime
        
        elapsedTime = endTime

        filestring += f"{ i }\n{ getTimestamp(startTime) } --> { getTimestamp(endTime) }\n{ text.strip() }\n\n"

os.makedirs("output", exist_ok=True)
with open("output/{}.{}".format(os.path.splitext(os.path.basename(FileName))[0], ('srt' if SRT else 'txt')), "w") as file:
    file.write(filestring)
# with open(f"output/{FileName.split("/")[-1]}.{'srt' if SRT else 'txt'}", "w") as file:
#     file.write(filestring)
