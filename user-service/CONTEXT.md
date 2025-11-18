# User Service - Контекст для LLM агентов

## Назначение микросервиса
user-service отвечает за регистрацию и аутентификацию пользователей в системе автомобильного детейлинга. Это единственный сервис с подключением к PostgreSQL базе данных.

## Роль в архитектуре
- **Порт**: 8001
- **База данных**: PostgreSQL (единственный сервис с БД)
- **Хранилище**: PostgreSQL через SQLAlchemy (async)
- **Миграции**: Alembic (автоматическое применение при старте)
- **Безопасность**: JWT токены, bcrypt хеширование паролей

## API Endpoints

### POST /api/users/register
Регистрация нового пользователя

**Request**:
```json
{
  "email": "client@example.com",
  "password": "strongpassword123",
  "full_name": "Иванов Петр Сергеевич",
  "phone_number": "+79991234567"
}
```

**Response (201 Created)**:
```json
{
  "user_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
  "email": "client@example.com",
  "full_name": "Иванов Петр Сергеевич",
  "created_at": "2024-05-21T12:00:00Z"
}
```

**Коды ответов**:
- 201 Created - успешная регистрация
- 409 Conflict - email или phone_number уже существует
- 422 Unprocessable Entity - невалидные данные

### POST /api/users/login
Аутентификация пользователя

**Request**:
```json
{
  "email": "client@example.com",
  "password": "strongpassword123"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Коды ответов**:
- 200 OK - успешная аутентификация
- 401 Unauthorized - неверные credentials
- 422 Unprocessable Entity - невалидные данные

## Структура проекта

```
user-service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI приложение с lifespan
│   ├── config.py                  # Pydantic Settings (POSTGRES_URL, JWT_*)
│   ├── database.py                # Async SQLAlchemy engine
│   ├── models/
│   │   └── user.py                # Pydantic модели (Request/Response)
│   ├── schemas/
│   │   └── user.py                # SQLAlchemy ORM модель User
│   ├── repositories/
│   │   └── db_user_repo.py        # UserRepository (async CRUD)
│   ├── services/
│   │   └── user_service.py        # UserService (бизнес-логика)
│   └── endpoints/
│       └── users.py               # FastAPI роутер
├── alembic/
│   ├── versions/
│   │   └── 001_create_users_table.py
│   └── env.py                     # Async Alembic env
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

## База данных

### Таблица users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone_number);
```

### Connection String
```
postgresql+asyncpg://detailing_user:detailing_pass@postgres-db:5432/detailing_db
```

## Ключевые файлы

### app/schemas/user.py - SQLAlchemy модель
```python
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
```

### app/repositories/db_user_repo.py - Репозиторий
Ключевые методы:
- `async def create_user(user_data)` - создание с IntegrityError обработкой
- `async def get_user_by_email(email)` - поиск по email
- `async def check_email_exists(email)` - проверка уникальности
- `async def check_phone_exists(phone)` - проверка уникальности

### app/services/user_service.py - Сервис
Ключевые методы:
- `async def register_user(request)` - валидация, хеширование, создание
- `async def authenticate_user(request)` - проверка credentials, JWT генерация

## Зависимости

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
```

## Переменные окружения

```bash
POSTGRES_URL=postgresql+asyncpg://detailing_user:detailing_pass@postgres-db:5432/detailing_db
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_SECONDS=3600
```

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8001"]
```

**ВАЖНО**: Миграции применяются автоматически перед запуском сервиса!

## Alembic миграции

### Применение миграций
```bash
# Автоматически при старте Docker контейнера
alembic upgrade head

# Локально
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/user-service
alembic upgrade head
```

### Создание новой миграции
```bash
alembic revision --autogenerate -m "description"
```

## Безопасность

### Хеширование паролей
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Хеширование
hashed = pwd_context.hash("password")

# Проверка
is_valid = pwd_context.verify("password", hashed)
```

### JWT токены
```python
from jose import jwt
from datetime import datetime, timedelta

# Создание токена
token = jwt.encode(
    {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=1)},
    SECRET_KEY,
    algorithm="HS256"
)
```

## Типичные задачи для LLM агента

### 1. Добавление нового поля в User
1. Изменить `app/schemas/user.py` (SQLAlchemy модель)
2. Изменить `app/models/user.py` (Pydantic модели)
3. Создать миграцию: `alembic revision --autogenerate -m "add field"`
4. Обновить `app/repositories/db_user_repo.py` если нужны новые запросы
5. Обновить `app/services/user_service.py` для обработки нового поля

### 2. Добавление нового эндпоинта
1. Создать Pydantic модели в `app/models/user.py`
2. Добавить метод в `app/repositories/db_user_repo.py`
3. Добавить бизнес-логику в `app/services/user_service.py`
4. Добавить роут в `app/endpoints/users.py`

### 3. Изменение JWT логики
Редактировать `app/services/user_service.py` метод `authenticate_user()`

### 4. Отладка проблем с БД
- Проверить connection string в `app/config.py`
- Проверить миграции: `alembic current`
- Посмотреть логи: `docker-compose logs user-service`
- Проверить healthcheck postgres: `docker-compose ps postgres-db`

## Интеграция с другими сервисами

user-service работает автономно и НЕ вызывает другие микросервисы. Другие сервисы могут проверять JWT токены, выданные user-service (в будущем).

## Запуск и тестирование

### Локально
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/user-service
pip install -r requirements.txt
export POSTGRES_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Docker
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project
docker-compose up user-service postgres-db
```

### Тест регистрации
```bash
curl -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"password123",
    "full_name":"Test User",
    "phone_number":"+79991234567"
  }'
```

### Тест логина
```bash
curl -X POST http://localhost:8001/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"password123"
  }'
```

## Известные проблемы и решения

### Проблема: Миграции не применяются
**Решение**: Проверить CMD в Dockerfile, убедиться что `alembic upgrade head` выполняется перед `uvicorn`

### Проблема: Ошибка подключения к PostgreSQL
**Решение**:
- Убедиться что postgres-db запущен: `docker-compose ps postgres-db`
- Проверить healthcheck: должен быть "healthy"
- Проверить depends_on в docker-compose.yml

### Проблема: 409 Conflict при регистрации
**Решение**: Email или phone_number уже существуют в БД. Это корректное поведение.

### Проблема: 401 Unauthorized при логине
**Решение**: Неверный email или password. Проверить данные.

## Важные замечания для LLM агентов

1. **ВСЕГДА используй async/await** - весь код асинхронный
2. **UUID везде** - все ID это UUID, не int
3. **Проверяй уникальность** - email и phone_number должны быть уникальны
4. **Хешируй пароли** - НИКОГДА не храни plain text пароли
5. **Валидация через Pydantic** - используй field_validator для кастомной валидации
6. **IntegrityError обработка** - ловить в repository при нарушении UNIQUE constraints
7. **Миграции обязательны** - любое изменение схемы БД требует миграцию
8. **Connection pooling** - SQLAlchemy engine уже настроен с pooling

## Документация API
Swagger UI: http://localhost:8001/docs
ReDoc: http://localhost:8001/redoc
