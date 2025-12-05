"use client";
import { useState } from "react";

export default function Home() {
  const [message, setMessage] = useState("");

  const checkBackend = async () => {
    try {
      // Trying to talk to our FastAPI backend
      const res = await fetch("http://localhost:8000/");
      const data = await res.json();
      setMessage(data.status);
    } catch (error) {
      setMessage("Error: Backend is unreachable!");
      console.error(error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-8">Auto-Didact V1</h1>
      <button
        onClick={checkBackend}
        className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-semibold transition"
      >
        Ping Backend
      </button>
      
      {/* If we get a message, show it here */}
      {message && (
        <div className="mt-8 p-4 bg-gray-800 rounded border border-gray-700">
          <p className="text-green-400 font-mono">{message}</p>
        </div>
      )}
    </div>
  );
}