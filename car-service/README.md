# Car Service

Микросервис для управления информацией об автомобилях и документах.

## Архитектура

Трехслойная архитектура:
- **Endpoints** (`app/endpoints/`): API endpoints
- **Services** (`app/services/`): Business logic layer
- **Repositories** (`app/repositories/`): Data access layer (in-memory storage)

## API Endpoints

### POST /api/cars
Добавление нового автомобиля.

**Request:**
```json
{
  "owner_id": "uuid",
  "license_plate": "string",
  "vin": "string (17 chars)",
  "make": "string",
  "model": "string",
  "year": 2024
}
```

**Response (201):**
```json
{
  "car_id": "uuid",
  "license_plate": "string",
  "vin": "string",
  "make": "string",
  "model": "string",
  "year": 2024
}
```

### GET /api/cars/{car_id}
Получение информации об автомобиле (для order-service).

**Response (200):**
```json
{
  "car_id": "uuid",
  "license_plate": "string",
  "vin": "string",
  "make": "string",
  "model": "string",
  "year": 2024
}
```

### POST /api/cars/{car_id}/documents
Добавление документа к автомобилю.

**Request:**
```json
{
  "document_type": "string",
  "file": "string (optional)"
}
```

**Response (200):**
```json
{
  "car_id": "uuid",
  "document_id": "uuid",
  "document_type": "string",
  "status": "pending"
}
```

## Запуск

### Локально
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### Docker
```bash
docker build -t car-service .
docker run -p 8002:8002 car-service
```

## Валидация

- VIN: 17 символов, только буквы и цифры
- License plate: уникальный
- Year: 1900 <= year <= 2025
- Дубликаты VIN/license_plate: HTTP 409 Conflict

## Health Check

```bash
GET /health
```

## API Documentation

После запуска доступна по адресу: http://localhost:8002/docs
