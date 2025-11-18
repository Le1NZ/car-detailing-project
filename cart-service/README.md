# Cart Service

Микросервис управления корзиной покупок для автосервиса.

## Описание

Cart Service предоставляет функциональность управления корзиной покупок для товаров и услуг автосервиса. Использует in-memory хранилище для временного хранения данных корзины.

## Архитектура

Проект реализован с использованием трехслойной архитектуры:

```
cart-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение, роутинг
│   ├── config.py            # Конфигурация сервиса
│   ├── models/
│   │   └── cart.py          # Pydantic модели
│   ├── repositories/
│   │   └── local_cart_repo.py  # In-memory хранилище
│   ├── services/
│   │   └── cart_service.py  # Бизнес-логика
│   └── endpoints/
│       └── cart.py          # HTTP endpoints
├── requirements.txt
├── Dockerfile
└── README.md
```

## API Endpoints

### 1. GET /api/cart
Получение корзины текущего пользователя

**Response:** `200 OK`
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {
      "item_id": "svc_oil_change",
      "type": "service",
      "name": "Замена масла",
      "quantity": 1,
      "price": 2500.00
    }
  ],
  "total_price": 2500.00
}
```

### 2. POST /api/cart/items
Добавление товара/услуги в корзину

**Request Body:**
```json
{
  "item_id": "svc_oil_change",
  "type": "service",
  "quantity": 1
}
```

**Response:** `200 OK`
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [...],
  "total_price": 2500.00
}
```

**Errors:**
- `404 Not Found` - item_id не найден в каталоге
- `400 Bad Request` - несоответствие типа товара/услуги

### 3. DELETE /api/cart/items/{item_id}
Удаление товара/услуги из корзины

**Response:** `204 No Content`

**Errors:**
- `404 Not Found` - item_id не найден в корзине

## Каталог товаров и услуг

Сервис использует встроенный каталог:

```python
CATALOG = {
    "svc_oil_change": {
        "type": "service",
        "name": "Замена масла",
        "price": 2500.00
    },
    "prod_oil_filter": {
        "type": "product",
        "name": "Масляный фильтр",
        "price": 1000.00
    },
    "svc_diagnostics": {
        "type": "service",
        "name": "Диагностика",
        "price": 1500.00
    }
}
```

## Технологический стек

- **Python**: 3.11
- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Validation**: Pydantic 2.5.0
- **Storage**: In-memory (Dict)

## Запуск сервиса

### Локальный запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск сервиса
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

### Запуск в Docker

```bash
# Сборка образа
docker build -t cart-service .

# Запуск контейнера
docker run -p 8004:8004 cart-service
```

### Запуск через Docker Compose

```bash
docker-compose up cart-service
```

## Документация API

После запуска сервиса документация доступна по адресам:
- Swagger UI: http://localhost:8004/docs
- ReDoc: http://localhost:8004/redoc

## Health Check

Проверка состояния сервиса:
```bash
curl http://localhost:8004/health
```

Response:
```json
{
  "status": "healthy",
  "service": "cart-service",
  "version": "1.0.0"
}
```

## Бизнес-логика

1. **Добавление товара**: При добавлении товара, который уже есть в корзине, увеличивается его количество
2. **Расчет стоимости**: `total_price = sum(item.price * item.quantity)` для всех товаров
3. **Пустая корзина**: Если у пользователя нет корзины, возвращается пустой список с total_price = 0
4. **Mock User ID**: Используется фиксированный UUID для тестирования

## Особенности реализации

- **In-memory storage**: Данные хранятся только в оперативной памяти (теряются при перезапуске)
- **Singleton pattern**: Репозиторий и сервис создаются один раз при старте
- **Dependency Injection**: FastAPI DI используется для внедрения зависимостей
- **Валидация**: Pydantic обеспечивает автоматическую валидацию данных
- **Type hints**: Полная типизация для повышения надежности кода

## Примеры использования

### Добавить товар в корзину
```bash
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_oil_change",
    "type": "service",
    "quantity": 1
  }'
```

### Получить корзину
```bash
curl http://localhost:8004/api/cart
```

### Удалить товар из корзины
```bash
curl -X DELETE http://localhost:8004/api/cart/items/svc_oil_change
```

## Соответствие требованиям ПР №6

- Трехслойная архитектура (endpoints → services → repositories)
- In-memory хранилище через LocalCartRepo
- Каталог товаров/услуг в cart_service.py
- Все указанные Pydantic модели
- Корректные HTTP коды ответов (200, 204, 404)
- Расчет total_price
- Mock user_id для тестирования
- Dockerfile с Python 3.11-slim
- Requirements.txt с указанными зависимостями
