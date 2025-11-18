# Fines Service - Контекст для LLM агентов

## Назначение
Проверка и оплата штрафов по номеру автомобиля.

## Роль
- **Порт**: 8007
- **Хранилище**: In-memory с тестовыми данными

## API

### GET /api/fines/check?license_plate={plate}
Проверка неоплаченных штрафов

**Response (200)**:
```json
[
  {
    "fine_id": "uuid",
    "amount": 500.0,
    "description": "Превышение скорости на 20-40 км/ч",
    "date": "2024-05-15"
  }
]
```

### POST /api/fines/{fine_id}/pay
Оплата штрафа

**Request**:
```json
{
  "payment_method_id": "card_123"
}
```

**Response (200)**:
```json
{
  "payment_id": "uuid",
  "fine_id": "uuid",
  "status": "paid"
}
```

**Коды**: 200 OK, 404 Not Found, 409 Conflict (уже оплачен)

## Тестовые данные

### app/repositories/local_fine_repo.py
```python
TEST_FINES = [
    {
        "license_plate": "А123БВ799",
        "amount": 500.00,
        "description": "Превышение скорости на 20-40 км/ч",
        "date": date(2024, 5, 15)
    },
    {
        "license_plate": "М456КЛ177",
        "amount": 1000.00,
        "description": "Проезд на красный свет",
        "date": date(2024, 6, 1)
    }
]
```

## Структура

```python
class LocalFineRepository:
    def __init__(self):
        self._fines: Dict[str, List[Fine]] = {}          # По license_plate
        self._fines_by_id: Dict[UUID, Fine] = {}         # По fine_id
```

## Типичные задачи

### Добавление тестового штрафа
Редактировать `TEST_FINES` в `local_fine_repo.py`

### Изменение логики оплаты
Редактировать `mark_fine_as_paid()` в repository или `pay_fine()` в service

## Зависимости
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

## Запуск
```bash
docker-compose up fines-service
```

Swagger: http://localhost:8007/docs
