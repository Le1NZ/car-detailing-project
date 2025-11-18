# Car Service - Контекст для LLM агентов

## Назначение микросервиса
car-service управляет каталогом автомобилей в системе детейлинга. Это stateless сервис с in-memory хранилищем. Предоставляет критический эндпоинт для проверки существования автомобиля, который используется order-service.

## Роль в архитектуре
- **Порт**: 8002
- **Хранилище**: In-memory (без базы данных)
- **Тип**: Stateless service
- **Взаимодействие**: Принимает HTTP запросы от order-service

## API Endpoints

### POST /api/cars
Добавление нового автомобиля в каталог

**Request**:
```json
{
  "owner_id": "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d",
  "license_plate": "А123БВ799",
  "vin": "XTA210930V0123456",
  "make": "Lada",
  "model": "Vesta",
  "year": 2021
}
```

**Response (201 Created)**:
```json
{
  "car_id": "a8b9c1d2-e3f4-5678-g9h1-i2j3k4l5m6n7",
  "license_plate": "А123БВ799",
  "vin": "XTA210930V0123456",
  "make": "Lada",
  "model": "Vesta",
  "year": 2021
}
```

**Коды ответов**:
- 201 Created - автомобиль успешно добавлен
- 409 Conflict - VIN или license_plate уже существует
- 422 Unprocessable Entity - невалидные данные

**Валидация**:
- VIN: ровно 17 символов, только буквы и цифры
- license_plate: уникален
- year: 1900 <= year <= 2025

### GET /api/cars/{car_id}
**КРИТИЧЕСКИ ВАЖНЫЙ ЭНДПОИНТ** для интеграции с order-service

**Response (200 OK)**:
```json
{
  "car_id": "a8b9c1d2-e3f4-5678-g9h1-i2j3k4l5m6n7",
  "license_plate": "А123БВ799",
  "vin": "XTA210930V0123456",
  "make": "Lada",
  "model": "Vesta",
  "year": 2021
}
```

**Response (404 Not Found)**:
```json
{
  "detail": "Car with ID {car_id} not found"
}
```

**Использование**: order-service делает GET запрос к этому эндпоинту при создании заказа для проверки существования автомобиля.

### POST /api/cars/{car_id}/documents
Добавление документов к автомобилю

**Request**:
```json
{
  "document_type": "СТС",
  "file": "scan_sts.pdf"
}
```

**Response (200 OK)**:
```json
{
  "car_id": "a8b9c1d2-e3f4-5678-g9h1-i2j3k4l5m6n7",
  "document_id": "doc_1k2j3h4g5f6e",
  "document_type": "СТС",
  "status": "added"
}
```

**Коды ответов**:
- 200 OK - документ успешно добавлен
- 404 Not Found - автомобиль не найден

## Структура проекта

```
car-service/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI приложение
│   ├── config.py                  # Конфигурация сервиса
│   ├── models/
│   │   └── car.py                 # Pydantic модели (4 класса)
│   ├── repositories/
│   │   └── local_car_repo.py      # In-memory хранилище
│   ├── services/
│   │   └── car_service.py         # Бизнес-логика
│   └── endpoints/
│       └── cars.py                # API endpoints
├── requirements.txt
├── Dockerfile
├── README.md
└── CONTEXT.md                     # Этот файл
```

## In-Memory хранилище

### LocalCarRepository
```python
class LocalCarRepository:
    def __init__(self):
        self.cars: List[Dict] = []          # Список автомобилей
        self.documents: List[Dict] = []     # Список документов
```

**Важно**: Данные теряются при перезапуске контейнера! Это ожидаемое поведение для stateless сервиса.

### Singleton pattern
```python
_repository_instance: Optional[LocalCarRepository] = None

def get_repository() -> LocalCarRepository:
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = LocalCarRepository()
    return _repository_instance
```

## Ключевые файлы

### app/models/car.py - Pydantic модели

```python
class AddCarRequest(BaseModel):
    owner_id: UUID
    license_plate: str = Field(..., min_length=1, max_length=20)
    vin: str = Field(..., min_length=17, max_length=17)
    make: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1900, le=2025)

    @field_validator("vin")
    @classmethod
    def validate_vin(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError("VIN must contain only letters and numbers")
        return v.upper()

class CarResponse(BaseModel):
    car_id: UUID
    license_plate: str
    vin: str
    make: str
    model: str
    year: int

class AddDocumentRequest(BaseModel):
    document_type: str = Field(..., min_length=1)
    file: Optional[str] = None

class DocumentResponse(BaseModel):
    car_id: UUID
    document_id: UUID
    document_type: str
    status: str
```

### app/repositories/local_car_repo.py - Репозиторий

Ключевые методы:
- `add_car(car_data: Dict) -> Dict` - добавление с проверкой уникальности VIN/plate
- `get_car_by_id(car_id: UUID) -> Optional[Dict]` - поиск по UUID
- `get_car_by_vin(vin: str) -> Optional[Dict]` - проверка дубликата VIN
- `get_car_by_plate(license_plate: str) -> Optional[Dict]` - проверка дубликата plate
- `add_document(car_id: UUID, doc_data: Dict) -> Dict` - добавление документа

### app/services/car_service.py - Сервис

Ключевые методы:
- `create_car(request: AddCarRequest) -> CarResponse`
- `get_car(car_id: UUID) -> CarResponse` - используется order-service!
- `add_document(car_id: UUID, request: AddDocumentRequest) -> DocumentResponse`

**Обработка ошибок**:
```python
try:
    car = self.repository.add_car(car_data)
    return CarResponse(**car)
except ValueError as e:
    # Дубликат VIN/plate - выбросить ValueError
    raise
```

### app/endpoints/cars.py - Endpoints

```python
@router.post("/cars", response_model=CarResponse, status_code=201)
async def add_car(request: AddCarRequest, service: CarService = Depends(get_car_service)):
    try:
        return service.create_car(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/cars/{car_id}", response_model=CarResponse)
async def get_car(car_id: UUID, service: CarService = Depends(get_car_service)):
    try:
        return service.get_car(car_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Car with ID {car_id} not found")
```

## Зависимости

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

**Минималистичный набор** - нет SQLAlchemy, нет asyncpg, нет Alembic.

## Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

## Интеграция с другими сервисами

### Входящие запросы

**От order-service**:
```python
# В order-service/app/services/car_client.py
async with httpx.AsyncClient() as client:
    response = await client.get(f"http://car-service:8002/api/cars/{car_id}")
    if response.status_code == 200:
        return True  # Автомобиль существует
    else:
        return False  # Автомобиль не найден
```

### Исходящие запросы
car-service НЕ делает запросы к другим сервисам. Работает автономно.

## Запуск и тестирование

### Локально
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project/car-service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker
```bash
cd /Users/fr4lzen/Documents/мирэа/микросы/пр7/project
docker-compose up car-service
```

### Тест добавления автомобиля
```bash
curl -X POST http://localhost:8002/api/cars \
  -H "Content-Type: application/json" \
  -d '{
    "owner_id":"550e8400-e29b-41d4-a716-446655440000",
    "license_plate":"А123БВ799",
    "vin":"XTA210930V0123456",
    "make":"Lada",
    "model":"Vesta",
    "year":2021
  }'
```

### Тест получения автомобиля (критический для order-service)
```bash
# Сохрани car_id из предыдущего ответа
curl http://localhost:8002/api/cars/{car_id}
```

### Тест добавления документа
```bash
curl -X POST http://localhost:8002/api/cars/{car_id}/documents \
  -H "Content-Type: application/json" \
  -d '{
    "document_type":"СТС",
    "file":"scan_sts.pdf"
  }'
```

## Типичные задачи для LLM агента

### 1. Добавление нового поля в Car
1. Изменить `AddCarRequest` и `CarResponse` в `app/models/car.py`
2. Обновить `car_data` dictionary в `app/services/car_service.py`
3. Обновить in-memory структуру в `app/repositories/local_car_repo.py`

**Важно**: Миграции БД НЕ нужны, так как это in-memory хранилище!

### 2. Добавление валидации
Добавить `@field_validator` в Pydantic модели (`app/models/car.py`)

### 3. Добавление нового эндпоинта
1. Создать Pydantic модели в `app/models/car.py`
2. Добавить метод в `app/repositories/local_car_repo.py`
3. Добавить бизнес-логику в `app/services/car_service.py`
4. Добавить роут в `app/endpoints/cars.py`

### 4. Изменение логики проверки дубликатов
Редактировать `app/repositories/local_car_repo.py` методы `get_car_by_vin()` и `get_car_by_plate()`

## Известные проблемы и решения

### Проблема: Данные теряются после перезапуска
**Решение**: Это нормально! car-service это stateless сервис. Данные хранятся только в памяти.

Если нужна персистентность:
1. Добавить PostgreSQL (как в user-service)
2. Добавить SQLAlchemy модели
3. Добавить Alembic миграции
4. Изменить Repository на DB-based

### Проблема: 409 Conflict при добавлении автомобиля
**Решение**: VIN или license_plate уже существует. Это корректное поведение.

### Проблема: order-service получает 404 при создании заказа
**Решение**:
- Проверить что car-service запущен: `docker-compose ps car-service`
- Проверить что car_id существует: `curl http://localhost:8002/api/cars/{car_id}`
- Проверить логи car-service: `docker-compose logs car-service`

### Проблема: VIN validation fails
**Решение**: VIN должен быть ровно 17 символов, только буквы и цифры. Проверить входные данные.

## Важные замечания для LLM агентов

1. **НЕ используй базу данных** - это in-memory сервис
2. **НЕ нужен Alembic** - нет БД, нет миграций
3. **UUID везде** - все ID это UUID, не int
4. **Singleton для repository** - один экземпляр на всё приложение
5. **Валидация через Pydantic** - используй field_validator
6. **ValueError для ошибок** - repository бросает ValueError при дубликатах
7. **HTTPException в endpoints** - конвертируй ValueError в HTTP коды
8. **GET /api/cars/{car_id} критичен** - order-service зависит от него!
9. **VIN uppercase** - всегда конвертируй VIN в верхний регистр
10. **Thread-safe не требуется** - FastAPI/Uvicorn однопоточный по умолчанию для in-memory

## Расширение функциональности

### Добавление поиска по номеру
```python
# В repository
def search_by_plate(self, plate: str) -> List[Dict]:
    return [car for car in self.cars if plate in car["license_plate"]]

# В service
def search_cars_by_plate(self, plate: str) -> List[CarResponse]:
    cars = self.repository.search_by_plate(plate)
    return [CarResponse(**car) for car in cars]

# В endpoints
@router.get("/cars/search")
async def search_cars(license_plate: str, service: CarService = Depends(...)):
    return service.search_cars_by_plate(license_plate)
```

### Добавление фильтрации по владельцу
```python
def get_cars_by_owner(self, owner_id: UUID) -> List[Dict]:
    return [car for car in self.cars if car["owner_id"] == str(owner_id)]
```

## Тестирование интеграции с order-service

1. Запустить оба сервиса:
```bash
docker-compose up car-service order-service
```

2. Добавить автомобиль в car-service:
```bash
curl -X POST http://localhost:8002/api/cars -H "Content-Type: application/json" -d '...'
# Сохранить car_id из ответа
```

3. Создать заказ в order-service с этим car_id:
```bash
curl -X POST http://localhost:8003/api/orders -H "Content-Type: application/json" -d '{
  "car_id": "<car_id>",
  "desired_time": "2024-12-20T10:00:00Z",
  "description": "Техническое обслуживание"
}'
```

4. Проверить логи:
```bash
# car-service должен показать GET запрос от order-service
docker-compose logs car-service | grep "GET /api/cars/"

# order-service должен успешно создать заказ
docker-compose logs order-service
```

## Документация API
Swagger UI: http://localhost:8002/docs
ReDoc: http://localhost:8002/redoc
