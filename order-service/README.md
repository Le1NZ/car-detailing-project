# Order Service

Микросервис для управления заказами на обслуживание автомобилей.

## Архитектура

Трехслойная архитектура:
- **Endpoints**: API endpoints (FastAPI routers)
- **Services**: Бизнес-логика и валидация
- **Repositories**: Слой доступа к данным (in-memory storage)

## Структура проекта

```
order-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Конфигурация приложения
│   ├── models/
│   │   └── order.py         # Pydantic модели
│   ├── repositories/
│   │   └── local_order_repo.py  # In-memory хранилище
│   ├── services/
│   │   ├── order_service.py     # Бизнес-логика заказов
│   │   └── car_client.py        # HTTP-клиент для car-service
│   └── endpoints/
│       └── orders.py        # API endpoints
├── requirements.txt
├── Dockerfile
└── README.md
```

## API Endpoints

### 1. POST /api/orders
Создание нового заказа

**Request:**
```json
{
  "car_id": "123e4567-e89b-12d3-a456-426614174000",
  "desired_time": "2025-11-20T10:00:00",
  "description": "Engine oil change and filter replacement"
}
```

**Response (201):**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "car_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "created",
  "appointment_time": "2025-11-20T10:00:00",
  "description": "Engine oil change and filter replacement",
  "created_at": "2025-11-15T14:30:00"
}
```

**Error (404):**
```json
{
  "message": "Car not found"
}
```

### 2. PATCH /api/orders/{order_id}/status
Обновление статуса заказа

**Request:**
```json
{
  "status": "in_progress"
}
```

**Response (200):**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "car_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "in_progress",
  "appointment_time": "2025-11-20T10:00:00",
  "description": "Engine oil change and filter replacement",
  "created_at": "2025-11-15T14:30:00"
}
```

**Допустимые переходы статусов:**
- created → in_progress
- in_progress → work_completed
- work_completed → car_issued

### 3. POST /api/orders/review?order_id={uuid}
Добавление отзыва к заказу

**Request:**
```json
{
  "rating": 5,
  "comment": "Excellent service, very professional staff"
}
```

**Response (201):**
```json
{
  "review_id": "660e8400-e29b-41d4-a716-446655440001",
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "published",
  "rating": 5,
  "comment": "Excellent service, very professional staff",
  "created_at": "2025-11-20T15:00:00"
}
```

**Error (409):**
```json
{
  "message": "Review for this order already exists"
}
```

## Интеграция с car-service

При создании заказа выполняется синхронная проверка существования автомобиля:

```python
# GET http://car-service:8002/api/cars/{car_id}
# 200 OK → создание заказа
# 404 Not Found → возврат 404 с message "Car not found"
```

## Запуск

### Локальный запуск
```bash
cd order-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

### Docker
```bash
docker build -t order-service .
docker run -p 8003:8003 order-service
```

## Конфигурация

Переменные окружения (опционально через .env):
- `CAR_SERVICE_URL`: URL car-service (по умолчанию: http://car-service:8002)
- `PORT`: Порт приложения (по умолчанию: 8003)

## Health Check

```bash
curl http://localhost:8003/health
```

## Документация API

Swagger UI: http://localhost:8003/docs
ReDoc: http://localhost:8003/redoc
