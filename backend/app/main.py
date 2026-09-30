from datetime import datetime, timezone
import logging
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_db
from .models import User, Event, RSVP, WaitlistEntry, Announcement, Notification
from .schemas import RegisterIn, LoginIn, TokenOut, UserOut, EventCreate, EventOut, RSVPIn, AnnouncementIn
from .auth import hash_password, verify_password, create_token, get_current_user, require_organizer
from .realtime import manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("event-rsvp")
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Real-Time Cloud Event RSVP Tracker", version="1.0.0")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins or ["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "event-rsvp-api", "time": datetime.now(timezone.utc)}

@app.post("/api/auth/register", response_model=TokenOut)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    role = payload.role if payload.role in {"attendee", "organizer"} else "attendee"
    if db.query(User).filter(func.lower(User.email) == payload.email.lower()).first():
        raise HTTPException(409, "Email is already registered")
    user = User(name=payload.name, email=payload.email.lower(), password_hash=hash_password(payload.password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": create_token(user), "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.post("/api/auth/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return {"access_token": create_token(user), "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)): return user

@app.get("/api/events", response_model=list[EventOut])
def list_events(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Event).order_by(Event.start_at.asc()).all()

@app.post("/api/events", response_model=EventOut)
def create_event(payload: EventCreate, db: Session = Depends(get_db), user: User = Depends(require_organizer)):
    if payload.end_at <= payload.start_at: raise HTTPException(400, "End time must be after start time")
    if payload.rsvp_deadline >= payload.start_at: raise HTTPException(400, "RSVP deadline must be before event start")
    event = Event(**payload.model_dump(), organizer_id=user.id)
    db.add(event); db.commit(); db.refresh(event)
    return event

@app.get("/api/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event = db.get(Event, event_id)
    if not event: raise HTTPException(404, "Event not found")
    return event

@app.put("/api/events/{event_id}", response_model=EventOut)
def update_event(event_id: int, payload: EventCreate, db: Session = Depends(get_db), user: User = Depends(require_organizer)):
    event = db.get(Event, event_id)
    if not event: raise HTTPException(404, "Event not found")
    if event.organizer_id != user.id: raise HTTPException(403, "You do not own this event")
    for k,v in payload.model_dump().items(): setattr(event,k,v)
    db.commit(); db.refresh(event)
    return event

@app.delete("/api/events/{event_id}")
def cancel_event(event_id: int, db: Session = Depends(get_db), user: User = Depends(require_organizer)):
    event = db.get(Event, event_id)
    if not event: raise HTTPException(404, "Event not found")
    if event.organizer_id != user.id: raise HTTPException(403, "You do not own this event")
    event.status = "CANCELLED"; db.commit()
    db.query(RSVP).filter(RSVP.event_id == event_id).update({RSVP.status: "NOT_GOING"})
    db.commit()
    return {"message": "Event cancelled"}

def counts(db: Session, event_id: int):
    rows = db.query(RSVP.status, func.sum(RSVP.guests + 1)).filter(RSVP.event_id == event_id).group_by(RSVP.status).all()
    data = {"GOING":0,"MAYBE":0,"NOT_GOING":0}
    for status, n in rows: data[status] = int(n or 0)
    wait = db.query(WaitlistEntry).filter(WaitlistEntry.event_id==event_id, WaitlistEntry.active==True).count()
    return {"going":data["GOING"],"maybe":data["MAYBE"],"not_going":data["NOT_GOING"],"waitlist":wait}

@app.post("/api/events/{event_id}/rsvp")
async def rsvp(event_id: int, payload: RSVPIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.status not in {"GOING","MAYBE","NOT_GOING"}: raise HTTPException(400, "Invalid RSVP status")
    event = db.get(Event, event_id)
    if not event: raise HTTPException(404, "Event not found")
    if event.status == "CANCELLED": raise HTTPException(409, "Event is cancelled")
    now = datetime.utcnow()
    if now > event.rsvp_deadline: raise HTTPException(409, "RSVP deadline has passed")
    existing = db.query(RSVP).filter_by(event_id=event_id, user_id=user.id).first()
    if existing and payload.idempotency_key and existing.idempotency_key == payload.idempotency_key:
        return {"status": existing.status, "duplicate": True, "counts": counts(db,event_id)}
    if payload.status == "GOING":
        current = counts(db,event_id)["going"]
        old_seats = (existing.guests + 1) if existing and existing.status == "GOING" else 0
        requested = payload.guests + 1
        if current - old_seats + requested > event.capacity:
            if not existing or existing.status != "GOING":
                entry = db.query(WaitlistEntry).filter_by(event_id=event_id,user_id=user.id,active=True).first()
                if not entry:
                    db.add(WaitlistEntry(event_id=event_id,user_id=user.id))
                if existing: existing.status = "MAYBE"; existing.guests = payload.guests
                else: db.add(RSVP(event_id=event_id,user_id=user.id,status="MAYBE",guests=payload.guests,idempotency_key=payload.idempotency_key))
                db.commit(); c=counts(db,event_id); await manager.broadcast(event_id,{"type":"rsvp_updated","counts":c}); return {"status":"WAITLISTED","counts":c}
            raise HTTPException(409, "Not enough capacity")
    if existing:
        existing.status=payload.status; existing.guests=payload.guests; existing.idempotency_key=payload.idempotency_key; existing.updated_at=now
        if payload.status != "GOING":
            for entry in db.query(WaitlistEntry).filter_by(event_id=event_id,user_id=user.id,active=True): entry.active=False
    else:
        db.add(RSVP(event_id=event_id,user_id=user.id,status=payload.status,guests=payload.guests,idempotency_key=payload.idempotency_key))
    db.commit(); c=counts(db,event_id)
    if payload.status == "GOING":
        note=Notification(user_id=user.id,event_id=event_id,type="RSVP_CONFIRMATION",message=f"Your RSVP for {event.title} is confirmed as Going.")
        db.add(note); db.commit()
    await manager.broadcast(event_id,{"type":"rsvp_updated","counts":c})
    return {"status":payload.status,"counts":c}

@app.get("/api/events/{event_id}/analytics")
def analytics(event_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    event=db.get(Event,event_id)
    if not event: raise HTTPException(404,"Event not found")
    if event.organizer_id != user.id and user.role != "attendee": raise HTTPException(403,"Forbidden")
    c=counts(db,event_id)
    total=c["going"]+c["maybe"]+c["not_going"]
    invited=db.query(User).count() if user.role=="organizer" else max(total,1)
    return {**c,"total_rsvps":total,"invited_users":invited,"response_rate":round(total/invited*100,2) if invited else 0,"capacity_utilization":round(c["going"]/event.capacity*100,2) if event.capacity else 0,"available_seats":max(event.capacity-c["going"],0),"conversion_rate":round(c["going"]/invited*100,2) if invited else 0}

@app.post("/api/events/{event_id}/announcements")
async def announcement(event_id:int,payload:AnnouncementIn,db:Session=Depends(get_db),user:User=Depends(require_organizer)):
    event=db.get(Event,event_id)
    if not event or event.organizer_id!=user.id: raise HTTPException(403,"Forbidden")
    item=Announcement(event_id=event_id,title=payload.title,message=payload.message); db.add(item)
    attendees=db.query(RSVP).filter(RSVP.event_id==event_id,RSVP.status.in_(["GOING","MAYBE"])).all()
    db.flush()
    for r in attendees: db.add(Notification(user_id=r.user_id,event_id=event_id,type="ANNOUNCEMENT",message=payload.message))
    db.commit(); await manager.broadcast(event_id,{"type":"announcement","title":payload.title,"message":payload.message})
    return {"id":item.id,"title":item.title,"message":item.message}

@app.get("/api/notifications")
def notifications(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(30).all()

@app.websocket("/ws/events/{event_id}")
async def websocket_endpoint(ws: WebSocket, event_id: int):
    await manager.connect(event_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(event_id, ws)
    except Exception:
        await manager.disconnect(event_id, ws)
