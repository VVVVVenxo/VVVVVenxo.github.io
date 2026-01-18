---
title: 【Unity】UI与渲染优化
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - UGUI
  - Canvas
  - DrawCall
  - 合批
  - LOD
description: 详解 Unity UI 渲染与优化：Canvas 渲染模式、Canvas Scaler、DrawCall、合批规则、LOD。
---

## Canvas 渲染模式

### Screen Space - Overlay

UI 元素直接渲染到屏幕上，**不依赖任何相机**，始终覆盖在所有 3D 场景内容之上。

**特点**：
- 渲染层级最高，不会被场景中的任何物体遮挡
- Canvas 会自动适配屏幕分辨率
- 无法实现 UI 与 3D 物体的穿插效果

**适用场景**：常规 HUD 界面、弹窗、菜单等需要始终显示在最前方的 UI。

---

### Screen Space - Camera

UI 元素由**指定的相机**进行渲染，Canvas 会被放置在相机前方的一个平面上。

**特点**：
- 可以控制 UI 与其他渲染层的前后关系
- 当相机设置为 **Perspective（透视模式）** 时，调整 UI 元素的 Rotation 可以呈现 3D 立体效果
- Canvas 的 RectTransform **不可直接编辑**，需通过相机或 `Plane Distance` 参数调整

**适用场景**：需要 UI 与粒子特效、3D 模型产生层级穿插的界面，或需要透视效果的 UI 动画。

---

### World Space

Canvas 作为**普通的 3D 物体**存在于世界空间中，其 RectTransform 完全可编辑。

**特点**：
- 会受到场景中其他物体的遮挡
- 可挂载到任意 GameObject 上，跟随物体移动
- 需要手动指定 `Event Camera` 以响应 UI 交互事件

**适用场景**：角色头顶的血条/名称、场景内的交互提示牌、VR/AR 中的空间 UI 等。

---

## Canvas Scaler 画布缩放器

Canvas Scaler 组件提供了三种缩放模式来适配不同分辨率：

| 模式 | 依据 | 特点 | 适用场景 |
|------|------|------|----------|
| Constant Pixel Size | 像素 | UI 像素大小固定 | 像素风格游戏 |
| Scale With Screen Size | 参考分辨率 | UI 按比例缩放 | 大多数游戏 |
| Constant Physical Size | 物理尺寸（DPI） | UI 物理大小固定 | 触摸屏应用 |

### Scale With Screen Size 详解

- 设置参考分辨率（Reference Resolution），UI 会按比例缩放
- 可通过 `Match` 参数控制宽高匹配优先级（0 = 宽度优先，1 = 高度优先）
- **推荐**：大多数游戏的首选模式

---

## DrawCall 概念

**DrawCall** 是 CPU 准备好渲染数据后，**告知 GPU 开始渲染的命令**。

### 为什么 DrawCall 影响性能？

- 每次 DrawCall 都有额外的 CPU 开销
- DrawCall 过多会导致 CPU 成为瓶颈
- 游戏会出现卡顿

**注意**：DrawCall 并不是越少越好。过度合批会导致传输数据量大增，造成带宽瓶颈。

---

## UGUI 合批规则

### 合批单位

- 合批以 **Canvas**（不包含子 Canvas）为单位
- 子 Canvas 会是另外一个批次
- 合批操作在**子线程**完成

### 合批流程

1. **找出所有 Canvas**，剔除不渲染的（透明度为 0、长宽为 0、在 RectMask2D 区域外）

2. **计算各 UI 控件的 Depth**

3. **Depth 计算规则**：
   - 按 Hierarchy 从上往下遍历
   - 不渲染：`Depth = -1`
   - 下面无相交元素：`Depth = 0`
   - 下面有相交元素且**可合批**：`Depth = 下层 Depth`
   - 下面有相交元素且**不可合批**：`Depth = 下层 Depth + 1`

4. **排序生成 VisiableList**：
   - 按 Depth 排序（从小到大）
   - Depth 相同按 Material ID 排序
   - Material ID 相同按 Texture ID 排序
   - 剔除 `Depth = -1` 的元素

5. **合批**：VisiableList 中相邻元素如果材质和贴图相同，即可合批

### 合批条件

| 条件 | 说明 |
|------|------|
| 材质球相同 | 使用相同的 Shader |
| 贴图相同 | 使用相同的纹理 |

**注意**：Text 和 Image 默认都用 `UI/Default` 材质，但贴图不同，所以无法合批。

---

## 静态合批（Static Batching）

勾选 `Static` 后，Unity 在 **Build 时**自动生成合并的网格。

### 特点

- 一次性提交顶点数据
- 根据场景管理系统判断子模型可见性
- 设置一次渲染状态，多次 DrawCall 分别绘制子模型

### 适用场景

- 静态场景物体（建筑、地形装饰等）
- 不会移动、旋转、缩放的物体

---

## 动态合批（Dynamic Batching）

在场景绘制前，将所有**共享同一材质**的模型的顶点信息**变换到世界空间**，然后通过一次 DrawCall 绘制。

### 特点

- 顶点变换由 CPU 完成，有性能消耗
- 适合小型网格模型
- 有顶点数量限制（通常 < 300 顶点）

---

## 静态合批 vs 动态合批

| 特性 | 静态合批 | 动态合批 |
|------|----------|----------|
| 合批时机 | Build 时 | 运行时 |
| 适用物体 | 静态物体 | 动态小物体 |
| CPU 开销 | 低 | 有（顶点变换） |
| 内存开销 | 高（存储合并网格） | 低 |
| 顶点限制 | 无 | 有（约 300 顶点） |

---

## LOD（Level of Detail）

LOD（多层次细节）根据摄像机与模型的距离决定显示哪个精度的模型。

### 原理

| 距离 | 模型精度 |
|------|----------|
| 近距离 | 高精度模型（High Poly） |
| 中距离 | 中精度模型（Medium Poly） |
| 远距离 | 低精度模型（Low Poly） |

### 特点

| 优点 | 缺点 |
|------|------|
| 降低 GPU 渲染压力 | 同一模型需要准备多个精度版本 |
| 提升远景渲染效率 | 增加内存占用 |

**本质**：以**内存换 GPU 性能**

---

## 降低 DrawCall 的方法

### UI 优化

| 方法 | 说明 |
|------|------|
| 图集打包 | 小图合成大图，多个小 DrawCall 合成一个 |
| 合理规划层级 | 避免不必要的 UI 遮挡造成 Depth 增加 |
| 减少 Mask 使用 | Mask 会打断合批 |

### 3D 优化

| 方法 | 说明 |
|------|------|
| 静态合批 | 勾选 Static |
| 动态合批 | 使用相同材质的小物体 |
| GPU Instancing | 相同网格的大量实例 |
| LOD | 远处使用低模 |
| 遮挡剔除 | 不渲染被遮挡的物体 |

### 图集规范

- 重复使用的 UI 打包为一个图集
- 图标根据数量分为多个图集
- 图集大小根据规范（通常 512 或 1024）

**注意**：过大的图集会增加带宽压力，需要权衡。
