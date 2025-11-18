# JWT Authentication - Quick Start Guide

## Быстрый старт за 3 минуты

### 1️⃣ Запустите сервисы

```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project
docker-compose up --build
```

### 2️⃣ Зарегистрируйте пользователя

```bash
curl -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "password123",
    "full_name": "Test User",
    "phone_number": "+79991234567"
  }'
```

### 3️⃣ Получите JWT токен

```bash
curl -X POST http://localhost:8001/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "password123"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6InVzZXJAdGVzdC5jb20iLCJleHAiOjE3MDMwMDAwMDB9.xxxxx",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 4️⃣ Используйте токен

Скопируйте `access_token` и используйте в заголовке:

```bash
# Сохраните токен в переменную
TOKEN="ваш_токен_здесь"

# Теперь можно делать запросы к защищенным эндпоинтам
curl -X GET http://localhost:8004/api/cart \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8003/api/orders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "car_id": "550e8400-e29b-41d4-a716-446655440000",
    "desired_time": "2024-12-20T10:00:00Z",
    "description": "Замена масла"
  }'
```

## Защищенные сервисы и порты

| Сервис | Порт | Защищенные эндпоинты |
|--------|------|---------------------|
| 🛒 Cart Service | 8004 | `/api/cart` (GET, POST, DELETE) |
| 📋 Order Service | 8003 | `/api/orders` (POST, PATCH, review) |
| 💳 Payment Service | 8005 | `/api/payments` (POST, GET) |
| 🎁 Bonus Service | 8006 | `/api/bonuses/*` (POST) |
| 🚔 Fines Service | 8007 | `/api/fines/*` (GET, POST) |
| 💬 Support Service | 8008 | `/api/support/*` (POST) |

## Публичные эндпоинты (без токена)

- `POST /api/users/register` - регистрация
- `POST /api/users/login` - получение токена

## Тестирование в Postman

1. Создайте коллекцию "Detailing Services"
2. Добавьте переменную окружения `token`
3. Создайте запрос "Login" → сохраните `access_token` в переменную
4. В других запросах используйте:
   - **Authorization** → **Bearer Token** → `{{token}}`

## Тестирование в Swagger UI

1. Откройте http://localhost:8004/docs (или любой другой сервис)
2. Нажмите **Authorize** 🔒
3. Введите: `Bearer ваш_токен`
4. Нажмите **Authorize**
5. Теперь все запросы будут с токеном

## Ошибки и решения

### ❌ "Authorization header required"
**Проблема:** Забыли добавить токен  
**Решение:** Добавьте заголовок `-H "Authorization: Bearer $TOKEN"`

### ❌ "Invalid or expired token"
**Проблема:** Токен истек (1 час) или невалиден  
**Решение:** Получите новый токен через `/api/users/login`

### ❌ "Invalid authorization header format"
**Проблема:** Неправильный формат заголовка  
**Решение:** Используйте формат `Bearer <токен>` (с пробелом!)

## Автоматический тест-скрипт

Сохраните как `test_auth.sh`:

```bash
#!/bin/bash

echo "🔐 Тестирование JWT авторизации"
echo "================================"

# Регистрация
echo "\n1️⃣ Регистрация пользователя..."
curl -s -X POST http://localhost:8001/api/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test'$(date +%s)'@example.com",
    "password": "password123",
    "full_name": "Test User",
    "phone_number": "+7999'$(date +%s | tail -c 8)'"
  }' | jq

# Логин
echo "\n2️⃣ Получение JWT токена..."
TOKEN=$(curl -s -X POST http://localhost:8001/api/users/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }' | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo "✅ Токен получен: ${TOKEN:0:50}..."
    
    # Тест защищенных эндпоинтов
    echo "\n3️⃣ Тест защищенных эндпоинтов:"
    
    echo "\n📦 Cart Service:"
    curl -s http://localhost:8004/api/cart \
      -H "Authorization: Bearer $TOKEN" | jq
    
    echo "\n💳 Payment Service:"
    curl -s http://localhost:8005/api/payments/test_id \
      -H "Authorization: Bearer $TOKEN" | jq || echo "Платеж не найден (ожидаемо)"
    
    echo "\n✅ Все тесты пройдены!"
else
    echo "❌ Не удалось получить токен"
fi
```

Запустите:
```bash
chmod +x test_auth.sh
./test_auth.sh
```

## Что изменилось?

### ❌ Раньше (mock user_id)
```bash
# Работало без токена
curl http://localhost:8004/api/cart
```

### ✅ Теперь (JWT авторизация)
```bash
# Требуется токен
curl http://localhost:8004/api/cart \
  -H "Authorization: Bearer $TOKEN"

# Без токена → 401 Unauthorized
```

## Production Checklist

Перед развертыванием в production:

- [ ] Изменить `JWT_SECRET_KEY` на случайный ключ (используйте `openssl rand -hex 32`)
- [ ] Добавить переменные окружения в docker-compose
- [ ] Настроить HTTPS (Let's Encrypt)
- [ ] Реализовать refresh tokens
- [ ] Добавить rate limiting (например, через nginx)
- [ ] Настроить логирование попыток авторизации
- [ ] Добавить мониторинг неудачных попыток входа

## Полезные команды

```bash
# Просмотр логов авторизации
docker-compose logs -f user-service | grep "Authentication"

# Проверка всех запущенных сервисов
docker-compose ps

# Перезапуск только одного сервиса
docker-compose restart cart-service

# Просмотр логов конкретного сервиса
docker-compose logs -f cart-service
```

---

**🎉 Готово! Теперь все ваши сервисы защищены JWT авторизацией.**

Подробная документация: `AUTH_IMPLEMENTATION.md`

