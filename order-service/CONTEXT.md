# Order Service - Контекст для LLM агентов

## Назначение
Управление заказами на обслуживание автомобилей. **КРИТИЧЕСКАЯ ОСОБЕННОСТЬ**: синхронный HTTP-вызов к car-service для проверки существования автомобиля.

## Роль в архитектуре
- **Порт**: 8003
- **Хранилище**: In-memory
- **HTTP клиент**: Делает GET запрос к car-service:8002
- **Зависимость**: car-service должен быть запущен

## API Endpoints

### POST /api/orders
Создание заказа с проверкой автомобиля через HTTP

**Request**:
```json
{
  "car_id": "uuid",
  "desired_time": "2024-12-20T10:00:00Z",
  "description": "Стучит в подвеске"
}
```

**Response (201)**:
```json
{
  "order_id": "ord_a1b2c3d4",
  "car_id": "uuid",
  "status": "created",
  "appointment_time": "2024-12-20T10:00:00Z"
}
```

**Коды**: 201 Created, 404 Not Found (car не найден), 422 Unprocessable Entity

### PATCH /api/orders/{order_id}/status
Обновление статуса заказа с валидацией переходов

**Request**:
```json
{
  "status": "in_progress"
}
```

**Допустимые переходы**:
- created → in_progress
- in_progress → work_completed
- work_completed → car_issued

**Коды**: 200 OK, 400 Bad Request (недопустимый переход), 404 Not Found

### POST /api/orders/review?order_id={uuid}
Добавление отзыва о работе

**Request**:
```json
{
  "rating": 5,
  "comment": "Отличная работа!"
}
```

**Коды**: 201 Created, 404 Not Found, 409 Conflict (отзыв уже есть)

## HTTP Integration (КРИТИЧЕСКИ ВАЖНО)

### app/services/car_client.py
```python
import httpx
from app.config import settings

class CarClient:
    def __init__(self):
        self.base_url = settings.CAR_SERVICE_URL  # http://car-service:8002

    async def verify_car_exists(self, car_id: str) -> bool:
        url = f"{self.base_url}/api/cars/{car_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url)
                return response.status_code == 200
            except httpx.RequestError:
                return False
```

### Использование в order_service.py
```python
async def create_order(self, request: CreateOrderRequest) -> OrderResponse:
    # КРИТИЧЕСКИЙ ШАГ: проверка существования автомобиля
    car_exists = await self.car_client.verify_car_exists(str(request.car_id))
    if not car_exists:
        raise ValueError(f"Car with ID {request.car_id} not found")

    # Создание заказа
    order = self.repository.create_order({...})
    return OrderResponse(**order)
```

## Конфигурация

### app/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "order-service"
    port: int = 8003
    CAR_SERVICE_URL: str = "http://car-service:8002"  # ВАЖНО!
```

### Environment Variables
```bash
CAR_SERVICE_URL=http://car-service:8002
```

## Зависимости

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2  # Для HTTP клиента
```

## Запуск

### Docker (с зависимостью)
```bash
docker-compose up car-service order-service
```

**docker-compose.yml фрагмент**:
```yaml
order-service:
  build: ./order-service
  ports:
    - "8003:8003"
  environment:
    - CAR_SERVICE_URL=http://car-service:8002
  depends_on:
    - car-service
```

## Типичные задачи

### 1. Добавление нового статуса
Изменить:
- `app/models/order.py` - добавить в Literal["created", "new_status", ...]
- `app/services/order_service.py` - обновить STATE_TRANSITIONS

### 2. Изменение URL car-service
Изменить переменную окружения `CAR_SERVICE_URL` в docker-compose.yml

### 3. Добавление timeout/retry логики
Изменить `app/services/car_client.py`:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
async def verify_car_exists(self, car_id: str) -> bool:
    # ...
```

## Проблемы и решения

### order-service возвращает 404 при создании заказа
**Причины**:
1. car-service не запущен → `docker-compose ps car-service`
2. Неверный CAR_SERVICE_URL → проверить environment в docker-compose.yml
3. car_id не существует в car-service → добавить автомобиль через POST /api/cars

**Отладка**:
```bash
# Проверить доступность car-service
docker-compose exec order-service curl http://car-service:8002/health

# Логи HTTP запросов
docker-compose logs order-service | grep "GET.*car-service"
```

### Connection refused при вызове car-service
**Решение**: Убедиться что в docker-compose.yml:
- car-service запущен раньше order-service (depends_on)
- Используется service name "car-service", а не "localhost"

## Swagger UI
http://localhost:8003/docs
