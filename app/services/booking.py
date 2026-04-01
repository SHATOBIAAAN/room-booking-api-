from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking
from app.models.room import Room
from app.schemas.booking import BookingCreate
from app.core.exceptions import BookingConflictError, BookingNotFoundError, RoomNotFoundError


def to_utc(dt: datetime, tz_name: str) -> datetime:
    """Конвертирует naive datetime (в заданной таймзоне) → UTC-aware datetime."""
    tz = ZoneInfo(tz_name)
    local_dt = dt.replace(tzinfo=tz)
    return local_dt.astimezone(timezone.utc)


async def get_bookings_for_room_on_date(
    session: AsyncSession, room_id: int, date: str
) -> list[Booking]:
    """
    Возвращает все бронирования комнаты, которые пересекают указанную дату.
    Корректно обрабатывает бронирования через полночь.
    Дата трактуется как UTC-день (00:00:00 → 00:00:00 следующего дня).
    """
    day_start = datetime.fromisoformat(date).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    # Начало следующего дня — единственный корректный способ захватить весь день,
    # включая бронирования с end_time = 23:59:59.999...
    day_end = day_start + timedelta(days=1)

    result = await session.execute(
        select(Booking).where(
            Booking.room_id == room_id,
            Booking.start_time < day_end,   # бронь начинается ДО конца дня
            Booking.end_time > day_start,   # бронь заканчивается ПОСЛЕ начала дня
        )
    )
    return list(result.scalars().all())


async def create_booking(session: AsyncSession, data: BookingCreate) -> Booking:
    """
    Создаёт бронирование с защитой от race condition через Pessimistic Locking.

    Стратегия блокировки:
      1. SELECT Room FOR UPDATE — блокируем строку комнаты, чтобы другие
         транзакции не могли параллельно войти в эту же критическую секцию.
      2. SELECT Booking WHERE overlap — проверяем пересечения ВНУТРИ блокировки.
      3. INSERT — создаём бронь.
    Пока транзакция не завершена (COMMIT), все параллельные запросы на эту же
    комнату будут ждать на шаге 1 — это гарантирует сериализацию.
    """
    start_utc = to_utc(data.start_time, data.timezone)
    end_utc = to_utc(data.end_time, data.timezone)

    # Шаг 1: блокируем строку комнаты (pessimistic lock).
    # Все конкурентные запросы на ту же комнату встанут здесь в очередь.
    room_result = await session.execute(
        select(Room).where(Room.id == data.room_id).with_for_update()
    )
    room = room_result.scalars().first()
    if not room:
        raise RoomNotFoundError()

    # Шаг 2: проверяем конфликты ВНУТРИ блокировки (безопасно от phantom read).
    # Классический overlap: A перекрывает B ⟺ A.start < B.end AND A.end > B.start
    result = await session.execute(
        select(Booking).where(
            Booking.room_id == data.room_id,
            Booking.start_time < end_utc,
            Booking.end_time > start_utc,
        )
    )
    existing = result.scalars().first()
    if existing:
        raise BookingConflictError()

    # Шаг 3: создаём бронирование
    booking = Booking(
        room_id=data.room_id,
        user_name=data.user_name,
        start_time=start_utc,
        end_time=end_utc,
        timezone=data.timezone,
    )
    session.add(booking)
    await session.commit()
    await session.refresh(booking)
    return booking


async def delete_booking(session: AsyncSession, booking_id: int) -> None:
    booking = await session.get(Booking, booking_id)
    if not booking:
        raise BookingNotFoundError()
    await session.delete(booking)
    await session.commit()

