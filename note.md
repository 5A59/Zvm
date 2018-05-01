
### 解析 class 文件  

### 运行时数据区  
#### Thread 私有
* PC
* Java 虚拟机栈 
* 栈帧 Frame
* 局部变量表
* 操作数栈
* 动态链接: 指向运行时常量池
* 方法返回

Thread {
  Pc
  Frame {
    LocalVars
    OperandStack
    DynamicLinking
  }
}

#### 线程共有
* Java 堆: 类实例和数组分配内存的地方, GC 的主要区域
* 方法区: 存储类结构信息, 包括运行时常量池，字段，方法，构造函数和方法的字节码，<init>, <cinit>
* 运行时常量池: 字面常量等等
* 本地方法栈: native 方法栈 暂不实现

JavaHeap
MethodArea {
 List<Class>
}

### 指令集和解释器  
### 类和对象  
### 方法调用  
### 数组  
### 本地方法调用(*)  
### 反射  
### 异常  
### 线程  
### gc  

### 整体架构 / 执行流程
* start: 命令行工具
* parse .class file: 解析 class 文件，保存成类信息
* init: 初始化数据区域，类信息等
* find main method
* run main method: 指令解释器，函数调用，线程，gc，异常，反射
* finish


### Java 虚拟机动态地加载、链接与初始化类和接口。
加载是根据特定名称查找类或接口类型的 二进制表示(Binary Representation)，并由此二进制表示创建类或接口的过程。
链接是为 了让类或接口可以被 Java 虚拟机执行，而将类或接口并入虚拟机运行时状态的过程。
类或接口的 初始化是指执行类或接口的初始化方法<clinit>。

Java 虚拟机为每个类型都维护一个常量池
当类或接口创建时(§5.3)，它的二进制表示中的 constant_pool 表(§4.4)被用来构 造运行时常量池。