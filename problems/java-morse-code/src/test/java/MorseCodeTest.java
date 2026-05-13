import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class MorseCodeTest {
    @Test void testEncodeHello() {
        assertEquals(".... . .-.. .-.. ---", MorseCode.encode("HELLO"));
    }

    @Test void testEncodeHelloWorld() {
        assertEquals(".... . .-.. .-.. --- / .-- --- .-. .-.. -..", MorseCode.encode("HELLO WORLD"));
    }

    @Test void testDecodeSOS() {
        assertEquals("SOS", MorseCode.decode("... --- ..."));
    }

    @Test void testEncodeNumbers() {
        assertEquals(".---- ..--- ...--", MorseCode.encode("123"));
    }

    @Test void testRoundtrip() {
        String text = "MORSE CODE TEST";
        assertEquals(text, MorseCode.decode(MorseCode.encode(text)));
    }

    @Test void testEmptyString() {
        assertEquals("", MorseCode.encode(""));
        assertEquals("", MorseCode.decode(""));
    }

    @Test void testCaseInsensitive() {
        assertEquals(MorseCode.encode("HELLO"), MorseCode.encode("hello"));
    }

    @Test void testSingleChar() {
        assertEquals(".-", MorseCode.encode("A"));
        assertEquals("A", MorseCode.decode(".-"));
    }
}
