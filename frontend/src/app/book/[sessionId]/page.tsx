"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

type Slot = {
  id: number;
  start_time: string;
  is_booked: boolean;
};

type Doctor = {
  doctor_id: number;
  name: string;
  specialty: string | null;
  qualifications: string | null;
  is_verified: boolean;
  available_slots: Slot[];
};

export default function BookAppointmentPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.sessionId as string;

  const [specialty, setSpecialty] = useState("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(false);
  const [booking, setBooking] = useState(false);

  const searchDoctors = async () => {
    setLoading(true);
    const token = localStorage.getItem("token");
    try {
      const url = specialty
        ? `http://localhost:8000/doctors/search?specialty=${encodeURIComponent(specialty)}`
        : `http://localhost:8000/doctors/search`;

      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json();
      setDoctors(data);
    } catch (err) {
      alert("Could not load doctors.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    searchDoctors();
  }, []);

  const handleBook = async (doctorId: number, slotId: number) => {
    setBooking(true);
    const token = localStorage.getItem("token");
    try {
      const response = await fetch("http://localhost:8000/appointments/book", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          session_id: sessionId,
          doctor_id: doctorId,
          slot_id: slotId,
        }),
      });

      if (response.ok) {
        alert("Appointment booked successfully!");
        router.push("/my-appointments");
      } else {
        const data = await response.json();
        alert(data.detail || "Could not book this slot.");
        searchDoctors(); // refresh in case slot was taken
      }
    } catch (err) {
      alert("Something went wrong.");
    } finally {
      setBooking(false);
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Find a Doctor</h1>

        <div className="flex gap-2 mb-6">
          <input
            type="text"
            value={specialty}
            onChange={(e) => setSpecialty(e.target.value)}
            placeholder="Filter by specialty (e.g. Cardiologist)"
            className="flex-1 border rounded px-3 py-2"
          />
          <button
            onClick={searchDoctors}
            className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700"
          >
            Search
          </button>
        </div>

        {loading && <p className="text-gray-500">Loading doctors...</p>}

        {!loading && doctors.length === 0 && (
          <p className="text-gray-500">No doctors found for this specialty.</p>
        )}

        <div className="flex flex-col gap-4">
          {doctors.map((doc) => (
            <div key={doc.doctor_id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-semibold text-lg">{doc.name}</p>
                  <p className="text-sm text-gray-600">{doc.specialty}</p>
                  {doc.qualifications && (
                    <p className="text-sm text-gray-500">{doc.qualifications}</p>
                  )}
                </div>
                {doc.is_verified && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                    ✓ Verified
                  </span>
                )}
              </div>

              {doc.available_slots.length === 0 ? (
                <p className="text-sm text-gray-400 mt-2">No open slots right now.</p>
              ) : (
                <div className="flex flex-wrap gap-2 mt-3">
                  {doc.available_slots.map((slot) => (
                    <button
                      key={slot.id}
                      disabled={booking}
                      onClick={() => handleBook(doc.doctor_id, slot.id)}
                      className="text-sm border border-blue-600 text-blue-600 rounded px-3 py-1 hover:bg-blue-600 hover:text-white disabled:opacity-50"
                    >
                      {new Date(slot.start_time).toLocaleString()}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}