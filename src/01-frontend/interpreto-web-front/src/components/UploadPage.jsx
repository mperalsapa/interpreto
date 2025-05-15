import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLanguage } from "../i18n/LanguageContext";
import Navbar from "./Navbar";

const baseUrl = import.meta.env.VITE_BASE_URL;

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadPercent, setUploadPercent] = useState(0); // New state for upload percentage
  const navigate = useNavigate();
  const { t } = useLanguage();

  const handleUpload = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);
    setUploadPercent(0); // Reset upload percentage

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

  return (
    <div className="flex min-h-screen min-w-screen flex-col justify-center bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="mx-auto my-auto w-100 rounded-md bg-white p-6 shadow-md dark:bg-gray-800 dark:shadow-lg">
        <h2 className="mb-4 text-2xl font-semibold text-gray-800 dark:text-gray-100">
          {t("upload_audio_or_video")}
        </h2>
        <input
          type="file"
          accept="audio/*,video/*"
          className={`${uploading ? "hidden" : ""} mb-4 block w-full text-sm text-gray-600 file:mr-4 file:rounded-md file:border-0 file:bg-blue-50 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-blue-700 hover:file:bg-blue-100 dark:text-gray-300 dark:file:bg-gray-700 dark:file:text-gray-200 dark:hover:file:bg-gray-600`}
          onChange={(e) => {
            setFile(e.target.files[0]);
          }}
        />
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={`w-full rounded-md border-gray-300 bg-gray-50 p-2 text-gray-900 shadow-md dark:border-gray-800 dark:bg-gray-700 dark:text-gray-100 ${
            uploading || !file
              ? "cursor-not-allowed bg-gray-400 dark:bg-gray-600"
              : "bg-blue-600 hover:bg-blue-700 hover:bg-gray-200 dark:bg-blue-500 dark:hover:bg-blue-600"
          }`}
        >
          {uploading ? t("uploading") : t("upload")}
        </button>
        {uploading && (
          <div className="mt-8">
            <div class="progress-bar h-[10px] w-full bg-gray-100 dark:bg-gray-900">
              <span
                style={{ width: uploadPercent + "%" }}
                className="relative block h-full bg-blue-600 dark:bg-blue-500"
              >
                <span className="absolute right-[-1rem] bottom-[-100%] block aspect-square w-[2rem] content-center rounded-xl bg-orange-400 px-1 text-center">
                  {Math.trunc(uploadPercent)}
                </span>
                <span className="absolute right-[-2rem] bottom-[-75%] block text-lg dark:text-white">
                  %
                </span>
              </span>
            </div>
            {uploadPercent == 100 && (
              <p className="mt-5 dark:text-gray-100">
                {t("upload_complete_wait_a_moment")}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
