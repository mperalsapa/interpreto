// src/components/MediaViewer.jsx
import React, { useEffect, useState } from "react";

export default function MediaViewer({ fileUrl, contentType, transcription }) {
    const [vttUrl, setVttUrl] = useState(null);

    useEffect(() => {
        if (contentType.startsWith("video/") && transcription && transcription.length) {
            // Generar WebVTT solo si transcription está disponible
            let vtt = generateVTT(transcription)
            setVttUrl(vtt);
        }
    }, [contentType, transcription]);

    const generateVTT = (transcription) => {
        let vtt = "WEBVTT\n\n";
        transcription.forEach((segment, i) => {
            console.log(transcription[i]);
            vtt += `${i + 1}\n${formatTime(segment.start)} --> ${formatTime(segment.end)}\n${segment.text}\n\n`;
        });
        return URL.createObjectURL(new Blob([vtt], { type: "text/vtt" }));
    };

    const formatTime = (seconds) => {
        const hrs = Math.floor(seconds / 3600).toString().padStart(2, "0");
        const mins = Math.floor((seconds % 3600) / 60).toString().padStart(2, "0");
        const secs = Math.floor(seconds % 60).toString().padStart(2, "0");
        const ms = Math.floor((seconds % 1) * 1000).toString().padStart(3, "0");
        return `${hrs}:${mins}:${secs}.${ms}`;
    };

    return (
        <div>
            {/* Mostrar el archivo solo si existe */}
            {fileUrl && (contentType.startsWith("video/") ? (
                <video controls width="100%">
                    <source src={fileUrl} />
                    {vttUrl && <track src={vttUrl} kind="subtitles" default />}
                </video>
            ) : (
                <audio controls>
                    <source src={fileUrl} />
                </audio>
            ))}

            {/* Mostrar la transcripción solo si existe */}
            {transcription && transcription.length > 0 && (
                <div style={{ marginTop: 20 }}>
                    <h3>Transcripción</h3>
                    <textarea
                        readOnly
                        value={transcription.map((l) => l.text).join("\n")}
                        rows={10}
                        style={{ width: "100%", fontFamily: "monospace" }}
                    />
                </div>
            )}
        </div>
    );
}

