# Fines Service

Микросервис для управления штрафами ГИБДД.

## Описание

Сервис предоставляет API для проверки и оплаты штрафов по номеру транспортного средства.

## Технологии

- Python 3.11
- FastAPI
- Pydantic
- Uvicorn

## Архитектура

Трехслойная архитектура:
- **Endpoints** (`app/endpoints/`) - HTTP endpoints
- **Services** (`app/services/`) - бизнес-логика
- **Repositories** (`app/repositories/`) - работа с данными (in-memory)

## API Endpoints

### 1. Проверка штрафов
```
GET /api/fines/check?license_plate={plate}
```

Возвращает список неоплаченных штрафов для указанного номера.

**Параметры:**
- `license_plate` (query) - номер транспортного средства

**Ответ:** 200 OK
```json
[
  {
    "fine_id": "uuid",
    "amount": 500.00,
    "description": "Превышение скорости на 20-40 км/ч",
    "date": "2024-05-15"
  }
]
```

### 2. Оплата штрафа
```
POST /api/fines/{fine_id}/pay
```

Оплачивает штраф.

**Параметры:**
- `fine_id` (path) - UUID штрафа

**Тело запроса:**
```json
{
  "payment_method_id": "card_123"
}
```

**Ответы:**
- 200 OK - штраф оплачен
```json
{
  "payment_id": "uuid",
  "fine_id": "uuid",
  "status": "paid"
}
```
- 404 Not Found - штраф не найден
- 409 Conflict - штраф уже оплачен

## Тестовые данные

Сервис предзаполнен тестовыми штрафами:
- **А123БВ799**: 500 руб. - Превышение скорости
- **М456КЛ177**: 1000 руб. - Проезд на красный свет

## Запуск

### Локально
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8007
```

### Docker
```bash
docker build -t fines-service .
docker run -p 8007:8007 fines-service
```

## Документация API

После запуска доступна по адресу:
- Swagger UI: http://localhost:8007/docs
- ReDoc: http://localhost:8007/redoc

## Health Check

```
GET /health
```

Возвращает статус сервиса.
