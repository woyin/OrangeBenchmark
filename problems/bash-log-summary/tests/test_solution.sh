#!/bin/bash
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/solution.sh"
PASS=0
FAIL=0

# Create test log
LOG=$(mktemp)
cat > "$LOG" << 'EOF'
10.0.0.1 - - [10/Oct/2023:13:55:36 +0000] "GET /a HTTP/1.1" 200 2326 "-" "Mozilla" 0.010
10.0.0.2 - - [10/Oct/2023:13:55:37 +0000] "GET /b HTTP/1.1" 404 512 "-" "Chrome" 0.030
10.0.0.1 - - [10/Oct/2023:13:55:38 +0000] "POST /c HTTP/1.1" 200 1024 "-" "Safari" 0.050
10.0.0.3 - - [10/Oct/2023:13:55:39 +0000] "GET /a HTTP/1.1" 500 0 "-" "Firefox" 0.100
EOF

OUTPUT=$(bash "$SCRIPT" "$LOG")

# Test 1: total requests
if echo "$OUTPUT" | grep -q "Total requests: 4"; then
    ((PASS++))
else
    echo "FAIL: expected 'Total requests: 4'"
    ((FAIL++))
fi

# Test 2: top IPs contains 10.0.0.1
if echo "$OUTPUT" | grep -q "10.0.0.1"; then
    ((PASS++))
else
    echo "FAIL: expected IP 10.0.0.1 in top IPs"
    ((FAIL++))
fi

# Test 3: status codes
if echo "$OUTPUT" | grep -q "200" && echo "$OUTPUT" | grep -q "404"; then
    ((PASS++))
else
    echo "FAIL: expected status codes 200 and 404"
    ((FAIL++))
fi

# Test 4: missing file returns error
if ! bash "$SCRIPT" "/nonexistent/file" 2>/dev/null; then
    ((PASS++))
else
    echo "FAIL: should fail on missing file"
    ((FAIL++))
fi

rm "$LOG"

echo "PASSED: $PASS"
echo "FAILED: $FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
