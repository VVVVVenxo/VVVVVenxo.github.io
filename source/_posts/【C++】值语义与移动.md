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
description: 理解 C++ 值语义：从拷贝到移动的演进，掌握左值右值、深浅拷贝、移动语义，以及 Rule of Five/Zero。
---

## 概述：为什么需要移动语义？

在 C++98 时代，对象传递主要依赖**拷贝**。但对于大型对象（如容器、字符串），深拷贝的开销很大：

```cpp
std::vector<int> createBigVector() {
    std::vector<int> v(1000000);  // 100 万个元素
    return v;  // C++98：拷贝 100 万个元素！
}
```

**核心问题**：当源对象即将销毁时（如函数返回值），拷贝它毫无意义，不如直接"偷走"它的资源。

**C++11 的解决方案**：引入**移动语义**，通过右值引用区分"需要保留的对象"和"即将销毁的对象"，实现资源的高效转移。

```
拷贝：分配新内存 → 复制数据 → 释放旧对象（慢）
移动：直接接管指针 → 置空旧对象（快）
```

---

## 一、值类别（Value Categories）

理解移动语义的前提是区分**左值**和**右值**。

### 左值 vs 右值

| 类型 | 定义 | 特点 | 示例 |
|------|------|------|------|
| **左值 (lvalue)** | 有名字、可以取地址 | 可出现在赋值号左边 | 变量 `a`、`arr[0]` |
| **右值 (rvalue)** | 没有名字、不能取地址 | 只能出现在赋值号右边 | `42`、`a + b` |

```cpp
int a = b + c;

// a 是左值：有名字，&a 合法
// b + c 是右值：没有名字，&(b + c) 编译失败
```

### C++11 对右值的细分

| 类型 | 说明 | 示例 |
|------|------|------|
| **纯右值 (prvalue)** | 临时变量、字面量 | `42`、`getValue()` 返回值 |
| **将亡值 (xvalue)** | 即将被移动的对象 | `std::move(str)` |

**将亡值的意义**：标记某个左值"可以被移动"，让编译器调用移动构造而非拷贝构造。

---

## 二、拷贝语义

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

### 浅拷贝 vs 深拷贝

| 特性 | 浅拷贝 | 深拷贝 |
|------|--------|--------|
| 内存分配 | 共享内存 | 独立内存 |
| 指针成员 | 拷贝地址 | 拷贝数据 |
| 修改影响 | 互相影响 | 互不影响 |
| 性能 | 快 | **较慢（问题所在）** |

**深拷贝的性能问题**：当对象即将销毁时，深拷贝仍然分配新内存、复制数据，这是浪费。移动语义正是为了解决这个问题。

---

## 三、移动语义

### 核心思想

移动语义不复制资源，而是**转移资源所有权**：

```
深拷贝：new + memcpy + delete  （三步）
移动：  ptr = other.ptr; other.ptr = nullptr;  （两步，无内存分配）
```

### 移动构造函数 & 移动赋值运算符

```cpp
class MyString {
    char* data;
    size_t size;
    
public:
    // 移动构造函数
    MyString(MyString&& other) noexcept 
        : data(other.data), size(other.size) {
        other.data = nullptr;  // 偷走资源
        other.size = 0;
    }
    
    // 移动赋值运算符
    MyString& operator=(MyString&& other) noexcept {
        if (this != &other) {
            delete[] data;         // 释放自己的资源
            data = other.data;     // 接管对方的资源
            size = other.size;
            other.data = nullptr;  // 置空对方
            other.size = 0;
        }
        return *this;
    }
};
```

**关键点**：
- 参数类型是 `T&&`（右值引用）
- 使用 `noexcept` 保证不抛异常（STL 容器会检查）
- 移动后将源对象置于**有效但未定义**的状态

### std::move 的本质

`std::move` **不移动任何东西**，它只是将左值**强制转换**为右值引用：

```cpp
template<typename T>
typename remove_reference<T>::type&& move(T&& arg) noexcept {
    return static_cast<typename remove_reference<T>::type&&>(arg);
}
```

**理解**：`std::move(x)` 告诉编译器"我不再需要 x 的值了，你可以移动它"。

```cpp
std::string str = "hello";
std::string str2 = std::move(str);  // 调用移动构造
// str 现在是空的（资源被移走）
```

**注意**：移动后的对象仍然存在，可以重新赋值或销毁，但不要再使用它的值。

---

## 四、引用类型总结

| 引用类型 | 语法 | 可绑定对象 | 典型用途 |
|----------|------|------------|----------|
| 左值引用 | `T&` | 左值 | 修改传入的变量 |
| 常量左值引用 | `const T&` | 左值、右值 | 只读参数（万能引用） |
| 右值引用 | `T&&` | 右值 | 移动语义 |

```cpp
int a = 10;

int& r1 = a;        // OK：左值引用绑定左值
int& r2 = 42;       // 错误：左值引用不能绑定右值

const int& r3 = a;  // OK：const 左值引用绑定左值
const int& r4 = 42; // OK：const 左值引用绑定右值（万能）

int&& r5 = 42;           // OK：右值引用绑定右值
int&& r6 = a;            // 错误：右值引用不能绑定左值
int&& r7 = std::move(a); // OK：move 将左值转为右值
```

---

## 五、Rule of Three / Five / Zero

如果类需要自定义资源管理函数，通常需要遵循以下规则。

### Rule of Three（C++98）

如果需要自定义以下任一项，通常需要全部自定义：

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

### Rule of Zero（现代 C++ 推荐）

**最佳实践**：不要手动管理资源，使用智能指针和标准容器，让编译器自动生成正确的特殊成员函数。

```cpp
class Modern {
    std::unique_ptr<int> data;        // 自动管理，禁止拷贝，支持移动
    std::vector<int> items;           // 自动深拷贝和移动
    std::shared_ptr<Resource> shared; // 引用计数共享
    
    // 不需要手写任何析构、拷贝、移动函数！
};
```

---

## 六、最佳实践

| 场景 | 推荐做法 |
|------|----------|
| 资源独占 | `std::unique_ptr` |
| 资源共享 | `std::shared_ptr` |
| 需要拷贝的容器 | `std::vector`、`std::string` |
| 函数参数（只读） | `const T&` |
| 函数参数（需要移动） | `T&&` 或值传递 + `std::move` |
| 返回局部对象 | 直接返回（编译器会 RVO/NRVO 优化） |

**总结**：

1. 优先使用 Rule of Zero，避免手动管理资源
2. 理解 `std::move` 只是类型转换，不是真正的移动
3. 移动后的对象处于有效但未定义状态，不要再使用其值
4. 移动构造/赋值应标记 `noexcept`
