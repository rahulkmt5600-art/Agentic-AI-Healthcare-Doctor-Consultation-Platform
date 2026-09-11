"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<string>("Checking...");
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((response) => response.json())
      .then((data) => setBackendStatus(data.status))
      .catch(() => setBackendStatus("Backend not reachable"));

    const token = localStorage.getItem("token");
    setIsLoggedIn(!!token);

    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setRole(payload.role);
      } catch {
        setRole(null);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsLoggedIn(false);
    setRole(null);
  };

  return (
    <main className="min-h-screen flex flex-col">
      {/* Hero section */}
      <div className="gradient-teal text-white py-20 px-6 text-center">
        <div className="max-w-2xl mx-auto animate-fade-in">
          <h1 className="text-5xl font-bold mb-3 tracking-tight">MediBridge</h1>
          <p className="text-teal-50 text-lg mb-8">
            AI-guided symptom assessment, connecting you with the right doctor.
          </p>

          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm rounded-full px-4 py-1.5 text-sm mb-10">
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === "ok" ? "bg-emerald-400" : "bg-red-400"
              }`}
            ></span>
            System status: {backendStatus === "ok" ? "All systems operational" : backendStatus}
          </div>

          {isLoggedIn ? (
            <div className="flex flex-col items-center gap-3">
              <p className="text-white font-medium">
                Welcome back <span className="opacity-80">({role})</span>
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                {role === "patient" && (
                  <>
                    <Link
                      href="/chat"
                      className="bg-white text-teal-700 rounded-full px-6 py-2.5 font-semibold hover:bg-teal-50 shadow-sm"
                    >
                      Talk to AI Health Assistant
                    </Link>
                    <Link
                      href="/my-appointments"
                      className="bg-white/10 border border-white/30 text-white rounded-full px-6 py-2.5 font-semibold hover:bg-white/20"
                    >
                      My Appointments
                    </Link>
                  </>
                )}
                {role === "doctor" && (
                  <Link
                    href="/doctor"
                    className="bg-white text-teal-700 rounded-full px-6 py-2.5 font-semibold hover:bg-teal-50 shadow-sm"
                  >
                    View Patient Conversations
                  </Link>
                )}
                {role === "admin" && (
                  <Link
                    href="/admin"
                    className="bg-white text-teal-700 rounded-full px-6 py-2.5 font-semibold hover:bg-teal-50 shadow-sm"
                  >
                    Admin Dashboard
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="bg-transparent border border-white/40 text-white rounded-full px-6 py-2.5 font-medium hover:bg-white/10"
                >
                  Log Out
                </button>
              </div>
            </div>
          ) : (
            <div className="flex justify-center gap-3">
              <Link
                href="/login"
                className="bg-white text-teal-700 rounded-full px-6 py-2.5 font-semibold hover:bg-teal-50 shadow-sm"
              >
                Log In
              </Link>
              <Link
                href="/signup"
                className="bg-transparent border border-white/40 text-white rounded-full px-6 py-2.5 font-semibold hover:bg-white/10"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Feature highlights */}
      <div className="flex-1 bg-slate-50 py-16 px-6">
        <div className="max-w-4xl mx-auto grid sm:grid-cols-3 gap-6">
          {[
            {
              icon: "💬",
              title: "AI Symptom Check",
              desc: "Describe how you're feeling in your own words, in English or Hinglish.",
            },
            {
              icon: "🩺",
              title: "Specialist Matching",
              desc: "Get pointed toward the right kind of doctor based on your symptoms.",
            },
            {
              icon: "📅",
              title: "Easy Booking",
              desc: "See real doctor availability and book a slot that works for you.",
            },
          ].map((f) => (
            <div
              key={f.title}
              className="card-hover bg-white border border-slate-200 rounded-2xl p-6 text-center"
            >
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-slate-800 mb-1">{f.title}</h3>
              <p className="text-sm text-slate-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}