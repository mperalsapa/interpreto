// src/components/MediaViewer.jsx
import React, { useEffect, useState } from "react";

export default function MediaViewer({ fileUrl, transcription, generateVTTCallback }) {
    const [vttUrl, setVttUrl] = useState(null);

    useEffect(() => {
        if (transcription && transcription.length) {
            let vtt = generateVTTCallback(transcription);
            setVttUrl(URL.createObjectURL(new Blob([vtt], { type: "text/vtt" })));
        }
    }, [transcription]);

    return (
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
            {fileUrl && (
                <video controls className="w-full rounded-lg">
                    <source src={fileUrl} />
                    {vttUrl && <track src={vttUrl} kind="subtitles" default />}
                </video>)
            }
        </div >
    )
}

