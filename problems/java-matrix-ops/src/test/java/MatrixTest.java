import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class MatrixTest {
    @Test void testIdentityMultiply() {
        Matrix id = new Matrix(new double[][]{{1,0},{0,1}});
        Matrix m = new Matrix(new double[][]{{2,3},{4,5}});
        Matrix r = id.multiply(m);
        assertEquals(2.0, r.get(0,0));
        assertEquals(3.0, r.get(0,1));
        assertEquals(4.0, r.get(1,0));
        assertEquals(5.0, r.get(1,1));
    }

    @Test void test2x2Determinant() {
        Matrix m = new Matrix(new double[][]{{1,2},{3,4}});
        assertEquals(-2.0, m.determinant(), 0.001);
    }

    @Test void test3x3Determinant() {
        Matrix m = new Matrix(new double[][]{{1,2,3},{4,5,6},{7,8,0}});
        assertEquals(27.0, m.determinant(), 0.001);
    }

    @Test void testTranspose() {
        Matrix m = new Matrix(new double[][]{{1,2,3},{4,5,6}});
        Matrix t = m.transpose();
        assertEquals(3, t.getRows());
        assertEquals(2, t.getCols());
        assertEquals(1.0, t.get(0,0));
        assertEquals(4.0, t.get(0,1));
    }

    @Test void testDimensionMismatch() {
        Matrix a = new Matrix(new double[][]{{1,2}});
        Matrix b = new Matrix(new double[][]{{1,2}});
        assertThrows(IllegalArgumentException.class, () -> a.multiply(b));
    }

    @Test void test1x1Determinant() {
        Matrix m = new Matrix(new double[][]{{42.0}});
        assertEquals(42.0, m.determinant(), 0.001);
    }

    @Test void testMultiply23x32() {
        Matrix a = new Matrix(new double[][]{{1,2,3},{4,5,6}});
        Matrix b = new Matrix(new double[][]{{7,8},{9,10},{11,12}});
        Matrix r = a.multiply(b);
        assertEquals(2, r.getRows());
        assertEquals(2, r.getCols());
        assertEquals(58.0, r.get(0,0), 0.001);
        assertEquals(64.0, r.get(0,1), 0.001);
    }
}
