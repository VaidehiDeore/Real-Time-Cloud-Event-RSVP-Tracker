# Real-Time Cloud-Based Event Planning & RSVP Tracker

A polished, real-time event planning and RSVP platform for organizers and attendees. The implementation uses a React + Vite frontend and FastAPI backend, with SQLite for zero-setup local development and PostgreSQL compatibility for cloud deployment. WebSockets provide live RSVP updates.

## Core features
- JWT authentication and Organizer/Attendee roles
- Event creation, publishing, editing and cancellation
- RSVP: Going / Maybe / Not Going
- Capacity-safe RSVP transactions and waitlist
- Idempotent RSVP requests
- Real-time dashboard updates through WebSockets
- Organizer analytics and capacity utilization
- Announcements and in-app notifications
- Invitee/token/QR-ready data model
- Failure handling, reconnects, logging and health endpoint
- Responsive light-theme dashboard UI

## Quick start (Windows PowerShell)

### Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open `http://localhost:5173`.

Demo accounts can be created from the registration screen. The backend automatically creates its local SQLite database on first start.

## Production/cloud direction
Set `DATABASE_URL` to a managed PostgreSQL database, deploy the FastAPI service behind HTTPS, and deploy the Vite build to a static hosting/CDN service. The WebSocket endpoint should be exposed through a WebSocket-capable reverse proxy/load balancer. JWT secrets and database credentials belong only in environment variables.

## API
Interactive API documentation is available at `http://localhost:8000/docs` while the backend is running.

## Screenshots
See `screenshots/` for evidence captured during development.

## Author
Vaidehi Deore
