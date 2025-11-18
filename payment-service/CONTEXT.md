# Payment Service - Контекст для LLM агентов

## Назначение
Обработка платежей + **RabbitMQ Publisher**. Публикует событие `payment_succeeded` после успешной оплаты.

## Роль
- **Порт**: 8005
- **Хранилище**: In-memory
- **RabbitMQ**: Publisher в очередь `payment_succeeded_queue`
- **Зависимость**: RabbitMQ должен быть healthy

## API

### POST /api/payments
Инициация платежа. Запускает фоновую задачу обработки (5 секунд).

**Request**:
```json
{
  "order_id": "ord_a1b2c3d4",
  "payment_method": "card"
}
```

**Response (201)**:
```json
{
  "payment_id": "pay_9a8b7c6d",
  "order_id": "ord_a1b2c3d4",
  "status": "pending",
  "amount": 4500.00,
  "currency": "RUB",
  "confirmation_url": "https://..."
}
```

### GET /api/payments/{payment_id}
Проверка статуса. Возвращает `succeeded` после обработки.

## RabbitMQ Integration (КРИТИЧНО)

### app/services/rabbitmq_publisher.py
```python
import aio_pika
import json

class RabbitMQPublisher:
    async def connect(self, amqp_url: str):
        self.connection = await aio_pika.connect_robust(amqp_url)
        self.channel = await self.connection.channel()
        self.queue = await self.channel.declare_queue("payment_succeeded_queue", durable=True)

    async def publish_payment_success(self, order_id: str, user_id: str, amount: float):
        message = json.dumps({"order_id": order_id, "user_id": user_id, "amount": amount})
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=message.encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key="payment_succeeded_queue"
        )
```

### Использование
```python
async def _process_payment_async(payment_id, order_id, user_id, amount):
    await asyncio.sleep(5)  # Симуляция обработки
    # Обновить статус на "succeeded"
    await rabbitmq_publisher.publish_payment_success(order_id, user_id, amount)
```

## Конфигурация

### Environment
```bash
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
```

### docker-compose.yml
```yaml
payment-service:
  environment:
    - AMQP_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    rabbitmq:
      condition: service_healthy
```

## Зависимости
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
aio-pika==9.3.1  # RabbitMQ async client
```

## Типичные задачи

### Изменение очереди
Редактировать `rabbitmq_publisher.py`: `declare_queue("new_queue_name", ...)`

### Изменение формата сообщения
Редактировать `publish_payment_success()` - изменить JSON структуру

### Добавление retry логики
Использовать `aio_pika.connect_robust()` (уже используется) - автоматические реконнекты

## Проблемы

### Connection refused к RabbitMQ
**Решение**:
- Проверить что RabbitMQ healthy: `docker-compose ps rabbitmq`
- Проверить AMQP_URL в environment
- Логи: `docker-compose logs rabbitmq`

### Сообщения не доставляются
**Решение**:
- Проверить RabbitMQ Management UI: http://localhost:15672 (guest/guest)
- Убедиться что очередь `payment_succeeded_queue` создана
- Проверить что bonus-service слушает ту же очередь

## Тестирование

1. Инициировать платеж:
```bash
curl -X POST http://localhost:8005/api/payments -H "Content-Type: application/json" -d '{"order_id":"test","payment_method":"card"}'
```

2. Проверить RabbitMQ UI через 5 секунд - должно появиться сообщение

3. Проверить логи bonus-service - должно быть начисление бонусов

Swagger: http://localhost:8005/docs
