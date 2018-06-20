public class Hello {
    static final int finalVaule = 13;
    static int staticValue = 12;
    int tmp = 0;
    public static void main(String[] args) {
        // System.out.println("hello");
        // int res = 1;
        // int i = 10;
        // T t = new T();
        // res = t.test(res);
        // res = add(i, 2);
        // res = t.test(res);
        // System.out.println(res);
        // System.out.println(1);

        // int[] array = {3, 4};
        // System.out.println(array[0]);
        // int[] a1 = new int[2];
        // a1[0] = 3;
        // System.out.println(a1[0]);
        // boolean[] bbarray = {true, false};
        // System.out.println(bbarray[0]);
        // short[] sarray = {12, 15};
        // System.out.println(sarray[0]);
        // byte[] barray = {1, 8};
        // System.out.println(barray[0]);
        // float[] farray = {12.1f, 13.5f};
        // System.out.println(farray[0]);
        // double[] darray = {12.121, 13.5};
        // System.out.println(darray[0]);
        // long[] larray = {123213, 123432};
        // System.out.println(larray[0]);
        // char[] carray = {'a', 'b'};
        // System.out.println(carray[0]);
        
        // char c = 'c';
        // System.out.println(c);

        // long a = 100l;
        // System.out.println(a);
        // double d = 12.5;
        // System.out.println(d);
        // float f = 11.6f;
        // System.out.println(f);
        // short s = 129;
        // System.out.println(s);
        // byte bb = 8;
        // System.out.println(bb);
        // boolean b = true;
        // boolean c = false;
        // System.out.println(b);
        // System.out.println(c);
        // Thread thread = new Thread() {
        //     public void run() {
        //         for (int i = 0; i < 10; i ++) {
        //             System.out.println("in thread");
        //             System.out.println(i);
        //         }
        //     }
        // };
        // thread.start();

        // for (int i = 0; i < 10; i ++) {
        //     System.out.println("in main thread");
        // }
        //
        
        // T t = new T();
        // t.m = 1;
        // System.out.println(t.m);
        T[] tarray = new T[3];
        tarray[0] = new T();
        tarray[0].m = 3;
        System.out.println(tarray[0].m);
    }

    public static int add(int i, int j) {
        return i + j;
    }

    public static class T {
        int m = 0;
        public int test(int i) {
            return 1 + i;
        }
    }
}
