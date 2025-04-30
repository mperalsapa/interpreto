import whisper
import sys
from datetime import timedelta as td

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

model = whisper.load_model("turbo")
# model = model.to("cpu")
result = model.transcribe(FileName)
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
    
    for i, chunk in enumerate(result["segments"]):
        startTime = chunk["timestamp"][0]
        endTime = chunk["timestamp"][1] if chunk["timestamp"][1] != None else startTime + 1
        text = chunk["text"]
        if startTime < elapsedTime:
            startTime += elapsedTime
            endTime += elapsedTime
        
        elapsedTime = endTime

        filestring += f"{ i }\n{ getTimestamp(startTime) } --> { getTimestamp(endTime) }\n{ text }\n\n"

with open("output/{}".format(FileName.split("/")[-1], ('srt' if SRT else 'txt')), "w") as file:
# with open(f"output/{FileName.split("/")[-1]}.{'srt' if SRT else 'txt'}", "w") as file:
    file.write(filestring)
