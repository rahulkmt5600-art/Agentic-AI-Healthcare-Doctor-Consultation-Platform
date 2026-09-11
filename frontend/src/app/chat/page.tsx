"use client";

import { useState, useRef, useEffect } from "react";

type Message = {
  sender: "patient" | "ai";
  text: string;
};

export default function ChatPage() {
  const [sessionId] = useState(() => `session-${Date.now()}`);

  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "ai",
      text: "Hi, I'm MediBridge AI. Tell me what symptoms you're experiencing, and I'll ask a few questions to help point you toward the right kind of doctor.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("gathering");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Automatically scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();

    // Show patient message
    setMessages((prev) => [
      ...prev,
      {
        sender: "patient",
        text: userMessage,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const token = localStorage.getItem("token");

      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",

        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },

        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
        }),
      });

      // Unauthorized
      if (response.status === 401) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: "Please log in to use the health assistant.",
          },
        ]);

        return;
      }

      // Not a patient
      if (response.status === 403) {
        setMessages((prev) => [
          ...prev,
          {
            sender: "ai",
            text: "Only patient accounts can use the health assistant.",
          },
        ]);

        return;
      }

      // Other errors
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();

      // Show AI response
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: data.reply,
        },
      ]);

      // Update stage
      setStage(data.stage);

    } catch (error) {
      console.error("Chat error:", error);

      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "Sorry, something went wrong connecting to the assistant.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Enter key handler
  const handleKeyPress = (
    e: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4">

      <div className="w-full max-w-2xl flex flex-col h-[85vh] border rounded-lg shadow-sm">

        {/* HEADER */}
        <div className="p-4 border-b">

          <h1 className="text-xl font-bold">
            MediBridge AI Health Assistant
          </h1>

          <p className="text-sm text-gray-500">
            Preliminary guidance only, not a substitute for a real doctor.
          </p>

        </div>


        {/* CHAT MESSAGES */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">

          {messages.map((msg, idx) => (

            <div
              key={idx}
              className={`max-w-[80%] px-4 py-2 rounded-lg whitespace-pre-wrap ${
                msg.sender === "patient"
                  ? "bg-blue-600 text-white self-end"
                  : "bg-gray-100 text-gray-900 self-start"
              }`}
            >
              {msg.text}
            </div>

          ))}


          {/* LOADING */}
          {loading && (

            <div className="bg-gray-100 text-gray-500 self-start px-4 py-2 rounded-lg">
              Thinking...
            </div>

          )}


          <div ref={messagesEndRef} />

        </div>


        {/* BOTTOM SECTION */}

        {stage === "done" ? (

          /* ASSESSMENT COMPLETE */

          <div className="p-4 border-t bg-green-50">

            <p className="text-green-700 font-semibold mb-2">
              Assessment complete
            </p>

            <a
              href={`/book/${sessionId}`}
              className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700 inline-block text-center"
            >
              Find a Doctor and Book
            </a>

          </div>

        ) : (

          /* INPUT */

          <div className="p-4 border-t flex gap-2">

            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Describe your symptoms..."
              className="flex-1 border rounded px-3 py-2"
              disabled={loading}
            />

            <button
              onClick={sendMessage}
              disabled={loading}
              className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "Sending..." : "Send"}
            </button>

          </div>

        )}

      </div>

    </main>
  );
}