from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False)

    bookings: Mapped[list["Booking"]] = relationship(back_populates="room", cascade="all, delete-orphan")
