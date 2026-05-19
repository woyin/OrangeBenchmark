use json_parser::parse_json;

#[test]
fn test_parse_simple_string() {
    let json = r#"{"name": "Alice"}"#;
    assert_eq!(parse_json(json, "name"), Some("Alice".to_string()));
}

#[test]
fn test_parse_nested() {
    let json = r#"{"user": {"name": "Bob"}}"#;
    assert_eq!(parse_json(json, "user.name"), Some("Bob".to_string()));
}

#[test]
fn test_parse_number() {
    let json = r#"{"age": 30}"#;
    assert_eq!(parse_json(json, "age"), Some("30".to_string()));
}

#[test]
fn test_parse_missing_key() {
    let json = r#"{"name": "Alice"}"#;
    assert_eq!(parse_json(json, "age"), None);
}

#[test]
fn test_parse_array() {
    let json = r#"{"items": ["a", "b", "c"]}"#;
    assert_eq!(parse_json(json, "items.0"), Some("a".to_string()));
}

#[test]
fn test_empty_object() {
    assert_eq!(parse_json("{}", "x"), None);
}
