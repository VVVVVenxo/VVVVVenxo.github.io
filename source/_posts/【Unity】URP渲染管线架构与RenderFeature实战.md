---
title: 【Unity】URP渲染管线架构与RenderFeature实战
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/gen/Unity-URP渲染管线架构与RenderFeature实战.png
date: 2026-10-22
tags:
  - Unity
  - URP
  - 渲染管线
  - RenderFeature
  - 后处理
description: 记录 Unity URP（通用渲染管线）的核心改进、四个核心类的职责、单帧渲染流程，以及自定义 ScriptableRendererFeature 后处理的代码模板与注意事项。
---

## 一、URP 与 Built-in 的区别

Built-in（内置管线）的渲染流程写死在引擎 C++ 层，C# 层无法直接修改渲染顺序。URP（通用渲染管线）将渲染流程拆分为 C# 层可控的 `RenderPass`，主要改进如下：

1. **流程可在 C# 层定制**：剔除、排序、渲染目标绑定和 Pass 执行顺序均由 C# 代码管理。
2. **单 Pass 多光源渲染**：Built-in 中每增加一盏逐像素光就会多执行一次 `ForwardAdd` Pass，导致 DrawCall 成倍增加；URP 将所有可见光源数据打包传入，在**一次 Pass 内算完主光源与附加光源**。
3. **原生支持 SRP Batcher**：将材质属性缓存在显存常量缓冲区（CBuffer）中，只要 Shader 变体一致即可合批，减少 CPU 切换渲染状态的开销。
4. **模块化扩展**：不再依赖挂载在相机上的 `OnRenderImage`，而是通过 `ScriptableRendererFeature` 插入自定义渲染通道。

---

## 二、URP 的四个核心类

```text
UniversalRenderPipelineAsset
  └── UniversalRenderPipeline
        └── UniversalRenderer
              ├── ScriptableRendererFeature
              └── ScriptableRenderPass
```

1. **`UniversalRenderPipelineAsset`**：管线配置文件（`.asset`），保存在磁盘上，用于配置阴影距离、抗锯齿（MSAA）、HDR 等全局参数，并在运行时创建管线实例。
2. **`UniversalRenderPipeline`**：管线运行时实例。每帧由引擎调用 `Render()`，负责对所有相机排序，并依次执行每个相机的渲染。
3. **`UniversalRenderer`**：单个相机的渲染器。负责管理相机的颜色与深度缓冲区，维护当前帧待执行的 `ScriptableRenderPass` 列表。
4. **`ScriptableRendererFeature` 与 `ScriptableRenderPass`**：
   - `ScriptableRenderPass` 是最小渲染单元（阴影、不透明物体、天空盒、透明物体、后处理本质上都是一个个 Pass）。
   - `ScriptableRendererFeature` 是挂载在 Renderer 面板上的扩展容器，负责创建 `ScriptableRenderPass` 并将其加入渲染列表。

---

## 三、单帧渲染流程与插入时机

### 1. 单相机渲染顺序

每帧渲染单个相机时，按以下顺序执行：

1. **视锥剔除（Cull）**：根据相机视锥体剔除不可见物体，收集可见物体与光源数据。
2. **注入并排序 Pass**：收集内置 Pass 与所有 `RendererFeature` 注入的自定义 Pass，按 `renderPassEvent` 数值从小到大排序。
3. **依次执行 Pass**：
   `渲染阴影贴图 → 预深度(DepthPrepass) → 不透明物体(Opaque) → 天空盒(Skybox) → 透明物体(Transparent) → 后处理(PostProcessing)`
4. **提交执行（Submit）**：各 Pass 中录制的 `CommandBuffer` 指令不会立即执行，直到末尾调用 `context.Submit()` 才一次性提交给 GPU。

### 2. 常用的 `RenderPassEvent` 插入时机

编写自定义 `RenderPass` 时，通过设置 `renderPassEvent` 指定执行位置：

- **`AfterRenderingOpaques`**：不透明物体绘制完成后执行。常用于抓取不透明背景画面，实现水体折射、热空气扭曲、角色描边。
- **`BeforeRenderingPostProcessing`**：所有三维物体绘制完成、内置后处理开始前执行。最常用于自定义全屏后处理（如 UI 背景模糊、受击红屏、径向模糊）。
- **`AfterRenderingPostProcessing`**：内置后处理完成后执行。常用于最终画面叠加效果（如故障风特效、截屏取图）。

---

## 四、自定义 `RenderFeature` 代码模板

编写自定义全屏后处理固定包含两个类：`ScriptableRendererFeature` 与 `ScriptableRenderPass`。核心函数只有三个：

- `Create()`：初始化材质与 Pass。
- `AddRenderPasses()`：每帧将 Pass 加入渲染队列。
- `Execute()`：使用 `CommandBuffer` 录制绘制指令。

```csharp
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class CustomPostProcessFeature : ScriptableRendererFeature
{
    [Serializable]
    public class Settings
    {
        public RenderPassEvent passEvent = RenderPassEvent.BeforeRenderingPostProcessing;
        public Material material;
        [Range(1, 4)] public int downsample = 2; // 降采样倍率
    }

    public Settings settings = new Settings();
    private CustomRenderPass m_Pass;

    public override void Create()
    {
        m_Pass = new CustomRenderPass(settings);
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (settings.material == null) return;

        // 仅对 Game 相机生效
        if (renderingData.cameraData.cameraType == CameraType.Game)
        {
            renderer.EnqueuePass(m_Pass);
        }
    }

    protected override void Dispose(bool disposing)
    {
        m_Pass?.Dispose();
    }

    private class CustomRenderPass : ScriptableRenderPass
    {
        private readonly Settings m_Settings;
        private RTHandle m_TempRT;

        public CustomRenderPass(Settings settings)
        {
            m_Settings = settings;
            renderPassEvent = settings.passEvent;
        }

        // 相机渲染前调用：分配或复用临时纹理
        public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
        {
            var desc = renderingData.cameraData.cameraTargetDescriptor;
            desc.depthBufferBits = 0; // 颜色后处理不需要深度缓冲
            desc.width  /= m_Settings.downsample;
            desc.height /= m_Settings.downsample;

            RenderingUtils.ReallocateIfNeeded(ref m_TempRT, desc, FilterMode.Bilinear,
                TextureWrapMode.Clamp, name: "_CustomTempRT");
        }

        // 执行渲染指令：相机颜色缓冲 -> 材质处理写入临时纹理 -> 写回相机颜色缓冲
        public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
        {
            RTHandle cameraColor = renderingData.cameraData.renderer.cameraColorTargetHandle;
            if (cameraColor == null || cameraColor.rt == null) return;

            CommandBuffer cmd = CommandBufferPool.Get("Custom PostProcess");

            Blitter.BlitCameraTexture(cmd, cameraColor, m_TempRT, m_Settings.material, 0);
            Blitter.BlitCameraTexture(cmd, m_TempRT, cameraColor);

            context.ExecuteCommandBuffer(cmd);
            CommandBufferPool.Release(cmd);
        }

        public void Dispose()
        {
            m_TempRT?.Release();
        }
    }
}
```

在 **URP Renderer Data** 面板底部点击 **Add Renderer Feature**，挂载该脚本并指定材质即可生效。

---

## 五、注意事项

1. **临时纹理关闭深度缓冲**：`cameraTargetDescriptor` 默认包含 24/32 位深度格式。创建颜色后处理的临时纹理时，需将 `desc.depthBufferBits` 设为 `0`，避免浪费显存和带宽。
2. **全屏效果优先降采样**：全屏模糊、泛光等效果应先将临时纹理宽高除以 2 或 4（`downsample`），减少像素采样数量。
3. **按需获取深度图与法线图**：若 Pass 需要读取 `_CameraDepthTexture` 或 `_CameraNormalsTexture`，在 `OnCameraSetup` 中调用 `ConfigureInput(ScriptableRenderPassInput.Depth)` 按需开启，不要在管线资产面板中全局常开。
4. **避免打断 SRP Batcher**：SRP Batcher 不兼容 `MaterialPropertyBlock`。在普通模型上使用 `MaterialPropertyBlock` 会导致该物体退化为独立 DrawCall。
