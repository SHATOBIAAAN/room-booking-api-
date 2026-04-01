from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.room import RoomCreate, RoomResponse
from app.services import room as room_service

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[RoomResponse])
async def get_rooms(session: AsyncSession = Depends(get_db)):
    return await room_service.get_all_rooms(session)


@router.post("", response_model=RoomResponse, status_code=201)
async def create_room(
    data: RoomCreate,
    session: AsyncSession = Depends(get_db),
):
    return await room_service.create_room(session, data)