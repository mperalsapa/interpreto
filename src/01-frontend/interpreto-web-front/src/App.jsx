import { useState } from "react";
const baseUrl = import.meta.env.VITE_BASE_URL

function App() {
  const [file, setFile] = useState(null);
  const [response, setResponse] = useState("");
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setResponse("");
    const res = await fetch(`${baseUrl}/upload`, {
      method: "POST",
      body: formData,
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.replace("data: ", "").trim();
          setResponse(prev => prev + "\n" + data);
        }
      }
    }

    setUploading(false);
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Sube un archivo de audio o video</h2>
      <input
        type="file"
        accept="audio/*,video/*"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <button onClick={handleUpload} disabled={!file || uploading}>
        {uploading ? "Subiendo..." : "Enviar"}
      </button>

      <pre style={{ marginTop: 20 }}>{response}</pre>
    </div>
  );
}

export default App;
