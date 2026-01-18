---
title: 【CSharp】类型与参数传递
toc: true
categories:
  - 技术笔记
  - C#
cover: /img/covers/earth.jpg
date: 2025-06-05
tags:
  - 值类型
  - 引用类型
  - 参数传递
  - ref
  - out
description: 理解 C# 中值类型与引用类型的区别、参数传递行为，以及 ref 和 out 关键字的用法。
---

## 值类型 vs 引用类型

### 基本区别

| 特性 | 值类型 | 引用类型 |
|------|--------|----------|
| 存储位置 | 栈（Stack） | 堆（Heap） |
| 存储内容 | 实际数据 | 对象的引用（地址） |
| 默认值 | 0 / false / '\0' | null |
| 赋值行为 | 复制值 | 复制引用 |
| 继承 | 隐式继承 `System.ValueType` | 继承 `System.Object` |

### 常见类型分类

| 值类型 | 引用类型 |
|--------|----------|
| `int`, `float`, `double`, `decimal` | `string` |
| `bool`, `char` | `class` |
| `struct` | `interface` |
| `enum` | `delegate` |
| 元组（值元组） | 数组 `[]` |

---

## 内存分配

### 值类型

值类型的数据直接存储在栈上（作为局部变量时）：

```
栈 (Stack)
┌─────────────┐
│  int a = 10 │  ← 直接存储值 10
├─────────────┤
│  int b = 20 │  ← 直接存储值 20
└─────────────┘
```

### 引用类型

引用类型在栈上存储引用，实际对象在堆上：

```
栈 (Stack)              堆 (Heap)
┌─────────────┐         ┌─────────────────┐
│  obj ───────┼────────►│  实际对象数据    │
└─────────────┘         └─────────────────┘
```

---

## 参数传递

### 值类型参数（值传递）

传递值类型时，传递的是**值的副本**，修改不影响原值：

```csharp
void Modify(int x)
{
    x = 100;  // 修改的是副本
}

int a = 10;
Modify(a);
Console.WriteLine(a);  // 输出: 10（未改变）
```

### 引用类型参数

传递引用类型时，传递的是**引用的副本**，可以修改对象内容：

```csharp
void Modify(int[] arr)
{
    arr[0] = 100;  // 修改堆上的对象
}

int[] nums = { 1, 2, 3 };
Modify(nums);
Console.WriteLine(nums[0]);  // 输出: 100（已改变）
```

### string 的特殊性

虽然 `string` 是引用类型，但它具有**不可变性**（Immutable）：

```csharp
void Modify(string s)
{
    s = "modified";  // 创建了新的 string 对象
}

string str = "original";
Modify(str);
Console.WriteLine(str);  // 输出: original（未改变）
```

---

## ref 和 out 关键字

两者都是引用传递，实现上都是指针，区别在于**语义**。

### ref 关键字

`ref` 表示引用传递，函数内可以读取也可以修改。变量在传参前**必须初始化**。

```csharp
void AddTen(ref int number)
{
    number += 10;  // 可以读取，也可以修改
}

int value = 5;       // 必须先初始化
AddTen(ref value);   // value 变为 15
```

### out 关键字

`out` 表示输出参数（变相的多返回值）。变量在传参前**不需要初始化**，但函数内**必须赋值**。

```csharp
void GetValues(out int x, out int y)
{
    x = 10;  // 函数内必须赋值
    y = 20;
}

int a, b;                  // 不需要初始化
GetValues(out a, out b);   // a = 10, b = 20
```

### ref vs out 对比

| 特性 | ref | out |
|------|-----|-----|
| 传参前是否需要初始化 | 是 | 否 |
| 函数内是否必须赋值 | 否 | 是 |
| 典型用途 | 修改已有变量 | 返回多个值 |

---

## struct vs class

### 基本对比

| 特性 | struct（值类型） | class（引用类型） |
|------|------------------|-------------------|
| 继承 | 不支持继承 | 支持继承 |
| 默认构造函数 | 不能定义无参构造（C# 10 前） | 可以定义 |
| 可为 null | 否（除非 Nullable） | 是 |
| 赋值行为 | 复制全部数据 | 复制引用 |
| 性能 | 小对象更快 | 大对象更合适 |

### struct 示例

```csharp
struct Point
{
    public int X;
    public int Y;
}

Point p1 = new Point { X = 10, Y = 20 };
Point p2 = p1;  // 复制整个结构体
p2.X = 100;
Console.WriteLine(p1.X);  // 输出: 10（p1 未受影响）
```

### class 示例

```csharp
class PointClass
{
    public int X;
    public int Y;
}

PointClass p1 = new PointClass { X = 10, Y = 20 };
PointClass p2 = p1;  // 复制引用
p2.X = 100;
Console.WriteLine(p1.X);  // 输出: 100（p1 也改变了）
```

### 何时使用 struct？

| 场景 | 推荐类型 |
|------|----------|
| 数据量小（< 16 字节） | struct |
| 不需要继承 | struct |
| 需要继承或多态 | class |
| 对象较大 | class |

---

## 装箱与拆箱

值类型转换为引用类型时发生**装箱（Boxing）**，反之为**拆箱（Unboxing）**：

```csharp
int value = 42;
object boxed = value;     // 装箱
int unboxed = (int)boxed; // 拆箱
```

**性能影响**：装箱/拆箱有性能开销，使用泛型可以避免：

```csharp
// 避免装箱
List<int> list = new List<int>();  // 泛型，无装箱

// 会装箱
ArrayList oldList = new ArrayList();
oldList.Add(42);  // int 被装箱为 object
```
