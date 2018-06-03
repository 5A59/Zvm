public class Hello {
    static final int finalVaule = 13;
    static int staticValue = 12;
    int tmp = 0;
    public static void main(String[] args) {
        int i = 0;
        int res = add(i, 2);
        // T t = new T();
        // res = t.test(res);
        // res = add(i, 2);
        // res = t.test(res);
    }

    public static int add(int i, int j) {
        return i + j;
    }

    public static class T {
        public int test(int i) {
            return 1 + i;
        }
    }
}
