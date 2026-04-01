class BookingConflictError(Exception):
    """Два бронирования пересекаются по времени (или комната занята)."""
    pass

class BookingNotFoundError(Exception):
    """Бронирование с таким ID не найдено."""
    pass

class RoomNotFoundError(Exception):
    """Комната с таким ID не найдена."""
    pass
