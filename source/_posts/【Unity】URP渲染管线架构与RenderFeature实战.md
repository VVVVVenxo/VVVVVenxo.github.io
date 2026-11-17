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
description: 用通俗直观的方式梳理 Unity URP（通用渲染管线）的核心设计、四个核心类与一帧渲染流程，并给出最简可用的 RenderFeature 自定义后处理代码模板与避坑要点。
---

Unity 从传统的 Built-in（内置管线）升级到 **URP（Universal Render Pipeline，通用渲染管线）**，最核心的变化只有一件事：**把原本写死在 C++ 引擎黑盒里的渲染流程，拆成一个个公开的 C# 工序（Pass），让开发者可以自由增删和调整顺序。**

本文去掉繁琐的底层术语，直接梳理日常开发最需要掌握的 URP 核心结构与 `RenderFeature` 扩展写法。

---

## 一、URP 相比 Built-in 到底改进了什么？

| 核心维度 | Built-in（内置管线） | URP（通用渲染管线） |
| :--- | :--- | :--- |
| **流程控制** | C++ 黑盒硬编码，只能局部插桩 | C# 层完全开源可控，按工序（Pass）排队执行 |
| **多光源开销** | 每多一盏实时光，物体就多画一遍（DrawCall 翻倍） | 所有可见灯光打包传入，**单次 Pass 算完所有光源** |
| **合批效率** | 传统动态/静态合批，材质不同即打断 | 原生支持 **SRP Batcher**，把材质参数常驻显存，大幅降低 CPU 开销 |
| **功能扩展** | 挂相机脚本写 `OnRenderImage` | 模块化的 `RendererFeature`，在面板上像插件一样随时开关 |

---

## 二、四个核心类：一条流水线看懂 URP

阅读或扩展 URP 时，只需要记住下面四个类的分工（可以把它们理解成一条工厂流水线）：

```text
UniversalRenderPipelineAsset  （总配置表：面板上的 .asset 文件，开关阴影/抗锯齿/HDR）
  └── UniversalRenderPipeline （总调度员：每帧遍历所有相机，先做视锥剔除）
        └── UniversalRenderer （车间主任：管理当前相机的画面缓冲，维护一条 Pass 队列）
              ├── ScriptableRendererFeature （外挂插槽：挂在面板上的功能模块，负责把 Pass 塞进队列）
              └── ScriptableRenderPass      （具体工序：最小执行单元，真正向 GPU 录制绘制指令）
```

我们在项目里写自定义渲染效果（比如描边、全屏模糊、屏幕扭曲），**99% 的工作就是写一个 `RendererFeature`（外挂插槽）+ 一个 `RenderPass`（具体工序）**，把它插进 URP 的默认流水线里。

---

## 三、一帧的渲染顺序与常用“插队点”

对于单个相机，URP 每帧默认按以下顺序依次执行各个 Pass：

```text
视锥剔除 → 渲染阴影贴图 → 画不透明物体(Opaque) → 画天空盒(Skybox) → 画透明物体(Transparent) → 后处理(PostProcess) → 提交 GPU
```

当我们编写自定义 `RenderPass` 时，通过设置 `renderPassEvent` 决定它在哪一步“插队”。日常开发最常用的只有以下 3 个时机：

1. **`AfterRenderingOpaques`（不透明物体画完后）**
   - 适合做：水体折射、热空气扭曲、角色遮挡描边。此时场景主体已经画完，可以抓取背景画面供后续半透明特效采样。
2. **`BeforeRenderingPostProcessing`（内置后处理前，最常用）**
   - 适合做：UI 背景模糊、受击红屏、径向模糊、自定义全屏滤镜。此时所有 3D 物体和特效都已画完，且还没经过 Tonemapping 色调映射。
3. **`AfterRenderingPostProcessing`（所有后处理完成后）**
   - 适合做：全屏故障艺术（Glitch）、最终画面压暗、截屏取图。

---

## 四、实战：最简 `RenderFeature` 代码模板

下面是一个干净、可直接复用的全屏后处理 `ScriptableRendererFeature` 模板。它的逻辑非常清晰，只做三件事：
1. **`Create()`**：初始化材质和 Pass 实例。
2. **`AddRenderPasses()`**：每帧把 Pass 塞进渲染队列。
3. **`Execute()`**：申请一张临时纹理，用自定义材质处理相机画面后再写回。

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
        public Material material; // 挂载你的后处理材质
        [Range(1, 4)] public int downsample = 2; // 降采样倍率（2 = 宽高减半，省性能）
    }

    public Settings settings = new Settings();
    private CustomRenderPass m_Pass;

    // 1. 初始化 Pass
    public override void Create()
    {
        m_Pass = new CustomRenderPass(settings);
    }

    // 2. 每帧将 Pass 注入渲染队列
    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (settings.material == null) return;

        // 仅对正常游戏相机生效，过滤掉材质预览窗口与反射探针
        if (renderingData.cameraData.cameraType == CameraType.Game)
        {
            renderer.EnqueuePass(m_Pass);
        }
    }

    protected override void Dispose(bool disposing)
    {
        m_Pass?.Dispose();
    }

    // =====================================================================
    // 具体执行绘制命令的 RenderPass
    // =====================================================================
    private class CustomRenderPass : ScriptableRenderPass
    {
        private readonly Settings m_Settings;
        private RTHandle m_TempRT;

        public CustomRenderPass(Settings settings)
        {
            m_Settings = settings;
            renderPassEvent = settings.passEvent;
        }

        // 每帧相机渲染前：按需分配临时纹理（分辨率不变时零开销复用）
        public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
        {
            var desc = renderingData.cameraData.cameraTargetDescriptor;
            desc.depthBufferBits = 0; // 后处理不需要深度缓冲，务必置 0 节省显存
            desc.width  /= m_Settings.downsample;
            desc.height /= m_Settings.downsample;

            RenderingUtils.ReallocateIfNeeded(ref m_TempRT, desc, FilterMode.Bilinear,
                TextureWrapMode.Clamp, name: "_CustomTempRT");
        }

        // 核心执行：相机画面 -> 材质处理写入临时纹理 -> 拷回相机画面
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

写好脚本后，只需在项目的 **URP Renderer Data** 资产面板底部点击 **Add Renderer Feature**，挂上这个脚本并拖入材质球即可生效。

---

## 五、日常开发的四个避坑要点

1. **临时纹理务必关闭深度（`depthBufferBits = 0`）**
   - 直接复制相机的 `cameraTargetDescriptor` 默认带有 24/32 位深度格式。做颜色后处理时如果不设为 `0`，会白白浪费一倍显存与移动端带宽。
2. **模糊等全屏效果先做降采样（Downsample）**
   - 在 2K 手机屏幕上直接全屏读写非常耗电。把临时纹理的宽高除以 2（像素量减少为 `1/4`），配合双线性过滤（`Bilinear`），肉眼几乎看不出区别，但性能提升立竿见影。
3. **按需申请深度图/法线图，不要在全局面板常开**
   - 如果某个特效需要读深度图（`_CameraDepthTexture`），不要去 URP Asset 面板里全局勾死，而是在对应 Pass 的 `OnCameraSetup` 里写一句 `ConfigureInput(ScriptableRenderPassInput.Depth)`。这样只有该特效激活时才会生成深度图。
4. **避免用 `MaterialPropertyBlock` 打断 SRP Batcher**
   - URP 依赖 **SRP Batcher** 合批，而 `MaterialPropertyBlock` 与之不兼容。一旦在普通模型上使用 `MaterialPropertyBlock`，该物体就会退化为独立 DrawCall。
