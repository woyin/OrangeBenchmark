use wasm_calculator::{add, div, eval_expression, mul, sub};

fn assert_close(actual: f64, expected: f64) {
    assert!((actual - expected).abs() < 1e-9, "actual={actual}, expected={expected}");
}

#[test]
fn arithmetic_functions_work() {
    assert_close(add(2.0, 3.0), 5.0);
    assert_close(sub(5.0, 3.0), 2.0);
    assert_close(mul(2.0, 3.0), 6.0);
    assert_close(div(6.0, 3.0), 2.0);
    assert!(div(1.0, 0.0).is_infinite());
}

#[test]
fn eval_handles_precedence_parentheses_and_space() {
    assert_close(eval_expression("1 + 2 * 3"), 7.0);
    assert_close(eval_expression("(1 + 2) * 3"), 9.0);
    assert_close(eval_expression("  3.5  +  2.5  "), 6.0);
    assert_close(eval_expression("((1 + 2))"), 3.0);
}

#[test]
fn eval_handles_invalid_empty_div_zero_large_and_negative() {
    assert!(eval_expression("").is_nan());
    assert!(eval_expression("1 + + 2").is_nan());
    assert!(eval_expression("1 / 0").is_infinite());
    assert_close(eval_expression("999999 * 999999"), 999998000001.0);
    assert_close(eval_expression("-5 + 3"), -2.0);
}

#[test]
#[ignore]
fn performance_smoke() {
    let mut value = 0.0;
    for _ in 0..50_000 {
        value += eval_expression("(1 + 2) * 3 - 4 / 2");
    }
    assert_close(value, 350000.0);
}
