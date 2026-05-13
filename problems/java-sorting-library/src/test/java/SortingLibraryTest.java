import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SortingLibraryTest {
    private List<Integer> unsorted = Arrays.asList(5, 3, 8, 1, 9, 2, 7, 4, 6);
    private List<Integer> sorted = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9);

    @Test void testQuickSort() { assertEquals(sorted, SortingLibrary.quickSort(unsorted)); }
    @Test void testMergeSort() { assertEquals(sorted, SortingLibrary.mergeSort(unsorted)); }
    @Test void testHeapSort() { assertEquals(sorted, SortingLibrary.heapSort(unsorted)); }

    @Test void testEmptyList() {
        assertEquals(Collections.emptyList(), SortingLibrary.quickSort(Collections.emptyList()));
    }

    @Test void testSingleElement() {
        assertEquals(List.of(1), SortingLibrary.mergeSort(List.of(1)));
    }

    @Test void testAlreadySorted() {
        assertEquals(sorted, SortingLibrary.heapSort(new ArrayList<>(sorted)));
    }

    @Test void testReverseSorted() {
        List<Integer> rev = Arrays.asList(9,8,7,6,5,4,3,2,1);
        assertEquals(sorted, SortingLibrary.quickSort(rev));
    }

    @Test void testDuplicates() {
        List<Integer> dupes = Arrays.asList(3, 1, 2, 3, 1);
        assertEquals(Arrays.asList(1,1,2,3,3), SortingLibrary.mergeSort(dupes));
    }

    @Test void testStrings() {
        List<String> names = Arrays.asList("Charlie", "Alice", "Bob");
        assertEquals(Arrays.asList("Alice", "Bob", "Charlie"), SortingLibrary.quickSort(names));
    }

    @Test void testLargeRandom() {
        Random rng = new Random(42);
        List<Integer> large = new ArrayList<>();
        for (int i = 0; i < 10000; i++) large.add(rng.nextInt());
        List<Integer> expected = new ArrayList<>(large);
        Collections.sort(expected);
        assertEquals(expected, SortingLibrary.mergeSort(large));
    }
}
