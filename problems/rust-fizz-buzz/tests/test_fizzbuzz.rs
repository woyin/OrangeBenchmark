use rust_fizz_buzz::fizzbuzz;

#[test]
fn test_basic() {
    let result = fizzbuzz(15);
    let expected = vec![
        "1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz",
        "11", "Fizz", "13", "14", "FizzBuzz"
    ];
    assert_eq!(result, expected);
}

#[test]
fn test_zero() {
    assert_eq!(fizzbuzz(0), Vec::<String>::new());
}

#[test]
fn test_single() {
    assert_eq!(fizzbuzz(1), vec!["1"]);
}

#[test]
fn test_three() {
    assert_eq!(fizzbuzz(3), vec!["1", "2", "Fizz"]);
}

#[test]
fn test_five() {
    assert_eq!(fizzbuzz(5), vec!["1", "2", "Fizz", "4", "Buzz"]);
}
