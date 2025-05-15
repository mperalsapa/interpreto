import { useEffect, useState, useRef } from "react";
import { useParams } from "react-router-dom";
import Navbar from "./Navbar";
import MediaViewer from "./MediaViewer";
import { useLanguage } from "../i18n/LanguageContext";

const baseUrl = import.meta.env.VITE_BASE_URL;

function JobPage() {
  const { file_id } = useParams();
  const [transcription, setTranscription] = useState([]);
  const [transcriptionFormat, setTranscriptionFormat] = useState("webvtt");
  const [fileDetails, setFileDetails] = useState(null);
  const [currentSegment, setCurrentSegment] = useState(null);
  const [interactiveViewer, setInteractiveViewer] = useState(true);
  const { t } = useLanguage();

  const fileUrl = `${baseUrl}/media/${file_id}`;

  useEffect(() => {
    fetch(`${baseUrl}/api/file/${file_id}`)
      .then((res) => res.json())
      .then((data) => {
        setFileDetails(data);
      })
      .catch((err) => {
        console.error("Error al obtener los detalles del archivo:", err);
      });
  }, [file_id]);

  useEffect(() => {
    if (!fileDetails) return;

    if (fileDetails.status === "completed") {
      // Fetch completed transcription
      fetch(`${baseUrl}/api/file/${file_id}/transcription`)
        .then((res) => res.json())
        .then((data) => {
          setTranscription(data);
        })
        .catch((err) => {
          console.error("Error al obtener la transcripción:", err);
        });
    } else {
      // Fetch WIP transcription over SSE
      const es = new EventSource(
        `${baseUrl}/api/file/${file_id}/transcription/stream`,
      );

      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.state === "transcribed_segment") {
            setTranscription((prev) => [...prev, data.message]);
          }
        } catch (err) {
          console.error("Error procesando SSE:", err);
        }
      };

      es.onerror = () => {
        es.close();
      };

      return () => {
        es.close();
      };
    }
  }, [fileDetails]);

  const generateSRT = (transcription) => {
    let srt = "";
    transcription.forEach((segment, i) => {
      srt += `${i + 1}\n`;
      srt += `${formatTime(segment.start, ",")} --> ${formatTime(segment.end, ",")}\n`;
      srt += `${segment.text}\n\n`;
    });

    return srt;
  };

  const generateVTT = (transcription) => {
    let vtt = "WEBVTT\n\n";
    transcription.forEach((segment, i) => {
      vtt += `${i + 1}\n${formatTime(segment.start)} --> ${formatTime(segment.end)}\n${segment.text}\n\n`;
    });
    return vtt;
  };

  const formatTime = (seconds, decimalSeparator = ".") => {
    const hrs = Math.floor(seconds / 3600)
      .toString()
      .padStart(2, "0");
    const mins = Math.floor((seconds % 3600) / 60)
      .toString()
      .padStart(2, "0");
    const secs = Math.floor(seconds % 60)
      .toString()
      .padStart(2, "0");
    const ms = Math.floor((seconds % 1) * 1000)
      .toString()
      .padStart(3, "0");
    return `${hrs}:${mins}:${secs}${decimalSeparator}${ms}`;
  };

  const getTranscriptionFormatted = (transcription) => {
    switch (transcriptionFormat) {
      case "srt":
        return generateSRT(transcription);
      case "webvtt":
        return generateVTT(transcription);
      case "txt":
        return transcription.map((segment) => segment.text).join("\n");
      default:
        return generateVTT(transcription);
    }
  };

  const handleTranscriptionFormatChange = (e) => {
    setTranscriptionFormat(e.target.value);
  };

  const handleCueChange = (cue) => {
    console.log(
      `New cue changed: ${cue.text}. Start: ${cue.startTime}, End: ${cue.endTime}`,
    );
    const index = transcription.findIndex(
      (segment) => cue.startTime.toFixed(1) === segment.start.toFixed(1),
    );
    if (index !== -1 && index !== currentSegment) {
      setCurrentSegment(index);
      const el = document.getElementById(`subtitle-${index}`);
      const container = document.getElementById("transcription-container");

      if (el && container) {
        // Asegura que el scroll ocurre solo dentro del contenedor
        const elTop = el.offsetTop;
        const elHeight = el.offsetHeight;
        const containerHeight = container.offsetHeight;

        container.scrollTo({
          top: elTop - containerHeight / 2 + elHeight / 2,
          behavior: "smooth",
        });
      }
    }
  };

  const handleCueClick = (index) => {
    const videos = document.getElementsByTagName("video");
    if (!videos) return;

    const video = videos[0];
    if (!video) return;

    const segment = transcription[index];
    if (!segment) return;

    video.currentTime = segment.start;
    video.play();
  };

  const downloadTranscription = () => {
    console.log("Downloading transcription in format:", transcriptionFormat);

    const blob = new Blob([getTranscriptionFormatted(transcription)], {
      type: "text/plain",
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = `${fileDetails.filename}_transcription.${transcriptionFormat}`;
    a.click();
    URL.revokeObjectURL(url);
    a.remove();
  };

  return (
    <div>
      <Navbar />
      <div className="flex min-h-screen flex-col items-center p-4 text-gray-900 dark:text-gray-100">
        {fileUrl && (
          <MediaViewer
            fileUrl={fileUrl}
            transcription={transcription}
            generateVTTCallback={generateVTT}
            onCueChange={handleCueChange}
            contentType={
              fileDetails?.content_type.startsWith("video/") ? "video" : "audio"
            }
          />
        )}
        {fileDetails && (
          <div className="my-4 w-full rounded-lg bg-white p-6 shadow-lg md:w-5/6 xl:w-1/2 dark:bg-gray-800">
            <h1 className="mb-4 text-xl font-bold">{fileDetails.filename}</h1>
            {!interactiveViewer && (
              <textarea
                readOnly
                value={getTranscriptionFormatted(transcription)}
                rows={10}
                className="h-80 w-full resize-none overflow-y-hidden rounded-lg border border-none bg-gray-100 p-2 font-mono text-gray-900 hover:overflow-y-auto dark:bg-gray-700 dark:text-gray-100"
              />
            )}
            {interactiveViewer && (
              <div
                className="relative h-80 w-full overflow-y-hidden rounded-lg border border-none bg-gray-100 p-2 hover:overflow-y-auto dark:bg-gray-700"
                id="transcription-container"
              >
                {transcription.map((segment, i) => (
                  <button
                    key={i}
                    id={`subtitle-${i}`}
                    className={`${i == currentSegment ? "border border-dashed bg-white dark:bg-gray-800" : "text-gray-900 dark:text-gray-100"} my-1 flex w-full flex-col items-start rounded-lg px-2 py-1 transition-colors duration-300 hover:bg-gray-200 dark:hover:bg-gray-600`}
                    onClick={() => handleCueClick(i)}
                  >
                    <div className="text-sm text-gray-300">
                      {formatTime(segment.start)} - {formatTime(segment.end)}
                    </div>
                    <div className="text-left">{segment.text}</div>
                  </button>
                ))}
              </div>
            )}

            {transcription && (
              <div className="mt-4 flex h-[42px] gap-5 text-gray-900 dark:text-gray-100">
                <button
                  onClick={() => setInteractiveViewer(!interactiveViewer)}
                  className="h-full w-full rounded-lg border border-gray-300 bg-gray-50 p-2 dark:border-gray-700 dark:bg-gray-700"
                >
                  {!interactiveViewer
                    ? t("set_interactive_viewer")
                    : t("set_raw_viewer")}
                </button>
                <div className="grid grid-cols-2 rounded-lg border border-gray-300 bg-gray-50 dark:border-gray-700 dark:bg-gray-700">
                  <select
                    id="format"
                    onChange={handleTranscriptionFormatChange}
                    className="dark:br-none h-full rounded-lg p-2 dark:bg-gray-700"
                  >
                    <option value="webvtt">WebVTT</option>
                    <option value="srt">SRT</option>
                    <option value="txt">{t("raw_text")}</option>
                  </select>
                  <button
                    onClick={downloadTranscription}
                    className="h-full w-full p-2"
                  >
                    {t("download")}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default JobPage;
