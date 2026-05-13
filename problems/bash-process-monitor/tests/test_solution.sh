#!/bin/bash
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/solution.sh"
PASS=0
FAIL=0

# Test 1: runs without error with count=1
OUTPUT=$(bash "$SCRIPT" --count 1 --interval 1 2>&1)
if [ $? -eq 0 ]; then
    ((PASS++))
else
    echo "FAIL: script exited with error"
    ((FAIL++))
fi

# Test 2: contains CPU usage info
if echo "$OUTPUT" | grep -qi "cpu"; then
    ((PASS++))
else
    echo "FAIL: output should contain CPU info"
    ((FAIL++))
fi

# Test 3: contains memory usage info
if echo "$OUTPUT" | grep -qi "memory\|mem"; then
    ((PASS++))
else
    echo "FAIL: output should contain memory info"
    ((FAIL++))
fi

# Test 4: contains timestamp
if echo "$OUTPUT" | grep -q "Timestamp"; then
    ((PASS++))
else
    echo "FAIL: output should contain Timestamp"
    ((FAIL++))
fi

echo "PASSED: $PASS"
echo "FAILED: $FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
