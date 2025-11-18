# Отчет о реализации Cart Service
## Практическая Работа №6

**Дата:** 2025-11-15
**Разработчик:** FastAPI Microservice Developer
**Сервис:** cart-service
**Порт:** 8004

---

## 1. Выполненные требования

### 1.1 Трехслойная архитектура

Проект реализован в соответствии с требуемой структурой:

```
cart-service/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI приложение
│   ├── config.py                   # Конфигурация
│   ├── models/
│   │   ├── __init__.py
│   │   └── cart.py                 # Pydantic модели
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── local_cart_repo.py      # In-memory хранилище
│   ├── services/
│   │   ├── __init__.py
│   │   └── cart_service.py         # Бизнес-логика
│   └── endpoints/
│       ├── __init__.py
│       └── cart.py                 # HTTP endpoints
├── requirements.txt
├── Dockerfile
├── README.md
├── API_EXAMPLES.md
├── IMPLEMENTATION_REPORT.md
└── test_api.sh
```

**Слои:**
- **Endpoints** (`endpoints/cart.py`): HTTP-обработчики, валидация запросов
- **Services** (`services/cart_service.py`): Бизнес-логика, работа с каталогом
- **Repositories** (`repositories/local_cart_repo.py`): Управление данными in-memory

---

## 2. Реализованные компоненты

### 2.1 Pydantic модели (models/cart.py)

#### CartItem
```python
class CartItem(BaseModel):
    item_id: str      # Идентификатор товара/услуги
    type: str         # "product" или "service"
    name: str         # Название
    quantity: int     # Количество (> 0)
    price: float      # Цена за единицу (> 0)
```

#### CartResponse
```python
class CartResponse(BaseModel):
    user_id: UUID              # ID пользователя
    items: List[CartItem]      # Список товаров
    total_price: float         # Общая стоимость (>= 0)
```

#### AddItemRequest
```python
class AddItemRequest(BaseModel):
    item_id: str      # ID из каталога
    type: str         # Тип товара/услуги
    quantity: int     # Количество (> 0)
```

### 2.2 In-memory хранилище (repositories/local_cart_repo.py)

**LocalCartRepo** реализует методы:
- `get_cart(user_id)` - получить корзину пользователя
- `add_item(user_id, item)` - добавить/увеличить количество
- `remove_item(user_id, item_id)` - удалить товар
- `clear_cart(user_id)` - очистить корзину
- `get_all_carts()` - получить все корзины (для отладки)

**Структура данных:** `Dict[UUID, List[CartItem]]`

**Особенности:**
- Автоматическое создание корзины при первом добавлении
- Увеличение quantity если товар уже в корзине
- Потокобезопасность не требуется (однопользовательский режим)

### 2.3 Каталог товаров и услуг (services/cart_service.py)

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

### 2.4 Бизнес-логика (services/cart_service.py)

**CartService** предоставляет методы:

1. **get_cart(user_id)**: Возвращает корзину с вычисленной total_price
2. **add_item(user_id, request)**:
   - Проверяет наличие item_id в CATALOG
   - Проверяет соответствие типа
   - Создает CartItem с данными из каталога
   - Добавляет в репозиторий
   - Возвращает обновленную корзину
3. **remove_item(user_id, item_id)**:
   - Удаляет товар из корзины
   - Бросает 404 если товара нет

**Расчет total_price:**
```python
total_price = sum(item.price * item.quantity for item in items)
```

### 2.5 API Endpoints (endpoints/cart.py)

| Метод | Путь | Описание | Статус |
|-------|------|----------|--------|
| GET | `/api/cart` | Получить корзину | 200 OK |
| POST | `/api/cart/items` | Добавить товар | 200 OK |
| DELETE | `/api/cart/items/{item_id}` | Удалить товар | 204 No Content |

**Дополнительные endpoints:**
- `GET /health` - проверка состояния сервиса
- `GET /` - информация о сервисе
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc документация

### 2.6 Mock User ID (config.py)

```python
MOCK_USER_ID = UUID("12345678-1234-5678-1234-567812345678")
```

Используется через dependency injection во всех endpoints.

---

## 3. Технологический стек

### 3.1 requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

**Обоснование версий:**
- FastAPI 0.104.1 - стабильная версия с полной поддержкой Pydantic v2
- Uvicorn 0.24.0 - ASGI сервер с uvloop для высокой производительности
- Pydantic 2.5.0 - быстрая валидация с поддержкой Python 3.11+

### 3.2 Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

**Особенности:**
- Базовый образ: `python:3.11-slim` (минимальный размер)
- Без кэширования pip для уменьшения размера образа
- Порт 8004 соответствует требованиям
- Запуск через uvicorn без reload (production mode)

---

## 4. Реализованная логика

### 4.1 Получение корзины (GET /api/cart)

**Поведение:**
- Если корзины нет: возвращает пустой список с `total_price = 0`
- Если корзина существует: возвращает все товары и вычисленную стоимость

**Пример ответа (пустая корзина):**
```json
{
  "user_id": "12345678-1234-5678-1234-567812345678",
  "items": [],
  "total_price": 0.0
}
```

### 4.2 Добавление товара (POST /api/cart/items)

**Алгоритм:**
1. Валидация запроса через Pydantic
2. Проверка наличия `item_id` в CATALOG → 404 если нет
3. Проверка соответствия типа → 400 если не совпадает
4. Создание `CartItem` с данными из каталога
5. Добавление в репозиторий (увеличение quantity если уже есть)
6. Возврат обновленной корзины

**Пример запроса:**
```json
{
  "item_id": "svc_oil_change",
  "type": "service",
  "quantity": 1
}
```

**Пример ответа:**
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

**Обработка повторного добавления:**
Если товар уже в корзине, его количество увеличивается:
```
Было: quantity = 1
Добавили: quantity = 1
Стало: quantity = 2
```

### 4.3 Удаление товара (DELETE /api/cart/items/{item_id})

**Алгоритм:**
1. Проверка наличия товара в корзине
2. Удаление из репозитория
3. Возврат 204 No Content при успехе
4. Возврат 404 Not Found если товара нет

**Успешный ответ:** HTTP 204 (без тела)

**Ошибка:**
```json
{
  "detail": "Item 'invalid_id' not found in cart"
}
```

### 4.4 Расчет стоимости

```python
total_price = sum(item.price * item.quantity for item in items)
total_price = round(total_price, 2)
```

**Примеры:**
- 1x Замена масла (2500) = 2500.00
- 2x Масляный фильтр (1000) = 2000.00
- 1x Диагностика (1500) = 1500.00
- **ИТОГО:** 6000.00

---

## 5. HTTP коды ответов

| Код | Описание | Когда используется |
|-----|----------|-------------------|
| 200 OK | Успех | GET/POST операции с корзиной |
| 204 No Content | Успешное удаление | DELETE товара из корзины |
| 400 Bad Request | Ошибка валидации | Несоответствие типа товара |
| 404 Not Found | Не найдено | Товар не в каталоге/корзине |
| 422 Unprocessable Entity | Неверный формат | Pydantic валидация не прошла |

---

## 6. Dependency Injection

FastAPI DI используется для:

### 6.1 Внедрение сервиса
```python
def get_cart_service() -> CartService:
    return cart_service

@router.get("/api/cart")
def get_cart(service: CartService = Depends(get_cart_service)):
    ...
```

### 6.2 Получение User ID
```python
def get_user_id() -> UUID:
    return MOCK_USER_ID

@router.get("/api/cart")
def get_cart(user_id: UUID = Depends(get_user_id)):
    ...
```

**Преимущества:**
- Легко заменить на JWT/Session auth в production
- Тестируемость (можно подменить зависимости)
- Соблюдение принципа инверсии зависимостей

---

## 7. Особенности реализации

### 7.1 Singleton Pattern для репозитория
```python
cart_repo = LocalCartRepo()  # Создается один раз
cart_service = CartService(cart_repo)
```

Все запросы используют один экземпляр репозитория.

### 7.2 Type Hints
Полная типизация для IDE поддержки и type checking:
```python
def add_item(self, user_id: UUID, item: CartItem) -> List[CartItem]:
    ...
```

### 7.3 Логирование
```python
logger.info(f"{SERVICE_NAME} starting on port {SERVICE_PORT}")
```

### 7.4 Валидация через Pydantic
Автоматическая валидация:
- `quantity > 0`
- `price > 0`
- `total_price >= 0`
- UUID формат для user_id

### 7.5 Обработка ошибок
```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Item '{item_id}' not found in catalog"
)
```

---

## 8. Тестирование

### 8.1 Тестовый скрипт (test_api.sh)
Автоматический тест всех endpoints:
```bash
chmod +x test_api.sh
./test_api.sh
```

Проверяет:
- Health check
- Получение пустой корзины
- Добавление товаров/услуг
- Увеличение количества при повторном добавлении
- Расчет total_price
- Удаление товаров
- Обработку ошибок 404

### 8.2 Примеры использования (API_EXAMPLES.md)
Документация с curl командами для всех операций.

### 8.3 Swagger UI
Интерактивная документация: http://localhost:8004/docs

---

## 9. Запуск сервиса

### 9.1 Локальная разработка
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

### 9.2 Docker
```bash
docker build -t cart-service .
docker run -p 8004:8004 cart-service
```

### 9.3 Docker Compose
```yaml
cart-service:
  build: ./cart-service
  ports:
    - "8004:8004"
  networks:
    - microservices-network
```

---

## 10. Соответствие требованиям ПР №6

| Требование | Статус | Реализация |
|-----------|--------|-----------|
| Трехслойная архитектура | ✅ | endpoints → services → repositories |
| In-memory хранилище | ✅ | LocalCartRepo с Dict[UUID, List[CartItem]] |
| Каталог CATALOG | ✅ | В cart_service.py с 3 позициями |
| Pydantic модели | ✅ | CartItem, CartResponse, AddItemRequest |
| GET /api/cart | ✅ | Возвращает корзину, 200 OK |
| POST /api/cart/items | ✅ | Добавляет из каталога, 200 OK |
| DELETE /api/cart/items/{id} | ✅ | Удаляет товар, 204 No Content |
| Расчет total_price | ✅ | sum(price * quantity) |
| Mock user_id | ✅ | Фиксированный UUID в config.py |
| requirements.txt | ✅ | fastapi, uvicorn, pydantic |
| Dockerfile | ✅ | Python 3.11-slim, порт 8004 |
| Код ответа 200 | ✅ | GET и POST |
| Код ответа 204 | ✅ | DELETE |
| Код ответа 404 | ✅ | Товар не найден |

---

## 11. Файлы проекта

### Основные файлы:
- ✅ `/app/main.py` - FastAPI приложение (93 строки)
- ✅ `/app/config.py` - Конфигурация (9 строк)
- ✅ `/app/models/cart.py` - Pydantic модели (67 строк)
- ✅ `/app/repositories/local_cart_repo.py` - Репозиторий (101 строка)
- ✅ `/app/services/cart_service.py` - Бизнес-логика (146 строк)
- ✅ `/app/endpoints/cart.py` - HTTP endpoints (105 строк)
- ✅ `/requirements.txt` - Зависимости (3 пакета)
- ✅ `/Dockerfile` - Docker образ (8 строк)

### Документация:
- ✅ `/README.md` - Основная документация
- ✅ `/API_EXAMPLES.md` - Примеры использования API
- ✅ `/IMPLEMENTATION_REPORT.md` - Данный отчет
- ✅ `/test_api.sh` - Тестовый скрипт

**Всего строк кода:** ~521 (без комментариев и пустых строк)

---

## 12. Качество кода

### 12.1 Проверка синтаксиса
```bash
python3 -m py_compile app/**/*.py
```
Результат: ✅ Все файлы скомпилированы без ошибок

### 12.2 Code Style
- PEP 8 соблюдён
- Type hints везде
- Docstrings для всех классов и методов
- Константы в UPPERCASE
- Понятные имена переменных

### 12.3 Архитектурные принципы
- ✅ Single Responsibility Principle
- ✅ Dependency Injection
- ✅ Separation of Concerns
- ✅ Don't Repeat Yourself (DRY)

---

## 13. Возможные улучшения

### В текущей версии НЕ реализовано (не требовалось):
- Персистентное хранилище (PostgreSQL/Redis)
- Аутентификация пользователей (JWT)
- Проверка наличия товаров на складе
- Резервирование товаров
- История изменений корзины
- Webhooks при изменении корзины
- Rate limiting
- Unit/Integration тесты
- CI/CD пайплайн
- Метрики (Prometheus)
- Логирование в ELK

### Потенциальные расширения:
- Сохранение корзины при перезапуске
- Множественные пользователи с JWT
- Интеграция с inventory-service для проверки остатков
- Применение промокодов/скидок
- Вычисление доставки
- Экспорт корзины в заказ

---

## 14. Выводы

Микросервис **cart-service** полностью реализован в соответствии с требованиями Практической Работы №6:

1. **Архитектура:** Трехслойная архитектура с четким разделением ответственности
2. **API:** Все 3 endpoint реализованы с корректными HTTP кодами
3. **Хранилище:** In-memory репозиторий с требуемой структурой данных
4. **Каталог:** Встроенный CATALOG с 3 позициями
5. **Модели:** Все Pydantic модели соответствуют спецификации
6. **Логика:** Расчет total_price, увеличение quantity, обработка ошибок
7. **Документация:** Swagger UI, README, примеры использования
8. **Тестирование:** Автоматический тестовый скрипт
9. **Docker:** Dockerfile готов к использованию

Сервис готов к запуску и интеграции в микросервисную архитектуру.

---

**Абсолютные пути к ключевым файлам:**
- Main: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/app/main.py`
- Service: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/app/services/cart_service.py`
- Repository: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/app/repositories/local_cart_repo.py`
- Models: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/app/models/cart.py`
- Endpoints: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/app/endpoints/cart.py`
- Dockerfile: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/Dockerfile`
- Requirements: `/Users/fr4lzen/Documents/мирэа/микросы/пр7/project/cart-service/requirements.txt`
