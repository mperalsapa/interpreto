import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "./Navbar";

import MediaViewer from "./MediaViewer";

const baseUrl = import.meta.env.VITE_BASE_URL;

function JobPage() {
    const { file_id } = useParams();
    const [transcription, setTranscription] = useState([]);
    const [visibleTranscription, setVisibleTranscription] = useState(false);
    const [transcriptionFormat, setTranscriptionFormat] = useState("webvtt");
    const [fileDetails, setFileDetails] = useState(null);

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
            const es = new EventSource(`${baseUrl}/api/file/${file_id}/transcription/stream`);

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
        })

        return srt;
    }

    const generateVTT = (transcription) => {
        let vtt = "WEBVTT\n\n";
        transcription.forEach((segment, i) => {
            vtt += `${i + 1}\n${formatTime(segment.start)} --> ${formatTime(segment.end)}\n${segment.text}\n\n`;
        });
        return vtt;
    };

    const formatTime = (seconds, decimalSeparator = ".") => {
        const hrs = Math.floor(seconds / 3600).toString().padStart(2, "0");
        const mins = Math.floor((seconds % 3600) / 60).toString().padStart(2, "0");
        const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
        const ms = Math.floor((seconds % 1) * 1000).toString().padStart(3, "0");
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
    }

    const handleTranscriptionFormatChange = (e) => {
        setTranscriptionFormat(e.target.value);
    }


    const downloadTranscription = () => {
        console.log("Downloading transcription in format:", transcriptionFormat);

        const blob = new Blob([getTranscriptionFormatted(transcription)], { type: "text/plain" });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.style.display = "none";
        a.href = url;
        a.download = `${fileDetails.filename}_transcription.${transcriptionFormat}`;
        a.click();
        URL.revokeObjectURL(url);
        a.remove();

    }

    return (
        <div>
            <Navbar />
            <div className="p-4 text-gray-900 dark:text-gray-100 min-h-screen ">
                <div className="w-full md:w-3/4 xl:w-1/2 mx-auto">

                    {fileUrl && (
                        <MediaViewer
                            fileUrl={fileUrl}
                            transcription={transcription}
                            generateVTTCallback={generateVTT}
                        />
                    )}
                    {fileDetails && (
                        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg my-4">
                            <h1 className="text-xl font-bold mb-4">{fileDetails.filename}</h1>
                            <textarea
                                readOnly
                                value={getTranscriptionFormatted(transcription)}
                                rows={10}
                                className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-mono"
                            />

                            {transcription && (<div className="mt-4 h-[42px] flex">
                                <label htmlFor="format" className=" h-full p-2 pl-3 border border-gray-300 dark:border-gray-700 rounded-lg rounded-r-none bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 ">Format</label>
                                <select
                                    id="format"
                                    onChange={handleTranscriptionFormatChange}
                                    className="h-full p-2 border border-gray-300 dark:border-gray-700 rounded-lg rounded-l-none bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                                >
                                    <option value="webvtt">WebVTT</option>
                                    <option value="srt">SRT</option>
                                    <option value="txt">Raw text</option>
                                </select>

                                <button onClick={downloadTranscription} className="h-full p-2 w-full ml-5 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100">
                                    Download
                                </button>
                            </div>)}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default JobPage;
