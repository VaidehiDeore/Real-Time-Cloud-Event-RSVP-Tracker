from collections import defaultdict
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, set[WebSocket]] = defaultdict(set)
        self.lock = asyncio.Lock()

    async def connect(self, event_id: int, ws: WebSocket):
        await ws.accept()
        async with self.lock:
            self.rooms[event_id].add(ws)

    async def disconnect(self, event_id: int, ws: WebSocket):
        async with self.lock:
            self.rooms[event_id].discard(ws)
            if not self.rooms[event_id]:
                self.rooms.pop(event_id, None)

    async def broadcast(self, event_id: int, payload: dict):
        dead = []
        for ws in list(self.rooms.get(event_id, set())):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(event_id, ws)

manager = ConnectionManager()
