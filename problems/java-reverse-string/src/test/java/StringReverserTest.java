import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class StringReverserTest {
    @Test
    public void testBasicString() {
        assertEquals("olleh", StringReverser.reverse("hello"));
    }

    @Test
    public void testEmptyString() {
        assertEquals("", StringReverser.reverse(""));
    }

    @Test
    public void testNullInput() {
        assertEquals("", StringReverser.reverse(null));
    }

    @Test
    public void testSingleCharacter() {
        assertEquals("a", StringReverser.reverse("a"));
    }

    @Test
    public void testUnicode() {
        assertEquals("界世好你", StringReverser.reverse("你好世界"));
    }

    @Test
    public void testPalindrome() {
        assertEquals("abcba", StringReverser.reverse("abcba"));
    }
}
