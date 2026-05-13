#!/bin/bash
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/solution.sh"
PASS=0
FAIL=0

SOURCE=$(mktemp -d)
BACKUP=$(mktemp -d)

# Create source files
echo "hello" > "$SOURCE/test.txt"
echo "world" > "$SOURCE/data.csv"

# Test 1: create backup
OUTPUT=$(bash "$SCRIPT" --source "$SOURCE" --backup-dir "$BACKUP" --retain-daily 7 --retain-weekly 4 --retain-monthly 3 2>&1)
if [ $? -eq 0 ]; then
    ((PASS++))
else
    echo "FAIL: backup creation failed"
    ((FAIL++))
fi

# Test 2: backup file exists
COUNT=$(ls "$BACKUP"/*.tar.gz 2>/dev/null | wc -l)
if [ "$COUNT" -ge 1 ]; then
    ((PASS++))
else
    echo "FAIL: expected at least 1 backup file"
    ((FAIL++))
fi

# Test 3: backup contains test.txt
LATEST=$(ls -t "$BACKUP"/*.tar.gz 2>/dev/null | head -1)
if tar tzf "$LATEST" 2>/dev/null | grep -q "test.txt"; then
    ((PASS++))
else
    echo "FAIL: backup should contain test.txt"
    ((FAIL++))
fi

# Test 4: second backup also works
bash "$SCRIPT" --source "$SOURCE" --backup-dir "$BACKUP" --retain-daily 7 2>&1
COUNT2=$(ls "$BACKUP"/*.tar.gz 2>/dev/null | wc -l)
if [ "$COUNT2" -ge 2 ]; then
    ((PASS++))
else
    echo "FAIL: expected at least 2 backups after second run"
    ((FAIL++))
fi

rm -rf "$SOURCE" "$BACKUP"

echo "PASSED: $PASS"
echo "FAILED: $FAIL"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
