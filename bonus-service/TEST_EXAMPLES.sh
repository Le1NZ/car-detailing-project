#!/bin/bash
# Примеры тестирования Bonus Service API

BASE_URL="http://localhost:8006"

echo "=========================================="
echo "BONUS SERVICE API - Примеры тестирования"
echo "=========================================="
echo ""

# 1. Health Check
echo "1. Health Check"
echo "----------------"
curl -X GET "${BASE_URL}/health"
echo -e "\n\n"

# 2. Root endpoint
echo "2. Root endpoint"
echo "----------------"
curl -X GET "${BASE_URL}/"
echo -e "\n\n"

# 3. Применение валидного промокода SUMMER24
echo "3. Применение промокода SUMMER24 (200 OK)"
echo "----------------------------------------"
curl -X POST "${BASE_URL}/api/bonuses/promocodes/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "123e4567-e89b-12d3-a456-426614174000",
    "promocode": "SUMMER24"
  }'
echo -e "\n\n"

# 4. Применение валидного промокода WELCOME10
echo "4. Применение промокода WELCOME10 (200 OK)"
echo "------------------------------------------"
curl -X POST "${BASE_URL}/api/bonuses/promocodes/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "223e4567-e89b-12d3-a456-426614174001",
    "promocode": "WELCOME10"
  }'
echo -e "\n\n"

# 5. Применение невалидного промокода
echo "5. Применение невалидного промокода (404 Not Found)"
echo "---------------------------------------------------"
curl -X POST "${BASE_URL}/api/bonuses/promocodes/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "323e4567-e89b-12d3-a456-426614174002",
    "promocode": "INVALID_CODE"
  }'
echo -e "\n\n"

# 6. Списание бонусов (недостаточно бонусов - 400 Bad Request)
echo "6. Списание бонусов - недостаточно (400 Bad Request)"
echo "----------------------------------------------------"
curl -X POST "${BASE_URL}/api/bonuses/spend" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "423e4567-e89b-12d3-a456-426614174003",
    "amount": 1000
  }'
echo -e "\n\n"

# 7. Симуляция начисления бонусов через RabbitMQ
echo "7. Симуляция RabbitMQ события (публикация в очередь)"
echo "-----------------------------------------------------"
echo "Для тестирования RabbitMQ используйте:"
echo ""
echo "docker exec rabbitmq rabbitmqadmin publish \\"
echo "  exchange=amq.default \\"
echo "  routing_key=payment_succeeded_queue \\"
echo "  payload='{\"order_id\":\"523e4567-e89b-12d3-a456-426614174004\",\"user_id\":\"c3f4e1a1-5b8a-4b0e-8d9b-9d4a6f1e2c3d\",\"amount\":10000.0}'"
echo ""
echo "Затем проверьте логи bonus-service:"
echo "docker logs bonus-service | grep 'accrued'"
echo -e "\n"

# 8. Списание бонусов после начисления (200 OK)
echo "8. Списание бонусов после начисления (200 OK)"
echo "---------------------------------------------"
echo "После выполнения шага 7, выполните:"
echo ""
echo "curl -X POST \"${BASE_URL}/api/bonuses/spend\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"order_id\": \"623e4567-e89b-12d3-a456-426614174005\","
echo "    \"amount\": 50"
echo "  }'"
echo -e "\n\n"

# 9. Swagger UI
echo "9. Интерактивная документация"
echo "-----------------------------"
echo "Swagger UI: ${BASE_URL}/docs"
echo "ReDoc: ${BASE_URL}/redoc"
echo -e "\n"

echo "=========================================="
echo "Все тесты завершены!"
echo "=========================================="
