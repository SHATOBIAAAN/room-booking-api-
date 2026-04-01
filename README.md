# Room Booking API

REST API для бронирования переговорных комнат. Написан на **FastAPI + PostgreSQL + SQLAlchemy 2.0 (async)**.

## Стек

| Компонент      | Инструмент            |
| -------------- | --------------------- |
| Фреймворк      | FastAPI (Python 3.12) |
| БД             | PostgreSQL 16         |
| ORM            | SQLAlchemy 2.0 async  |
| Миграции       | Alembic               |
| Валидация      | Pydantic V2           |
| Инфраструктура | Docker Compose        |

---

## Запуск

### Одной командой

```bash
docker compose up --build
```

Это поднимет PostgreSQL и API. Миграции применяются **автоматически** при старте контейнера — таблицы создадутся сами.

API будет доступен на `http://localhost:8000`.

---

## Примеры curl-запросов

### GET /rooms — Список переговорок

```bash
curl -s http://localhost:8000/rooms | jq
```

Ответ:

```json
[
    { "id": 1, "name": "Большой зал", "capacity": 20 },
    { "id": 2, "name": "Малая переговорка", "capacity": 6 }
]
```

---

### POST /rooms — Создать переговорку

```bash
curl -s -X POST http://localhost:8000/rooms \
  -H "Content-Type: application/json" \
  -d '{"name": "Большой зал", "capacity": 20}' | jq
```

Ответ `201 Created`:

```json
{ "id": 1, "name": "Большой зал", "capacity": 20 }
```

---

### POST /bookings — Создать бронирование

Время передаётся в **локальной таймзоне** пользователя. Сервер сам конвертирует в UTC.

```bash
curl -s -X POST http://localhost:8000/bookings \
  -H "Content-Type: application/json" \
  -d '{
    "room_id": 1,
    "user_name": "Иван Петров",
    "start_time": "2030-06-01T10:00:00",
    "end_time": "2030-06-01T12:00:00",
    "timezone": "Europe/Moscow"
  }' | jq
```

Ответ `201 Created`:

```json
{
    "id": 1,
    "room_id": 1,
    "user_name": "Иван Петров",
    "start_time": "2030-06-01T07:00:00Z",
    "end_time": "2030-06-01T09:00:00Z",
    "timezone": "Europe/Moscow"
}
```

Если время занято — `409 Conflict`:

```json
{ "detail": "Room already booked for this time" }
```

---

### GET /bookings — Бронирования комнаты на дату

Параметр `date` трактуется как UTC-день. Возвращает **все** бронирования, пересекающие этот день, включая те, что начались накануне и продолжаются через полночь.

```bash
curl -s "http://localhost:8000/bookings?room_id=1&target_date=2030-06-01" | jq
```

Ответ:

```json
[
    {
        "id": 1,
        "room_id": 1,
        "user_name": "Иван Петров",
        "start_time": "2030-06-01T07:00:00Z",
        "end_time": "2030-06-01T09:00:00Z",
        "timezone": "Europe/Moscow"
    }
]
```

---

### DELETE /bookings/{id} — Отменить бронирование

```bash
curl -s -X DELETE http://localhost:8000/bookings/1 -w "%{http_code}"
```

Ответ `204 No Content` (тело пустое).

Если бронь не найдена — `404 Not Found`:

```json
{ "detail": "Booking not found" }
```

---

### GET /health — Healthcheck

```bash
curl -s http://localhost:8000/health
```

```json
{ "status": "ok" }
```

---

## Тест на Race Condition (состояние гонки)

Скрипт отправляет **5 параллельных** запросов на бронирование одной комнаты на одинаковое время.

### Требования

```bash
pip install httpx
```

### Запуск

```bash
# Убедитесь, что API запущен (docker compose up)
python tests/test_race_condition.py
```

### Ожидаемый результат

```
🚀 Запускаем тест на race condition...

✅ Создана комната id=1

📊 Результаты:
  ✅ 201 — {"id": 1, "room_id": 1, ...}
  ❌ 409 — {"detail": "Room already booked for this time"}
  ❌ 409 — {"detail": "Room already booked for this time"}
  ❌ 409 — {"detail": "Room already booked for this time"}
  ❌ 409 — {"detail": "Room already booked for this time"}

📈 Итого:
  Успешных (201): 1
  Конфликтов (409): 4

✅ ТЕСТ ПРОЙДЕН — ровно одно бронирование создано, остальные получили 409
```

---

## Архитектурные решения

### Защита от Race Condition — Pessimistic Locking

Используется стратегия **Pessimistic Lock** через `SELECT ... FOR UPDATE` на строку комнаты:

1. Первый запрос блокирует строку комнаты в PostgreSQL.
2. Все конкурентные запросы на **ту же комнату** встают в очередь на этом шаге.
3. Внутри блокировки — проверяем пересечения по времени и создаём бронь.
4. После `COMMIT` блокировка снимается — следующий запрос заходит, видит занятый слот, получает `409`.

Это гарантирует **сериализацию** запросов на одну комнату и исключает Phantom Read.

### Работа с таймзонами

- Клиент передаёт `start_time`/`end_time` как naive datetime + отдельное поле `timezone` (IANA-идентификатор, например `Asia/Yekaterinburg`).
- Сервер конвертирует в UTC через `ZoneInfo` и хранит в БД с типом `TIMESTAMPTZ`.
- `GET /bookings?date=YYYY-MM-DD` ищет бронирования, пересекающие UTC-день от `00:00:00` до `00:00:00` следующего дня — корректно обрабатывает переход через полночь.

### Неоднозначности, решённые самостоятельно

| Ситуация                                                | Принятое решение                                                                                                                     |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Параметр `date` в GET /bookings — в какой таймзоне?     | Трактуется как UTC-день. Обосновано: сервер хранит всё в UTC, фильтрация по UTC-дню однозначна и предсказуема.                       |
| Что блокировать при race condition — комнату или бронь? | Строку комнаты (`SELECT Room FOR UPDATE`). Это создаёт узкую точку сериализации без оверхеда на блокировку большого диапазона строк. |
| Нужна ли уникальность имён комнат?                      | Нет ограничения — позволяет создавать комнаты с одинаковыми именами (разные этажи/корпуса).                                          |

---

## Где использовал AI

### AI помогал с:

- Базовая структура проекта (папки, слои, `__init__` файлы)
- Настройка Alembic `env.py` с asyncio
- Написание скрипта тестирования race condition
- Настройка Docker и docker-compose.yml
- Написание README.md
