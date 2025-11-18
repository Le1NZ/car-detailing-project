#!/bin/bash

# Fines Service API Tests
# Запустите сервис перед тестированием: uvicorn app.main:app --port 8007

BASE_URL="http://localhost:8007"

echo "=== Fines Service API Tests ==="
echo ""

echo "1. Health Check"
curl -s "$BASE_URL/health" | python3 -m json.tool
echo -e "\n"

echo "2. Проверка штрафов для А123БВ799 (должно вернуть 2 штрафа)"
curl -s "$BASE_URL/api/fines/check?license_plate=А123БВ799" | python3 -m json.tool
echo -e "\n"

echo "3. Проверка штрафов для В456ГД177 (должно вернуть 1 штраф)"
curl -s "$BASE_URL/api/fines/check?license_plate=В456ГД177" | python3 -m json.tool
echo -e "\n"

echo "4. Проверка штрафов для несуществующего номера (должно вернуть 404)"
curl -s -w "\nHTTP Status: %{http_code}\n" "$BASE_URL/api/fines/check?license_plate=НЕИЗВЕСТНЫЙ" | python3 -m json.tool
echo -e "\n"

echo "5. Оплата штрафа fine_112233 (должно вернуть payment_id)"
curl -s -X POST "$BASE_URL/api/fines/fine_112233/pay" \
  -H "Content-Type: application/json" \
  -d '{"payment_method_id": "card_method"}' | python3 -m json.tool
echo -e "\n"

echo "6. Повторная попытка оплаты fine_112233 (должно вернуть 409 Conflict)"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BASE_URL/api/fines/fine_112233/pay" \
  -H "Content-Type: application/json" \
  -d '{"payment_method_id": "card_method"}' | python3 -m json.tool
echo -e "\n"

echo "7. Проверка штрафов для А123БВ799 после оплаты (должно вернуть 1 штраф)"
curl -s "$BASE_URL/api/fines/check?license_plate=А123БВ799" | python3 -m json.tool
echo -e "\n"

echo "8. Оплата несуществующего штрафа (должно вернуть 404)"
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$BASE_URL/api/fines/fine_999999/pay" \
  -H "Content-Type: application/json" \
  -d '{"payment_method_id": "card_method"}' | python3 -m json.tool
echo -e "\n"

echo "=== Tests Complete ==="
