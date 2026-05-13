import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class FizzBuzzTest {
    @Test void testFizzBuzz15() {
        List<String> result = FizzBuzz.generate(15);
        assertEquals(15, result.size());
        assertEquals("1", result.get(0));
        assertEquals("Fizz", result.get(2));
        assertEquals("Buzz", result.get(4));
        assertEquals("FizzBuzz", result.get(14));
    }

    @Test void testZeroReturnsEmpty() {
        assertEquals(Collections.emptyList(), FizzBuzz.generate(0));
    }

    @Test void testNegativeReturnsEmpty() {
        assertEquals(Collections.emptyList(), FizzBuzz.generate(-5));
    }

    @Test void testSingleElement() {
        assertEquals(List.of("1"), FizzBuzz.generate(1));
    }

    @Test void testFirstFive() {
        List<String> r = FizzBuzz.generate(5);
        assertEquals(List.of("1", "2", "Fizz", "4", "Buzz"), r);
    }

    @Test void testLargeInput() {
        List<String> r = FizzBuzz.generate(1000);
        assertEquals(1000, r.size());
        assertEquals("FizzBuzz", r.get(14));
        assertEquals("FizzBuzz", r.get(29));
    }
}
