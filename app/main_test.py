from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from typing import List

# Usar db_test para SQLite
from app.db_test import engine, Base
from app.routers import auth, payments, tickets, visits, reservations, announcements
from app.auth import get_current_user
from app.models import User

# Importar todos los modelos para que se creen las tablas
from app.models.user import User
from app.models.condominium import Condominium
from app.models.unit import Unit
from app.models.payment import Payment
from app.models.ticket import Ticket, TicketAttachment
from app.models.visit import Visit
from app.models.reservation import Reservation
from app.models.announcement import Announcement
from app.models.message import Message

Base.metadata.create_all(bind=engine)

app = FastAPI(title="CondoSmart API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(visits.router, prefix="/api/visits", tags=["visits"])
app.include_router(reservations.router, prefix="/api/reservations", tags=["reservations"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])

security = HTTPBearer()
active_connections: List[WebSocket] = []

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            for connection in active_connections:
                if connection != websocket:
                    await connection.send_text(data)
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.get("/")
async def root():
    return {"message": "CondoSmart API", "status": "running", "database": "SQLite (test)"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Iniciando CondoSmart API en modo prueba (SQLite)...")
    print("📝 Base de datos: test_condosmart.db")
    print("🌐 Servidor: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

