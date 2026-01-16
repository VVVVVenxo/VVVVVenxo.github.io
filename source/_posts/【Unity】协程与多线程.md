---
title: 【Unity】协程与多线程
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - 协程
  - 多线程
  - JobSystem
description: 理解 Unity 协程的原理与用法，协程与线程的区别，以及 JobSystem 多线程方案。
---

## 什么是协程？

Unity 中的协程（Coroutine）是一种基于**迭代器（Iterator）** 的轻量级协作式多任务机制，允许在主线程中**分阶段执行逻辑**。

### 协程的本质

协程可以分成两部分：

1. **协程函数本体**：通过 `yield return` 决定分步执行
2. **协程调度器**：Unity 内部的调度器，根据 `yield return` 的返回值决定何时继续执行

```csharp
IEnumerator Test()
{
    print("第一次");
    yield return 1;
    print("第二次");
    yield return 2;
    print("第三次");
    yield return 3;
}

// 手动模拟协程执行
IEnumerator ie = Test();
while (ie.MoveNext())  // 执行到 yield return 为止
{
    print(ie.Current);  // 获取 yield return 返回的值
}
```

---

## 协程的使用

### 基本用法

```csharp
void Start()
{
    // 开启协程
    Coroutine c1 = StartCoroutine(TestCoroutine(1, "123"));
    
    // 或者
    IEnumerator ie = TestCoroutine(1, "123");
    StartCoroutine(ie);
    
    // 关闭协程
    StopCoroutine(c1);
    StopAllCoroutines();
}

IEnumerator TestCoroutine(int i, string str)
{
    print(i);
    yield return new WaitForSeconds(5f);
    print(str);  // 等待 5 秒后执行
    
    while (true)
    {
        print("每隔 5 秒打印");
        yield return new WaitForSeconds(5f);
    }
}
```

### yield return 类型

| 用法 | 效果 | 执行时机 |
|------|------|----------|
| `yield return null` | 等待下一帧 | Update 和 LateUpdate 之间 |
| `yield return new WaitForSeconds(n)` | 等待 n 秒 | Update 和 LateUpdate 之间 |
| `yield return new WaitForFixedUpdate()` | 等待下一个物理帧 | FixedUpdate 之后 |
| `yield return new WaitForEndOfFrame()` | 等待渲染完成 | LateUpdate 之后 |
| `yield break` | 立即结束协程 | - |

```csharp
IEnumerator Example()
{
    yield return null;                        // 下一帧
    yield return new WaitForSeconds(5f);      // 等待 5 秒
    yield return new WaitForFixedUpdate();    // 下一个物理帧
    yield return new WaitForEndOfFrame();     // 渲染完成后（适合截图）
    yield break;                              // 结束协程
}
```

---

## 协程的应用场景

- 异步加载资源
- 下载文件
- 场景异步加载
- 批量创建防止卡顿
- 延时执行逻辑

---

## 协程注意事项

### 生命周期

| 情况 | 协程是否继续执行 |
|------|------------------|
| 组件单独失活（Enabled = false） | ✅ 继续执行 |
| GameObject 失活 | ❌ 停止 |
| GameObject 销毁 | ❌ 停止 |

### 记得关闭协程！

协程开启后如果不手动关闭，可能导致意外行为：

```csharp
void OnDestroy()
{
    StopAllCoroutines();  // 销毁时停止所有协程
}
```

---

## 协程 vs 线程

| 特性 | 协程 | 线程 |
|------|------|------|
| 并发类型 | 协作式（伪并发） | 抢占式（真并发） |
| 执行位置 | 主线程 | 独立线程 |
| 访问 Unity API | ✅ 可以 | ❌ 不可以 |
| 线程安全问题 | 无 | 有 |
| 适用场景 | 延时、分帧 | CPU 密集计算 |

---

## Unity 中的多线程

Unity 支持多线程，但**子线程无法访问 Unity API**（如 Transform、GameObject 等）。

### 多线程使用方式

```csharp
using System.Threading;

void Start()
{
    Thread thread = new Thread(BackgroundWork);
    thread.Start();
}

void BackgroundWork()
{
    // 只能做纯计算，不能访问 Unity 对象
    int result = HeavyCalculation();
    
    // 结果存入公共容器，主线程读取
    resultQueue.Enqueue(result);
}

void Update()
{
    // 主线程从容器读取结果
    while (resultQueue.Count > 0)
    {
        var result = resultQueue.Dequeue();
        // 使用 result 更新 Unity 对象
    }
}
```

### 典型应用

- 网络通信
- 寻路计算
- 大量数据处理

---

## JobSystem

JobSystem 是 Unity 提供的**高性能多线程方案**，通过**作业（Job）** 而不是线程来管理多线程代码。

### 特点

- 跨多个核心管理工作线程
- 通常每个逻辑 CPU 核心对应一个工作线程
- 避免上下文切换开销
- 作业系统管理依赖关系，确保正确的执行顺序

### 工作原理

```
┌─────────────┐
│  Job Queue  │  ← 作业队列
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│         Work Threads             │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐    │
│  │ T1 │ │ T2 │ │ T3 │ │ T4 │    │  ← 工作线程（每核心一个）
│  └────┘ └────┘ └────┘ └────┘    │
└──────────────────────────────────┘
```

### 优势

- 充分利用多核 CPU
- 无需手动管理线程
- 与 Burst 编译器配合可获得极高性能

---

## 总结

| 场景 | 推荐方案 |
|------|----------|
| 延时执行、分帧加载 | 协程 |
| 网络通信、简单后台计算 | 多线程 |
| 高性能并行计算 | JobSystem + Burst |
