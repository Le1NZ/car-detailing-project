# Bonus Service - Контекст для LLM агентов

## Назначение
Управление бонусами + **RabbitMQ Consumer**. Автоматически начисляет бонусы при получении события от payment-service.

## Роль
- **Порт**: 8006
- **Хранилище**: In-memory Dict[UUID, float] для балансов
- **RabbitMQ**: Consumer очереди `payment_succeeded_queue`
- **Зависимость**: RabbitMQ должен быть healthy

## API

### POST /api/bonuses/promocodes/apply
Применение промокода к заказу

**Request**:
```json
{
  "order_id": "uuid",
  "promocode": "SUMMER24"
}
```

### POST /api/bonuses/spend
Списание бонусов с баланса

**Request**:
```json
{
  "order_id": "uuid",
  "amount": 100
}
```

## RabbitMQ Consumer (КРИТИЧНО)

### app/services/rabbitmq_consumer.py
```python
import aio_pika
import json

class RabbitMQConsumer:
    async def start(self):
        connection = await aio_pika.connect_robust(settings.AMQP_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue("payment_succeeded_queue", durable=True)

        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                body = json.loads(message.body.decode())
                order_id = body["order_id"]
                user_id = body["user_id"]
                amount = body["amount"]

                # Начисление 1% бонусов
                bonuses = amount * 0.01
                await self.bonus_service.accrue_bonuses(user_id, order_id, amount, rate=0.01)

        await queue.consume(on_message)
```

### Запуск через lifespan
```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    rabbitmq_consumer = RabbitMQConsumer(bonus_service=bonus_service)
    await rabbitmq_consumer.start()
    yield
    # Shutdown
    await rabbitmq_consumer.stop()

app = FastAPI(lifespan=lifespan)
```

## Промокоды

### app/repositories/local_bonus_repo.py
```python
PROMOCODES = [
    {"code": "SUMMER24", "discount_amount": 500.00, "active": True},
    {"code": "WELCOME10", "discount_amount": 1000.00, "active": True}
]
```

## Конфигурация

```bash
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
BONUS_ACCRUAL_RATE=0.01  # 1%
```

## Зависимости
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
aio-pika==9.3.1
```

## Типичные задачи

### Изменение процента бонусов
Редактировать `settings.BONUS_ACCRUAL_RATE` или константу в коде (по умолчанию 0.01 = 1%)

### Добавление промокода
Добавить в `PROMOCODES` list в `app/repositories/local_bonus_repo.py`

### Изменение логики начисления
Редактировать `accrue_bonuses()` в `app/services/bonus_service.py`

## Проблемы

### Бонусы не начисляются
**Решение**:
1. Проверить что bonus-service запущен
2. Проверить логи: `docker-compose logs bonus-service | grep "Accrued"`
3. Проверить RabbitMQ Management UI - есть ли consumer на очереди
4. Убедиться что payment-service публикует сообщения

### Consumer не стартует
**Решение**:
- Проверить `lifespan` в main.py
- Проверить AMQP_URL
- Логи: `docker-compose logs bonus-service | grep "RabbitMQ"`

## Тестирование интеграции

1. Запустить payment-service и bonus-service
2. Создать платеж в payment-service
3. Через 5 секунд проверить логи bonus-service:
```bash
docker-compose logs bonus-service
# Ожидается: "Accrued 45.0 bonuses to user ..." (если amount=4500)
```

Swagger: http://localhost:8006/docs
