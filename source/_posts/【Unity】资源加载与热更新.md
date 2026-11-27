---
title: 【Unity】资源加载与热更新
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/gen/Unity-资源加载与热更新.png
date: 2026-07-28
tags:
  - Unity
  - 资源管理
  - 热更新
  - HybridCLR
  - 异步加载
description: 梳理 Unity 的资源加载体系——从 Resources、AssetBundle 到 Addressables，同步与异步加载的原理与陷阱，引用计数管理，以及 Lua 与 HybridCLR 两种热更新方案的对比。
---

## 一、资源加载方案演进

Unity 的资源加载方案随版本不断演进：

- **`Resources.Load`**：简单但过时。打包时会把文件放在 Resources 目录下，导致包体首包过大、启动慢，且很难做热更。
- **AssetBundle（AB）**：Unity 标准的资源分包方案，支持压缩、热更、按需加载。但依赖管理很麻烦（容易从 AB 里加载出重复的贴图）。
- **Addressables**：Unity 基于 AB 封装的新系统，自动管理依赖和内存，支持异步加载，是现在的首选。

---

## 二、Resources 的同步与异步加载

`Resources` 用于通过代码动态加载 Resources 文件夹下指定路径的资源，避免繁琐的拖曳操作。

> 注意：预制体加载出来一定要**实例化**，否则只是加载到内存里并没有真正使用。

### 同步加载

```csharp
TextAsset ta = Resources.Load<TextAsset>("Tex/TextJPG");
```

### 异步加载

**异步加载的作用**：同步加载大体积资源会阻塞主线程并造成掉帧。异步加载将磁盘读取与解压放到后台线程处理，避免阻塞主线程。

> **注意**：异步加载无法在调用当帧立即获得资源，至少需要等待**一帧**。

**方式一：完成事件监听**

```csharp
ResourceRequest rq = Resources.LoadAsync<Texture>("Tex/TextJPG");
// 立即注册资源加载结束的事件监听
rq.completed += LoadOver;

private void LoadOver(AsyncOperation rq)
{
    print("加载结束");
    tex = (rq as ResourceRequest).asset as Texture;
}
```

**方式二：通过协程**

```csharp
IEnumerator Load()
{
    // 迭代器函数遇到 yield return 时会停止执行后面的代码，
    // 协程协调器通过返回值判断何时执行下一步
    ResourceRequest rq = Resources.LoadAsync<Texture>("Tex/TextJPG");
    // Unity 知道此时在异步加载资源
    yield return rq;
    // 加载完毕后才会执行后面的代码
    tex = rq.asset as Texture;
}
```

**两种方式对比**：

| 方式 | 好处 | 坏处 |
|------|------|------|
| 完成事件监听 | 写法简单 | 只能在加载结束后处理，属「线性加载」 |
| 协程异步加载 | 可处理复杂逻辑（同时加载多个资源、更新进度条），属「并行加载」 | 写法稍麻烦 |

---

## 三、异步加载的时序问题

UI 打开不能卡顿，所以必须用异步。但异步会导致**时序问题**：比如玩家快速点击打开又关闭，可能加载还没完成界面就已经关闭了，等加载回调回来时去操作一个已销毁的界面就会报错。

应对方式：

- **防连点**：在真正加载前检查 `IsLoading` 标记位，防止玩家快速点击导致弹出两个相同界面。
- **存活检查**：封装一个资源加载器，支持用 `CancellationToken`，或在回调里检查 `GameObject` 是否还存活，来防止这种异步 BUG。

---

## 四、引用计数管理

UI 贴图共享很严重。比如「通用弹窗底板」，A 界面用了，B 界面也用了。如果 A 关闭时直接 `Unload`，B 就会花屏。

**引用计数**：每当一个资源被一个界面引用，计数 +1；界面关闭，计数 -1；当计数为 0 时才卸载资源。这样可以确保只有当 A 和 B 都关闭了，底板才真正从内存卸载。

---

## 五、ScriptableObject

`ScriptableObject` 是一种轻量级的数据容器，用于共享配置数据或资源。相比 `MonoBehaviour`，它不会挂载到 GameObject 上，也不占用场景内存。常用于配置表、技能参数、关卡数据。

---

## 六、热更新

### 传统方案：Lua

C# 编译成 DLL 无法热更（安卓除外，iOS 不允许 JIT）。所以传统做法是把逻辑写在 **Lua 脚本**里——Lua 是文本文件，可以打成 AB 包下载。游戏运行时，嵌入的 Lua 虚拟机（C 语言写的）解释执行这些文本。C# 和 Lua 通过预生成的静态 Wrap 桥接文件交互。关于 Lua 核心语法、Mixin 框架模式与 xLua 底层桥接链路，详见 [【Unity】Lua编程与xLua热更新机制](/2026/10/20/%E3%80%90Unity%E3%80%91Lua%E7%BC%96%E7%A8%8B%E4%B8%8ExLua%E7%83%AD%E6%9B%B4%E6%96%B0%E6%9C%BA%E5%88%B6/)。

### 现代方案：HybridCLR

**HybridCLR**（原华佗）是 Unity 较新的全 C# 热更方案。

**原理**：它扩充了 Unity 的 IL2CPP 虚拟机，让它不仅能运行编译好的 AOT 代码，还能解释执行动态加载的 DLL 二进制流。这就实现了全 C# 热更，不需要写 Lua，开发效率更高。

### 补充：IL 与 IL2CPP

要理解 HybridCLR，先理解 IL 和 IL2CPP。

**IL（Intermediate Language，中间语言）**：C# 编译器将源代码编译生成的平台无关中间字节码，在运行时或打包时再由虚拟机/AOT 编译器转换为目标平台机器码。

**IL2CPP**：Unity 官方用来「加速和加密」的机制，它会：

- 把 C# 的 IL 代码转换成 C++ 代码；
- 再由 C++ 编译器转成真正的机器码（Native Code）。

这样做到了更快的性能（C++ 静态编译）和更安全的保护（反编译更难）。但一旦转成机器码，就**不能再动态修改和加载代码**了——所以不能热更。

**HybridCLR 的做法**：主包代码仍通过 IL2CPP 静态编译为原生机器码，同时在 `libil2cpp` 运行时内扩充了动态元数据注册与 IL 字节码解释器，支持在运行期动态加载热更 DLL 并解释执行。

比如把角色逻辑、数值计算这些容易改动的模块用 HybridCLR 保留 IL；把资源加载、基础工具库这些不需要热更的部分用 IL2CPP 编译成原生代码。这样就能做到：

- 有需要更新时，只需更新一个 DLL 或热更包，不需要重新打包整款游戏；
- 同时保留了性能好的部分。

演进关系总结：Mono 支持运行时加载但部分平台受限；IL2CPP 将 IL 静态编译为 C++ 原生代码以提升性能并满足 AOT 平台限制，但无法直接动态加载新程序集；HybridCLR 在 IL2CPP 运行时中补充了 IL 解释器，形成「AOT 原生代码 + 热更 IL 解释执行」的混合模式。
