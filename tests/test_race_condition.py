import asyncio
import httpx

BASE_URL = "http://localhost:8000"


async def create_room() -> int:
    """Создаём комнату и возвращаем её id."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/rooms",
            json={"name": "Тестовая комната", "capacity": 5},
        )
        return response.json()["id"]


async def create_booking(client: httpx.AsyncClient, room_id: int) -> tuple[int, dict]:
    """Отправляет один запрос на бронирование, возвращает (статус, тело)."""
    response = await client.post(
        f"{BASE_URL}/bookings",
        json={
            "room_id": room_id,
            "user_name": "Тестовый пользователь",
            "start_time": "2030-06-01T10:00:00",
            "end_time": "2030-06-01T11:00:00",
            "timezone": "Europe/Moscow",
        },
    )
    return response.status_code, response.json()


async def main():
    print("🚀 Запускаем тест на race condition...\n")

    # Создаём комнату
    room_id = await create_room()
    print(f"✅ Создана комната id={room_id}\n")

    # Запускаем 5 одновременных запросов на одно и то же время
    async with httpx.AsyncClient() as client:
        tasks = [create_booking(client, room_id) for _ in range(5)]
        results = await asyncio.gather(*tasks)

    # Считаем результаты
    created = [(status, body) for status, body in results if status == 201]
    conflicts = [(status, body) for status, body in results if status == 409]
    other = [(status, body) for status, body in results if status not in (201, 409)]

    print("📊 Результаты:")
    for status, body in results:
        icon = "✅" if status == 201 else "❌"
        print(f"  {icon} {status} — {body}")

    print(f"\n📈 Итого:")
    print(f"  Успешных (201): {len(created)}")
    print(f"  Конфликтов (409): {len(conflicts)}")
    print(f"  Других: {len(other)}")

    # Проверяем результат
    print()
    if len(created) == 1 and len(conflicts) == 4:
        print("✅ ТЕСТ ПРОЙДЕН — ровно одно бронирование создано, остальные получили 409")
    elif len(created) > 1:
        print(f"❌ ТЕСТ ПРОВАЛЕН — создано {len(created)} бронирований вместо одного!")
    else:
        print("⚠️  Неожиданный результат — проверь логи сервера")


if __name__ == "__main__":
    asyncio.run(main())
