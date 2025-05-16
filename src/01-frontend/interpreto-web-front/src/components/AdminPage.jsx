import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import Navbar from "./Navbar";

export default function AdminPage() {
  const [files, setFiles] = useState([]);
  const [fetchedFiles, setFetchedFiles] = useState(false);
  const navigate = useNavigate();
  const baseUrl = import.meta.env.VITE_BASE_URL;

  useEffect(() => {
    // Fetch files from "/api/admin/files"
    // passing the administrator token in the headers
    const token = localStorage.getItem("administrator-token");
    if (!token) {
      navigate("/");
    }

    fetch(`${baseUrl}/api/admin/files`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    })
      .then((res) => {
        if (!res.ok) {
          navigate("/");
          return null;
        } else {
          return res.json();
        }
      })
      .then((data) => {
        setFiles(data);
        setFetchedFiles(true);
      });
  }, []);

  return (
    <div className="flex min-h-screen min-w-screen flex-col justify-center bg-gray-100 dark:bg-gray-900">
      <Navbar />
      <div className="mx-auto my-auto w-200 rounded-md bg-white p-6 shadow-md dark:bg-gray-800 dark:shadow-lg">
        <h1 className="mb-4 text-2xl font-semibold text-gray-800 dark:text-gray-100">
          Files
        </h1>
        <div className="relative h-80 w-full overflow-y-hidden rounded-lg border border-none bg-gray-100 p-2 hover:overflow-y-auto dark:bg-gray-700">
          {fetchedFiles &&
            files.map((file, i) => (
              <Link
                key={i}
                className="my-1 flex w-full flex-col items-start rounded-lg px-2 py-1 transition-colors duration-300 hover:bg-gray-200 dark:hover:bg-gray-600"
                to={`/file/${file._id}`}
              >
                <div className="text-sm text-gray-300">
                  {file.created_at}
                  {file.status == "completed" ? ` - ${file.completed_at}` : ""}
                </div>
                <div className="text-left text-gray-200">{file.filename}</div>
              </Link>
            ))}
        </div>
      </div>
    </div>
  );
}
