---
title: 【Unity】GC原理与优化
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/4.avif
date: 2026-07-28
tags:
  - Unity
  - GC
  - 性能优化
  - 内存管理
  - CSharp
description: 剖析 Unity 中的 GC 机制——三种 GC、触发时机、回收算法（引用计数与根搜索、Boehm 与 SGen 分代 GC），并系统总结从字符串、集合、Lambda、装箱到对象池的 GC 优化实战。
---

## 一、Unity 中的三种 GC

作为游戏程序员，我们要了解的 GC 有三种：

- **Unity 的 GC**（即 Mono Runtime GC）
- **C# 的 GC**（CLR GC）
- **Lua GC**

对于目前绝大多数基于 Unity 引擎开发的项目，其托管堆内存是由 Mono 分配和管理的。「托管」的本意是 Mono 可以自动改变堆的大小来适应所需内存，并适时调用 GC 释放不再需要的内存。

但 GC **并不是实时管理**的，需要通过程序员手动或系统定时触发。因为 GC 是一个耗时操作，可能在不合时宜的时候触发（造成明显卡顿）。所以优化 GC 就是优化堆内存——尽量减少堆内存分配，及时回收堆内存。例如：游戏中我们希望在切换 Loading 时触发 GC，而在战斗中控制它不被触发。

---

## 二、GC 的触发时机

**被动触发**：GC 会不时地自动运行（频率因平台而异）。

**主动触发**（程序员调用）：

- **Mono GC**：`Resources.UnloadUnusedAssets()`
- **C# GC**：`GC.Collect()`
- **Lua GC**：`collectgarbage("collect")` 做一次完整的垃圾收集循环

需要说明：`Resources.UnloadUnusedAssets()` 内部本身就会调用 `GC.Collect()`。

Unity 还提供了一个更暴力的 `Resources.UnloadAssets()`，但它无论资源是不是「垃圾」都会直接删除，是一个很危险的接口，建议确定资源不再使用时才调用。

---

## 三、GC 如何释放堆内存

如何判断一个对象是否需要被回收，就是 GC 的策略算法。一般有以下几种：

**1. 引用计数**

每个对象上维护一个字段，统计有多少对象正在使用自己。当引用计数为 0 时，对象就可以从内存中删除。

**2. 根搜索**

从一个根（引用地址）开始遍历所有的叶子，然后把所有不需要的叶子清除。

**影响 GC 性能的主要因素**：可达对象数量、托管堆大小。

---

## 四、GC 的回收算法

**Boehm GC**：Mono 在 2.10 版本前使用贝姆垃圾回收（Boehm conservative collector）。而 Unity 中 Mono 的版本长期停留在 2.10 之前，所以一直集成的是 Boehm GC。

**SGen 分代 GC**：2.10 之后使用了 Simple Generational GC（SGen-GC），即分代垃圾回收。

分代 GC 采用**标记-压缩算法**：通过一个图的数据结构收集对象的根（指向托管堆的关系线）。为了优化内存结构、减少搜索成本，GC 为每个托管堆对象分为三个等级——**0 代、1 代、2 代**：

- 每当 `new` 一个对象，该对象被定义为第 0 代；
- GC 回收时先从第 0 代开始；
- 一次回收之后，0 代中没被回收的对象升为第 1 代；
- 回收第 1 代时，没被清理的对象升为第 2 代。

CLR 会为各代选择一个预算容量：

- 0 代通常为 256KB - 4MB
- 1 代为 512KB - 4MB
- 2 代不受限制，最大可扩充至操作系统的整个内存空间

代数越高，说明对象经历回收的次数越多，也就意味着它最不容易被清除。这种分代思想将对象分割成新老对象，配对不同的清除条件，巧妙地避免了每次都直接清理整个堆（避免卡顿）。

---

## 五、GC 优化实战

频繁的堆内存分配会导致 GC 频繁触发、卡顿。下面按产生 GC 的场景分类总结优化手段。

### 1. 字符串操作

**问题**：频繁使用 `+` 或 `String.Format` 会生成中间字符串，增加 GC。

**优化**：用 `StringBuilder` 重用，避免每次创建新实例，尤其在循环中：

```csharp
private readonly StringBuilder _builder = new StringBuilder(); // 预创建

public string Concatenate(string a, string b)
{
    _builder.Clear();
    _builder.Append(a).Append(b);
    return _builder.ToString();
}
```

### 2. 集合与循环

**临时集合对象创建**：在每帧执行的 `Update()` 中 `new List<>()` 或 `new Dictionary<>()` 会持续产生 GC。优化是预分配集合并重用，通过 `Clear()` 重置而非重新实例化：

```csharp
private readonly List<int> _list = new List<int>(100); // 预分配

private void Update()
{
    _list.Clear(); // 重用对象
    for (int i = 0; i < 100; i++) _list.Add(i);
}
```

**foreach 的 GC**：遍历 `Dictionary` 时 `GetEnumerator()` 可能产生 32B 的 GC。优化是优先用 `for` 循环，并缓存 `Count` 减少属性访问开销：

```csharp
int count = list.Count; // 缓存 Count，避免每次访问触发边界检查
for (int i = 0; i < count; i++)
{
    var item = list[i];
}
```

### 3. 委托与 Lambda

**问题**：Lambda 引用局部变量会产生**闭包分配**（Closure Allocation），引用成员变量会产生**委托分配**（Delegate Allocation）。

**优化**：引用静态变量避免 GC 分配；高频逻辑（如每帧事件）改用显式方法调用而非 Lambda。

```csharp
// 避免：捕获局部变量产生 GC
int count = 0;
InvokeAction(() => { count++; });

// 建议：使用静态方法
InvokeAction(() => { StaticMethod(); });
```

### 4. 装箱

**问题**：值类型赋值给 `object`（如 `object obj = 10;`）会触发装箱，产生 GC。

> 装箱产生垃圾的原理：当一个值类型变量被装箱时，Unity 在堆上创建一个临时的 `System.Object` 来包装它。`System.Object` 是引用类型，所以这个临时对象被处理时会产生垃圾。

**优化**：用泛型约束避免装箱，确保泛型类型实现 `IEquatable<T>`，避免调用 `object.Equals`：

```csharp
public struct GenericStruct<T> where T : IEquatable<T>
{
    public bool Equals(T other) { ... } // 避免装箱
}
```

### 5. 资源释放与对象池

**非托管资源**：文件句柄、数据库连接等未释放会增加内存占用，间接提升 GC 频率。用 `IDisposable` + `using` 确保及时释放：

```csharp
using (var file = File.Open("file.txt"))
{
    // 操作文件
} // 自动调用 Dispose()
```

**高频对象创建/销毁**：如子弹、特效等频繁实例化，用**对象池**复用对象而非重复创建：

```csharp
public class ObjectPool<T> where T : new()
{
    private Stack<T> _pool = new Stack<T>();
    public T Get() => _pool.Count > 0 ? _pool.Pop() : new T();
    public void Return(T item) => _pool.Push(item);
}
```

> 注意：对象池并不能解决实例化卡顿，只是把卡顿提前了。

---

## 六、优化清单

一份实战速查清单：

1. **缓存**：能缓存的数据尽量缓存，把局部引用变量提升为公共成员。
2. **条件分配**：只在满足特定条件时才 GC Alloc。
3. **定时器**：用定时器减少 GC 分配频率。
4. **集合**：`List` 用 `Clear()` 代替 `new`。
5. **对象池**：复用子弹、特效等高频对象。
6. **字符串**：能不拼接就不拼接，必须拼接时用 `StringBuilder`。
7. **Unity API**：`gameObject.tag ==` 改用 `CompareTag`。
8. **装箱**：注意 `String.Format` 等隐式装箱。
9. **协程**：`yield return 0`（装箱）改为 `yield return null`。
10. **LINQ 和正则**：后台有装箱操作，最好少用。
11. **减少 GC 管理对象**：比如存树的下一个节点，可以用 id 代表对应节点，减少 GC 需要管理的对象数量。
12. **手动强制 GC**：在合适时机（如 Loading）手动触发 GC 并扩展堆大小，让 GC 可控。
