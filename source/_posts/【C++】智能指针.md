---
title: 【C++】智能指针
toc: true
categories:
  - 技术笔记
  - C++
cover: /img/covers/keyboard.jpg
date: 2025-06-05
tags:
  - 内存管理
  - 智能指针
  - RAII
description: 详解 C++ 智能指针：shared_ptr、unique_ptr 和 weak_ptr 的原理、使用场景及如何解决内存泄漏和循环引用问题。
---

## 为什么需要智能指针？

手动管理内存（`new`/`delete`）容易导致：
- **内存泄漏**：忘记释放内存
- **悬空指针**：释放后继续使用
- **重复释放**：同一块内存被释放多次

智能指针利用 **RAII（资源获取即初始化）** 机制，在对象离开作用域时自动调用析构函数释放内存。

---

## 三种智能指针

| 类型 | 所有权 | 引用计数 | 典型场景 |
|------|--------|----------|----------|
| `shared_ptr` | 共享 | 有 | 多个对象共享同一资源 |
| `unique_ptr` | 独占 | 无 | 资源只能有一个所有者 |
| `weak_ptr` | 无所有权 | 观察 | 打破循环引用 |

---

## shared_ptr：共享所有权

多个 `shared_ptr` 可以指向同一个对象，通过**引用计数**管理生命周期。当最后一个 `shared_ptr` 销毁时，对象被释放。

```cpp
#include <memory>

auto sp1 = std::make_shared<int>(42);  // 引用计数 = 1
{
    auto sp2 = sp1;   // 引用计数 = 2
    auto sp3 = sp1;   // 引用计数 = 3
}  // sp2, sp3 离开作用域，引用计数 = 1

// sp1 离开作用域时，引用计数 = 0，内存被释放
```

### 常用操作

```cpp
sp.use_count()  // 获取引用计数
sp.reset()      // 释放所有权，引用计数 -1
sp.get()        // 获取原始指针
```

---

## unique_ptr：独占所有权

同一时间只能有一个 `unique_ptr` 拥有对象。**不能拷贝，只能移动**。

```cpp
auto up1 = std::make_unique<int>(42);

// auto up2 = up1;  // 编译错误！不能拷贝

auto up2 = std::move(up1);  // 转移所有权
// 此时 up1 == nullptr
```

### 适用场景

- 工厂函数返回值
- 类成员的独占资源
- 容器中存储多态对象

```cpp
class Widget {};

std::unique_ptr<Widget> createWidget() {
    return std::make_unique<Widget>();
}
```

---

## weak_ptr：弱引用

`weak_ptr` 是对 `shared_ptr` 管理对象的弱引用，**不增加引用计数**，用于解决循环引用问题。

### 循环引用问题

```cpp
class B;  // 前向声明

class A {
public:
    std::shared_ptr<B> ptrB;
    ~A() { std::cout << "A destroyed" << std::endl; }
};

class B {
public:
    std::shared_ptr<A> ptrA;  // 循环引用！
    ~B() { std::cout << "B destroyed" << std::endl; }
};

int main() {
    auto a = std::make_shared<A>();
    auto b = std::make_shared<B>();
    a->ptrB = b;
    b->ptrA = a;
    // 离开作用域时，A 和 B 都不会被释放！（内存泄漏）
}
```

### 使用 weak_ptr 解决

```cpp
class B {
public:
    std::weak_ptr<A> ptrA;  // 改为 weak_ptr
    ~B() { std::cout << "B destroyed" << std::endl; }
};

// 现在可以正常释放
```

### weak_ptr 常用操作

```cpp
std::shared_ptr<int> sp = std::make_shared<int>(42);
std::weak_ptr<int> wp = sp;

wp.expired()   // 检查对象是否已被释放
wp.lock()      // 获取 shared_ptr（如果对象还在）

if (auto locked = wp.lock()) {
    // 安全使用 *locked
}
```

---

## 使用建议

| 场景 | 推荐使用 |
|------|----------|
| 资源独占，无需共享 | `unique_ptr` |
| 多处共享同一资源 | `shared_ptr` |
| 打破循环引用、缓存、观察者 | `weak_ptr` |
| 优先使用 | `make_shared` / `make_unique` |

**注意**：避免用原始指针初始化多个智能指针，会导致重复释放。

```cpp
int* raw = new int(42);
std::shared_ptr<int> sp1(raw);
std::shared_ptr<int> sp2(raw);  // 危险！两个独立的引用计数
```
