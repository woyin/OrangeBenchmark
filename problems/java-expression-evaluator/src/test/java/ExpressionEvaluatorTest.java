import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

import java.util.Map;

public class ExpressionEvaluatorTest {

    private ExpressionEvaluator eval;

    @BeforeEach
    public void setUp() {
        eval = new ExpressionEvaluator();
    }

    @Test
    public void testBasicArithmetic() {
        assertEquals(7.0, eval.evaluate("3 + 4"), 1e-9);
        assertEquals(-1.0, eval.evaluate("3 - 4"), 1e-9);
        assertEquals(12.0, eval.evaluate("3 * 4"), 1e-9);
        assertEquals(2.5, eval.evaluate("10 / 4"), 1e-9);
    }

    @Test
    public void testOperatorPrecedence() {
        // Multiplication before addition
        assertEquals(14.0, eval.evaluate("2 + 3 * 4"), 1e-9);
        // Division before subtraction
        assertEquals(7.0, eval.evaluate("10 - 6 / 2"), 1e-9);
        // Left-to-right for same precedence
        assertEquals(9.0, eval.evaluate("2 + 3 + 4"), 1e-9);
        assertEquals(24.0, eval.evaluate("2 * 3 * 4"), 1e-9);
    }

    @Test
    public void testParentheses() {
        assertEquals(20.0, eval.evaluate("(2 + 3) * 4"), 1e-9);
        assertEquals(2.0, eval.evaluate("(10 - 4) / 3"), 1e-9);
        // 2 * (3 + 4) * 5 = 2 * 7 * 5 = 70
        assertEquals(70.0, eval.evaluate("2 * (3 + 4) * 5"), 1e-9);
    }

    @Test
    public void testPowerOperator() {
        assertEquals(8.0, eval.evaluate("2 ^ 3"), 1e-9);
        assertEquals(9.0, eval.evaluate("3 ^ 2"), 1e-9);
        // Right-associative: 2 ^ 3 ^ 2 = 2 ^ (3 ^ 2) = 2 ^ 9 = 512
        assertEquals(512.0, eval.evaluate("2 ^ 3 ^ 2"), 1e-9);
    }

    @Test
    public void testVariables() {
        Map<String, Double> vars = Map.of("x", 5.0, "y", 3.0);
        assertEquals(8.0, eval.evaluate("x + y", vars), 1e-9);
        assertEquals(15.0, eval.evaluate("x * y", vars), 1e-9);
        assertEquals(2.0, eval.evaluate("x - y", vars), 1e-9);
    }

    @Test
    public void testBuiltInVariables() {
        assertEquals(Math.PI, eval.evaluate("pi"), 1e-9);
        assertEquals(Math.E, eval.evaluate("e"), 1e-9);
        assertEquals(0.0, eval.evaluate("sin(pi)"), 1e-9);
    }

    @Test
    public void testFunctions() {
        assertEquals(0.0, eval.evaluate("sin(0)"), 1e-9);
        assertEquals(1.0, eval.evaluate("cos(0)"), 1e-9);
        assertEquals(1.0, eval.evaluate("tan(pi/4)"), 1e-9);
        assertEquals(5.0, eval.evaluate("sqrt(25)"), 1e-9);
        assertEquals(3.0, eval.evaluate("abs(-3)"), 1e-9);
        assertEquals(1.0, eval.evaluate("log(exp(1))"), 1e-9);
        assertEquals(Math.E, eval.evaluate("exp(1)"), 1e-9);
    }

    @Test
    public void testUnaryMinus() {
        assertEquals(-5.0, eval.evaluate("-5"), 1e-9);
        assertEquals(-5.0, eval.evaluate("-(3+2)"), 1e-9);
        assertEquals(2.0, eval.evaluate("3 + -1"), 1e-9);
        assertEquals(1.0, eval.evaluate("-(-1)"), 1e-9);
    }

    @Test
    public void testDivisionByZero() {
        assertThrows(ArithmeticException.class, () -> eval.evaluate("1 / 0"));
    }

    @Test
    public void testUndefinedVariable() {
        assertThrows(IllegalArgumentException.class, () -> eval.evaluate("x + 1"));
    }

    @Test
    public void testComplexNestedExpression() {
        // sqrt(3^2 + 4^2) should be 5
        assertEquals(5.0, eval.evaluate("sqrt(3^2 + 4^2)"), 1e-9);
        // sin(pi/6) should be approximately 0.5
        assertEquals(0.5, eval.evaluate("sin(pi / 6)"), 1e-9);
        // 2 * (3 + sqrt(16)) - 1 = 2 * 7 - 1 = 13
        assertEquals(13.0, eval.evaluate("2 * (3 + sqrt(16)) - 1"), 1e-9);
    }

    @Test
    public void testEmptyExpressionThrows() {
        assertThrows(IllegalArgumentException.class, () -> eval.evaluate(""));
        assertThrows(IllegalArgumentException.class, () -> eval.evaluate("   "));
    }
}
