# Bonus Service

Микросервис для управления бонусной системой и промокодами.

## Описание

Bonus Service отвечает за:
- Применение промокодов к заказам
- Списание бонусов пользователей
- Автоматическое начисление бонусов при успешной оплате (через RabbitMQ)

## Архитектура

Трехслойная архитектура:
- **Endpoints** (`app/endpoints/`) - REST API endpoints
- **Services** (`app/services/`) - Бизнес-логика
- **Repositories** (`app/repositories/`) - Слой доступа к данным (in-memory)

## API Endpoints

### POST /api/bonuses/promocodes/apply
Применить промокод к заказу

**Request Body:**
```json
{
  "order_id": "ord_a1b2c3d4",
  "promocode": "SUMMER24"
}
```

**Response (200 OK):**
```json
{
  "order_id": "ord_a1b2c3d4",
  "promocode": "SUMMER24",
  "status": "applied",
  "discount_amount": 500.00
}
```

**Errors:**
- 404 Not Found - промокод недействителен

### POST /api/bonuses/spend
Списать бонусы с баланса пользователя

**Request Body:**
```json
{
  "order_id": "ord_a1b2c3d4",
  "amount": 1000
}
```

**Response (200 OK):**
```json
{
  "order_id": "ord_a1b2c3d4",
  "bonuses_spent": 1000,
  "new_balance": 2500.0
}
```

**Errors:**
- 400 Bad Request - недостаточно бонусов

### GET /health
Проверка здоровья сервиса

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "bonus-service"
}
```

## RabbitMQ Integration

Сервис подписан на очередь `payment_succeeded_queue` для автоматического начисления бонусов.

**Формат сообщения:**
```json
{
  "order_id": "uuid",
  "user_id": "uuid",
  "amount": 10000.00
}
```

**Логика начисления:** 1% от суммы платежа

## Предзаполненные промокоды

- `SUMMER24` - скидка 500 руб.
- `WELCOME10` - скидка 1000 руб.

## Конфигурация

Переменные окружения (или `.env` файл):

```env
SERVICE_NAME=bonus-service
SERVICE_PORT=8006
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
PAYMENT_QUEUE=payment_succeeded_queue
BONUS_ACCRUAL_RATE=0.01
```

## Запуск

### С Docker
```bash
docker build -t bonus-service .
docker run -p 8006:8006 bonus-service
```

### С Docker Compose
```bash
docker-compose up bonus-service
```

### Локально
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8006
```

## Технологии

- **FastAPI** - веб-фреймворк
- **Pydantic** - валидация данных
- **aio-pika** - асинхронный клиент RabbitMQ
- **Python 3.11** - язык программирования

## Структура проекта

```
bonus-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение
│   ├── config.py               # Конфигурация
│   ├── models/
│   │   └── bonus.py            # Pydantic модели
│   ├── repositories/
│   │   └── local_bonus_repo.py # In-memory хранилище
│   ├── services/
│   │   ├── bonus_service.py    # Бизнес-логика
│   │   └── rabbitmq_consumer.py # RabbitMQ consumer
│   └── endpoints/
│       └── bonuses.py          # API endpoints
├── requirements.txt
├── Dockerfile
└── README.md
```

## Логирование

Сервис логирует все важные события:
- Применение промокодов
- Списание бонусов
- Начисление бонусов через RabbitMQ
- Ошибки и предупреждения

Уровень логирования: INFO
