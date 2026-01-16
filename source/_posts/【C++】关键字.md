---
title: 【C++】关键字
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - 关键字
  - const
  - static
  - extern
  - explicit
description: 详解 C++ 常用关键字：const、static、extern、explicit 的用法与应用场景。
---

本文介绍 C++ 中几个常用关键字的用法：`const`（常量）、`static`（静态）、`extern`（外部链接）、`explicit`（禁止隐式转换）。

---

## const 关键字

`const` 用于定义常量，表示该值不可被修改。

### 基本用法

```cpp
const int MAX_SIZE = 100;  // 常量
MAX_SIZE = 200;            // 编译错误
```

### 指针与 const

| 写法 | 名称 | 含义 |
|------|------|------|
| `const int* p` | 常量指针 | 指向的内容不可修改 |
| `int* const p` | 指针常量 | 指针本身不可修改 |
| `const int* const p` | 双重 const | 两者都不可修改 |

```cpp
int a = 10, b = 20;

const int* p1 = &a;   // 常量指针
*p1 = 30;             // 错误：不能修改指向的值
p1 = &b;              // OK：可以修改指针指向

int* const p2 = &a;   // 指针常量
*p2 = 30;             // OK：可以修改指向的值
p2 = &b;              // 错误：不能修改指针指向
```

### 顶层 const vs 底层 const

| 类型 | 说明 | 示例 |
|------|------|------|
| **顶层 const** | 对象本身是 const | `int* const p`（指针本身） |
| **底层 const** | 指向的对象是 const | `const int* p`（指向的值） |

### const 成员函数

```cpp
class MyClass {
    int value;
public:
    int getValue() const {    // const 成员函数
        // value = 10;        // 错误：不能修改成员
        return value;
    }
    
    void setValue(int v) {    // 非 const 成员函数
        value = v;
    }
};

const MyClass obj;
obj.getValue();    // OK：const 对象只能调用 const 成员函数
obj.setValue(10);  // 错误
```

### const 函数重载

`const` 成员函数可以与非 `const` 版本重载：

```cpp
class Container {
public:
    int& operator[](int index);             // 非 const 版本
    const int& operator[](int index) const; // const 版本
};

Container c;
const Container cc;

c[0] = 10;   // 调用非 const 版本
int v = cc[0]; // 调用 const 版本
```

---

## static 关键字

`static` 用于声明静态成员，使数据或函数与对象脱离，在内存中只有一份。

### static 的三种场景

| 场景 | 作用 |
|------|------|
| 文件作用域 | 限制变量/函数只在本文件可见 |
| 函数作用域 | 局部静态变量，只初始化一次 |
| 类作用域 | 静态成员，所有对象共享 |

### 静态成员

```cpp
class Account {
public:
    static double rate;
    static void set_rate(const double& x) { rate = x; }
};

// 必须在类外定义静态成员（分配内存）
double Account::rate = 8.0;

int main() {
    Account::set_rate(5.0);  // 通过类名调用
    
    Account a;
    a.set_rate(7.0);         // 通过对象调用
}
```

### 静态函数的特点

- **没有 this 指针**
- 只能访问静态成员
- 可以通过类名或对象调用

### 单例模式

利用静态成员实现单例模式：

```cpp
class Singleton {
public:
    static Singleton& getInstance() {
        static Singleton instance;  // 局部静态，延迟初始化
        return instance;
    }
    
    void doSomething() { /* ... */ }
    
private:
    Singleton() {}                           // 私有构造
    Singleton(const Singleton&) = delete;    // 禁止拷贝
};

// 使用
Singleton::getInstance().doSomething();
```

**局部静态的优势**：只有在首次调用时才分配内存，避免浪费。

---

## extern 关键字

### 外部声明

`extern` 用于声明一个变量或函数定义在其他文件中：

```cpp
// file1.cpp
int globalVar = 42;  // 定义

// file2.cpp
extern int globalVar;  // 声明（不分配内存）
void func() {
    std::cout << globalVar;  // 使用
}
```

### extern "C"

用于在 C++ 中调用 C 语言编写的函数，告诉编译器使用 C 的链接规范（不进行名称修饰）：

```cpp
// 声明一个 C 函数
extern "C" void cFunction(int a, int b);

// 声明多个 C 函数
extern "C" {
    void func1();
    void func2();
    int func3(int x);
}
```

**为什么需要**：C++ 支持函数重载，会对函数名进行修饰（name mangling）。C 不支持重载，不会修饰函数名。`extern "C"` 确保链接时能找到正确的函数。

---

## explicit 关键字

`explicit` 用于禁止构造函数的隐式类型转换。

### 隐式转换问题

```cpp
class MyInt {
public:
    MyInt(int value) : val(value) {}  // 允许隐式转换
private:
    int val;
};

void process(MyInt mi) { /* ... */ }

process(42);  // 隐式转换：int -> MyInt，可能不是预期行为
```

### 使用 explicit 禁止

```cpp
class MyInt {
public:
    explicit MyInt(int value) : val(value) {}
private:
    int val;
};

void process(MyInt mi) { /* ... */ }

process(42);           // 编译错误：不允许隐式转换
process(MyInt(42));    // OK：显式构造
```

### 适用场景

- 单参数构造函数（或只有一个非默认参数）
- 类型转换运算符

```cpp
class Rational {
public:
    explicit Rational(int num, int den = 1);  // 推荐使用 explicit
    
    explicit operator bool() const;  // 转换运算符也可以用 explicit
};
```

---

## 关键字对比

| 关键字 | 作用 | 典型场景 |
|--------|------|----------|
| `const` | 定义不可修改的值 | 常量、只读参数、const 成员函数 |
| `static` | 静态存储/链接 | 静态成员、单例模式、局部持久变量 |
| `extern` | 声明外部定义的变量/函数 | 跨文件共享全局变量、C 兼容 |
| `explicit` | 禁止隐式类型转换 | 单参数构造函数、类型转换运算符 |
