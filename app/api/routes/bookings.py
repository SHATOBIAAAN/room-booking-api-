from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services import booking as booking_service


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingResponse])
async def get_bookings(
    room_id: int,
    target_date: date,  # Используем date из datetime для автоматической валидации YYYY-MM-DD
    session: AsyncSession = Depends(get_db),
):
    # Превращаем объект date обратно в строку, так как сервис ожидает строку
    return await booking_service.get_bookings_for_room_on_date(
        session, room_id, str(target_date)
    )


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking(
    data: BookingCreate,
    session: AsyncSession = Depends(get_db),
):
    # Больше никаких try-except! Ошибки поймает глобальный хендлер в main.py
    return await booking_service.create_booking(session, data)


@router.delete("/{booking_id}", status_code=204)
async def delete_booking(
    booking_id: int,
    session: AsyncSession = Depends(get_db),
):
    # Больше никаких try-except! Ошибки поймает глобальный хендлер в main.py
    await booking_service.delete_booking(session, booking_id)