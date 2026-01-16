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
description: 深入理解 C++ 内存管理：内存分区、动态分配、常见问题、RAII 与智能指针、内存对齐。
---

## 概述

C++ 赋予程序员直接操作内存的能力，但"能力越大，责任越大"。手动管理内存容易出错，是 C++ 程序 bug 的主要来源之一。

**本文主线**：

```
内存分区（基础）
    ↓
动态内存分配（方法）
    ↓
常见问题（内存泄漏、悬空指针、重复释放）
    ↓
解决方案（RAII + 智能指针）
    ↓
进阶话题（内存对齐）
```

---

## 一、内存分区

C++ 程序运行时，内存被划分为以下区域：

| 区域 | 说明 |
|------|------|
| **栈 (Stack)** | 函数局部变量，系统自动管理，分配较小（约 1MB） |
| **堆 (Heap)** | `malloc`/`free` 动态分配，手动管理，可分配较大内存 |
| **自由存储区** | `new`/`delete` 分配，C++ 概念，通常用堆实现 |
| **全局/静态区** | 全局变量和静态变量 |
| **常量区** | 字符串字面量等常量 |

### 堆 vs 栈

| 特性 | 堆 | 栈 |
|------|-----|-----|
| 管理方式 | 手动申请/释放 | 系统自动管理 |
| 可分配大小 | 较大（32 位约 4GB） | 较小（约 1MB） |
| 内存碎片 | 会产生 | 不会产生 |
| 分配效率 | 较低 | 较高 |
| 增长方向 | 低地址 → 高地址 | 高地址 → 低地址 |

### 堆 vs 自由存储区

- **堆**：C 和操作系统的术语
- **自由存储区**：C++ 的抽象概念，通过 `new`/`delete` 管理

C++ 通常用堆实现自由存储区，但可以通过重载 `operator new` 改用其他内存（如对象池）。

---

## 二、动态内存分配

### malloc/free vs new/delete

| 特性 | malloc/free | new/delete |
|------|-------------|------------|
| 来源 | C 标准库函数 | C++ 运算符 |
| 是否需要指定大小 | 是 | 否 |
| 返回类型 | `void*` 需强转 | 类型指针，类型安全 |
| 内存来源 | 堆 | 自由存储区 |
| 调用构造/析构函数 | **否** | **是** |

```cpp
// C 风格
int* p1 = (int*)malloc(sizeof(int));
*p1 = 42;
free(p1);

// C++ 风格
int* p2 = new int(42);  // 分配 + 初始化
delete p2;              // 析构 + 释放
```

**关键区别**：`new` 会调用构造函数，`delete` 会调用析构函数；`malloc`/`free` 不会。

---

## 三、内存管理的常见问题

手动管理内存容易出现以下问题：

### 1. 内存泄漏 (Memory Leak)

分配的内存没有释放，导致内存持续增长：

```cpp
void leak() {
    int* p = new int(42);
    // 忘记 delete p;
}  // p 离开作用域，但内存没释放 → 泄漏
```

### 2. 悬空指针 (Dangling Pointer)

指针指向的内存已释放，但指针仍在使用：

```cpp
int* p = new int(42);
delete p;
*p = 100;  // 危险！p 已经是悬空指针
```

### 3. 重复释放 (Double Free)

同一块内存被释放多次：

```cpp
int* p = new int(42);
delete p;
delete p;  // 危险！重复释放，未定义行为
```

### 4. 数组释放不匹配

`new[]` 必须与 `delete[]` 配对：

```cpp
int* arr = new int[10];
delete arr;    // 错误！应该用 delete[]
delete[] arr;  // 正确
```

---

## 四、RAII 与智能指针

### RAII：资源获取即初始化

**RAII (Resource Acquisition Is Initialization)** 是 C++ 解决资源管理问题的核心思想：

- **获取资源时**：在构造函数中获取
- **释放资源时**：在析构函数中释放

当对象离开作用域时，析构函数自动调用，资源自动释放。

```cpp
// 不推荐：手动管理
void badExample() {
    int* p = new int(42);
    // 如果中间抛出异常，delete 不会执行 → 内存泄漏
    delete p;
}

// 推荐：使用 RAII（智能指针）
void goodExample() {
    auto p = std::make_unique<int>(42);
    // 无论正常返回还是抛异常，都会自动释放
}
```

---

### 智能指针

智能指针是 RAII 的典型应用，自动管理动态内存的生命周期。

| 类型 | 所有权 | 引用计数 | 典型场景 |
|------|--------|----------|----------|
| `unique_ptr` | 独占 | 无 | 资源只有一个所有者 |
| `shared_ptr` | 共享 | 有 | 多处共享同一资源 |
| `weak_ptr` | 无所有权 | 观察 | 打破循环引用 |

---

### unique_ptr：独占所有权

同一时间只能有一个 `unique_ptr` 拥有对象。**不能拷贝，只能移动**。

```cpp
auto up1 = std::make_unique<int>(42);

// auto up2 = up1;  // 编译错误！不能拷贝

auto up2 = std::move(up1);  // 转移所有权
// 此时 up1 == nullptr
```

**使用场景**：工厂函数返回值、类成员的独占资源。

---

### shared_ptr：共享所有权

多个 `shared_ptr` 可以指向同一个对象，通过**引用计数**管理生命周期。

```cpp
auto sp1 = std::make_shared<int>(42);  // 引用计数 = 1
{
    auto sp2 = sp1;   // 引用计数 = 2
    auto sp3 = sp1;   // 引用计数 = 3
}  // sp2, sp3 离开作用域，引用计数 = 1

// sp1 离开作用域时，引用计数 = 0，内存被释放
```

---

### weak_ptr：弱引用

`weak_ptr` 不增加引用计数，用于**打破循环引用**。

**循环引用问题**：

```cpp
class A {
public:
    std::shared_ptr<B> ptrB;  // A 持有 B
};

class B {
public:
    std::shared_ptr<A> ptrA;  // B 持有 A → 循环引用！
};

// A 和 B 互相持有，引用计数永远不为 0，内存泄漏
```

**解决方案**：

```cpp
class B {
public:
    std::weak_ptr<A> ptrA;  // 改为 weak_ptr，打破循环
};
```

---

### 智能指针使用建议

| 场景 | 推荐 |
|------|------|
| 资源独占 | `unique_ptr`（首选） |
| 资源共享 | `shared_ptr` |
| 打破循环引用 | `weak_ptr` |
| 创建方式 | `make_unique` / `make_shared` |

**注意事项**：

```cpp
// 错误：用原始指针初始化多个智能指针
int* raw = new int(42);
std::shared_ptr<int> sp1(raw);
std::shared_ptr<int> sp2(raw);  // 危险！两个独立的引用计数

// 正确：使用 make_shared 或从已有 shared_ptr 拷贝
auto sp1 = std::make_shared<int>(42);
auto sp2 = sp1;  // 共享同一引用计数
```

---

## 五、内存对齐

### 为什么需要内存对齐？

CPU 从内存取数据是按**固定长度**进行的（如 32 位机每次取 4 字节）。若数据未对齐，需要多次内存访问并进行掩码、移位操作，效率很低。

### 对齐原则

1. 结构体首地址能被最宽成员的对齐值整除
2. 每个成员的偏移量能被该成员大小整除
3. 结构体总大小能被最宽成员大小整除

不满足时，编译器会进行**填充（padding）**。

### 最佳实践

声明结构体时，将大成员放在前面，小成员组合在一起，减少填充浪费：

```cpp
// 不好的写法（产生额外填充）
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

## 总结

| 主题 | 要点 |
|------|------|
| 内存分区 | 栈（自动）、堆（手动）、全局/静态区、常量区 |
| 动态分配 | 优先使用 `new`/`delete`，C++ 会调用构造/析构 |
| 常见问题 | 内存泄漏、悬空指针、重复释放、数组释放不匹配 |
| 解决方案 | RAII + 智能指针，自动管理资源生命周期 |
| 智能指针 | `unique_ptr`（独占）、`shared_ptr`（共享）、`weak_ptr`（打破循环） |
| 内存对齐 | 大成员在前，减少 padding |
