---
title: CSharp 的 ref 和 out
toc: true
categories:
  - 技术分享
  - C#
tags:
  - 基础
  - 参数传递
description: 理解 C# 中 ref 和 out 关键字的区别：两者都是引用传递，但在初始化要求和语义上有所不同。
---

## ref 和 out 的区别

这两个都是引用，实现上都是指针，区别在于语义。

### ref 关键字

`ref` 是引用，你在函数内可能会获取值，也可能会赋值。C# 要求变量在使用前必须初始化，因此 `ref` 修饰的变量在传参前就必须先初始化。

```csharp
void AddTen(ref int number)
{
    number += 10; // 可以读取，也可以修改
}

// 调用时
int value = 5;       // 必须先初始化
AddTen(ref value);   // value 变为 15
```

### out 关键字

`out` 是输出（变相的多返回值），为了解决早年 C# 没有元组的多返回值问题。它在语义上表示离开函数时一定会被赋值，因此在传参之前变量不必初始化，但在函数内一定要赋值，以保证语义正确。

```csharp
void GetValues(out int x, out int y)
{
    x = 10;  // 函数内必须赋值
    y = 20;  // 函数内必须赋值
}

// 调用时
int a, b;              // 不需要初始化
GetValues(out a, out b); // a = 10, b = 20
```

## 对比总结

| 特性 | ref | out |
|------|-----|-----|
| 传参前是否需要初始化 | 是 | 否 |
| 函数内是否必须赋值 | 否 | 是 |
| 典型用途 | 修改已有变量 | 返回多个值 |