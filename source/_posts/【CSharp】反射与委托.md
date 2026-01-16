---
title: 【CSharp】反射与委托
toc: true
categories:
  - 技术笔记
  - C#
cover: /img/covers/earth.jpg
date: 2025-06-05
tags:
  - 反射
  - 委托
  - 事件
description: 理解 C# 中的反射机制、委托与事件的区别，以及如何正确使用 Action/Func 避免内存泄漏。
---

## 反射（Reflection）

反射是一种在**运行时**获取类型信息、动态创建对象、调用方法等操作的机制。

### 反射的优缺点

| 优点 | 缺点 |
|------|------|
| 动态调用方法和属性，代码更灵活 | 可以随意访问私有属性和方法，存在安全漏洞 |
| 与运行时代码不产生耦合 | 性能开销大，存在类型转换成本 |
| 易于开发插件和测试工具 | 代码难以读懂和维护 |

### 常见使用场景

- 编辑器扩展工具
- 热更新框架
- 序列化/反序列化
- 依赖注入框架

### 基本用法

```csharp
using System;
using System.Reflection;

public class MyClass
{
    private int value = 42;
    public void SayHello(string name) => Console.WriteLine($"Hello, {name}!");
}

// 获取类型信息
Type type = typeof(MyClass);

// 动态创建实例
object obj = Activator.CreateInstance(type);

// 动态调用方法
MethodInfo method = type.GetMethod("SayHello");
method.Invoke(obj, new object[] { "World" });  // 输出: Hello, World!

// 访问私有字段
FieldInfo field = type.GetField("value", BindingFlags.NonPublic | BindingFlags.Instance);
Console.WriteLine(field.GetValue(obj));  // 输出: 42
```

---

## 委托（Delegate）

委托是 C# 中的类型安全的函数指针，可以引用一个或多个方法。

### 委托的基本使用

```csharp
// 定义委托类型
public delegate void MyDelegate(int value);

// 使用委托
MyDelegate del = SomeMethod;
del(42);  // 调用
```

### Action 和 Func

系统预定义的泛型委托，使用更方便：

| 类型 | 特点 | 示例 |
|------|------|------|
| `Action` | 无返回值 | `Action<int, string>` |
| `Func` | 有返回值（最后一个泛型参数） | `Func<int, int, bool>` |

```csharp
// Action：无返回值
Action<string> onMessage = (msg) => Debug.Log(msg);
onMessage("Hello");

// Func：有返回值
Func<int, int, int> add = (a, b) => a + b;
int result = add(1, 2);  // result = 3
```

---

## 事件（Event）

事件是对委托的**封装**，提供了更安全的发布-订阅模式。

### 委托 vs 事件

| 特性 | Delegate | Event |
|------|----------|-------|
| 外部赋值 `=` | ✅ 允许 | ❌ 禁止 |
| 外部调用 `Invoke` | ✅ 允许 | ❌ 禁止 |
| `+=` / `-=` | ✅ 允许 | ✅ 允许 |

**事件的核心优势**：防止外部代码清空其他人的监听，更安全。

```csharp
public class Player
{
    // 委托：外部可以直接赋值，危险！
    public Action OnDeath;
    
    // 事件：外部只能 += 或 -=，安全
    public event Action OnDamage;
    
    public void TakeDamage()
    {
        OnDamage?.Invoke();
    }
}

// 外部使用
player.OnDeath = null;      // 委托：可以清空所有监听（危险）
player.OnDamage = null;     // 事件：编译错误！
player.OnDamage += MyHandler; // 事件：只能这样订阅
```

---

## 内存泄漏防范

### 问题场景

如果 View 销毁了，但 Model 里的 Action 还持有 View 的方法引用，View 就无法被 GC 回收。

```csharp
public class Model
{
    public Action<int> OnValueChanged;
}

public class View : MonoBehaviour
{
    private Model model;
    
    void Start()
    {
        model.OnValueChanged += UpdateUI;  // 订阅
    }
    
    void UpdateUI(int value) { /* ... */ }
    
    // 如果不反注册，View 销毁后仍被 Model 引用，无法 GC
}
```

### 解决方案

在 `OnDestroy` 中反注册所有事件：

```csharp
public class BasePanel : MonoBehaviour
{
    protected Model model;
    
    protected virtual void OnDestroy()
    {
        // 反注册所有事件，确保引用断开
        if (model != null)
        {
            model.OnValueChanged -= UpdateUI;
        }
    }
    
    protected virtual void UpdateUI(int value) { }
}
```

---

## 最佳实践

| 场景 | 建议 |
|------|------|
| 类内部回调 | 使用 `Action` / `Func` |
| 对外暴露的通知 | 使用 `event` |
| UI 界面 | 在 `OnDestroy` 中反注册所有事件 |
| 单例 Model | 切换场景时清理所有订阅者 |
