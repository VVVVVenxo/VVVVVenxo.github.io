---
title: 【C++】拷贝控制
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - 拷贝控制
  - 深拷贝
  - 浅拷贝
description: 理解 C++ 中的浅拷贝与深拷贝：原理、区别、应用场景，以及如何正确实现拷贝构造函数和赋值运算符。
---

## 浅拷贝 (Shallow Copy)

### 定义

浅拷贝通过**直接拷贝**对象的成员。若对象中有指针成员，拷贝的只是指针的值（内存地址），即两个对象**共享同一块内存**。

### 原理

浅拷贝通过编译器自动生成的拷贝构造函数和赋值运算符进行。对指针成员的拷贝只是复制了指针地址，而不是指针指向的数据。

```cpp
class Shallow {
public:
    int* data;
    
    Shallow(int value) {
        data = new int(value);
    }
    
    // 编译器自动生成的拷贝构造函数（浅拷贝）
    // Shallow(const Shallow& other) : data(other.data) {}
    
    ~Shallow() {
        delete data;  // 危险！
    }
};

Shallow a(42);
Shallow b = a;  // 浅拷贝：b.data 和 a.data 指向同一块内存

// 当 a 和 b 都析构时，同一块内存被 delete 两次！
```

### 问题

| 问题 | 说明 |
|------|------|
| **悬空指针** | 一个对象释放内存后，另一个对象的指针变为悬空 |
| **重复释放** | 多个对象析构时尝试释放同一块内存 |
| **意外修改** | 修改一个对象会影响另一个对象 |

---

## 深拷贝 (Deep Copy)

### 定义

深拷贝通过**递归拷贝**对象的每一部分（包括指针成员），为每个对象分配**独立的内存**，避免对象间共享资源。

### 原理

深拷贝需要手动实现拷贝构造函数和赋值运算符。在拷贝指针成员时，为每个对象创建独立的内存副本。

```cpp
class Deep {
public:
    int* data;
    
    Deep(int value) {
        data = new int(value);
    }
    
    // 深拷贝：拷贝构造函数
    Deep(const Deep& other) {
        data = new int(*other.data);  // 分配新内存，拷贝值
    }
    
    // 深拷贝：赋值运算符
    Deep& operator=(const Deep& other) {
        if (this != &other) {         // 防止自赋值
            delete data;              // 释放旧内存
            data = new int(*other.data);  // 分配新内存
        }
        return *this;
    }
    
    ~Deep() {
        delete data;  // 安全释放
    }
};

Deep a(42);
Deep b = a;  // 深拷贝：b.data 指向新分配的内存

*b.data = 100;  // 不会影响 a.data
```

---

## 浅拷贝 vs 深拷贝

| 特性 | 浅拷贝 | 深拷贝 |
|------|--------|--------|
| 内存分配 | 共享同一块内存 | 各自独立的内存 |
| 默认行为 | 编译器自动生成 | 需手动实现 |
| 指针成员 | 拷贝地址 | 拷贝数据 |
| 修改影响 | 互相影响 | 互不影响 |
| 析构安全 | 可能重复释放 | 安全 |
| 性能 | 快 | 相对较慢 |

---

## 应用场景

### 浅拷贝适用

- 对象没有指针成员，或指针指向的资源由外部管理
- 明确需要共享资源的场景
- 使用智能指针（`shared_ptr`）管理共享资源

### 深拷贝适用

- 对象拥有动态分配的资源（如 `new` 出来的内存）
- 需要确保每个对象拥有独立资源
- 修改一个对象不应影响其他对象

---

## Rule of Three / Five

如果类需要自定义以下任意一个，通常需要自定义全部：

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
    // 构造函数
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
    
    // 4. 移动构造函数（C++11）
    Resource(Resource&& other) noexcept : data(other.data) {
        other.data = nullptr;
    }
    
    // 5. 移动赋值运算符（C++11）
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

优先使用**智能指针**和**标准容器**，让编译器自动生成的拷贝控制函数正确工作，避免手动管理内存。

```cpp
#include <memory>
#include <vector>

class Modern {
    std::unique_ptr<int> data;        // 自动深拷贝语义（禁止拷贝）
    std::vector<int> items;           // 自动深拷贝
    std::shared_ptr<Resource> shared; // 引用计数共享
};
```
