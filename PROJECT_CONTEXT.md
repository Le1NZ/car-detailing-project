# Проект: Система автомобильного детейлинга - Общий контекст

## Описание проекта
Микросервисная система для управления автомобильным детейлингом, разработанная в рамках Практической Работы №6. Состоит из 8 микросервисов с различными паттернами взаимодействия.

## Академические требования (Практическая Работа №6)
- ✅ Трехслойная архитектура (models → repositories → services → endpoints)
- ✅ Python + FastAPI
- ✅ PostgreSQL + SQLAlchemy + Alembic (user-service)
- ✅ Синхронное HTTP взаимодействие (order-service → car-service)
- ✅ Асинхронное RabbitMQ взаимодействие (payment-service → bonus-service)
- ✅ Docker + docker-compose для всех сервисов
- ✅ Автоматическое применение миграций при старте

## Архитектура системы

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    USER     │     │     CAR     │     │    CART     │     │   SUPPORT   │
│  SERVICE    │     │   SERVICE   │     │   SERVICE   │     │   SERVICE   │
│   :8001     │     │    :8002    │     │    :8004    │     │    :8008    │
│ PostgreSQL  │     │  Stateless  │     │  In-memory  │     │  In-memory  │
└─────────────┘     └──────┬──────┘     └─────────────┘     └─────────────┘
                           │
                    HTTP GET (sync)
                           │
                    ┌──────▼──────┐
                    │    ORDER    │
                    │   SERVICE   │
                    │    :8003    │
                    │  In-memory  │
                    └─────────────┘

┌─────────────┐                           ┌─────────────┐
│   PAYMENT   │   RabbitMQ (async)        │    BONUS    │
│   SERVICE   ├──────payment_events──────▶│   SERVICE   │
│    :8005    │   payment_succeeded_queue │    :8006    │
│  Publisher  │                           │   Consumer  │
└─────────────┘                           └─────────────┘

┌─────────────┐
│    FINES    │
│   SERVICE   │
│    :8007    │
│  In-memory  │
└─────────────┘

Infrastructure:
┌──────────────┐        ┌──────────────┐
│  PostgreSQL  │        │   RabbitMQ   │
│    :5432     │        │  :5672/15672 │
└──────────────┘        └──────────────┘
```

## Микросервисы

### 1. user-service (8001)
- **Функция**: Регистрация и аутентификация пользователей
- **База данных**: PostgreSQL (единственный с БД)
- **Технологии**: SQLAlchemy (async), Alembic, JWT, bcrypt
- **API**: POST /api/users/register, POST /api/users/login
- **Файл контекста**: `user-service/CONTEXT.md`

### 2. car-service (8002)
- **Функция**: Каталог автомобилей
- **Хранилище**: In-memory (stateless)
- **Критичный эндпоинт**: GET /api/cars/{car_id} (используется order-service)
- **API**: POST /api/cars, GET /api/cars/{car_id}, POST /api/cars/{car_id}/documents
- **Файл контекста**: `car-service/CONTEXT.md`

### 3. order-service (8003)
- **Функция**: Управление заказами на обслуживание
- **Особенность**: Делает HTTP GET к car-service для валидации car_id
- **Технологии**: httpx (HTTP client)
- **API**: POST /api/orders, PATCH /api/orders/{id}/status, POST /api/orders/review
- **Файл контекста**: `order-service/CONTEXT.md`

### 4. cart-service (8004)
- **Функция**: Корзина товаров и услуг
- **Хранилище**: In-memory с каталогом CATALOG
- **API**: GET /api/cart, POST /api/cart/items, DELETE /api/cart/items/{id}
- **Файл контекста**: `cart-service/CONTEXT.md`

### 5. payment-service (8005)
- **Функция**: Обработка платежей + RabbitMQ Publisher
- **Особенность**: Публикует события в очередь после успешной оплаты
- **Технологии**: aio-pika, asyncio.create_task
- **API**: POST /api/payments, GET /api/payments/{id}
- **Файл контекста**: `payment-service/CONTEXT.md`

### 6. bonus-service (8006)
- **Функция**: Бонусная система + RabbitMQ Consumer
- **Особенность**: Слушает очередь payment_succeeded_queue, автоначисление 1%
- **Технологии**: aio-pika, lifespan events
- **API**: POST /api/bonuses/promocodes/apply, POST /api/bonuses/spend
- **Файл контекста**: `bonus-service/CONTEXT.md`

### 7. fines-service (8007)
- **Функция**: Проверка и оплата штрафов
- **Хранилище**: In-memory с тестовыми данными
- **API**: GET /api/fines/check, POST /api/fines/{id}/pay
- **Файл контекста**: `fines-service/CONTEXT.md`

### 8. support-service (8008)
- **Функция**: Служба поддержки (тикет-система)
- **Хранилище**: In-memory
- **API**: POST /api/support/tickets, POST /api/support/tickets/{id}/messages
- **Файл контекста**: `support-service/CONTEXT.md`

## Паттерны взаимодействия

### 1. Синхронное HTTP (order → car)
**Реализовано в**: order-service
**Библиотека**: httpx

```python
# order-service/app/services/car_client.py
async with httpx.AsyncClient() as client:
    response = await client.get(f"http://car-service:8002/api/cars/{car_id}")
    if response.status_code == 200:
        # Автомобиль существует
    else:
        # 404 - автомобиль не найден
```

**Проверка**: Создать заказ с несуществующим car_id → ожидается 404

### 2. Асинхронное RabbitMQ (payment → bonus)
**Publisher**: payment-service
**Consumer**: bonus-service
**Очередь**: payment_succeeded_queue

**Формат сообщения**:
```json
{
  "order_id": "uuid",
  "user_id": "uuid",
  "amount": 4500.00
}
```

**Проверка**:
1. POST /api/payments
2. Подождать 5 секунд (симуляция обработки)
3. Проверить логи bonus-service: должно быть "Accrued X bonuses to user ..."

### 3. PostgreSQL (user → postgres-db)
**Реализовано в**: user-service
**Драйвер**: asyncpg
**ORM**: SQLAlchemy (async)
**Миграции**: Alembic (автоматически при старте)

**Connection String**:
```
postgresql+asyncpg://detailing_user:detailing_pass@postgres-db:5432/detailing_db
```

## Структура проекта

```
project/
├── user-service/              # PostgreSQL + JWT
│   ├── app/
│   ├── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── car-service/               # Stateless
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── order-service/             # HTTP client
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── cart-service/              # In-memory cart
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── payment-service/           # RabbitMQ Publisher
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── bonus-service/             # RabbitMQ Consumer
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── fines-service/             # Fines management
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── support-service/           # Ticket system
│   ├── app/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── CONTEXT.md
├── docker-compose.yml         # Orchestration
├── README.md                  # User documentation
├── PROJECT_CONTEXT.md         # Этот файл
└── DOCKER_DEPLOYMENT.md       # Deployment guide
```

## Технологический стек

### Общие зависимости
- Python 3.11
- FastAPI 0.104.1
- Uvicorn 0.24.0
- Pydantic 2.5.0

### Специфичные для сервисов
- **user-service**: SQLAlchemy, asyncpg, Alembic, passlib, python-jose
- **order-service**: httpx
- **payment-service**: aio-pika
- **bonus-service**: aio-pika

## Переменные окружения

### user-service
```bash
POSTGRES_URL=postgresql+asyncpg://detailing_user:detailing_pass@postgres-db:5432/detailing_db
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_SECONDS=3600
```

### order-service
```bash
CAR_SERVICE_URL=http://car-service:8002
```

### payment-service
```bash
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
```

### bonus-service
```bash
AMQP_URL=amqp://guest:guest@rabbitmq:5672/
BONUS_ACCRUAL_RATE=0.01
```

## Порты сервисов

| Сервис | Порт | URL |
|--------|------|-----|
| user-service | 8001 | http://localhost:8001 |
| car-service | 8002 | http://localhost:8002 |
| order-service | 8003 | http://localhost:8003 |
| cart-service | 8004 | http://localhost:8004 |
| payment-service | 8005 | http://localhost:8005 |
| bonus-service | 8006 | http://localhost:8006 |
| fines-service | 8007 | http://localhost:8007 |
| support-service | 8008 | http://localhost:8008 |
| postgres-db | 5432 | N/A (internal) |
| rabbitmq | 5672 | N/A (AMQP) |
| rabbitmq-ui | 15672 | http://localhost:15672 |

## Запуск проекта

### Полный запуск всех сервисов
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project
docker-compose up --build -d
```

### Проверка статуса
```bash
docker-compose ps
```

### Просмотр логов
```bash
docker-compose logs -f
docker-compose logs <service-name>
```

### Остановка
```bash
docker-compose down
docker-compose down -v  # С удалением volumes
```

## Тестирование системы

### 1. Health checks
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
# ... для всех сервисов
```

### 2. Тест регистрации пользователя
```bash
curl -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","full_name":"Test User","phone_number":"+79991234567"}'
```

### 3. Тест HTTP взаимодействия (order → car)
```bash
# Добавить автомобиль
curl -X POST http://localhost:8002/api/cars -H "Content-Type: application/json" \
  -d '{"owner_id":"550e8400-e29b-41d4-a716-446655440000","license_plate":"А123БВ799","vin":"XTA210930V0123456","make":"Lada","model":"Vesta","year":2021}'

# Создать заказ (проверка HTTP-вызова к car-service)
curl -X POST http://localhost:8003/api/orders -H "Content-Type: application/json" \
  -d '{"car_id":"<car_id>","desired_time":"2024-12-20T10:00:00Z","description":"ТО"}'
```

### 4. Тест RabbitMQ (payment → bonus)
```bash
# Инициировать платеж
curl -X POST http://localhost:8005/api/payments -H "Content-Type: application/json" \
  -d '{"order_id":"550e8400-e29b-41d4-a716-446655440000","payment_method":"card"}'

# Через 5 секунд проверить логи
docker-compose logs bonus-service | grep "Accrued"
```

## Типичные задачи для LLM агентов

### Добавление нового микросервиса
1. Создать директорию с трехслойной архитектурой
2. Создать Dockerfile
3. Добавить в docker-compose.yml
4. Создать CONTEXT.md
5. Обновить PROJECT_CONTEXT.md и README.md

### Изменение паттерна взаимодействия
1. Определить тип взаимодействия (sync/async)
2. Для HTTP: добавить HTTP client в services
3. Для RabbitMQ: добавить publisher/consumer
4. Обновить docker-compose.yml (depends_on, environment)

### Добавление новой функциональности
1. Определить в каком сервисе должна быть функция
2. Создать Pydantic модели
3. Добавить методы в repository
4. Добавить бизнес-логику в service
5. Добавить endpoint
6. Обновить CONTEXT.md сервиса

### Отладка проблем
1. Проверить статус: `docker-compose ps`
2. Посмотреть логи: `docker-compose logs <service>`
3. Проверить healthchecks для postgres/rabbitmq
4. Проверить переменные окружения в docker-compose.yml
5. Проверить depends_on между сервисами

## Известные проблемы

### user-service не стартует
**Причина**: PostgreSQL не healthy
**Решение**: Подождать 10-15 секунд, проверить `docker-compose ps postgres-db`

### order-service возвращает 404 при создании заказа
**Причина**: car-service не запущен или car_id не существует
**Решение**: Проверить car-service, добавить автомобиль

### bonus-service не получает события
**Причина**: RabbitMQ не запущен или очереди нет
**Решение**: Проверить RabbitMQ Management UI (localhost:15672)

### Данные теряются после перезапуска
**Причина**: In-memory хранилище (кроме user-service)
**Решение**: Это нормальное поведение для stateless сервисов

## Расширение проекта

### Добавление API Gateway
Использовать nginx или Kong для единой точки входа

### Добавление аутентификации
Использовать JWT токены из user-service для защиты эндпоинтов

### Добавление мониторинга
Prometheus + Grafana для метрик, ELK для логов

### Добавление CI/CD
GitHub Actions для автоматических тестов и деплоя

## Ссылки на документацию

- Swagger UI для всех сервисов: http://localhost:800X/docs (где X = 1-8)
- RabbitMQ Management: http://localhost:15672 (guest/guest)
- Общая документация: `README.md`
- Деплой: `DOCKER_DEPLOYMENT.md`
- Контекст сервисов: `<service-name>/CONTEXT.md`

## Контакты и поддержка

Проект разработан для Практической Работы №6 по микросервисной архитектуре.
Все сервисы следуют единым стандартам FastAPI и best practices Python.
