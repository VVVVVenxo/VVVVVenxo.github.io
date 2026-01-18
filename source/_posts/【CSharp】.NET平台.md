---
title: 【CSharp】.NET 平台
toc: true
categories:
  - 技术笔记
  - C#
cover: /img/covers/earth.jpg
date: 2025-06-05
tags:
  - .NET
  - CLR
  - 跨平台
description: 理解微软 .NET 平台的架构：CLI、CIL、CLR 的概念，以及如何实现跨语言和跨平台。
---

## .NET 平台概述

.NET 是微软推出的开发平台，支持多种编程语言（C#、F#、VB.NET 等）开发各类应用程序。

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                    开发语言层                            │
│         C#      F#      VB.NET      C++/CLI            │
└─────────────────────────────────────────────────────────┘
                           ↓ 编译
┌─────────────────────────────────────────────────────────┐
│                    CIL (中间语言)                        │
│               Common Intermediate Language              │
└─────────────────────────────────────────────────────────┘
                           ↓ JIT 编译
┌─────────────────────────────────────────────────────────┐
│                    CLR (运行时)                          │
│               Common Language Runtime                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    机器码                                │
│              Windows / Linux / macOS                    │
└─────────────────────────────────────────────────────────┘
```

---

## 核心概念

### CLI（公共语言基础结构）

**Common Language Infrastructure**

CLI 是一套**规范**，定义了：
- 可执行代码的格式
- 运行时环境的要求
- 类型系统
- 元数据格式

所有 .NET 语言都遵循这套规范，因此可以互操作。

### CIL（公共中间语言）

**Common Intermediate Language**

也称为 MSIL（Microsoft Intermediate Language）或 IL。

- 所有 .NET 语言编译后都生成 CIL
- CIL 是**平台无关**的中间代码
- 类似于 Java 的字节码

```
C#   ──编译──┐
             │
F#   ──编译──┼──► CIL (.dll / .exe) ──► CLR ──► 机器码
             │
VB   ──编译──┘
```

### CLR（公共语言运行时）

**Common Language Runtime**

CLR 是 .NET 程序的**运行时环境**，负责：

| 功能 | 说明 |
|------|------|
| **JIT 编译** | 将 CIL 即时编译为机器码 |
| **内存管理** | 自动垃圾回收（GC） |
| **类型安全** | 运行时类型检查 |
| **异常处理** | 统一的异常处理机制 |
| **安全管理** | 代码访问安全 |

---

## 跨语言实现

### 为什么能跨语言？

1. 所有 .NET 语言都遵循 **CLI 规范**
2. 所有语言编译后都生成相同的 **CIL**
3. 共享相同的 **CLR** 运行时
4. 共享相同的 **BCL**（基础类库）

### 跨语言互操作示例

```csharp
// C# 定义的类
public class CSharpClass
{
    public string Greet() => "Hello from C#";
}
```

```vb
' VB.NET 调用 C# 类
Dim obj As New CSharpClass()
Console.WriteLine(obj.Greet())  ' 可以直接调用
```

### CTS（公共类型系统）

**Common Type System**

CTS 定义了所有 .NET 语言共用的类型规范：

| C# 类型 | VB.NET 类型 | CTS 类型 |
|---------|-------------|----------|
| `int` | `Integer` | `System.Int32` |
| `string` | `String` | `System.String` |
| `bool` | `Boolean` | `System.Boolean` |

---

## 跨平台实现

### .NET 的演进

| 版本 | 平台支持 |
|------|----------|
| .NET Framework | 仅 Windows |
| .NET Core | Windows / Linux / macOS |
| .NET 5+ | 统一平台，全面跨平台 |

### 跨平台原理

1. **CIL 平台无关**：编译后的 IL 代码不包含平台特定指令
2. **平台特定 CLR**：每个操作系统有对应的 CLR 实现
3. **JIT 编译**：运行时将 CIL 编译为当前平台的机器码

```
CIL 代码
    │
    ├─► Windows CLR ──► x86/x64 机器码
    │
    ├─► Linux CLR ──► x86/x64 机器码
    │
    └─► macOS CLR ──► ARM64/x64 机器码
```

---

## 编译过程详解

### 两阶段编译

```
┌──────────────────────────────────────────────────────────┐
│ 第一阶段：开发时编译                                       │
│                                                          │
│  源代码 (.cs) ──► C# 编译器 ──► 程序集 (.dll/.exe)         │
│                              包含：CIL + 元数据           │
└──────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────┐
│ 第二阶段：运行时编译（JIT）                                 │
│                                                          │
│  CIL ──► JIT 编译器 ──► 本机机器码 ──► CPU 执行            │
│                                                          │
│  * JIT = Just-In-Time（即时编译）                         │
│  * 只编译实际执行的代码                                    │
│  * 编译结果可缓存复用                                      │
└──────────────────────────────────────────────────────────┘
```

### AOT 编译

**Ahead-Of-Time（预先编译）**

.NET 也支持 AOT 编译，在发布时直接生成机器码：
- 启动速度更快
- 无需 JIT 开销
- 适用于移动端、WebAssembly

---

## 总结

| 概念 | 全称 | 作用 |
|------|------|------|
| CLI | Common Language Infrastructure | 跨语言互操作的规范 |
| CIL | Common Intermediate Language | 平台无关的中间代码 |
| CLR | Common Language Runtime | 执行 CIL 的运行时环境 |
| CTS | Common Type System | 统一的类型系统 |
| JIT | Just-In-Time | 运行时编译为机器码 |
| AOT | Ahead-Of-Time | 预先编译为机器码 |
