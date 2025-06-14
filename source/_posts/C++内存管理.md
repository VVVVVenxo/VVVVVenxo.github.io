---
title: C++内存管理
---

### C++中的内存分区
1. 堆，使用malloc、free动态分配和释放空间，能分配较大的内存；
2. 栈，为函数的局部变量分配内存，能分配较小的内存；
3. 全局/静态存储区，用于存储全局变量和静态变量；
4. 常量存储区，专门用来存放常量；
5. 自由存储区：通过new和delete分配和释放空间的内存，具体实现可能是堆或者内存池。
***

> ##### 堆和自由存储区的区别：
> 堆是C和操作系统的术语，自由存储区是C++的术语，指的是通过new和delete动态分配和释放对象的抽象概念；基本上C++也会用堆区实现自由存储，但程序员可以通过重载操作符，改用其他内存实现自由存储，比如全局变量做的对象池。
> ##### 堆和栈的区别：
> 1. 堆中的内存需要手动申请和手动释放，栈中内存是由OS自动申请和自动释放；
>2. 堆能分配的内存较大（4G(32位机器)），栈能分配的内存较小（1M）；
>3. 在堆中分配和释放内存会产生内存碎片，栈不会产生内存碎片；
>4. 堆的分配效率低，栈的分配效率高；
>5. 堆地址从低向上，栈由高向下。

***

### 内存泄漏（Memory Leak）
是指程序在运行过程中分配了内存空间，但在不再使用这些内存时，没有释放它们，导致这部分内存无法被重新利用。长期下去，内存泄漏会导致程序占用越来越多的内存，甚至可能导致程序崩溃。

***

### 使用C/C++进行内存的分配、释放。
C使用`malloc/free`，C++使用`new/delete`，前者是C语言中的库函数，后者是C++语言的运算符，对于自定义对象，`malloc/free`只进行分配内存和释放内存，无法调用其构造函数和析构函数，只有`new/delete`能做到，完成对象的空间分配和初始化，以及对象的销毁和释放空间，不能混用，具体区别如下：

>1. `new`分配内存空间无需指定分配内存大小，malloc需要；
>2. `new`返回类型指针，类型安全，`malloc`返回void*，再强制转换成所需要的类型；
>3. `new`是从自由存储区获得内存，`malloc`从堆中获取内存；
>4. 对于类对象，`new`会调用构造函数和析构函数，`malloc`不会（核心）。

***

### 内存对齐
**C++进行内存对齐的原因：**
关键在于CPU存取数据的效率问题。为了提高效率，计算机从内存中取数据是按照一个固定长度的。比如在32位机上，CPU每次都是取32bit数据的，也就是4字节；若不进行对齐，要取出两块地址中的数据，进行掩码和移位等操作，写入目标寄存器内存，效率很低。内存对齐一方面可以节省内存，一方面可以提升数据读取的速度。

关键在于CPU存取数据的效率问题。为了提高效率，计算机从内存中取数据是按照一个固定长度的。比如在32位机上，CPU每次都是取32bit数据的，也就是4字节；若不进行对齐，要取出两块地址中的数据，进行掩码和移位等操作，写入目标寄存器内存，效率很低。内存对齐一方面可以节省内存，一方面可以提升数据读取的速度。

**C++对齐的原则**
1. 结构体变量的首地址能够被其最宽基本类型成员的对齐值所整除；
2. 结构体内每一个成员的相对于起始地址的偏移量能够被该变量的大小整除；
3. 结构体总体大小能够被最宽成员大小整除；如果不满足这些条件，编译器就会进行一个填充（padding）。

**我们应该怎么做？**
声明数据结构时，字节对齐的数据依次声明，然后小成员组合在一起，能省去一些浪费的空间，不要把小成员参杂声明在字节对齐的数据之间。