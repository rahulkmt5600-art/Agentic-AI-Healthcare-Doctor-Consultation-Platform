from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import engine, Base, SessionLocal
import models
import schemas
from auth import hash_password, verify_password, create_access_token, get_current_user_email, require_doctor
from graph import run_chat_turn

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MediBridge API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "MediBridge backend is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)

    new_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    db.refresh(new_user)

    if user.role == "patient":
        patient_profile = models.Patient(user_id=new_user.id, age=user.age)
        db.add(patient_profile)
        db.commit()
    elif user.role == "doctor":
        doctor_profile = models.Doctor(user_id=new_user.id, specialty=user.specialty)
        db.add(doctor_profile)
        db.commit()

    return new_user

@app.post("/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": token}

@app.get("/users", response_model=list[schemas.UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email)
):
    return db.query(models.User).all()

@app.post("/chat", response_model=schemas.ChatResponse)
def chat(
    request: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or not user.patient_profile:
        raise HTTPException(status_code=403, detail="Only patients can use the chat assistant")

    result = run_chat_turn(request.session_id, request.message, user.patient_profile.id)
    return result

@app.get("/doctor/conversations", response_model=list[schemas.ConversationSummary])
def list_conversations_for_doctor(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_doctor(current_user_email, db)

    conversations = db.query(models.Conversation).order_by(
        models.Conversation.created_at.desc()
    ).all()

    results = []
    for conv in conversations:
        patient_name = conv.patient.user.name if conv.patient and conv.patient.user else "Unknown"
        results.append(schemas.ConversationSummary(
            id=conv.id,
            session_id=conv.session_id,
            patient_name=patient_name,
            stage=conv.stage,
            created_at=conv.created_at,
        ))
    return results

@app.get("/doctor/conversations/{conversation_id}", response_model=schemas.ConversationDetail)
def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_doctor(current_user_email, db)

    conv = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    patient_name = conv.patient.user.name if conv.patient and conv.patient.user else "Unknown"

    return schemas.ConversationDetail(
        id=conv.id,
        session_id=conv.session_id,
        patient_name=patient_name,
        stage=conv.stage,
        created_at=conv.created_at,
        messages=conv.messages,
    )

@app.post("/appointments", response_model=schemas.AppointmentOut)
def request_appointment(
    request: schemas.AppointmentCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or not user.patient_profile:
        raise HTTPException(status_code=403, detail="Only patients can request appointments")

    conversation = db.query(models.Conversation).filter(
        models.Conversation.session_id == request.session_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.patient_id != user.patient_profile.id:
        raise HTTPException(status_code=403, detail="This conversation does not belong to you")

    last_ai_message = db.query(models.Message).filter(
        models.Message.conversation_id == conversation.id,
        models.Message.sender == "ai"
    ).order_by(models.Message.id.desc()).first()

    specialty_guess = last_ai_message.content if last_ai_message else None

    appointment = models.Appointment(
        conversation_id=conversation.id,
        patient_id=user.patient_profile.id,
        status="requested",
        requested_specialty=specialty_guess,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return schemas.AppointmentOut(
        id=appointment.id,
        conversation_id=appointment.conversation_id,
        patient_name=user.name,
        doctor_name=None,
        status=appointment.status,
        requested_specialty=appointment.requested_specialty,
        created_at=appointment.created_at,
    )

@app.get("/doctor/appointments", response_model=list[schemas.AppointmentSummary])
def list_open_appointments(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_doctor(current_user_email, db)

    appointments = db.query(models.Appointment).filter(
        models.Appointment.status == "requested"
    ).order_by(models.Appointment.created_at.desc()).all()

    results = []
    for appt in appointments:
        patient_name = appt.patient.user.name if appt.patient and appt.patient.user else "Unknown"
        results.append(schemas.AppointmentSummary(
            id=appt.id,
            conversation_id=appt.conversation_id,
            patient_name=patient_name,
            doctor_name=None,
            status=appt.status,
            requested_specialty=appt.requested_specialty,
            created_at=appt.created_at,
        ))
    return results


@app.post("/doctor/appointments/{appointment_id}/accept", response_model=schemas.AppointmentSummary)
def accept_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    doctor_user = require_doctor(current_user_email, db)

    appointment = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status != "requested":
        raise HTTPException(status_code=400, detail="This appointment is no longer available")

    appointment.doctor_id = doctor_user.doctor_profile.id
    appointment.status = "accepted"
    db.commit()
    db.refresh(appointment)

    patient_name = appointment.patient.user.name if appointment.patient and appointment.patient.user else "Unknown"

    return schemas.AppointmentSummary(
        id=appointment.id,
        conversation_id=appointment.conversation_id,
        patient_name=patient_name,
        doctor_name=doctor_user.name,
        status=appointment.status,
        requested_specialty=appointment.requested_specialty,
        created_at=appointment.created_at,
    )

@app.put("/doctor/profile")
def update_doctor_profile(
    update: schemas.DoctorProfileUpdate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    doctor_user = require_doctor(current_user_email, db)
    doctor_user.doctor_profile.qualifications = update.qualifications
    db.commit()
    return {"message": "Profile updated"}


@app.post("/doctor/slots", response_model=schemas.SlotOut)
def add_availability_slot(
    slot: schemas.SlotCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    doctor_user = require_doctor(current_user_email, db)

    new_slot = models.AvailabilitySlot(
        doctor_id=doctor_user.doctor_profile.id,
        start_time=slot.start_time,
        is_booked=False,
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    return new_slot


@app.get("/doctor/slots", response_model=list[schemas.SlotOut])
def get_my_slots(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    doctor_user = require_doctor(current_user_email, db)

    slots = db.query(models.AvailabilitySlot).filter(
        models.AvailabilitySlot.doctor_id == doctor_user.doctor_profile.id
    ).order_by(models.AvailabilitySlot.start_time).all()

    return slots


from typing import Optional

@app.get("/doctors/search", response_model=list[schemas.DoctorSearchResult])
def search_doctors(
    specialty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    query = db.query(models.Doctor)
    if specialty:
        query = query.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))

    doctors = query.all()

    results = []
    for doc in doctors:
        open_slots = [s for s in doc.availability_slots if not s.is_booked]
        results.append(schemas.DoctorSearchResult(
            doctor_id=doc.id,
            name=doc.user.name,
            specialty=doc.specialty,
            qualifications=doc.qualifications,
            is_verified=doc.is_verified,
            available_slots=open_slots,
        ))
    return results


@app.post("/appointments/book", response_model=schemas.BookingOut)
def book_appointment(
    booking: schemas.BookingCreate,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or not user.patient_profile:
        raise HTTPException(status_code=403, detail="Only patients can book appointments")

    conversation = db.query(models.Conversation).filter(
        models.Conversation.session_id == booking.session_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.patient_id != user.patient_profile.id:
        raise HTTPException(status_code=403, detail="This conversation does not belong to you")

    slot = db.query(models.AvailabilitySlot).filter(
        models.AvailabilitySlot.id == booking.slot_id,
        models.AvailabilitySlot.doctor_id == booking.doctor_id,
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.is_booked:
        raise HTTPException(status_code=400, detail="This slot has already been booked")

    last_ai_message = db.query(models.Message).filter(
        models.Message.conversation_id == conversation.id,
        models.Message.sender == "ai"
    ).order_by(models.Message.id.desc()).first()
    specialty_guess = last_ai_message.content if last_ai_message else None

    appointment = models.Appointment(
        conversation_id=conversation.id,
        patient_id=user.patient_profile.id,
        doctor_id=booking.doctor_id,
        slot_id=slot.id,
        status="booked",
        requested_specialty=specialty_guess,
    )
    db.add(appointment)

    slot.is_booked = True

    db.commit()
    db.refresh(appointment)

    doctor = db.query(models.Doctor).filter(models.Doctor.id == booking.doctor_id).first()

    return schemas.BookingOut(
        id=appointment.id,
        doctor_name=doctor.user.name,
        slot_time=slot.start_time,
        status=appointment.status,
        created_at=appointment.created_at,
    )

@app.get("/my-appointments", response_model=list[schemas.MyBookingOut])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    user = db.query(models.User).filter(models.User.email == current_user_email).first()
    if not user or not user.patient_profile:
        raise HTTPException(status_code=403, detail="Only patients can view their appointments")

    appointments = db.query(models.Appointment).filter(
        models.Appointment.patient_id == user.patient_profile.id
    ).order_by(models.Appointment.created_at.desc()).all()

    results = []
    for appt in appointments:
        results.append(schemas.MyBookingOut(
            id=appt.id,
            doctor_name=appt.doctor.user.name,
            specialty=appt.doctor.specialty,
            slot_time=appt.slot.start_time,
            status=appt.status,
            created_at=appt.created_at,
        ))
    return results

from auth import require_admin

@app.get("/admin/users", response_model=list[schemas.AdminUserOut])
def list_all_users(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_admin(current_user_email, db)
    return db.query(models.User).all()


@app.get("/admin/doctors", response_model=list[schemas.AdminDoctorOut])
def list_all_doctors(
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_admin(current_user_email, db)

    doctors = db.query(models.Doctor).all()
    results = []
    for doc in doctors:
        results.append(schemas.AdminDoctorOut(
            doctor_id=doc.id,
            user_id=doc.user.id,
            name=doc.user.name,
            email=doc.user.email,
            specialty=doc.specialty,
            qualifications=doc.qualifications,
            is_verified=doc.is_verified,
        ))
    return results


@app.put("/admin/doctors/{doctor_id}/verify")
def verify_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_admin(current_user_email, db)

    doctor = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    doctor.is_verified = True
    db.commit()
    return {"message": f"Doctor {doctor.user.name} is now verified"}


@app.delete("/admin/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user_email: str = Depends(get_current_user_email),
):
    require_admin(current_user_email, db)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete an admin account")

    db.delete(user)
    db.commit()
    return {"message": f"User {user.name} deleted"}