from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import bookings, rooms
from app.core.exceptions import (
    BookingConflictError,
    BookingNotFoundError,
    RoomNotFoundError,
)

app = FastAPI(title="Room Booking API")

# --- ГЛОБАЛЬНЫЕ ОБРАБОТЧИКИ ОШИБОК (Exception Handlers) ---

@app.exception_handler(RoomNotFoundError)
async def room_not_found_handler(request: Request, exc: RoomNotFoundError):
    return JSONResponse(status_code=404, content={"detail": "Room not found"})

@app.exception_handler(BookingNotFoundError)
async def booking_not_found_handler(request: Request, exc: BookingNotFoundError):
    return JSONResponse(status_code=404, content={"detail": "Booking not found"})

@app.exception_handler(BookingConflictError)
async def booking_conflict_handler(request: Request, exc: BookingConflictError):
    return JSONResponse(status_code=409, content={"detail": "Room already booked for this time"})

# --- РОУТЕРЫ ---

app.include_router(rooms.router)
app.include_router(bookings.router)

@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}