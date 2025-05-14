import { useState } from "react";
import { useNavigate } from "react-router-dom";
import MediaViewer from "./MediaViewer";
import Navbar from "./Navbar";

const baseUrl = import.meta.env.VITE_BASE_URL;

export default function UploadPage() {
    const [file, setFile] = useState(null);
    const [fileUrl, setFileUrl] = useState(null);
    const [contentType, setContentType] = useState("");
    const [uploading, setUploading] = useState(false);
    const [uploadPercent, setUploadPercent] = useState(0); // New state for upload percentage
    const navigate = useNavigate();

    const handleUpload = async () => {
        if (!file) return;
        const formData = new FormData();
        formData.append("file", file);
        setUploading(true);
        setUploadPercent(0); // Reset upload percentage

        // Mostrar el fichero localmente mientras se sube
        setFileUrl(URL.createObjectURL(file));
        setContentType(file.type);

        try {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", `${baseUrl}/api/upload`, true);

            // Track upload progress
            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    const percent = Math.round((event.loaded / event.total) * 100);
                    setUploadPercent(percent);
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    const data = JSON.parse(xhr.responseText);
                    if (data.state === "existing" || data.state === "uploaded") {
                        navigate(`/file/${data.file_id}`);
                    }
                } else {
                    const data = JSON.parse(xhr.responseText);
                    console.error("Error en la carga:", data.message);
                    alert(data.message || "Hubo un error al subir el archivo.");
                }
            };

            xhr.onerror = () => {
                console.error("Error al contactar con el servidor.");
                alert("Hubo un error al procesar el archivo.");
            };

            xhr.onloadend = () => {
                setUploading(false);
            };

            xhr.send(formData);
        } catch (error) {
            console.error("Error al contactar con el servidor:", error);
            alert("Hubo un error al procesar el archivo.");
            setUploading(false);
        }
    };


    const testUpload = async () => {
        // this function is for ui testing purposes only, does not upload nothing
        // loop from 1 to 100% in 10 seconds
        setUploading(true);
        for (let i = 0; i <= 100; i++) {
            setTimeout(() => {
                setUploadPercent(i);
            }, i * 100);
        }

        setTimeout(() => {
            // setUploading(false);
            setUploadPercent(50);
        }, 10001);
    }

    const handleTestUpload = (e) => {
        const value = e.target.value;

        if (value == 0 || value == 100) {
            setUploading(false)
        } else {
            setUploading(true)
            setUploadPercent(value);
        }

    }

    return (
        <div className="min-w-screen min-h-screen bg-gray-100 dark:bg-gray-900 flex flex-col justify-center">
            <Navbar />


            <div className="p-6 max-w-lg mx-auto my-auto bg-white shadow-md rounded-md dark:bg-gray-800 dark:shadow-lg s">
                <h2 className="text-2xl font-semibold text-gray-800 mb-4 dark:text-gray-100">
                    Upload a video or audio file
                </h2>
                <input
                    type="file"
                    accept="audio/*,video/*"
                    className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 mb-4 dark:text-gray-300 dark:file:bg-gray-700 dark:file:text-gray-200 dark:hover:file:bg-gray-600"
                    onChange={(e) => {
                        setFile(e.target.files[0]);
                    }}
                />
                <button
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    className={`w-full py-2 px-4 text-white font-semibold rounded-md ${uploading || !file
                        ? "bg-gray-400 cursor-not-allowed dark:bg-gray-600"
                        : "bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600"
                        }`}
                >
                    {uploading ? "Subiendo..." : "Enviar"}
                </button>
                {uploading && (
                    <div className="mt-8">
                        {/* <input className="w-full" type="range" min="0" max="0" step="0.1" value={uploadPercent} /> */}
                        <div class="progress-bar w-full h-[10px] bg-gray-100 dark:bg-gray-900">

                            <span style={{ width: uploadPercent + "%" }} className="h-full block bg-blue-600 dark:bg-blue-500 relative">
                                <span className="block absolute right-[-1rem] bottom-[-100%] px-1 text-center content-center aspect-square w-[2rem] rounded-xl bg-orange-400">{Math.trunc(uploadPercent)}</span>
                                <span className="block absolute right-[-2rem] bottom-[-75%] dark:text-white text-lg">%</span>
                            </span>
                        </div>
                    </div>
                )}

                {/* <input onChange={handleTestUpload} class="w-full mt-5" type="range" name="" id="" min="0" max="100" step="0.1" /> */}
            </div>
        </div>
    );
}
