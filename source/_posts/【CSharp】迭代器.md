---
title: 【CSharp】迭代器
toc: true
categories:
  - 技术笔记
  - C#
cover: /img/covers/earth.jpg
date: 2025-06-05
tags:
  - 迭代器
  - yield
  - foreach
description: 理解 C# 迭代器模式：IEnumerable/IEnumerator 接口、foreach 的本质，以及 yield return 语法糖的实现原理。
---

## 什么是迭代器？

迭代器（Iterator）是一种设计模式，提供一种方法顺序访问聚合对象中的各个元素，而又**不暴露内部结构**。

在 C# 中，迭代器通过 `IEnumerable` 和 `IEnumerator` 接口实现。

---

## IEnumerable 与 IEnumerator

### 接口定义

```csharp
// 可枚举对象
public interface IEnumerable
{
    IEnumerator GetEnumerator();
}

// 枚举器
public interface IEnumerator
{
    object Current { get; }    // 当前元素
    bool MoveNext();           // 移动到下一个元素
    void Reset();              // 重置到初始位置
}
```

### 手动实现示例

```csharp
public class MyCollection : IEnumerable, IEnumerator
{
    private string[] items = { "A", "B", "C" };
    private int position = -1;

    // IEnumerable
    public IEnumerator GetEnumerator()
    {
        Reset();  // 每次获取枚举器时重置
        return this;
    }

    // IEnumerator - 当前元素
    public object Current
    {
        get { return items[position]; }
    }

    // IEnumerator - 移动到下一个
    public bool MoveNext()
    {
        position++;
        return position < items.Length;
    }

    // IEnumerator - 重置
    public void Reset()
    {
        position = -1;
    }
}
```

---

## foreach 的本质

`foreach` 循环是语法糖，编译器会将其转换为对迭代器接口的调用。

### foreach 语法

```csharp
foreach (var item in collection)
{
    Console.WriteLine(item);
}
```

### 编译器展开后

```csharp
IEnumerator enumerator = collection.GetEnumerator();
try
{
    while (enumerator.MoveNext())
    {
        var item = enumerator.Current;
        Console.WriteLine(item);
    }
}
finally
{
    // 如果实现了 IDisposable，则调用 Dispose
    if (enumerator is IDisposable disposable)
    {
        disposable.Dispose();
    }
}
```

### 执行流程

1. 调用 `GetEnumerator()` 获取枚举器
2. 调用 `MoveNext()` 移动到下一个元素
3. 如果 `MoveNext()` 返回 `true`，获取 `Current` 赋值给循环变量
4. 重复步骤 2-3，直到 `MoveNext()` 返回 `false`

---

## yield return 语法糖

C# 2.0 引入了 `yield` 关键字，可以更简洁地实现迭代器。

### 基本用法

```csharp
public class MyCollection : IEnumerable<string>
{
    private string[] items = { "A", "B", "C" };

    public IEnumerator<string> GetEnumerator()
    {
        for (int i = 0; i < items.Length; i++)
        {
            yield return items[i];  // 暂停并返回当前值
        }
    }

    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
```

### yield 的工作原理

`yield return` 会让方法"暂停"，保留当前状态：

1. 第一次调用 `MoveNext()` 时，执行到第一个 `yield return`
2. 返回值赋给 `Current`，方法暂停
3. 下次调用 `MoveNext()` 时，从暂停处继续执行
4. 遇到下一个 `yield return` 或方法结束

```csharp
public IEnumerable<int> GetNumbers()
{
    Console.WriteLine("开始");
    yield return 1;
    Console.WriteLine("第一个之后");
    yield return 2;
    Console.WriteLine("第二个之后");
    yield return 3;
    Console.WriteLine("结束");
}

// 使用
foreach (var num in GetNumbers())
{
    Console.WriteLine($"得到: {num}");
}

// 输出：
// 开始
// 得到: 1
// 第一个之后
// 得到: 2
// 第二个之后
// 得到: 3
// 结束
```

### yield break

用于提前终止迭代：

```csharp
public IEnumerable<int> GetNumbersUntilZero(int[] numbers)
{
    foreach (var num in numbers)
    {
        if (num == 0)
            yield break;  // 终止迭代
        yield return num;
    }
}
```

---

## 延迟执行（Lazy Evaluation）

使用 `yield` 实现的迭代器具有**延迟执行**特性：元素只在需要时才计算。

```csharp
public IEnumerable<int> GetInfiniteNumbers()
{
    int i = 0;
    while (true)
    {
        yield return i++;  // 无限序列
    }
}

// 只取前 5 个
foreach (var num in GetInfiniteNumbers().Take(5))
{
    Console.WriteLine(num);  // 0, 1, 2, 3, 4
}
```

### 优点

- 节省内存：不需要一次性生成所有元素
- 支持无限序列
- 与 LINQ 完美配合

---

## 泛型版本

实际开发中推荐使用泛型版本：

| 接口 | 泛型版本 |
|------|----------|
| `IEnumerable` | `IEnumerable<T>` |
| `IEnumerator` | `IEnumerator<T>` |

```csharp
public class MyList<T> : IEnumerable<T>
{
    private T[] items;

    public IEnumerator<T> GetEnumerator()
    {
        foreach (var item in items)
        {
            yield return item;
        }
    }

    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
```
