# Support Service - Контекст для LLM агентов

## Назначение
Управление обращениями в службу поддержки (тикет-система).

## Роль
- **Порт**: 8008
- **Хранилище**: In-memory Dict[UUID, Ticket] и Dict[UUID, List[Message]]

## API

### POST /api/support/tickets
Создание обращения

**Request**:
```json
{
  "subject": "Проблема с бонусами",
  "message": "Бонусы не начислились после оплаты",
  "order_id": "uuid"
}
```

**Response (201)**:
```json
{
  "ticket_id": "uuid",
  "status": "open",
  "created_at": "2024-06-12T09:00:00Z"
}
```

**Валидация**: subject и message не должны быть пустыми (min_length=1)

### POST /api/support/tickets/{ticket_id}/messages
Добавление сообщения в тикет

**Request**:
```json
{
  "message": "Могли бы вы прислать скриншот?"
}
```

**Response (201)**:
```json
{
  "message_id": "uuid",
  "ticket_id": "uuid",
  "author_id": "support_agent_01",
  "message": "Могли бы вы...",
  "created_at": "2024-06-12T09:15:00Z"
}
```

**Коды**: 201 Created, 404 Not Found, 409 Conflict (тикет закрыт), 422 Unprocessable Entity

## Модели

### Ticket
```python
class Ticket:
    ticket_id: UUID
    user_id: UUID
    subject: str
    message: str
    order_id: Optional[UUID]
    status: str  # open, in_progress, closed
    created_at: datetime
```

### Message
```python
class Message:
    message_id: UUID
    ticket_id: UUID
    author_id: str
    message: str
    created_at: datetime
```

## Бизнес-логика

### Проверка закрытых тикетов
```python
def add_message_to_ticket(self, ticket_id: UUID, request: AddMessageRequest, author_id: str):
    ticket = self.repository.get_ticket_by_id(ticket_id)
    if not ticket:
        raise ValueError("Ticket not found")

    if self.repository.is_ticket_closed(ticket_id):
        raise RuntimeError("Cannot add message to closed ticket")

    # Добавить сообщение
```

## Mock данные

### app/config.py
```python
mock_user_id: str = "c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d"
```

В production user_id будет из JWT токена.

## Типичные задачи

### Добавление нового статуса тикета
Изменить Literal["open", "in_progress", "closed", "new_status"] в models

### Добавление автоматического закрытия
Редактировать `support_service.py` - добавить логику закрытия через N дней

### Добавление поиска тикетов
Новый эндпоинт GET /api/support/tickets?user_id=...

## Зависимости
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
```

## Запуск
```bash
docker-compose up support-service
```

Swagger: http://localhost:8008/docs
