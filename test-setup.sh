#!/bin/bash

echo "Testing Pizza Index API Setup..."
echo "=================================="

# Test 1: Check if FastAPI is running
echo "1. Testing FastAPI service..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ FastAPI is running on localhost:8000"
else
    echo "   ❌ FastAPI is not running on localhost:8000"
    exit 1
fi

# Test 2: Check if Nginx is running
echo "2. Testing Nginx service..."
if sudo systemctl is-active --quiet nginx; then
    echo "   ✅ Nginx is running"
else
    echo "   ❌ Nginx is not running"
    exit 1
fi

# Test 3: Test HTTP access
echo "3. Testing HTTP access..."
if curl -s http://api.monitorthesituation.lol/health > /dev/null; then
    echo "   ✅ HTTP access works"
else
    echo "   ❌ HTTP access failed"
    echo "   Check DNS and Nginx configuration"
fi

# Test 4: Test CORS headers
echo "4. Testing CORS headers..."
CORS_RESPONSE=$(curl -s -H "Origin: https://monitorthesituation.lol" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     -I http://api.monitorthesituation.lol/pizza-index/live)

if echo "$CORS_RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo "   ✅ CORS headers are set correctly"
else
    echo "   ❌ CORS headers are missing"
fi

# Test 5: Test pizza index endpoint
echo "5. Testing pizza index endpoint..."
PIZZA_RESPONSE=$(curl -s http://api.monitorthesituation.lol/pizza-index/live)
if echo "$PIZZA_RESPONSE" | grep -q "pizza"; then
    echo "   ✅ Pizza index endpoint works"
else
    echo "   ❌ Pizza index endpoint failed"
fi

# Test 6: Check SSL certificate (if exists)
echo "6. Checking SSL certificate..."
if sudo certbot certificates | grep -q "api.monitorthesituation.lol"; then
    echo "   ✅ SSL certificate exists"
    echo "   Testing HTTPS..."
    if curl -s https://api.monitorthesituation.lol/health > /dev/null; then
        echo "   ✅ HTTPS access works"
    else
        echo "   ❌ HTTPS access failed"
    fi
else
    echo "   ⚠️  SSL certificate not found"
    echo "   Run: sudo certbot --nginx -d api.monitorthesituation.lol"
fi

echo ""
echo "Setup test completed!"
echo "If all tests pass, your API should be ready for the frontend." 