import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MediaViewer from "./MediaViewer";

const baseUrl = import.meta.env.VITE_BASE_URL;

export default function UploadPage() {
    const [file, setFile] = useState(null);
    const [jobId, setJobId] = useState(null);
    const [fileUrl, setFileUrl] = useState(null);
    const [contentType, setContentType] = useState("");
    const [uploading, setUploading] = useState(false);
    const navigate = useNavigate();

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        setUploading(true);

        // Mostrar el fichero localmente mientras se sube
        setFileUrl(URL.createObjectURL(file));
        setContentType(file.type);

        try {
            const res = await fetch(`${baseUrl}/api/upload`, {
                method: "POST",
                body: formData,
            });

            const data = await res.json();

            if (res.status === 200) {
                if (data.state === "existing" || data.state === "uploaded") {
                    // Si el archivo ya existe, redirigimos al job correspondiente
                    setJobId(data.job_id);
                    navigate(`/job/${data.job_id}`);
                }
            } else {
                console.error("Error en la carga:", data.message);
                alert(data.message || "Hubo un error al subir el archivo.");
            }
        } catch (error) {
            console.error("Error al contactar con el servidor:", error);
            alert("Hubo un error al procesar el archivo.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div style={{ padding: 20 }}>
            <h2>Sube un archivo de audio o video</h2>
            <input
                type="file"
                accept="audio/*,video/*"
                onChange={(e) => {
                    setFile(e.target.files[0]);
                }}
            />
            <button onClick={handleUpload} disabled={!file || uploading}>
                {uploading ? "Subiendo..." : "Enviar"}
            </button>
            {uploading && <progress value={uploading ? 100 : 0} max="100" />}
            {fileUrl && <MediaViewer fileUrl={fileUrl} contentType={contentType} />}
        </div>
    );
}
