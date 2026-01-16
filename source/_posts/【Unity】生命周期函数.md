---
title: 【Unity】生命周期函数
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - 生命周期
  - MonoBehaviour
  - Update
description: 详解 Unity MonoBehaviour 的生命周期函数执行顺序，包括 Awake、Start、Update、FixedUpdate、LateUpdate 等。
---

## 生命周期概述

Unity 中挂载 MonoBehaviour 脚本的 GameObject 会按照特定顺序调用生命周期函数。

---

## 场景加载阶段（First Scene Load）

场景开始时，每个物体只调用一次。

### Awake

- 在预设被**实例化之后**立即调用
- **不受脚本是否启用影响**（只要 GameObject 是激活的）
- 总是在任何 `Start()` 之前调用
- 适合做初始化、获取组件引用

```csharp
void Awake()
{
    // 获取组件引用
    rb = GetComponent<Rigidbody>();
}
```

### OnEnable

- 在对象**激活（Active）** 且**脚本启用（Enabled）** 时调用
- 每次对象从禁用变为启用时都会调用
- 适合注册事件监听

---

## 第一帧更新之前（Before First Frame Update）

### Start

- 在脚本**启用后**，第一次 `Update()` 之前调用
- 只调用一次
- 适合做依赖其他组件已初始化的逻辑

```csharp
void Start()
{
    // 此时其他物体的 Awake 已执行完毕
    target = FindObjectOfType<Player>();
}
```

---

## Awake vs Start

| 特性 | Awake | Start |
|------|-------|-------|
| 调用时机 | 实例化时 | 第一帧 Update 前 |
| 受脚本启用影响 | ❌ 否 | ✅ 是 |
| 调用顺序 | 先 | 后 |
| 典型用途 | 自身初始化 | 依赖外部的初始化 |

---

## 更新阶段（Update Order）

### FixedUpdate

- 按**固定时间间隔**调用（默认 0.02 秒，即 50 FPS）
- **独立于帧率**
- 一帧内可能调用多次（帧率低时）或不调用（帧率极高时）
- 适合**物理计算**

```csharp
void FixedUpdate()
{
    // 物理移动，无需乘以 deltaTime
    rb.AddForce(Vector3.forward * force);
}
```

### Update

- **每帧调用一次**
- 调用频率随帧率变化
- 适合常规游戏逻辑、输入检测

```csharp
void Update()
{
    // 移动需要乘以 deltaTime
    transform.Translate(Vector3.forward * speed * Time.deltaTime);
}
```

### LateUpdate

- 在**所有 Update 执行完毕后**调用
- 每帧调用一次
- 适合**相机跟随**、需要等待其他物体更新完毕的逻辑

```csharp
void LateUpdate()
{
    // 相机跟随，确保角色已移动完毕
    transform.position = player.position + offset;
}
```

---

## Update vs FixedUpdate

| 特性 | Update | FixedUpdate |
|------|--------|-------------|
| 调用频率 | 每帧一次 | 固定时间间隔 |
| 受帧率影响 | ✅ 是 | ❌ 否 |
| 移动计算 | 需乘 `Time.deltaTime` | 不需要 |
| 典型用途 | 输入、动画、游戏逻辑 | 物理计算、刚体操作 |

---

## 其他重要生命周期函数

### OnDisable

- 对象被禁用或脚本被禁用时调用
- 适合取消事件监听

### OnDestroy

- 对象被销毁时调用
- 适合清理资源、反注册事件

### OnApplicationPause

- 应用暂停时调用（如切换到后台）

### OnApplicationQuit

- 应用退出时调用

---

## 生命周期流程图

```
初始化阶段
    │
    ├─► Awake()
    │
    ├─► OnEnable()
    │
    └─► Start()
           │
           ▼
    ┌──────────────────────────────────────┐
    │            游戏循环                   │
    │                                      │
    │  FixedUpdate() ◄─┐                   │
    │       │          │ (可能多次)         │
    │       ▼          │                   │
    │  Physics ────────┘                   │
    │       │                              │
    │       ▼                              │
    │  Update()                            │
    │       │                              │
    │       ▼                              │
    │  LateUpdate()                        │
    │       │                              │
    │       ▼                              │
    │  Rendering                           │
    │       │                              │
    └───────┼──────────────────────────────┘
            │
            ▼ (循环)
           
销毁阶段
    │
    ├─► OnDisable()
    │
    └─► OnDestroy()
```

---

## 常见问题

### 为什么 Awake 比 Start 更适合初始化？

`Awake` 在所有脚本的 `Start` 之前执行，因此在 `Awake` 中初始化的组件可以确保在其他脚本的 `Start` 中被访问。

### 为什么物理操作要放在 FixedUpdate？

物理引擎按固定时间步长计算，与 `FixedUpdate` 同步。在 `Update` 中操作物理会导致不稳定的结果。
