"""Pydantic модели для платежей."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InitiatePaymentRequest(BaseModel):
    """Запрос на инициацию платежа."""

    order_id: str = Field(..., description="Идентификатор заказа (UUID)")
    payment_method: str = Field(..., description="Метод оплаты (card, sbp)")


class PaymentResponse(BaseModel):
    """Ответ при инициации платежа."""

    payment_id: str = Field(..., description="Уникальный идентификатор платежа")
    order_id: str = Field(..., description="Идентификатор заказа")
    status: str = Field(..., description="Статус платежа (pending, succeeded, failed)")
    amount: float = Field(..., description="Сумма платежа")
    currency: str = Field(default="RUB", description="Валюта")
    confirmation_url: str = Field(..., description="URL для подтверждения платежа")


class PaymentStatusResponse(BaseModel):
    """Ответ при запросе статуса платежа."""

    payment_id: str = Field(..., description="Идентификатор платежа")
    status: str = Field(..., description="Статус платежа (pending, succeeded, failed)")
    paid_at: Optional[datetime] = Field(None, description="Время оплаты")


# Алиасы для обратной совместимости
PaymentCreateRequest = InitiatePaymentRequest
PaymentCreateResponse = PaymentResponse
