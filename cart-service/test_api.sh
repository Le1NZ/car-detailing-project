#!/bin/bash
# Test script for Cart Service API

BASE_URL="http://localhost:8004"

echo "==================================="
echo "Cart Service API Test Script"
echo "==================================="
echo ""

# Health Check
echo "1. Health Check"
echo "GET $BASE_URL/health"
curl -s -X GET "$BASE_URL/health" | python3 -m json.tool
echo -e "\n"

# Get empty cart
echo "2. Get Empty Cart"
echo "GET $BASE_URL/api/cart"
curl -s -X GET "$BASE_URL/api/cart" | python3 -m json.tool
echo -e "\n"

# Add service to cart
echo "3. Add Service (Oil Change)"
echo "POST $BASE_URL/api/cart/items"
curl -s -X POST "$BASE_URL/api/cart/items" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_oil_change",
    "type": "service",
    "quantity": 1
  }' | python3 -m json.tool
echo -e "\n"

# Add product to cart
echo "4. Add Product (Oil Filter)"
echo "POST $BASE_URL/api/cart/items"
curl -s -X POST "$BASE_URL/api/cart/items" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "prod_oil_filter",
    "type": "product",
    "quantity": 2
  }' | python3 -m json.tool
echo -e "\n"

# Add another service
echo "5. Add Another Service (Diagnostics)"
echo "POST $BASE_URL/api/cart/items"
curl -s -X POST "$BASE_URL/api/cart/items" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_diagnostics",
    "type": "service",
    "quantity": 1
  }' | python3 -m json.tool
echo -e "\n"

# Get cart with items
echo "6. Get Cart with Items"
echo "GET $BASE_URL/api/cart"
curl -s -X GET "$BASE_URL/api/cart" | python3 -m json.tool
echo -e "\n"

# Add same item again (should increase quantity)
echo "7. Add Same Service Again (should increase quantity)"
echo "POST $BASE_URL/api/cart/items"
curl -s -X POST "$BASE_URL/api/cart/items" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "svc_oil_change",
    "type": "service",
    "quantity": 1
  }' | python3 -m json.tool
echo -e "\n"

# Remove item from cart
echo "8. Remove Item (Oil Filter)"
echo "DELETE $BASE_URL/api/cart/items/prod_oil_filter"
curl -s -X DELETE "$BASE_URL/api/cart/items/prod_oil_filter" -w "\nHTTP Status: %{http_code}\n"
echo -e "\n"

# Get final cart state
echo "9. Get Final Cart State"
echo "GET $BASE_URL/api/cart"
curl -s -X GET "$BASE_URL/api/cart" | python3 -m json.tool
echo -e "\n"

# Test 404 - item not in catalog
echo "10. Test 404 - Item Not in Catalog"
echo "POST $BASE_URL/api/cart/items"
curl -s -X POST "$BASE_URL/api/cart/items" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "invalid_item",
    "type": "service",
    "quantity": 1
  }' | python3 -m json.tool
echo -e "\n"

# Test 404 - remove non-existent item
echo "11. Test 404 - Remove Non-existent Item"
echo "DELETE $BASE_URL/api/cart/items/non_existent_item"
curl -s -X DELETE "$BASE_URL/api/cart/items/non_existent_item" -w "\nHTTP Status: %{http_code}\n"
echo -e "\n"

echo "==================================="
echo "Test Complete!"
echo "==================================="
