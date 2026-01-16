---
title: 【C++】内存管理
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - 内存管理
  - 堆栈
  - 智能指针
  - RAII
description: 深入理解 C++ 内存管理：内存分区、堆栈区别、malloc/new、内存对齐、智能指针及 RAII 模式。
---

## C++ 中的内存分区

| 区域 | 说明 |
|------|------|
| **堆 (Heap)** | 使用 `malloc`/`free` 动态分配和释放，能分配较大内存 |
| **栈 (Stack)** | 为函数局部变量分配内存，由系统自动管理，分配较小 |
| **全局/静态区** | 存储全局变量和静态变量 |
| **常量区** | 存放常量（字符串字面量等） |
| **自由存储区** | 通过 `new`/`delete` 分配释放，可能是堆或内存池 |

### 堆和自由存储区的区别

堆是 C 和操作系统的术语，自由存储区是 C++ 的术语，指通过 `new`/`delete` 动态分配和释放对象的抽象概念。C++ 通常用堆实现自由存储，但程序员可以通过重载 `operator new`，改用其他内存实现（如对象池）。

### 堆和栈的区别

| 特性 | 堆 | 栈 |
|------|-----|-----|
| 管理方式 | 手动申请/释放 | 系统自动管理 |
| 可分配大小 | 较大（32位约4GB） | 较小（约1MB） |
| 内存碎片 | 会产生 | 不会产生 |
| 分配效率 | 较低 | 较高 |
| 增长方向 | 低地址 → 高地址 | 高地址 → 低地址 |

---

## 内存泄漏 (Memory Leak)

程序在运行过程中分配了内存空间，但在不再使用时没有释放，导致这部分内存无法被重新利用。长期下去会导致程序占用越来越多内存，甚至崩溃。

---

## malloc/free vs new/delete

C 使用 `malloc`/`free`，C++ 使用 `new`/`delete`。

| 特性 | malloc/free | new/delete |
|------|-------------|------------|
| 类型 | 库函数 | 运算符 |
| 是否需要指定大小 | 是 | 否 |
| 返回类型 | `void*` 需强转 | 类型指针，类型安全 |
| 内存来源 | 堆 | 自由存储区 |
| 是否调用构造/析构函数 | 否 | 是 |

---

## RAII：资源获取即初始化

为了避免手动管理内存导致的泄漏问题，C++ 推荐使用 **RAII (Resource Acquisition Is Initialization)** 模式。

```cpp
// 不推荐：手动管理内存
void badExample() {
    int* p = new int(42);
    // 如果中间抛出异常，内存泄漏
    delete p;
}

// 推荐：使用智能指针
#include <memory>
void goodExample() {
    auto p = std::make_unique<int>(42);
    // 离开作用域时自动释放，无需手动 delete
}
```

---

## 内存对齐

### 为什么需要内存对齐？

CPU 从内存取数据是按固定长度进行的（如 32 位机每次取 4 字节）。若数据未对齐，需要多次内存访问并进行掩码、移位操作，效率很低。内存对齐可以提升数据读取速度。

### 对齐原则

1. 结构体首地址能被最宽成员的对齐值整除
2. 每个成员的偏移量能被该成员大小整除
3. 结构体总大小能被最宽成员大小整除

不满足时，编译器会进行填充（padding）。

### 最佳实践

声明结构体时，将大成员放在前面，小成员组合在一起，可减少填充浪费：

```cpp
// 不好的写法（可能产生额外填充）
struct Bad {
    char a;    // 1 byte + 7 padding
    double b;  // 8 bytes
    char c;    // 1 byte + 7 padding
};  // 总共 24 bytes

// 好的写法
struct Good {
    double b;  // 8 bytes
    char a;    // 1 byte
    char c;    // 1 byte + 6 padding
};  // 总共 16 bytes
```

---

## 智能指针

手动管理内存（`new`/`delete`）容易导致：
- **内存泄漏**：忘记释放内存
- **悬空指针**：释放后继续使用
- **重复释放**：同一块内存被释放多次

智能指针利用 RAII 机制，在对象离开作用域时自动释放内存。

### 三种智能指针

| 类型 | 所有权 | 引用计数 | 典型场景 |
|------|--------|----------|----------|
| `shared_ptr` | 共享 | 有 | 多个对象共享同一资源 |
| `unique_ptr` | 独占 | 无 | 资源只能有一个所有者 |
| `weak_ptr` | 无所有权 | 观察 | 打破循环引用 |

---

### shared_ptr：共享所有权

多个 `shared_ptr` 可以指向同一个对象，通过**引用计数**管理生命周期。

```cpp
#include <memory>

auto sp1 = std::make_shared<int>(42);  // 引用计数 = 1
{
    auto sp2 = sp1;   // 引用计数 = 2
    auto sp3 = sp1;   // 引用计数 = 3
}  // sp2, sp3 离开作用域，引用计数 = 1

// sp1 离开作用域时，引用计数 = 0，内存被释放
```

---

### unique_ptr：独占所有权

同一时间只能有一个 `unique_ptr` 拥有对象。**不能拷贝，只能移动**。

```cpp
auto up1 = std::make_unique<int>(42);

// auto up2 = up1;  // 编译错误！不能拷贝

auto up2 = std::move(up1);  // 转移所有权
// 此时 up1 == nullptr
```

---

### weak_ptr：弱引用

`weak_ptr` 是对 `shared_ptr` 管理对象的弱引用，**不增加引用计数**，用于解决循环引用问题。

```cpp
class A {
public:
    std::shared_ptr<B> ptrB;
};

class B {
public:
    std::weak_ptr<A> ptrA;  // 使用 weak_ptr 打破循环引用
};
```

---

### 智能指针使用建议

| 场景 | 推荐使用 |
|------|----------|
| 资源独占，无需共享 | `unique_ptr` |
| 多处共享同一资源 | `shared_ptr` |
| 打破循环引用、缓存、观察者 | `weak_ptr` |
| 优先使用 | `make_shared` / `make_unique` |

**注意**：避免用原始指针初始化多个智能指针，会导致重复释放。
