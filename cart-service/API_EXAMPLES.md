# Cart Service API Examples

## Базовый URL
```
http://localhost:8004
```

## 1. Health Check

### Request
```bash
curl http://localhost:8004/health
```

### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "cart-service",
  "version": "1.0.0"
}
```

---

## 2. Получить корзину (GET /api/cart)

### Request
```bash
curl http://localhost:8004/api/cart
```

### Response - Пустая корзина (200 OK)
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [],
  "total_price": 0.0
}
```

### Response - Корзина с товарами (200 OK)
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {
      "item_id": "svc_oil_change",
      "type": "service",
      "name": "Замена масла",
      "quantity": 2,
      "price": 2500.0
    },
    {
      "item_id": "prod_oil_filter",
      "type": "product",
      "name": "Масляный фильтр",
      "quantity": 1,
      "price": 1000.0
    }
  ],
  "total_price": 6000.0
}
```

---

## 3. Добавить товар/услугу (POST /api/cart/items)

### Добавить услугу "Замена масла"

#### Request
```bash
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_oil_change",
    "type": "service",
    "quantity": 1
  }'
```

#### Response (200 OK)
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {
      "item_id": "svc_oil_change",
      "type": "service",
      "name": "Замена масла",
      "quantity": 1,
      "price": 2500.0
    }
  ],
  "total_price": 2500.0
}
```

### Добавить товар "Масляный фильтр"

#### Request
```bash
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "prod_oil_filter",
    "type": "product",
    "quantity": 2
  }'
```

#### Response (200 OK)
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {
      "item_id": "svc_oil_change",
      "type": "service",
      "name": "Замена масла",
      "quantity": 1,
      "price": 2500.0
    },
    {
      "item_id": "prod_oil_filter",
      "type": "product",
      "name": "Масляный фильтр",
      "quantity": 2,
      "price": 1000.0
    }
  ],
  "total_price": 4500.0
}
```

### Добавить услугу "Диагностика"

#### Request
```bash
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_diagnostics",
    "type": "service",
    "quantity": 1
  }'
```

#### Response (200 OK)
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {
      "item_id": "svc_oil_change",
      "type": "service",
      "name": "Замена масла",
      "quantity": 1,
      "price": 2500.0
    },
    {
      "item_id": "prod_oil_filter",
      "type": "product",
      "name": "Масляный фильтр",
      "quantity": 2,
      "price": 1000.0
    },
    {
      "item_id": "svc_diagnostics",
      "type": "service",
      "name": "Диагностика",
      "quantity": 1,
      "price": 1500.0
    }
  ],
  "total_price": 6000.0
}
```

### Ошибка: товар не найден в каталоге

#### Request
```bash
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "invalid_item",
    "type": "service",
    "quantity": 1
  }'
```

#### Response (404 Not Found)
```json
{
  "detail": "Item 'invalid_item' not found in catalog"
}
```

---

## 4. Удалить товар из корзины (DELETE /api/cart/items/{item_id})

### Успешное удаление

#### Request
```bash
curl -X DELETE http://localhost:8004/api/cart/items/prod_oil_filter
```

#### Response (204 No Content)
```
(пустой ответ)
```

### Ошибка: товар не найден в корзине

#### Request
```bash
curl -X DELETE http://localhost:8004/api/cart/items/non_existent_item
```

#### Response (404 Not Found)
```json
{
  "detail": "Item 'non_existent_item' not found in cart"
}
```

---

## Доступные товары и услуги (CATALOG)

| ID | Тип | Название | Цена |
|---|---|---|---|
| `svc_oil_change` | service | Замена масла | 2500.00 ₽ |
| `prod_oil_filter` | product | Масляный фильтр | 1000.00 ₽ |
| `svc_diagnostics` | service | Диагностика | 1500.00 ₽ |

---

## Сценарий использования

### 1. Проверка здоровья сервиса
```bash
curl http://localhost:8004/health
```

### 2. Добавление нескольких товаров
```bash
# Добавить замену масла
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{"item_id": "svc_oil_change", "type": "service", "quantity": 1}'

# Добавить масляный фильтр (2 шт)
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{"item_id": "prod_oil_filter", "type": "product", "quantity": 2}'

# Добавить диагностику
curl -X POST http://localhost:8004/api/cart/items \
  -H "Content-Type: application/json" \
  -d '{"item_id": "svc_diagnostics", "type": "service", "quantity": 1}'
```

### 3. Просмотр корзины
```bash
curl http://localhost:8004/api/cart
```

Результат:
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [
    {"item_id": "svc_oil_change", "type": "service", "name": "Замена масла", "quantity": 1, "price": 2500.0},
    {"item_id": "prod_oil_filter", "type": "product", "name": "Масляный фильтр", "quantity": 2, "price": 1000.0},
    {"item_id": "svc_diagnostics", "type": "service", "name": "Диагностика", "quantity": 1, "price": 1500.0}
  ],
  "total_price": 6000.0
}
```

### 4. Удаление товара
```bash
curl -X DELETE http://localhost:8004/api/cart/items/prod_oil_filter
```

### 5. Финальная проверка корзины
```bash
curl http://localhost:8004/api/cart
```

---

## Swagger UI Documentation

Интерактивная документация доступна по адресу:
```
http://localhost:8004/docs
```

## ReDoc Documentation

Альтернативная документация:
```
http://localhost:8004/redoc
```
