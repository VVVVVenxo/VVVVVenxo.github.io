---
title: 【Unity】DrawCall与合批优化
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/gen/Unity-DrawCall与合批优化.png
date: 2026-07-28
tags:
  - Unity
  - UGUI
  - DrawCall
  - 性能优化
  - 合批
description: 深入理解 DrawCall 的概念与开销，剖析 UGUI 的合批规则（以 Canvas 为单位、Depth 计算、VisibleList 排序），并对比静态合批与动态合批，总结降低 DrawCall 的实战策略。
---

## 什么是 DrawCall

DrawCall 是 CPU 准备好渲染数据后，通知 GPU 开始渲染一次网格的命令。

每一次 DrawCall 前，CPU 都需要做一些额外的准备工作（设置渲染状态、提交数据），这些准备动作会带来额外的开销。DrawCall 越多，CPU 的开销越大，当 DrawCall 过多时就会影响 CPU 效率，导致游戏卡顿。

因此，**降低 DrawCall** 是渲染性能优化的核心手段之一，而**合批（Batching）** 就是减少 DrawCall 的主要方式。

---

## UGUI 的合批规则

要理解 UGUI 合批，先明确几个前提：

- UGUI 中 Canvas 下可以嵌套子 Canvas，但**合批是以 Canvas（不包含子 Canvas）为单位**的——子 Canvas 会是另外一个批次。
- 合批的计算操作是在**子线程**完成的。

完整的合批流程如下。

### ① 收集 Canvas

既然合批以 Canvas 为单位，第一步自然是把所有 Canvas 找出来，然后剔除掉不必渲染的 Canvas（透明度为 0、长宽为 0、在 RectMask2D 控件下且在其区域外）。

### ② 计算 Depth 深度值

计算 Canvas 下各 UI 控件的深度值 Depth（注意：Image 属性里也有个 depth，两者不是同一个东西）。

按照 Hierarchy 中从上往下的顺序依次遍历 Canvas 下所有 UI 元素，对于当前元素 `CurrentUI`：

1. 如果 `CurrentUI` 不渲染，则 `Depth = -1`。
2. 如果 `CurrentUI` 要渲染，但下面没有其他 UI 元素与其相交，则 `Depth = 0`。
3. 如果 `CurrentUI` 要渲染，下面只有一个元素 `LowerUI` 与其相交：
   - 两者可以合批（材质和贴图完全相同）：`CurrentUI.Depth = LowerUI.Depth`
   - 两者不能合批：`CurrentUI.Depth = LowerUI.Depth + 1`
4. 如果下面有 n 个元素与其相交，则分别计算出 n 个 Depth，`CurrentUI.Depth` 取其最大值。

> 两个 UI 元素「相交」，是指这两个元素的**网格有相交**（有重叠部分），一定要注意**不是**两个元素的 Rect 区域相交。

由于计算相交要遍历所有 UI 元素和已计算的底层元素（平方复杂度），源码中使用**分组计算包围盒矩形**的方法加速：以 16 个 UI 元素为一组计算 Group 网格 Rect，检查是否与底层元素相交时，先判断是否与底层 Group 相交，相交再与 Group 中的元素做精确判定。

### ③ 排序生成 VisibleList

各元素 Depth 计算完毕后，依次按照 **Depth → material ID → texture ID → RendererOrder（Hierarchy 顺序）** 排序（优先级依次递减，均为从小到大）：

1. 先按 Depth 从小到大排序；
2. Depth 相同的元素，再按 material ID 从小到大排序；
3. material ID 相同的元素，再按 texture ID 从小到大排序；
4. texture ID 相同的元素，最后按 Hierarchy 上的顺序排序（越上面越靠前）。

然后剔除 `Depth = -1` 的元素，得到合批前的 UI 元素队列，称为 **VisibleList**。

### ④ 合并网格

得到 VisibleList 后，判断其中**相邻**的元素是否能合批（相同的材质和贴图）。注意这里不再考虑 Depth 是否相同——只要相邻且材质贴图相同，即使 Depth 不同也能合批。然后一个批次一个批次地合并网格，提交给 GPU 渲染。

---

## 合批的基本条件

两个 UI 控件能合批的基本条件是：使用的**材质球（Shader）和贴图**要完全相同。

比如 Text 和 Image 默认使用的材质球都是 `UI/Default`，但两者使用的贴图不同（文字用字体贴图），所以 Text 和 Image 注定无法合批。

**打断合批的常见情况**：

1. 材质或贴图不同。
2. Hierarchy 层级穿插：例如 Image A 和 Image B 本可合批，但中间夹了一个 Text，就会导致 A 和 B 无法合批，变成 3 个 DrawCall。
3. 使用了 Mask（会造成额外的 DrawCall 和状态切换）。
4. UI 元素的 Z 轴不为 0 或进行了旋转，导致不再共面。

---

## 静态合批与动态合批

除了 UGUI 的 UI 合批，场景物体也有合批机制。

**静态合批**

勾选 Static 后，Unity 在 Build 时会自动生成合并的网格，并以文件形式存储合并后的数据。场景加载时一次性提交整个合并模型的顶点数据，根据场景管理系统判断各子模型的可见性，设置一次渲染状态，调用多次 DrawCall 分别绘制每个子模型。

**动态合批**

专门为优化场景中共享同一材质的**动态 GameObject** 渲染而设计，目标是以最小代价合并小型网格、减少 DrawCall。

原理是在场景绘制前，将所有共享同一材质的模型的**顶点信息变换到世界空间**，然后通过一次 DrawCall 绘制多个模型。顶点变换由 CPU 完成，所以会带来一些 CPU 性能消耗。

---

## 降低 DrawCall 的策略

1. **UI 层面**：小图合大图（打图集），多个小 DrawCall 合成大 DrawCall。
2. **合批处理**：保证可合批元素的材质、贴图一致，避免层级穿插打断合批。

但是——**DrawCall 并不是追求极限越小越好**。

决定渲染性能的除了 DrawCall，还有用于传输渲染数据的**总线带宽**。当我们用 Draw Call Batching 把同种材质的网格拼在一起时，可能造成同一时间需要传输的数据（Texture、VB/IB 等）大大增加，以至于造成带宽「堵塞」。在资源无法及时传输时，GPU 只能等待，反倒降低了游戏帧率。

**图集的实践建议**：

- 重复使用的通用 UI 打包为一个图集。
- 图标根据数量分为多个图集，或由美术直接提供图集自己做裁切。
- 图集大小根据规范略有不同，大多是 512 或 1024。
