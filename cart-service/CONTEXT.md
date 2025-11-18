# Cart Service - Контекст для LLM агентов

## Назначение
Управление корзиной товаров/услуг для пользователей. In-memory хранилище с каталогом предопределенных услуг.

## Роль
- **Порт**: 8004
- **Хранилище**: In-memory Dict[UUID, List[CartItem]]
- **Тип**: Stateless с каталогом услуг

## API

### GET /api/cart
Получение корзины текущего пользователя. Возвращает пустую корзину если нет items.

### POST /api/cart/items
Добавление товара/услуги из каталога. Увеличивает quantity если уже есть.

**Request**:
```json
{
  "item_id": "svc_oil_change",
  "type": "service",
  "quantity": 1
}
```

### DELETE /api/cart/items/{item_id}
Удаление из корзины. Возвращает 204 No Content.

## Каталог услуг

### app/services/cart_service.py
```python
CATALOG = {
    "svc_oil_change": {"type": "service", "name": "Замена масла", "price": 2500.00},
    "prod_oil_filter": {"type": "product", "name": "Масляный фильтр", "price": 1000.00},
    "svc_diagnostics": {"type": "service", "name": "Диагностика", "price": 1500.00}
}
```

## Repository

```python
class LocalCartRepository:
    def __init__(self):
        self.carts: Dict[UUID, List[CartItem]] = {}
```

## Типичные задачи

### Добавление нового товара в каталог
Редактировать `CATALOG` в `app/services/cart_service.py`

### Изменение логики total_price
Изменить расчет в `cart_service.py`:
```python
total_price = sum(item.price * item.quantity for item in items)
```

## Зависимости
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

## Запуск
```bash
docker-compose up cart-service
```

Swagger: http://localhost:8004/docs
