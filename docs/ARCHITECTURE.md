# Architecture

React/Vite client → FastAPI REST API → SQLAlchemy → SQLite (local) or PostgreSQL (cloud).

React clients also maintain a WebSocket connection to `/ws/events/{event_id}`. Successful RSVP mutations broadcast the authoritative counts to connected clients. Authentication uses JWT bearer tokens. Capacity and uniqueness are enforced by the backend/database rather than the UI.

For production, place the API behind HTTPS and a WebSocket-capable reverse proxy/load balancer, use managed PostgreSQL, and store secrets in the cloud platform's secret/environment configuration.
