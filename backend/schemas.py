from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["patient", "doctor", "admin"] = "patient"
    age: Optional[int] = None
    specialty: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    stage: str

class MessageOut(BaseModel):
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationSummary(BaseModel):
    id: int
    session_id: str
    patient_name: str
    stage: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetail(BaseModel):
    id: int
    session_id: str
    patient_name: str
    stage: str
    created_at: datetime
    messages: list[MessageOut]

    class Config:
        from_attributes = True

class AppointmentCreate(BaseModel):
    session_id: str

class AppointmentOut(BaseModel):
    id: int
    conversation_id: int
    patient_name: str
    doctor_name: Optional[str] = None
    status: str
    requested_specialty: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AppointmentSummary(BaseModel):
    id: int
    conversation_id: int
    patient_name: str
    doctor_name: Optional[str] = None
    status: str
    requested_specialty: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True        

class DoctorProfileUpdate(BaseModel):
    qualifications: str

class SlotCreate(BaseModel):
    start_time: datetime

class SlotOut(BaseModel):
    id: int
    start_time: datetime
    is_booked: bool

    class Config:
        from_attributes = True        

class DoctorSearchResult(BaseModel):
    doctor_id: int
    name: str
    specialty: Optional[str] = None
    qualifications: Optional[str] = None
    is_verified: bool
    available_slots: list[SlotOut]

    class Config:
        from_attributes = True        

class BookingCreate(BaseModel):
    session_id: str
    doctor_id: int
    slot_id: int

class BookingOut(BaseModel):
    id: int
    doctor_name: str
    slot_time: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True        

class MyBookingOut(BaseModel):
    id: int
    doctor_name: str
    specialty: Optional[str] = None
    slot_time: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class AdminUserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True

class AdminDoctorOut(BaseModel):
    doctor_id: int
    user_id: int
    name: str
    email: str
    specialty: Optional[str] = None
    qualifications: Optional[str] = None
    is_verified: bool

    class Config:
        from_attributes = True