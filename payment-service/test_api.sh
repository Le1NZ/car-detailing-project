#!/bin/bash

# Скрипт для тестирования Payment Service API
# Использование: ./test_api.sh

BASE_URL="http://localhost:8005"

echo "=== Payment Service API Tests ==="
echo ""

# 1. Health Check
echo "1. Health Check:"
curl -X GET "$BASE_URL/health" | jq .
echo -e "\n"

# 2. Создание платежа для существующего заказа
echo "2. Создание платежа для заказа ord_a1b2c3d4:"
PAYMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_a1b2c3d4",
    "payment_method": "card"
  }')
echo "$PAYMENT_RESPONSE" | jq .
PAYMENT_ID=$(echo "$PAYMENT_RESPONSE" | jq -r '.payment_id')
echo -e "\n"

# 3. Получение статуса платежа (сразу после создания - должен быть pending)
echo "3. Получение статуса платежа (pending):"
curl -X GET "$BASE_URL/api/payments/$PAYMENT_ID" | jq .
echo -e "\n"

# 4. Ожидание обработки платежа (5 секунд)
echo "4. Ожидание обработки платежа (5 секунд)..."
sleep 6

# 5. Получение статуса платежа (после обработки - должен быть succeeded)
echo "5. Получение статуса платежа (succeeded):"
curl -X GET "$BASE_URL/api/payments/$PAYMENT_ID" | jq .
echo -e "\n"

# 6. Попытка повторной оплаты того же заказа (должна вернуть 409 Conflict)
echo "6. Попытка повторной оплаты (ожидается 409 Conflict):"
curl -X POST "$BASE_URL/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_a1b2c3d4",
    "payment_method": "card"
  }' | jq .
echo -e "\n"

# 7. Попытка оплаты несуществующего заказа (должна вернуть 404 Not Found)
echo "7. Попытка оплаты несуществующего заказа (ожидается 404 Not Found):"
curl -X POST "$BASE_URL/api/payments" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_nonexistent",
    "payment_method": "card"
  }' | jq .
echo -e "\n"

# 8. Получение несуществующего платежа (должна вернуть 404 Not Found)
echo "8. Получение несуществующего платежа (ожидается 404 Not Found):"
curl -X GET "$BASE_URL/api/payments/pay_nonexistent" | jq .
echo -e "\n"

echo "=== Tests Completed ==="
