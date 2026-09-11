"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

type Message = {
  sender: string;
  content: string;
  created_at: string;
};

type ConversationDetail = {
  id: number;
  session_id: string;
  patient_name: string;
  stage: string;
  created_at: string;
  messages: Message[];
};

export default function ConversationDetailPage() {
  const params = useParams();
  const conversationId = params.id;

  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      const token = localStorage.getItem("token");

      try {
        const response = await fetch(
          `http://localhost:8000/doctor/conversations/${conversationId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        if (response.status === 401) {
          setError("Please log in to view this page.");
          return;
        }
        if (response.status === 403) {
          setError("Only doctor accounts can access this page.");
          return;
        }
        if (response.status === 404) {
          setError("Conversation not found.");
          return;
        }

        const data = await response.json();
        setConversation(data);
      } catch (err) {
        setError("Could not load conversation.");
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [conversationId]);

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <Link href="/doctor" className="text-blue-600 hover:underline text-sm">
          ← Back to all conversations
        </Link>

        {loading && <p className="text-gray-500 mt-4">Loading...</p>}
        {error && <p className="text-red-600 mt-4">{error}</p>}

        {conversation && (
          <>
            <div className="mt-4 mb-6">
              <h1 className="text-2xl font-bold">{conversation.patient_name}</h1>
              <p className="text-sm text-gray-500">
                {new Date(conversation.created_at).toLocaleString()} — Status: {conversation.stage}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              {conversation.messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`max-w-[80%] px-4 py-2 rounded-lg whitespace-pre-wrap ${
                    msg.sender === "patient"
                      ? "bg-blue-600 text-white self-end ml-auto"
                      : "bg-gray-100 text-gray-900 self-start"
                  }`}
                >
                  {msg.content}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}