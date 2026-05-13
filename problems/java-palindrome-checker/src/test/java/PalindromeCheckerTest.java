import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class PalindromeCheckerTest {
    @Test void testClassicPalindrome() {
        assertTrue(PalindromeChecker.isPalindrome("A man a plan a canal Panama"));
    }

    @Test void testSimplePalindrome() {
        assertTrue(PalindromeChecker.isPalindrome("racecar"));
    }

    @Test void testNotPalindrome() {
        assertFalse(PalindromeChecker.isPalindrome("hello"));
    }

    @Test void testEmptyString() {
        assertTrue(PalindromeChecker.isPalindrome(""));
    }

    @Test void testSingleChar() {
        assertTrue(PalindromeChecker.isPalindrome("a"));
    }

    @Test void testNull() {
        assertFalse(PalindromeChecker.isPalindrome(null));
    }

    @Test void testNumericPalindrome() {
        assertTrue(PalindromeChecker.isPalindrome("12321"));
    }

    @Test void testWithPunctuation() {
        assertTrue(PalindromeChecker.isPalindrome("Was it a car or a cat I saw?"));
    }
}
