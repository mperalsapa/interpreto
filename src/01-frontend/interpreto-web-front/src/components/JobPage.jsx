import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Navbar from "./Navbar";

import MediaViewer from "./MediaViewer";

const baseUrl = import.meta.env.VITE_BASE_URL;

function JobPage() {
    const { job_id } = useParams();
    const [transcription, setTranscription] = useState([]);
    const [visibleTranscription, setVisibleTranscription] = useState(false);
    const [transcriptionFormat, setTranscriptionFormat] = useState("webvtt");

    const fileUrl = `${baseUrl}/media/${job_id}`;

    useEffect(() => {
        const es = new EventSource(`${baseUrl}/api/job/${job_id}`);

        es.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                if (data.state === "transcribed_segment") {
                    setTranscription((prev) => [...prev, data["message"]]);
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
    }, [job_id]);

    const generateSRT = (transcription) => {
        let srt = "";
        transcription.forEach((segment, i) => {
            srt += `${i + 1}\n`;
            srt += `${formatTime(segment.start, ",")} --> ${formatTime(segment.end, ".")}\n`;
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


    const toggleTranscriptionVisibility = () => {
        setVisibleTranscription(!visibleTranscription);
    }

    return (
        <div>
            <Navbar />
            <div className="p-4 text-gray-900 dark:text-gray-100 min-h-screen ">
                <div className="w-full md:w-3/4 xl:w-1/2 mx-auto">
                    <h1 className="text-xl font-bold mb-4">Trabajo {job_id}</h1>
                    {fileUrl && (
                        <MediaViewer
                            fileUrl={fileUrl}
                            transcription={transcription}
                            generateVTTCallback={generateVTT}
                        />
                    )}
                    {transcription && transcription.length > 0 && visibleTranscription && (
                        <div className="mt-6">
                            <hr className="my-4 border-gray-300 dark:border-gray-700" />
                            <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Transcription</h3>
                            <textarea
                                readOnly
                                value={getTranscriptionFormatted(transcription)}
                                rows={10}
                                className="w-full p-3 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-mono"
                            />
                            <div className="mt-4 flex items-center space-x-4">
                                <label htmlFor="format" className="text-gray-700 dark:text-gray-300 font-medium">Format:</label>
                                <select
                                    id="format"
                                    onChange={handleTranscriptionFormatChange}
                                    className="p-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                                >
                                    <option value="webvtt">WebVTT</option>
                                    <option value="srt">SRT</option>
                                    <option value="txt">Raw text</option>
                                </select>
                            </div>
                        </div>
                    )
                    }
                    <hr className="my-4 border-gray-300 dark:border-gray-700" />
                    <button
                        onClick={toggleTranscriptionVisibility}
                        className={`w-full py-3 px-5 text-white font-semibold rounded-lg mt-3 transition-colors duration-300 ${transcription
                            ? "bg-gray-400 cursor-not-allowed dark:bg-gray-600"
                            : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                            }`}
                    >
                        {visibleTranscription ? "Hide transcription" : "Show transcription"}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default JobPage;
