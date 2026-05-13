#!/bin/bash
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/solution.sh"
PASS=0
FAIL=0

DIR=$(mktemp -d)

# Create test CSVs
cat > "$DIR/a.csv" << 'EOF'
name,age,city
Alice,30,NYC
Bob,25,LA
EOF

cat > "$DIR/b.csv" << 'EOF'
name,age,city
Charlie,35,Chicago
Alice,30,NYC
EOF

OUTPUT="$DIR/output.csv"

# Test 1: merge and check header
bash "$SCRIPT" "$OUTPUT" "$DIR/a.csv" "$DIR/b.csv"
if head -1 "$OUTPUT" | grep -q "name,age,city"; then
    ((PASS++))
else
    echo "FAIL: header not preserved"
    ((FAIL++))
fi

# Test 2: deduplication
LINES=$(wc -l < "$OUTPUT")
if [ "$LINES" -eq 4 ]; then  # header + 3 unique rows
    ((PASS++))
else
    echo "FAIL: expected 4 lines (header+3), got $LINES"
    ((FAIL++))
fi

# Test 3: sorted by first column
if tail -n +2 "$OUTPUT" | head -1 | grep -q "Alice"; then
    ((PASS++))
else
    echo "FAIL: first data row should be Alice (sorted)"
    ((FAIL++))
fi

rm -rf "$DIR"

echo "PASSED: $PASS"
echo "FAILED: $FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
