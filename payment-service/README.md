# Payment Service

Микросервис обработки платежей с поддержкой RabbitMQ Publisher.

## Архитектура

Сервис реализован по трехслойной архитектуре:

1. **Endpoints Layer** (`app/endpoints/`) - HTTP API endpoints (контроллеры)
2. **Services Layer** (`app/services/`) - бизнес-логика и интеграции
3. **Repositories Layer** (`app/repositories/`) - работа с данными

## Основные компоненты

### RabbitMQ Publisher
- Подключение к RabbitMQ при старте приложения
- Публикация событий в очередь `payment_succeeded_queue`
- Формат сообщения:
  ```json
  {
    "order_id": "ord_a1b2c3d4",
    "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
    "amount": 4500.00
  }
  ```

### Процесс обработки платежа

1. POST /api/payments - создание платежа со статусом `pending`
2. Запуск фоновой задачи (asyncio.create_task)
3. Симуляция обработки платежа (5 секунд)
4. Обновление статуса на `succeeded`
5. Публикация события в RabbitMQ

## API Endpoints

### POST /api/payments
Создание нового платежа.

**Request:**
```json
{
  "order_id": "ord_a1b2c3d4",
  "payment_method": "card"
}
```

**Response (201):**
```json
{
  "payment_id": "pay_9a8b7c6d",
  "order_id": "ord_a1b2c3d4",
  "status": "pending",
  "amount": 4500.00,
  "currency": "RUB",
  "confirmation_url": "https://payment.gateway/confirm?token=..."
}
```

**Errors:**
- 404 Not Found - заказ не найден
- 409 Conflict - заказ уже оплачен

### GET /api/payments/{payment_id}
Получение статуса платежа.

**Response (200):**
```json
{
  "payment_id": "pay_9a8b7c6d",
  "status": "succeeded",
  "paid_at": "2024-06-11T14:30:00Z"
}
```

**Errors:**
- 404 Not Found - платеж не найден

### GET /health
Health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "payment-service",
  "rabbitmq_connected": true
}
```

## Запуск

### Локально
```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск (требуется RabbitMQ)
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### Docker
```bash
# Сборка образа
docker build -t payment-service .

# Запуск контейнера
docker run -p 8005:8005 \
  -e AMQP_URL=amqp://guest:guest@rabbitmq:5672/ \
  payment-service
```

## Конфигурация

Настройки задаются через переменные окружения или файл `.env`:

- `SERVICE_NAME` - название сервиса (по умолчанию: payment-service)
- `PORT` - порт приложения (по умолчанию: 8005)
- `AMQP_URL` - URL подключения к RabbitMQ (по умолчанию: amqp://guest:guest@rabbitmq:5672/)

## Зависимости

- FastAPI 0.104.1 - веб-фреймворк
- Uvicorn 0.24.0 - ASGI сервер
- Pydantic 2.5.0 - валидация данных
- pydantic-settings 2.1.0 - управление настройками
- aio-pika 9.3.1 - асинхронный клиент для RabbitMQ

## Тестовые данные

Сервис содержит заглушку с тестовыми заказами:

```python
"ord_a1b2c3d4": {
    "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
    "amount": 4500.00
}
"ord_test123": {
    "user_id": "test-user-id-123",
    "amount": 2500.00
}
```

## Логирование

Все операции логируются с уровнями:
- INFO - успешные операции
- WARNING - не найденные ресурсы
- ERROR - ошибки обработки

Формат: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
