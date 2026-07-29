---
title: 【Unity】UGUI 源码解读
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/gen/Unity-UGUI-源码解读.png
date: 2026-07-29
tags:
  - Unity
  - UGUI
  - 源码
  - 渲染
  - 事件系统
description: 从源码层面剖析 UGUI 的运作机制——图形绘制管线（Rebuild/OnPopulateMesh）、基于射线与接口的事件系统、Graphic 家族继承体系、Image 精灵生成算法（九宫格/Tiled/Filled）以及布局系统的脏标记与更新流程。
---

## 前置概念

在深入源码前，先明确几个网格相关的基础概念：

- **mesh**：网格
- **vertex**：组成网格的顶点
- **triangle**：绘制顶点的顺序
- **UV**：纹理贴图坐标，决定网格顶点和贴图之间的对应关系

---

## 一、图形绘制过程

UGUI 中所有可见元素（Image、Text、RawImage）最终都要生成网格并提交渲染。这个过程由 `CanvasUpdateRegistry` 统一驱动：当某个 Graphic 被标记为脏（需要重绘）时，会注册到更新队列，在合适时机统一执行 `Rebuild`。

![图形绘制-绘制过程](/img/posts/ugui-01.png)

如上面的时序图所示，一次 `CanvasUpdate` 的绘制流程为：

1. `CanvasUpdateRegistry` 调用 `PerformUpdate()`；
2. 对每个需要重建的 `Graphic` 调用 `Rebuild()`；
3. `Rebuild` 内部依次调用 `UpdateGeometry()` → `DoMeshGeneration()`；
4. 最终回调 `OnPopulateMesh()`——**这是我们重写自定义网格的关键入口**。

![图形绘制细节](/img/posts/ugui-02.png)

---

## 二、事件系统

**为什么 UI 可以点击？** 核心是「射线 + 碰撞检测 + 事件派发」三步。

### 从摄像机生成射线

第一步，从摄像机处生成一条射线：

![生成射线](/img/posts/ugui-03.png)

```csharp
var ray = mainCamera.ScreenPointToRay(Input.mousePosition);
Physics.Raycast(ray, out RaycastHit hitInfo);
if (hitInfo.collider != null && hitInfo.collider.gameObject != null)
{
    if (Input.GetMouseButtonDown(0))
    {
        Debug.Log("Button Clicked!");
    }
}
```

### 射线检测与事件触发

射线和物体进行碰撞检测，如果检测到碰撞，说明 UI 被点击到了，随后触发事件。

![射线检测](/img/posts/ugui-04.png)

![事件触发流程](/img/posts/ugui-05.png)

![事件派发](/img/posts/ugui-06.png)

### 面向接口编程

UGUI 事件系统的精髓在于**面向接口编程**：事件系统根本不关心鼠标下面点击到的是什么 GameObject，只要它实现了对应的接口，就认为它拥有这种能力。

![面向接口编程](/img/posts/ugui-07.png)

例如 `ExecuteEvents.pointerClickHandler` 会遍历 root，找到实现了 `IPointerClickHandler` 接口、并且能处理当前点击事件的 GameObject。所以这里的 handler 就是刚刚点击的 button。

![handler 查找](/img/posts/ugui-08.png)

---

## 三、Graphic 家族

UGUI 的所有可视组件都源自一套清晰的继承体系。

![Graphic 家族继承图](/img/posts/ugui-09.png)

继承链的关键节点：

- **`Graphic`**：抽象基类，继承自 `UIBehaviour`，实现 `ICanvasElement`。定义了顶点生成、材质、颜色等最核心的绘制能力。
- **`MaskableGraphic`**：继承自 `Graphic`，额外实现 `IClippable`、`IMaskable`、`IMaterialModifier`，赋予了被 Mask 裁剪的能力。
- **`Image` / `RawImage` / `Text`**：都继承自 `MaskableGraphic`。其中 `Image` 还实现了 `ISerializationCallbackReceiver`、`ILayoutElement`、`ICanvasRaycastFilter` 等接口。

![Image 属性分析](/img/posts/ugui-10.png)

![Image 源码](/img/posts/ugui-11.png)

---

## 四、ImageSprite 生成算法

Image 组件根据 `Image.Type` 的不同，采用不同的网格生成算法。

### Sliced（九宫格）

Slice 算法首先根据图片设置的四个边距（border），得到四个重要的点，从而划分出一个**九宫格**。每个九宫格里面的图片都可以认为是一个 Simple 图片。

![九宫格顶点计算](/img/posts/ugui-12.png)

如图，四个关键顶点通过 border 与 padding 计算得出：

```csharp
s_VertScratch[0] = new Vector2(padding.x, padding.y);
s_VertScratch[3] = new Vector2(rect.width - padding.z, rect.height - padding.w);

s_VertScratch[1].x = border.x;
s_VertScratch[1].y = border.y;
s_VertScratch[2].x = rect.width  - border.z;
s_VertScratch[2].y = rect.height - border.w;
```

### Tiled（平铺）

Tiled 通过 for 循环从 0 到最大宽度进行填充：如果要填充的值大于最大宽度，那么会对一张 Simple 图片进行裁剪，然后填充。

![Tiled 平铺](/img/posts/ugui-13.png)

### Filled（填充）

![Filled 填充](/img/posts/ugui-14.png)

Filled 的水平和垂直方向同理。以 **Radial 90** 为基础：

![Radial 90](/img/posts/ugui-15.png)

之后的 180、360 填充都基于这个 90 度的方式来实现。例如：

- 在 180 里 `fillAmount = 0.4`，代表其中一个 90 度区域填充了 0.8；
- 在 360 里 `fillAmount = 0.2`，代表其中一个 90 度区域填充了 0.8。

---

## 五、Selectable 可交互组件

`Selectable` 是所有可交互 UI 控件（Button、Toggle、Slider 等）的基类。

![Selectable 接口](/img/posts/ugui-16.png)

Selectable 实现了这么多接口，代表它有做这么多种动作的能力。这也再次印证了前面的观点：

![接口能力](/img/posts/ugui-17.png)

> 事件系统根本不管鼠标下面点击到的是什么 GameObject，只要实现了对应的接口，就认为它拥有这种能力。

---

## 六、布局系统

UGUI 的自动布局（Horizontal/Vertical/Grid Layout Group）基于**脏标记 + 统一更新**的机制。

![布局系统](/img/posts/ugui-18.png)

![Horizontal 布局](/img/posts/ugui-19.png)

![布局更新](/img/posts/ugui-20.png)

工作流程：

- `SetDirty` 接口表示这个 UI 元素需要重新布局，随后注册到 `LayoutRebuild` 队列里；
- 最后需要更新的时候，在 `PerformUpdate` 里最终对布局进行统一计算与更新。

这种「标记脏 → 统一 Rebuild」的设计与图形绘制的思路一致——把分散的修改合并到一帧的固定时机批量处理，避免频繁重算带来的性能浪费。这也是为什么**频繁修改 UI 会导致 Canvas Rebuild、影响性能**的根本原因。
