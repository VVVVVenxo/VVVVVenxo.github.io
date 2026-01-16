---
title: 【C++】值语义与移动
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - C++11
  - 右值引用
  - 移动语义
  - 拷贝控制
description: 理解 C++ 值语义：左值与右值、深浅拷贝、右值引用、移动语义，以及 Rule of Five。
---

## 左值与右值

在 C++11 中，所有的值必属于**左值**或**右值**之一。

| 类型 | 定义 | 特点 |
|------|------|------|
| **左值 (lvalue)** | 有名字、可以取地址的值 | 可以出现在赋值号左边 |
| **右值 (rvalue)** | 没有名字、不能取地址的值 | 只能出现在赋值号右边 |

```cpp
int a = b + c;

// a 是左值：有名字，&a 合法
// b + c 是右值：没有名字，&(b + c) 编译失败
```

### 右值的细分

C++11 将右值进一步细分为**纯右值**和**将亡值**：

| 类型 | 说明 | 示例 |
|------|------|------|
| **纯右值 (prvalue)** | 临时变量、字面量 | `42`、`getValue()` 返回值 |
| **将亡值 (xvalue)** | 即将被移动的对象 | `std::move(str)` |

---

## 左值引用与右值引用

### 左值引用 (T&)

绑定到左值，是具名变量的别名。

```cpp
int a = 10;
int& ref = a;    // OK
int& ref2 = 42;  // 错误：左值引用不能绑定右值
```

### 右值引用 (T&&)

C++11 新增，绑定到右值。

```cpp
int&& rref = 42;           // OK
int&& rref2 = a;           // 错误：右值引用不能绑定左值
int&& rref3 = std::move(a); // OK：move 将左值转为将亡值
```

### 常量左值引用：万能引用

`const T&` 可以绑定到左值和右值：

```cpp
const int& r1 = a;    // 绑定到左值
const int& r2 = 42;   // 绑定到右值
```

---

## 浅拷贝与深拷贝

### 浅拷贝 (Shallow Copy)

直接拷贝对象成员。若有指针成员，拷贝的只是指针地址，两个对象**共享同一块内存**。

```cpp
class Shallow {
public:
    int* data;
    
    Shallow(int value) { data = new int(value); }
    ~Shallow() { delete data; }  // 危险：可能重复释放
};

Shallow a(42);
Shallow b = a;  // b.data 和 a.data 指向同一块内存
```

**问题**：悬空指针、重复释放、意外修改。

### 深拷贝 (Deep Copy)

为每个对象分配**独立的内存**，拷贝数据而非地址。

```cpp
class Deep {
public:
    int* data;
    
    Deep(int value) { data = new int(value); }
    
    // 深拷贝构造函数
    Deep(const Deep& other) {
        data = new int(*other.data);  // 分配新内存
    }
    
    // 深拷贝赋值运算符
    Deep& operator=(const Deep& other) {
        if (this != &other) {
            delete data;
            data = new int(*other.data);
        }
        return *this;
    }
    
    ~Deep() { delete data; }
};
```

### 对比

| 特性 | 浅拷贝 | 深拷贝 |
|------|--------|--------|
| 内存分配 | 共享内存 | 独立内存 |
| 指针成员 | 拷贝地址 | 拷贝数据 |
| 修改影响 | 互相影响 | 互不影响 |
| 性能 | 快 | 较慢 |

---

## 移动语义

右值引用的核心价值在于实现**移动语义**，避免不必要的深拷贝。

### 移动构造函数

```cpp
class MyString {
    char* data;
public:
    // 移动构造函数
    MyString(MyString&& other) noexcept 
        : data(other.data) {
        other.data = nullptr;  // 偷走资源
    }
    
    // 移动赋值运算符
    MyString& operator=(MyString&& other) noexcept {
        if (this != &other) {
            delete[] data;
            data = other.data;
            other.data = nullptr;
        }
        return *this;
    }
};
```

### std::move

`std::move` 将左值转为将亡值，使其可以被移动：

```cpp
std::string str = "hello";
std::string str2 = std::move(str);  // str 的资源被移走
// str 现在是空的
```

---

## Rule of Three / Five

如果类需要自定义以下任意一个，通常需要自定义全部。

### Rule of Three（C++98）

1. 析构函数
2. 拷贝构造函数
3. 拷贝赋值运算符

### Rule of Five（C++11）

在 Rule of Three 基础上，加上：

4. 移动构造函数
5. 移动赋值运算符

```cpp
class Resource {
    int* data;
public:
    Resource(int value) : data(new int(value)) {}
    
    // 1. 析构函数
    ~Resource() { delete data; }
    
    // 2. 拷贝构造函数
    Resource(const Resource& other) : data(new int(*other.data)) {}
    
    // 3. 拷贝赋值运算符
    Resource& operator=(const Resource& other) {
        if (this != &other) {
            delete data;
            data = new int(*other.data);
        }
        return *this;
    }
    
    // 4. 移动构造函数
    Resource(Resource&& other) noexcept : data(other.data) {
        other.data = nullptr;
    }
    
    // 5. 移动赋值运算符
    Resource& operator=(Resource&& other) noexcept {
        if (this != &other) {
            delete data;
            data = other.data;
            other.data = nullptr;
        }
        return *this;
    }
};
```

---

## 现代 C++ 建议

优先使用**智能指针**和**标准容器**，让编译器自动生成正确的拷贝控制函数：

```cpp
#include <memory>
#include <vector>

class Modern {
    std::unique_ptr<int> data;        // 禁止拷贝，支持移动
    std::vector<int> items;           // 自动深拷贝
    std::shared_ptr<Resource> shared; // 引用计数共享
};
```

| 场景 | 推荐 |
|------|------|
| 资源独占 | `unique_ptr` |
| 资源共享 | `shared_ptr` |
| 需要拷贝的容器 | `vector`、`string` 等标准容器 |
