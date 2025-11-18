"""Эндпоинты для работы с платежами."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends

from app.models import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentStatusResponse,
)
from app.services import payment_service
from app.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post(
    "",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать платеж",
    description="Инициирует процесс оплаты для заказа. "
                "Платеж создается со статусом 'pending' и обрабатывается асинхронно."
)
async def create_payment(
    request: PaymentCreateRequest,
    user_id: UUID = Depends(get_current_user_id)
) -> PaymentCreateResponse:
    """
    Создать новый платеж.

    Args:
        request: Данные для создания платежа

    Returns:
        Данные созданного платежа

    Raises:
        HTTPException: 404 если заказ не найден, 409 если заказ уже оплачен
    """
    try:
        # Используем user_id из JWT токена и amount из запроса (или дефолт)
        payment = await payment_service.initiate_payment(
            order_id=request.order_id,
            payment_method=request.payment_method,
            user_id=str(user_id),
            amount=5000.0  # Можно добавить в request модель если нужно
        )

        return PaymentCreateResponse(
            payment_id=payment["payment_id"],
            order_id=payment["order_id"],
            status=payment["status"],
            amount=payment["amount"],
            currency=payment["currency"],
            confirmation_url=payment["confirmation_url"]
        )

    except ValueError as e:
        error_msg = str(e)

        # Определяем тип ошибки
        if "not found" in error_msg.lower():
            logger.warning(f"Order not found: {request.order_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {request.order_id} not found"
            )
        elif "already paid" in error_msg.lower():
            logger.warning(f"Order already paid: {request.order_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Order {request.order_id} already paid"
            )
        else:
            logger.error(f"Unexpected error creating payment: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )


@router.get(
    "/{payment_id}",
    response_model=PaymentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Получить статус платежа",
    description="Возвращает текущий статус платежа и время оплаты (если применимо)."
)
async def get_payment_status(
    payment_id: str,
    user_id: UUID = Depends(get_current_user_id)
) -> PaymentStatusResponse:
    """
    Получить статус платежа.

    Args:
        payment_id: Идентификатор платежа

    Returns:
        Статус платежа

    Raises:
        HTTPException: 404 если платеж не найден
    """
    payment = payment_service.get_payment(payment_id)

    if not payment:
        logger.warning(f"Payment not found: {payment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )

    return PaymentStatusResponse(
        payment_id=payment["payment_id"],
        status=payment["status"],
        paid_at=payment.get("paid_at")
    )
