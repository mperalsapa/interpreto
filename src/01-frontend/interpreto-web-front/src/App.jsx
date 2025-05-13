// src/App.jsx
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import UploadPage from "./components/UploadPage";
import JobPage from "./components/JobPage";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/file/:file_id" element={<JobPage />} />
      </Routes>
    </Router>
  );
}
