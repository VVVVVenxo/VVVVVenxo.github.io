---
title: 【Unity】Canvas 渲染模式
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - UGUI
  - Canvas
  - 渲染
description: 详解 Unity Canvas 的三种渲染模式：Screen Space-Overlay、Screen Space-Camera 和 World Space，以及它们的适用场景。
---

## Canvas 渲染模式

### 1. Screen Space - Overlay

UI 元素直接渲染到屏幕上，**不依赖任何相机**，始终覆盖在所有 3D 场景内容之上。

**特点**：
- 渲染层级最高，不会被场景中的任何物体遮挡
- Canvas 会自动适配屏幕分辨率
- 无法实现 UI 与 3D 物体的穿插效果

**适用场景**：常规 HUD 界面、弹窗、菜单等需要始终显示在最前方的 UI。

---

### 2. Screen Space - Camera

UI 元素由**指定的相机**进行渲染，Canvas 会被放置在相机前方的一个平面上（通过 `Plane Distance` 参数控制距离）。

**特点**：
- 可以控制 UI 与其他渲染层的前后关系
- 当相机设置为 **Perspective（透视模式）** 时，调整 UI 元素的 Rotation 可以呈现 3D 立体效果
- Canvas 的 RectTransform **不可直接编辑**，需通过相机或 `Plane Distance` 参数调整显示效果

**适用场景**：需要 UI 与粒子特效、3D 模型产生层级穿插的界面，或需要透视效果的 UI 动画。

---

### 3. World Space

Canvas 作为**普通的 3D 物体**存在于世界空间中，其 RectTransform 完全可编辑（位置、旋转、缩放均可自由调整）。

**特点**：
- 会受到场景中其他物体的遮挡
- 可挂载到任意 GameObject 上，跟随物体移动
- 需要手动指定 `Event Camera` 以响应 UI 交互事件

**适用场景**：角色头顶的血条/名称、场景内的交互提示牌、VR/AR 中的空间 UI 等。
