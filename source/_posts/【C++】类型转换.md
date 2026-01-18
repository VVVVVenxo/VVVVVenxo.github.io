---
title: 【C++】类型转换
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - 类型转换
  - cast
description: 详解 C++ 中的四种类型转换关键字：const_cast、static_cast、dynamic_cast 和 reinterpret_cast，分析它们的使用场景和区别。
---

## 概述

C++ 提供了四种类型转换运算符，用于替代 C 风格的强制类型转换，提供更明确的语义和更好的类型安全。

| 转换类型 | 用途 | 安全性 | 检查时机 |
|----------|------|--------|----------|
| `const_cast` | 去除/添加 const 属性 | 中 | 编译期 |
| `static_cast` | 基本类型转换、类层次向上/向下转换 | 中 | 编译期 |
| `dynamic_cast` | 类层次安全向下转换 | 高 | 运行期 |
| `reinterpret_cast` | 任意类型的二进制重新解释 | 低 | 无检查 |

---

## const_cast

用于去除或添加 `const` 属性，**只能用于指针或引用**。

```cpp
const int a = 10;
int* p = const_cast<int*>(&a);  // 去除 const
*p = 20;  // 未定义行为（修改真正的 const 对象）

int b = 10;
const int* cp = &b;
int* mp = const_cast<int*>(cp);  // 合法，b 本身不是 const
*mp = 30;  // OK
```

**注意**：只能改变对象的**底层 const**（指针指向的对象是否为 const），不能改变顶层 const（指针本身是否为 const）。

---

## static_cast

用于编译期已知类型关系的转换：

- 基本数据类型之间的转换（int、float、enum 等）
- 类层次间的向上转换（派生类 → 基类）✅ 安全
- 类层次间的向下转换（基类 → 派生类）⚠️ 不安全（无运行时检查）

```cpp
// 基本类型转换
double d = 3.14;
int i = static_cast<int>(d);  // i = 3

// 类层次转换
class Base {};
class Derived : public Base {};

Derived* pd = new Derived();
Base* pb = static_cast<Base*>(pd);      // 向上转换，安全

Base* pb2 = new Base();
Derived* pd2 = static_cast<Derived*>(pb2);  // 向下转换，不安全！
```

**限制**：
- 不能转换无关类型的指针
- 不能去除 const 属性

---

## dynamic_cast

用于**运行时安全的类层次转换**，主要用于向下转换（基类 → 派生类）。

```cpp
class Base {
public:
    virtual ~Base() {}  // 必须有虚函数
};

class Derived : public Base {};

Base* pb = new Derived();
Derived* pd = dynamic_cast<Derived*>(pb);  // 成功，pd != nullptr

Base* pb2 = new Base();
Derived* pd2 = dynamic_cast<Derived*>(pb2);  // 失败，pd2 == nullptr
```

**特点**：
- 父类**必须有虚函数**，否则编译不通过
- 指针转换失败返回 `nullptr`
- 引用转换失败抛出 `std::bad_cast` 异常

---

## reinterpret_cast

将数据的二进制形式**重新解释**为另一种类型，不进行任何检查。

```cpp
int i = 42;
int* p = &i;

// 指针转整数
uintptr_t addr = reinterpret_cast<uintptr_t>(p);

// 整数转指针
int* p2 = reinterpret_cast<int*>(addr);

// 不同类型指针互转（危险！）
float* fp = reinterpret_cast<float*>(p);
```

**警告**：这是最不安全的转换，仅在底层编程（如内存映射、硬件接口）中使用。

---

## static_cast vs dynamic_cast

| 特性 | static_cast | dynamic_cast |
|------|-------------|--------------|
| 检查时机 | 编译期 | 运行期 |
| 需要虚函数 | 否 | 是 |
| 向下转换安全性 | 不安全 | 安全 |
| 性能 | 无额外开销 | 有 RTTI 开销 |
| 失败时行为 | 未定义行为 | 返回 nullptr 或抛异常 |
