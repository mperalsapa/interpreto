import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import MediaViewer from "./MediaViewer";

const baseUrl = import.meta.env.VITE_BASE_URL;

function JobPage() {
    const { job_id } = useParams();
    const [transcription, setTranscription] = useState([]);
    const [fileType, setFileType] = useState("video");
    const [fileUrl, setFileUrl] = useState(`${baseUrl}/media/${job_id}`);

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

    return (
        <div className="p-4">
            <h1 className="text-xl font-bold mb-4">Trabajo {job_id}</h1>
            {fileUrl && (
                <MediaViewer
                    fileUrl={fileUrl}
                    contentType={"video/mp4"}
                    transcription={transcription}
                />
            )}
            {/* {fileUrl && (
                fileType === "video" ? (
                    <video controls width="100%">
                        <source src={fileUrl} />
                        <track src={generateVTT()} kind="subtitles" default />
                    </video>
                ) : (
                    <audio controls>
                        <source src={fileUrl} />
                    </audio>
                )
            )} */}
        </div>
    );
}

export default JobPage;
