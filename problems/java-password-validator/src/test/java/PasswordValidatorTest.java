import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class PasswordValidatorTest {
    PasswordValidator v = new PasswordValidator(8, true, true, true, true);

    @Test void testValidPassword() {
        assertTrue(v.validate("Abcdefg1!"));
    }

    @Test void testTooShort() {
        assertFalse(v.validate("Ab1!"));
    }

    @Test void testNoUppercase() {
        assertFalse(v.validate("abcdefg1!"));
    }

    @Test void testNoLowercase() {
        assertFalse(v.validate("ABCDEFG1!"));
    }

    @Test void testNoDigit() {
        assertFalse(v.validate("Abcdefg!!"));
    }

    @Test void testNoSpecial() {
        assertFalse(v.validate("Abcdefg12"));
    }

    @Test void testNullPassword() {
        assertFalse(v.validate(null));
    }

    @Test void testStrengthLevels() {
        assertEquals(0, v.getStrength("short"));
        PasswordValidator lax = new PasswordValidator(4, false, false, false, false);
        assertEquals(1, lax.getStrength("abcd"));
    }

    @Test void testGetFailures() {
        List<String> failures = v.getFailures("ab");
        assertFalse(failures.isEmpty());
    }

    @Test void testAllRulesDisabled() {
        PasswordValidator none = new PasswordValidator(0, false, false, false, false);
        assertTrue(none.validate("anything"));
    }
}
