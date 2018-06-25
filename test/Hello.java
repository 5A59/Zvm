public class Hello {
    static final int finalVaule = 13;
    static int staticValue = 12;
    int tmp = 0;
    public static void main(String[] args) {
        System.out.println("=================");
        System.out.println("Hello world");
        System.out.println("=================");
        testPrint();
        test();
        testBase();
        testArray();
        testThread();
        testClass();
        checkCast();

        // checkNull();

        testGC();
        testSwitch();
        testReturn();
        // testException();
    }

    public static void testException() {
        System.out.println("======== test exception =========");
        try {
            testException1();
        } catch(Exception ex) {
            System.out.println("exception catched");
        }
    }

    public static void testException1() throws TestException {
        throw new TestException();
    }

    public static void testPrint() {
        System.out.println("======== test print =========");
        System.out.println(1);
    }

    public static void testReturn() {
        System.out.println("======== test return =========");
        System.out.println(-100);
        T t = newT();
        System.out.println(t.n);
        int i = returnI();
        System.out.println(i);
        double d = returnD();
        System.out.println(d);
        float f = returnF();
        System.out.println(f);
        long l = returnL();
        System.out.println(l);
    }

    public static void testSwitch() {
        System.out.println("======== test switch =========");
        int i = 1;
        int b = switchTest(i);
        System.out.println(b);
        b = switchTest(2);
        System.out.println(b);
        b = switchTest(0);
        System.out.println(b);
        b = switchTest(5);
        System.out.println(b);

        System.out.println("=============");
        b = lookUpSwitchTest(-100);
        System.out.println(b);
        b = lookUpSwitchTest(1);
        System.out.println(b);
        b = lookUpSwitchTest(100);
        System.out.println(b);
        b = lookUpSwitchTest(20);
        System.out.println(b);
    }

    public static void testGC() {
        System.out.println("======== test gc =========");
        testGC2();
        for (int i = 0; i < 9; i ++) {
            T t = new T();
        }
    }

    public static void testGC2() {
        for (int i = 0; i < 9; i ++) {
            T t = new T();
        }
    }

    public static void testClass() {
        System.out.println("======== test class =========");
        T t = new T();
        t.m = 1;
        t.not.n = 3;
        System.out.println(t.m);
        t.test1();
        
        T1 t1 = new T();
        T1 t2 = new T1();
    }

    public static void testThread() {
        System.out.println("======== test thread =========");
        Thread thread = new Thread() {
            public void run() {
                for (int i = 0; i < 10; i ++) {
                    System.out.println("in thread");
                    System.out.println(i);
                }
            }
        };
        thread.start();

        for (int i = 0; i < 10; i ++) {
            System.out.println("in main thread");
        }
    }

    public static void testBase() {
        System.out.println("======== test base type =========");
        char c = 'c';
        System.out.println(c);

        long a = 100l;
        System.out.println(a);
        double d = 12.5;
        System.out.println(d);
        float f = 11.6f;
        System.out.println(f);
        short s = 129;
        System.out.println(s);
        byte bb = 8;
        System.out.println(bb);
        boolean b = true;
        boolean cc = false;
        System.out.println(b);
        System.out.println(cc);
    }

    public static void test() {
        System.out.println("======== test operation ========");
        System.out.println("hello");
        int res = 1;
        int i = 10;
        T t = new T();
        res = t.test(res);
        res = add(i, 2);
        res = t.test(res);
        System.out.println(res);
        System.out.println(1);
        System.out.println(1 + 1);
        System.out.println(2 - 1);
        System.out.println(3 << 1);
        System.out.println(3 >> 1);
        System.out.println(2 ^ 1);
        System.out.println(1 | 1);
        System.out.println(2 & 1);
    }

    public static void checkNull() {
        System.out.println("======== test null check ========");
        T t = null;
        System.out.println(t.m);
        if (t == null) {
            t = new T();
            System.out.println(t.m);
        }
    }

    public static void checkCast() {
        System.out.println("======== test cast ========");
        T1 t = new T();
        if (t instanceof T) {
            T t1 = (T) t;
            System.out.println("instance of 1");
        }
        T2 t2 = new T2();
        if (t2 instanceof T) {
            T t1 = (T) t;
            System.out.println("instance of");
        }
    }

    public static void testArray() {
        System.out.println("======== test  array ========");
        int[] array = {3, 4};
        System.out.println(array[0]);
        System.out.println(array.length);
        int[] a1 = new int[2];
        a1[0] = 3;
        System.out.println(a1[0]);
        boolean[] bbarray = {true, false};
        System.out.println(bbarray[0]);
        short[] sarray = {12, 15};
        System.out.println(sarray[0]);
        byte[] barray = {1, 8};
        System.out.println(barray[0]);
        float[] farray = {12.1f, 13.5f};
        System.out.println(farray[0]);
        double[] darray = {12.121, 13.5};
        System.out.println(darray[0]);
        long[] larray = {123213, 123432};
        System.out.println(larray[0]);
        char[] carray = {'a', 'b'};
        System.out.println(carray[0]);

        T[] tarray = new T[3];
        tarray[0] = new T();
        tarray[0].m = 3;
        System.out.println(tarray[0].m);
    }

    public static T newT() {
        return new T();
    }

    public static int returnI() {
        return 1;
    }

    public static float returnF() {
        return 1.0f;
    }

    public static double returnD() {
        return 1.0;
    }

    public static long returnL() {
        return 1l;
    }

    public static int switchTest(int i) {
        switch(i) {
            case 0: return 0;
            case 1: return 1;
            case 2: return 2;
            default: return -1;
        }
    }

    public static int lookUpSwitchTest(int i) {
        switch(i) {
            case -100: return -100;
            case 1: return 1;
            case 100: return 100;
            default: return -1;
        }
    }

    public static int add(int i, int j) {
        return i + j;
    }

    public static class NOT {
        public int n = 0;
    }

    public static class T extends T1 {
        public static NOT not = new NOT();
        public static int s = 3;
        public int n = 3;
        public int test(int i) {
            m = 3;
            return 1 + i;
        }

        public void test1() {
            super.test1();
            System.out.println("class T method test1");
        }
    }

    public static class T1 extends T2{
        public int m;
        public void test1() {
            System.out.println("super class T1 method test1");
        }
    }

    public static class T2 {
        public void test1() {
            System.out.println("super class T2 method test1");
        }

        public void test2() {
            System.out.println("super class T2 method test2");
        }
    }

    public static class TestException extends RuntimeException {
    }
}
