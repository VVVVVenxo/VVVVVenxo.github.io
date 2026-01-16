---
title: 【C++】左值与右值
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
description: 理解 C++11 中的左值、右值、纯右值、将亡值概念，以及左值引用与右值引用的区别和使用场景。
---

## 左值与右值的定义

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

---

## C++11 对右值的细分

C++11 将右值进一步细分为**纯右值**和**将亡值**：

```
        值
       / \
     左值  右值
          / \
      纯右值  将亡值
```

### 纯右值 (prvalue)

等同于 C++98 中的右值概念：
- **临时变量**：非引用返回的函数返回值、表达式结果
- **字面量**：`true`、`42`、`3.14`、`"hello"`

```cpp
int getValue() { return 42; }

int x = getValue();  // getValue() 的返回值是纯右值
int y = 1 + 2;       // 1 + 2 的结果是纯右值
```

### 将亡值 (xvalue)

C++11 新增的概念，表示**即将被移动的对象**：
- `std::move()` 的返回值
- 返回右值引用 `T&&` 的函数返回值
- 转换为 `T&&` 的类型转换结果

```cpp
std::string str = "hello";
std::string str2 = std::move(str);  // std::move(str) 是将亡值
// str 的资源被"偷走"，str 变为空
```

**将亡值的意义**：通过"盗取"其他变量的内存空间，避免不必要的内存分配和释放，延长变量值的生命期。

---

## 左值引用与右值引用

### 左值引用 (T&)

绑定到左值，是具名变量的别名。

```cpp
int a = 10;
int& ref = a;    // OK：左值引用绑定到左值
int& ref2 = 42;  // 编译错误：左值引用不能绑定到右值
```

### 右值引用 (T&&)

C++11 新增，绑定到右值，是匿名变量的别名。

```cpp
int&& rref = 42;           // OK：右值引用绑定到右值
int&& rref2 = a;           // 编译错误：右值引用不能绑定到左值
int&& rref3 = std::move(a); // OK：std::move 将左值转为将亡值
```

---

## 常量左值引用：万能引用

`const T&` 是一个"万能"的引用类型，可以绑定到几乎所有值：

| 绑定对象 | 是否允许 |
|----------|----------|
| 非常量左值 | ✅ |
| 常量左值 | ✅ |
| 右值 | ✅ |

```cpp
int a = 2;
const int b = 3;

const int& r1 = a;    // 绑定到非常量左值
const int& r2 = b;    // 绑定到常量左值
const int& r3 = 42;   // 绑定到右值
```

**注意**：常量左值引用绑定的右值在其"余生"中是**只读的**。

---

## 代码示例汇总

```cpp
int a;

// 左值引用
int& ref1 = a;        // OK
int& ref2 = 2;        // 错误：左值引用不能绑定右值

// 常量左值引用（万能）
const int& cref1 = a;  // OK：绑定非常量左值
const int& cref2 = 2;  // OK：绑定右值

// 右值引用
int&& rref1 = 2;             // OK
int&& rref2 = a;             // 错误：右值引用不能绑定左值
int&& rref3 = std::move(a);  // OK：move 将左值转为将亡值
```

---

## 移动语义的应用

右值引用的核心价值在于实现**移动语义**，避免不必要的深拷贝：

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

MyString createString() {
    return MyString("hello");  // 返回值可被移动
}

MyString s = createString();  // 触发移动构造，而非拷贝构造
```
