"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type ConversationSummary = {
  id: number;
  session_id: string;
  patient_name: string;
  stage: string;
  created_at: string;
};

type Slot = {
  id: number;
  start_time: string;
  is_booked: boolean;
};

export default function DoctorDashboard() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [slots, setSlots] = useState<Slot[]>([]);
  const [qualifications, setQualifications] = useState("");
  const [newSlotDate, setNewSlotDate] = useState("");
  const [newSlotTime, setNewSlotTime] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [addingSlot, setAddingSlot] = useState(false);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const fetchData = async () => {
    try {
      const [convRes, slotsRes] = await Promise.all([
        fetch("http://localhost:8000/doctor/conversations", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://localhost:8000/doctor/slots", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (convRes.status === 401 || slotsRes.status === 401) {
        setError("Please log in to view this page.");
        return;
      }
      if (convRes.status === 403 || slotsRes.status === 403) {
        setError("Only doctor accounts can access this dashboard.");
        return;
      }

      setConversations(await convRes.json());
      setSlots(await slotsRes.json());
    } catch (err) {
      setError("Could not load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSaveQualifications = async () => {
    if (!qualifications.trim()) return;
    setSavingProfile(true);
    try {
      const response = await fetch("http://localhost:8000/doctor/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ qualifications }),
      });
      if (response.ok) {
        alert("Qualifications updated!");
        setQualifications("");
      } else {
        alert("Could not update qualifications.");
      }
    } catch (err) {
      alert("Something went wrong.");
    } finally {
      setSavingProfile(false);
    }
  };

  const handleAddSlot = async () => {
    if (!newSlotDate || !newSlotTime) {
      alert("Please pick both a date and a time.");
      return;
    }
    setAddingSlot(true);
    try {
      const startTime = `${newSlotDate}T${newSlotTime}:00`;
      const response = await fetch("http://localhost:8000/doctor/slots", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ start_time: startTime }),
      });
      if (response.ok) {
        setNewSlotDate("");
        setNewSlotTime("");
        fetchData();
      } else {
        alert("Could not add this slot.");
      }
    } catch (err) {
      alert("Something went wrong.");
    } finally {
      setAddingSlot(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-3xl mx-auto">
        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && !error && (
          <>
            {/* Profile Section */}
            <h1 className="text-2xl font-bold mb-4">My Profile</h1>
            <div className="border rounded-lg p-4 mb-10 flex flex-col gap-3">
              <div>
                <label className="text-sm font-medium block mb-1">Update Qualifications</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={qualifications}
                    onChange={(e) => setQualifications(e.target.value)}
                    placeholder="e.g. MBBS, MD (Cardiology)"
                    className="flex-1 border rounded px-3 py-2"
                  />
                  <button
                    onClick={handleSaveQualifications}
                    disabled={savingProfile}
                    className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700 disabled:opacity-50"
                  >
                    Save
                  </button>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium block mb-1">Add Available Time Slot</label>
                <div className="flex gap-2">
                  <input
                    type="date"
                    value={newSlotDate}
                    onChange={(e) => setNewSlotDate(e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <input
                    type="time"
                    value={newSlotTime}
                    onChange={(e) => setNewSlotTime(e.target.value)}
                    className="border rounded px-3 py-2"
                  />
                  <button
                    onClick={handleAddSlot}
                    disabled={addingSlot}
                    className="bg-green-600 text-white rounded px-4 py-2 hover:bg-green-700 disabled:opacity-50"
                  >
                    Add Slot
                  </button>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium mb-1">Your Slots</p>
                {slots.length === 0 ? (
                  <p className="text-sm text-gray-500">No slots added yet.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {slots.map((slot) => (
                      <span
                        key={slot.id}
                        className={`text-sm px-3 py-1 rounded-full ${
                          slot.is_booked
                            ? "bg-gray-200 text-gray-500 line-through"
                            : "bg-blue-100 text-blue-700"
                        }`}
                      >
                        {new Date(slot.start_time).toLocaleString()}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Conversations Section */}
            <h1 className="text-2xl font-bold mb-4">All Patient Conversations</h1>
            <div className="flex flex-col gap-3">
              {conversations.map((conv) => (
                <Link
                  key={conv.id}
                  href={`/doctor/${conv.id}`}
                  className="border rounded-lg p-4 hover:bg-gray-50 flex justify-between items-center"
                >
                  <div>
                    <p className="font-semibold">{conv.patient_name}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(conv.created_at).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`text-sm px-3 py-1 rounded-full font-medium ${
                      conv.stage === "done"
                        ? "bg-green-100 text-green-700"
                        : "bg-yellow-100 text-yellow-700"
                    }`}
                  >
                    {conv.stage === "done" ? "Completed" : "In progress"}
                  </span>
                </Link>
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}