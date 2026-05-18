use rust_string_manipulation::{capitalize_first, title_case, count_words, reverse_words, is_pangram};

// capitalize_first tests
#[test]
fn test_capitalize_basic() {
    assert_eq!(capitalize_first("hello"), "Hello");
}

#[test]
fn test_capitalize_empty() {
    assert_eq!(capitalize_first(""), "");
}

#[test]
fn test_capitalize_already_capitalized() {
    assert_eq!(capitalize_first("Hello"), "Hello");
}

#[test]
fn test_capitalize_single_char() {
    assert_eq!(capitalize_first("a"), "A");
}

// title_case tests
#[test]
fn test_title_case_basic() {
    assert_eq!(title_case("hello world"), "Hello World");
}

#[test]
fn test_title_case_empty() {
    assert_eq!(title_case(""), "");
}

#[test]
fn test_title_case_single_word() {
    assert_eq!(title_case("hello"), "Hello");
}

#[test]
fn test_title_case_already_titled() {
    assert_eq!(title_case("Hello World"), "Hello World");
}

// count_words tests
#[test]
fn test_count_words_basic() {
    assert_eq!(count_words("hello world"), 2);
}

#[test]
fn test_count_words_empty() {
    assert_eq!(count_words(""), 0);
}

#[test]
fn test_count_words_single() {
    assert_eq!(count_words("hello"), 1);
}

#[test]
fn test_count_words_multiple_spaces() {
    assert_eq!(count_words("  hello   world  "), 2);
}

// reverse_words tests
#[test]
fn test_reverse_words_basic() {
    assert_eq!(reverse_words("hello world"), "world hello");
}

#[test]
fn test_reverse_words_empty() {
    assert_eq!(reverse_words(""), "");
}

#[test]
fn test_reverse_words_single() {
    assert_eq!(reverse_words("hello"), "hello");
}

#[test]
fn test_reverse_words_multiple() {
    assert_eq!(reverse_words("one two three"), "three two one");
}

// is_pangram tests
#[test]
fn test_pangram_basic() {
    assert!(is_pangram("The quick brown fox jumps over the lazy dog"));
}

#[test]
fn test_pangram_not() {
    assert!(!is_pangram("Hello World"));
}

#[test]
fn test_pangram_empty() {
    assert!(!is_pangram(""));
}

#[test]
fn test_pangram_case_insensitive() {
    assert!(is_pangram("THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"));
}
