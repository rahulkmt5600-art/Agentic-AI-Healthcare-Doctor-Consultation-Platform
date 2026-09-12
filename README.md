# MediBridge

MediBridge is a full-stack healthcare platform that connects patients with doctors through an AI-guided symptom assessment. Patients describe their symptoms to an AI Health Assistant, which asks clarifying questions, provides a preliminary urgency assessment, suggests a relevant doctor specialty, and helps the patient book an appointment with a verified doctor.

> **Important:** The AI Health Assistant is **not a doctor**. It does not provide a definitive diagnosis or prescribe medication. All final medical decisions are made by licensed doctors.

---

## Features

### For Patients
- Sign up and log in securely
- Chat with an AI Health Assistant in **English or Hinglish** (Hindi written in Roman script)
- AI asks thorough clarifying questions before giving an assessment
- Receive a preliminary urgency level and suggested doctor specialty
- Search for doctors by specialty, view qualifications and real availability
- Book a specific appointment time slot
- View all booked appointments and their status

### For Doctors
- Sign up and log in securely
- View all patient conversations, including the full AI-guided chat history
- Update professional qualifications
- Add and manage available appointment time slots
- View appointment bookings

### For Admins
- View all registered users
- Verify doctor accounts
- Remove user accounts

### AI Safety Guardrails
- Never provides a definitive diagnosis
- Never prescribes medication or dosages
- Always recommends seeing a licensed doctor
- Immediately prioritizes emergency guidance for potentially life-threatening symptoms
- Specialty suggestions are grounded in a curated medical knowledge base using Retrieval-Augmented Generation (RAG)

---

## Tech Stack

**Frontend**
- Next.js (App Router)
- React
- TypeScript
- Tailwind CSS

**Backend**
- Python
- FastAPI

**Database**
- PostgreSQL
- SQLAlchemy (ORM)

**AI**
- LangChain
- LangGraph (structured multi-stage conversation flow)
- RAG with FAISS (vector search over a medical knowledge base)
- Google Gemini (LLM + embeddings)

**Authentication**
- JWT (JSON Web Tokens)
- bcrypt password hashing

---

## Project Structure

```
medibridge/
├── frontend/
│   └── src/app/
│       ├── page.tsx                 # Homepage
│       ├── login/page.tsx
│       ├── signup/page.tsx
│       ├── chat/page.tsx            # Patient AI chat
│       ├── book/[sessionId]/page.tsx   # Doctor search & booking
│       ├── my-appointments/page.tsx # Patient's booked appointments
│       ├── doctor/page.tsx          # Doctor dashboard
│       ├── doctor/[id]/page.tsx     # Conversation detail view
│       └── admin/page.tsx           # Admin dashboard
│
└── backend/
    ├── main.py           # All API endpoints
    ├── models.py         # SQLAlchemy models
    ├── schemas.py        # Pydantic request/response schemas
    ├── auth.py           # Password hashing, JWT, role checks
    ├── graph.py           # LangGraph conversation flow
    ├── rag.py             # RAG retrieval module
    ├── database.py        # Database connection setup
    ├── medical_knowledge.txt   # RAG knowledge base
    ├── requirements.txt
    └── .env               # API keys (not committed to Git)
```

---

## Database Schema

| Table | Description |
|---|---|
| `users` | Shared account info: name, email, hashed password, role |
| `patients` | Patient-specific profile (linked to users) |
| `doctors` | Doctor-specific profile: specialty, qualifications, verification status |
| `conversations` | One AI chat session per patient interaction |
| `messages` | Individual messages within a conversation |
| `appointments` | A booked appointment linking patient, doctor, and slot |
| `availability_slots` | Specific bookable time slots created by doctors |

---

## Getting Started

### Prerequisites
- Node.js
- Python 3.11+
- PostgreSQL
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/app/apikey))

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```
GOOGLE_API_KEY=your_api_key_here
```

Create the PostgreSQL database:
```sql
CREATE DATABASE medibridge;
```

Update the connection string in `database.py` with your PostgreSQL credentials, then run:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## Environment Variables

| Variable | Location | Description |
|---|---|---|
| `GOOGLE_API_KEY` | `backend/.env` | API key for Google Gemini (chat + embeddings) |

**Never commit `.env` files to version control.**

---

## Roadmap

- [ ] Docker containerization
- [ ] Production cloud deployment
- [ ] Additional language support beyond English/Hinglish
- [ ] Doctor-to-patient messaging after appointment booking
- [ ] Expanded medical knowledge base for RAG

---

## Disclaimer

MediBridge's AI Health Assistant provides preliminary, non-diagnostic guidance only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of a qualified healthcare provider with any questions regarding a medical condition. In case of a medical emergency, contact emergency services immediately.
