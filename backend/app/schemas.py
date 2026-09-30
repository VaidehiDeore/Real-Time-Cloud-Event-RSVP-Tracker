from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: str
    password: str = Field(min_length=6)
    role: str = "attendee"

class LoginIn(BaseModel):
    email: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class EventCreate(BaseModel):
    title: str
    description: str = ""
    event_type: str = "Workshop"
    start_at: datetime
    end_at: datetime
    venue: str
    online_link: str | None = None
    capacity: int = Field(gt=0, le=100000)
    rsvp_deadline: datetime

class EventOut(EventCreate):
    id: int
    organizer_id: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RSVPIn(BaseModel):
    status: str
    guests: int = Field(default=0, ge=0, le=20)
    idempotency_key: str | None = Field(default=None, max_length=120)

class AnnouncementIn(BaseModel):
    title: str
    message: str

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)
