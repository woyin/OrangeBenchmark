import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class JsonParserTest {
    @Test void testParseString() {
        assertEquals("hello", JsonParser.parse("\"hello\""));
    }

    @Test void testParseNumber() {
        assertEquals(42.0, JsonParser.parse("42"));
        assertEquals(-3.14, JsonParser.parse("-3.14"));
    }

    @Test void testParseBoolean() {
        assertEquals(true, JsonParser.parse("true"));
        assertEquals(false, JsonParser.parse("false"));
    }

    @Test void testParseNull() {
        assertNull(JsonParser.parse("null"));
    }

    @Test void testParseEmptyObject() {
        Object r = JsonParser.parse("{}");
        assertTrue(r instanceof Map);
        assertTrue(((Map)r).isEmpty());
    }

    @Test void testParseSimpleObject() {
        Object r = JsonParser.parse("{\"name\":\"Alice\",\"age\":30}");
        assertEquals("Alice", JsonParser.getString(r, "name"));
        assertEquals(30.0, JsonParser.getNumber(r, "age"));
    }

    @Test void testParseArray() {
        Object r = JsonParser.parse("[1,2,3]");
        assertTrue(r instanceof List);
        assertEquals(3, ((List)r).size());
    }

    @Test void testNestedObject() {
        Object r = JsonParser.parse("{\"user\":{\"name\":\"Bob\"}}");
        assertEquals("Bob", JsonParser.getString(r, "user.name"));
    }

    @Test void testStringEscapes() {
        assertEquals("line1\nline2", JsonParser.parse("\"line1\\nline2\""));
    }

    @Test void testMalformedJson() {
        assertThrows(IllegalArgumentException.class, () -> JsonParser.parse("{invalid}"));
    }

    @Test void testComplexNested() {
        String json = "{\"items\":[{\"id\":1},{\"id\":2}],\"count\":2}";
        Object r = JsonParser.parse(json);
        assertEquals(2.0, JsonParser.getNumber(r, "count"));
    }
}
