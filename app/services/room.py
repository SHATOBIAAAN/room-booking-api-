from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.room import Room
from app.schemas.room import RoomCreate

async def get_all_rooms(session: AsyncSession) -> list[Room]:
    result = await session.execute(select(Room))
    return list(result.scalars().all())

async def create_room(session: AsyncSession, data: RoomCreate) -> Room:
    room = Room(name=data.name, capacity=data.capacity)
    session.add(room)
    await session.commit()
    await session.refresh(room)
    return room
