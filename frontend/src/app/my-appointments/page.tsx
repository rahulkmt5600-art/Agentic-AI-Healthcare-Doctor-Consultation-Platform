"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type MyBooking = {
  id: number;
  doctor_name: string;
  specialty: string | null;
  slot_time: string;
  status: string;
  created_at: string;
};

export default function MyAppointmentsPage() {
  const [appointments, setAppointments] = useState<MyBooking[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAppointments = async () => {
      const token = localStorage.getItem("token");
      try {
        const response = await fetch("http://localhost:8000/my-appointments", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          setError("Please log in to view this page.");
          return;
        }
        if (response.status === 403) {
          setError("Only patient accounts can view appointments.");
          return;
        }

        setAppointments(await response.json());
      } catch (err) {
        setError("Could not load your appointments.");
      } finally {
        setLoading(false);
      }
    };

    fetchAppointments();
  }, []);

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-2xl mx-auto">
        <Link href="/" className="text-blue-600 hover:underline text-sm">
          Back home
        </Link>

        <h1 className="text-2xl font-bold mt-4 mb-6">My Appointments</h1>

        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && !error && appointments.length === 0 && (
          <p className="text-gray-500">You have no booked appointments yet.</p>
        )}

        <div className="flex flex-col gap-3">
          {appointments.map((appt) => (
            <div key={appt.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-semibold text-lg">{appt.doctor_name}</p>
                  {appt.specialty && (
                    <p className="text-sm text-gray-500">{appt.specialty}</p>
                  )}
                </div>
                <span className="text-sm px-3 py-1 rounded-full font-medium bg-green-100 text-green-700">
                  {appt.status}
                </span>
              </div>
              <p className="text-sm text-gray-700">
                Appointment time: {new Date(appt.slot_time).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}