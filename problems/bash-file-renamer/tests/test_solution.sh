#!/bin/bash
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/solution.sh"
PASS=0
FAIL=0

setup() {
    TEST_DIR=$(mktemp -d)
    touch "$TEST_DIR/photo_001.jpg"
    touch "$TEST_DIR/photo_002.jpg"
    touch "$TEST_DIR/document.txt"
}

cleanup() {
    rm -rf "$TEST_DIR"
}

assert_file_exists() {
    if [ -f "$1" ]; then
        ((PASS++))
    else
        echo "FAIL: expected file $1 to exist"
        ((FAIL++))
    fi
}

# Test 1: basic pattern replacement
setup
bash "$SCRIPT" "$TEST_DIR" "photo_" "img_"
assert_file_exists "$TEST_DIR/img_001.jpg"
assert_file_exists "$TEST_DIR/img_002.jpg"
assert_file_exists "$TEST_DIR/document.txt"
cleanup

# Test 2: dry run should not rename
setup
bash "$SCRIPT" "$TEST_DIR" "photo_" "img_" --dry-run
assert_file_exists "$TEST_DIR/photo_001.jpg"
cleanup

# Test 3: lowercase conversion
setup
touch "$TEST_DIR/UPPER.TXT"
bash "$SCRIPT" "$TEST_DIR" "" "" --lower
assert_file_exists "$TEST_DIR/upper.txt"
cleanup

echo "PASSED: $PASS"
echo "FAILED: $FAIL"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
