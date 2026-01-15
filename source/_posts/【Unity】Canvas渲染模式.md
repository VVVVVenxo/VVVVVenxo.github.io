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

只显示所创建的 Canvas 中的内容，即只渲染画布。UI 始终覆盖在屏幕最上层。

### 2. Screen Space - Camera

只显示相机所渲染的区域。当相机的 Projection 设置为 Perspective（透视模式）而非 Orthographic（正交模式）时，通过调整 Canvas 中 Image 或其他物体的 Rotation，可以制作 3D 立体效果的 UI。

但在这种模式下不可以更改 Canvas 的 RectTransform，只能通过相机来调整 Canvas 的显示位置和大小。

### 3. World Space

Canvas 的 RectTransform 完全可编辑，Canvas 被当作一个普通的 3D 物体（类似 Cube）在场景中渲染。

**适用场景**：如果把 Canvas 挂载到游戏角色上，这种模式非常适合制作角色头顶的血条或名称显示。