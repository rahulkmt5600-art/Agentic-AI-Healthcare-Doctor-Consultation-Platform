"use client";

import { useEffect, useState } from "react";

type AdminUser = {
  id: number;
  name: string;
  email: string;
  role: string;
};

type AdminDoctor = {
  doctor_id: number;
  user_id: number;
  name: string;
  email: string;
  specialty: string | null;
  qualifications: string | null;
  is_verified: boolean;
};

export default function AdminDashboard() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [doctors, setDoctors] = useState<AdminDoctor[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

  const fetchData = async () => {
    try {
      const [usersRes, doctorsRes] = await Promise.all([
        fetch("http://localhost:8000/admin/users", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("http://localhost:8000/admin/doctors", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (usersRes.status === 401 || doctorsRes.status === 401) {
        setError("Please log in to view this page.");
        return;
      }
      if (usersRes.status === 403 || doctorsRes.status === 403) {
        setError("Only admin accounts can access this dashboard.");
        return;
      }

      setUsers(await usersRes.json());
      setDoctors(await doctorsRes.json());
    } catch (err) {
      setError("Could not load admin data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleVerify = async (doctorId: number) => {
    try {
      const response = await fetch(
        `http://localhost:8000/admin/doctors/${doctorId}/verify`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (response.ok) {
        fetchData();
      } else {
        alert("Could not verify this doctor.");
      }
    } catch (err) {
      alert("Something went wrong.");
    }
  };

  const handleDelete = async (userId: number, name: string) => {
    if (!confirm(`Are you sure you want to delete ${name}? This cannot be undone.`)) return;

    try {
      const response = await fetch(`http://localhost:8000/admin/users/${userId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        fetchData();
      } else {
        const data = await response.json();
        alert(data.detail || "Could not delete this user.");
      }
    } catch (err) {
      alert("Something went wrong.");
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-3xl mx-auto">
        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        {!loading && !error && (
          <>
            <h1 className="text-2xl font-bold mb-4">Doctor Verification</h1>
            <div className="flex flex-col gap-3 mb-10">
              {doctors.map((doc) => (
                <div key={doc.doctor_id} className="border rounded-lg p-4 flex justify-between items-center">
                  <div>
                    <p className="font-semibold">{doc.name}</p>
                    <p className="text-sm text-gray-500">{doc.email}</p>
                    <p className="text-sm text-gray-600">{doc.specialty} — {doc.qualifications}</p>
                  </div>
                  {doc.is_verified ? (
                    <span className="text-sm bg-green-100 text-green-700 px-3 py-1 rounded-full">
                      Verified
                    </span>
                  ) : (
                    <button
                      onClick={() => handleVerify(doc.doctor_id)}
                      className="bg-blue-600 text-white rounded px-4 py-2 hover:bg-blue-700"
                    >
                      Verify
                    </button>
                  )}
                </div>
              ))}
            </div>

            <h1 className="text-2xl font-bold mb-4">All Users</h1>
            <div className="flex flex-col gap-2">
              {users.map((u) => (
                <div key={u.id} className="border rounded-lg p-3 flex justify-between items-center">
                  <div>
                    <p className="font-medium">{u.name} <span className="text-xs text-gray-400">({u.role})</span></p>
                    <p className="text-sm text-gray-500">{u.email}</p>
                  </div>
                  {u.role !== "admin" && (
                    <button
                      onClick={() => handleDelete(u.id, u.name)}
                      className="text-sm text-red-600 hover:underline"
                    >
                      Delete
                    </button>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}