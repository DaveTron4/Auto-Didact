"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState("");
  const [context, setContext] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus("");
      setVideoUrl("");
    }
  };

  const uploadPDF = async () => {
    if (!file) {
      setStatus("Please select a PDF file first");
      return;
    }

    setIsLoading(true);
    setStatus("Uploading and processing PDF...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch("http://localhost:8000/test-ingest", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        setStatus(`✓ Success! Uploaded ${data.chunks_uploaded} chunks to vector database.`);
      } else {
        setStatus(`✗ Error: ${data.detail || "Upload failed"}`);
      }
    } catch (error) {
      setStatus("✗ Error: Backend is unreachable!");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateVideo = async () => {
    if (!context.trim()) {
      setStatus("Please enter some context text for video generation");
      return;
    }

    setIsLoading(true);
    setStatus("Generating video script...");
    setVideoUrl("");

    try {
      const res = await fetch("http://localhost:8000/generate-video", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          context: context,
          title: "Auto-Didact Video",
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus(`✓ Video generated successfully!`);
        setVideoUrl(data.video_path);
      } else {
        setStatus(`✗ Error: ${data.detail || "Video generation failed"}`);
      }
    } catch (error) {
      setStatus("✗ Error: Backend is unreachable!");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const checkBackend = async () => {
    try {
      const res = await fetch("http://localhost:8000/");
      const data = await res.json();
      setStatus(`✓ ${data.status}`);
    } catch (error) {
      setStatus("✗ Error: Backend is unreachable!");
      console.error(error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            🎥 Auto-Didact
          </h1>
          <p className="text-gray-400 text-lg">Transform PDFs into Educational Videos</p>
          <button
            onClick={checkBackend}
            className="mt-4 text-sm text-gray-500 hover:text-gray-300 underline"
          >
            Test Backend Connection
          </button>
        </div>

        {/* Status Message */}
        {status && (
          <div className={`mb-8 p-4 rounded-lg border ${
            status.startsWith("✓") 
              ? "bg-green-900/20 border-green-500/50 text-green-400" 
              : status.startsWith("✗")
              ? "bg-red-900/20 border-red-500/50 text-red-400"
              : "bg-blue-900/20 border-blue-500/50 text-blue-400"
          }`}>
            <p className="font-mono text-sm">{status}</p>
          </div>
        )}

        {/* PDF Upload Section */}
        <div className="bg-gray-800 rounded-xl p-8 mb-8 border border-gray-700">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            <span className="mr-2">📄</span> Step 1: Upload PDF
          </h2>
          <p className="text-gray-400 mb-6">
            Upload a PDF document to ingest into the vector database for retrieval.
          </p>
          
          <div className="flex flex-col gap-4">
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-400
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-600 file:text-white
                hover:file:bg-blue-500 file:cursor-pointer
                cursor-pointer"
            />
            
            {file && (
              <p className="text-sm text-gray-500">
                Selected: <span className="text-white">{file.name}</span>
              </p>
            )}

            <button
              onClick={uploadPDF}
              disabled={!file || isLoading}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Processing..." : "Upload & Process PDF"}
            </button>
          </div>
        </div>

        {/* Video Generation Section */}
        <div className="bg-gray-800 rounded-xl p-8 border border-gray-700">
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            <span className="mr-2">🎬</span> Step 2: Generate Video
          </h2>
          <p className="text-gray-400 mb-6">
            Enter text context or use the uploaded PDF content to generate an educational video.
          </p>
          
          <div className="flex flex-col gap-4">
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Enter context for video generation (e.g., 'Photosynthesis is the process by which plants convert sunlight into energy...')"
              rows={6}
              className="w-full p-4 bg-gray-900 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />

            <button
              onClick={generateVideo}
              disabled={!context.trim() || isLoading}
              className="px-6 py-3 bg-purple-600 hover:bg-purple-500 rounded-lg font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Generating Video..." : "Generate Video"}
            </button>

            {videoUrl && (
              <div className="mt-4 p-4 bg-gray-900 rounded-lg border border-green-500/50">
                <p className="text-green-400 mb-2">Video saved to:</p>
                <code className="text-sm text-gray-300 break-all">{videoUrl}</code>
              </div>
            )}
          </div>
        </div>

        {/* Loading Indicator */}
        {isLoading && (
          <div className="mt-8 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-3 text-gray-400">Processing...</span>
          </div>
        )}
      </div>
    </div>
  );
}