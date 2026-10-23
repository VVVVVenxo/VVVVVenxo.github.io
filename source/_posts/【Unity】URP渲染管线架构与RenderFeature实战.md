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
  - 性能优化
description: 解析 Unity URP（通用渲染管线）的核心架构、一帧渲染流程与 C# 调度机制，并通过完整的自定义 ScriptableRendererFeature 与 RTHandle 双缓冲 Kawase 模糊实战，掌握现代 Unity 渲染管线扩展与调试方法。
---

在理解了实时渲染管线的底层数学与 Shader 编程之后，客户端工程落地的下一步是掌握引擎如何组织并调度一整帧的绘制命令。Unity 从 Built-in 内置管线演进到 **SRP（Scriptable Render Pipeline，可编程渲染管线）**，其核心变革是将原本固化在 C++ 引擎黑盒中的渲染流程暴露给 C# 层。

本文围绕商业项目最常用的 **URP（Universal Render Pipeline）**，梳理其核心类职责、一帧的执行链路，并编写一个基于现代 `RTHandle` API 的自定义 `ScriptableRendererFeature` 屏幕后处理模块。

---

## 一、从 Built-in 到 URP：架构差异对比

在 Built-in 管线中，开发者只能通过 `CameraEvent` 挂载 `CommandBuffer`，或者使用 `OnRenderImage` 拦截渲染结果，无法修改主管线的剔除、灯光分配和 Pass 执行顺序。URP 基于 SRP 接口层重构了整套调度模型：

| 维度 | Built-in 内置管线 | URP（通用渲染管线） |
| :--- | :--- | :--- |
| **管线控制权** | C++ 引擎底层硬编码，C# 仅能局部插桩 | C# 层完全控制剔除、排序、渲染目标绑定与 Pass 调度 |
| **多光源处理** | 主平行光走 `ForwardBase`，每多一盏逐像素光额外增加 1 个 `ForwardAdd` Pass（DrawCall 成倍增加） | **Single-Pass Forward**：所有可见光源数据打包进常量缓冲区/结构化缓冲区，**单次 Pass 完成主光源与附加光源计算** |
| **合批机制** | 静态合批 / 动态合批 / GPU Instancing | 原生支持 **SRP Batcher**（按 Shader 变体合并 CBuffer 状态切换） |
| **扩展方式** | `OnRenderImage` / `Camera.AddCommandBuffer` | 模块化的 `ScriptableRendererFeature` + `ScriptableRenderPass` |
| **渲染目标管理** | 传统 `RenderTexture.GetTemporary` | 基于 **`RTHandle`** 的动态分辨率缩放与生命周期管理 |

---

## 二、URP 四大核心对象与职责边界

阅读或扩展 URP 源码时，只需抓住以下四个核心类及其层级关系：

```text
UniversalRenderPipelineAsset (配置资产：序列化保存在磁盘上的管线参数)
  └── UniversalRenderPipeline (管线实例：接管 Render 入口，遍历相机、执行剔除)
        └── UniversalRenderer : ScriptableRenderer (渲染器：管理当前相机的 RT 与 Pass 队列)
              ├── ScriptableRendererFeature (功能特性：可插拔的扩展容器，负责创建并注入 Pass)
              └── ScriptableRenderPass (渲染通道：最小执行单元，通过 CommandBuffer 录制 GPU 指令)
```

1. **`UniversalRenderPipelineAsset`**：继承自 `RenderPipelineAsset`，是在 Project 窗口创建的 `.asset` 配置文件（保存阴影距离、抗锯齿 MSAA、HDR 开关、Renderer 列表等设置），并负责实例化运行时管线对象。
2. **`UniversalRenderPipeline`**：继承自 `RenderPipeline`。每帧由引擎调用其 `Render(ScriptableRenderContext context, List<Camera> cameras)` 函数，负责对相机排序，并依次调用每个相机的渲染流程。
3. **`UniversalRenderer`（继承自 `ScriptableRenderer`）**：管理单个相机的渲染上下文、颜色与深度缓冲区（`_CameraColorAttachment` / `_CameraDepthAttachment`），维护一个待执行的 `m_ActiveRenderPassQueue` 列表。
4. **`ScriptableRenderPass`**：URP 的最小工作单元。阴影绘制、预深度、不透明几何体、天空盒、透明几何体、后处理，本质上都是一个个派生自 `ScriptableRenderPass` 的实例。

### 关键机制：`ScriptableRenderContext` 的延迟提交

在 URP 的 C# 代码中，调用 `cmd.DrawMesh` 或 `context.DrawRenderers` **并不会立即触发 GPU 绘制**，而是将渲染命令录制到命令列表（Command List）中。直到管线在相机渲染末尾调用：

```csharp
context.Submit();
```

CPU 才会将累积的所有 `CommandBuffer` 一次性提交给底层图形 API（DirectX 12 / Vulkan / Metal / OpenGL）执行。

---

## 三、URP 一帧的完整渲染流程

当 `UniversalRenderPipeline.RenderSingleCamera` 被调用时，一帧的标准执行顺序如下：

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 1：剔除与光照准备 (CPU)                                             │
│   1. camera.TryGetCullingParameters() 获取相机视锥参数                   │
│   2. context.Cull(ref cullingParameters) 执行视锥剔除，得到 CullingResults│
│   3. 提取可见光源、构建主光与附加光常量缓冲区数据                         │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 2：组装并排序 RenderPass 队列 (Setup)                               │
│   1. 添加内置 Pass（ShadowCaster / DepthPrepass / Opaque / Skybox / ...）│
│   2. 遍历挂载的 RendererFeature，调用 AddRenderPasses() 注入自定义 Pass   │
│   3. 按 RenderPassEvent 枚举值从小到大对所有 Pass 进行稳定排序             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 3：依次执行 RenderPass 队列 (Execute)                               │
│   [BeforeRenderingShadows]  → MainLightShadowCasterPass (渲染主光阴影贴图)│
│   [AfterRenderingPrePasses] → DepthOnlyPass / DepthNormalOnlyPass       │
│   [BeforeRenderingOpaques]  → 注入：自定义早期 Pass（如屏幕空间 AO）       │
│   [Render Opaques]          → DrawObjectsPass (Opaque, Front-to-Back)   │
│   [AfterRenderingOpaques]   → SkyboxPass (利用 Early-Z 仅填充无遮挡背景)  │
│   [Render Transparents]     → DrawObjectsPass (Transparent, Back-to-Front)│
│   [BeforeRenderingPostProcessing] → 注入：自定义屏幕特效 / 模糊 / 描边     │
│   [AfterRenderingPostProcessing]  → UberPostProcess / FinalBlitPass     │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 阶段 4：清理与提交 (Cleanup & Submit)                                    │
│   1. 遍历所有 Pass 调用 OnCameraCleanup() 释放每帧临时资源                │
│   2. context.Submit() 将录制的全部命令提交至 GPU 执行                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### `RenderPassEvent` 常用插入时机速查

编写自定义效果时，通过设置 `renderPassEvent` 决定你的 Pass 插入在管线的哪个位置：

| `RenderPassEvent` 枚举值 | 数值 | 典型工程应用场景 |
| :--- | :---: | :--- |
| `BeforeRenderingShadows` | 50 | 自定义阴影映射、虚拟阴影贴图准备 |
| `AfterRenderingPrePasses` | 150 | 此时可安全读取 `_CameraDepthTexture` 与 `_CameraNormalsTexture`（如自定义体积光、SSAO） |
| `BeforeRenderingOpaques` | 250 | 地面贴花预处理、背景预绘制 |
| `AfterRenderingOpaques` | 300 | **最常用插入点之一**：抓取不透明物体画面（`_CameraOpaqueTexture`）用于水体折射、热空气扭曲、角色边缘描边 |
| `AfterRenderingSkybox` | 350 | 抓取包含天空盒的完整不透明背景、大气散射云层 |
| `AfterRenderingTransparents` | 450 | 位于所有 3D 物体绘制完成后、内置后处理（Bloom/Tonemapping）之前 |
| `BeforeRenderingPostProcessing` | 500 | **最常用后处理插入点**：自定义全屏滤镜、径向模糊、UI 背景高斯/Kawase 模糊 |
| `AfterRenderingPostProcessing` | 600 | 最终画面叠加效果（如全屏故障艺术 Glitch、自定义色彩分级、截图抓取） |

---

## 四、实战：编写自定义 `ScriptableRendererFeature`（Dual Kawase 模糊）

在商业客户端中，打开全屏 UI 弹窗时经常需要将底层 3D 画面虚化，或者制作受击/冲刺时的屏幕后处理。传统的 2D 高斯模糊采样次数多、带宽开销大，工业界普遍采用 **Kawase Blur（川濑模糊）**——通过多层降采样（Downsample）与升采样（Upsample）配合硬件双线性插值（Bilinear Filtering），用极少的纹理采样次数即可获得平滑的大半径模糊。

下面基于 Unity URP 现代 **`RTHandle` 与 `Blitter` API**，实现一套完整的 Kawase 屏幕模糊 `RendererFeature`。

### 1. 第一步：编写 Kawase Blur 后处理 Shader

新建 `Hidden/Custom/KawaseBlur.shader`。使用 URP 内置的 `Vert` 全屏三角形顶点函数（位于 `Blit.hlsl`，只需 3 个顶点即可覆盖全屏，比传统 4 顶点 Quad 少了中心对角线的 `2x2` 像素块额外开销）：

```hlsl
Shader "Hidden/Custom/KawaseBlur"
{
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "RenderType" = "Opaque" }
        LOD 100
        ZWrite Off
        ZTest Always
        Cull Off

        Pass
        {
            Name "KawaseBlurPass"

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"

            // _BlitTexture 与 _BlitTexture_TexelSize 由 Blitter.BlitCameraTexture 自动绑定
            float _BlurOffset;

            half4 Frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                float2 uv = input.texcoord;
                float2 d  = _BlitTexture_TexelSize.xy * (_BlurOffset + 0.5);

                // 利用硬件 Bilinear 线性插值，四角偏移采样求均值
                half4 col  = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv + float2(-d.x, -d.y));
                col       += SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv + float2( d.x, -d.y));
                col       += SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv + float2(-d.x,  d.y));
                col       += SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv + float2( d.x,  d.y));

                return col * 0.25h;
            }
            ENDHLSL
        }
    }
}
```

### 2. 第二步：实现 `ScriptableRendererFeature` 与 `ScriptableRenderPass`

新建 C# 脚本 `KawaseBlurRenderFeature.cs`，包含序列化配置类、RenderPass 执行逻辑与 `RTHandle` 内存生命周期管理：

```csharp
using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

public class KawaseBlurRenderFeature : ScriptableRendererFeature
{
    [Serializable]
    public class BlurSettings
    {
        public RenderPassEvent renderPassEvent = RenderPassEvent.BeforeRenderingPostProcessing;
        public Shader blurShader;
        [Range(1, 4)] public int downsample = 2;       // 初始降采样倍率
        [Range(1, 6)] public int iterations = 3;       // 模糊迭代次数
        [Range(0.5f, 5f)] public float blurSpread = 1.2f; // 每次迭代的步长系数
    }

    [SerializeField] private BlurSettings m_Settings = new BlurSettings();
    private Material m_Material;
    private KawaseBlurRenderPass m_RenderPass;

    // 1. 初始化：在管线加载或 Inspector 参数修改时调用
    public override void Create()
    {
        if (m_Settings.blurShader == null)
        {
            m_Settings.blurShader = Shader.Find("Hidden/Custom/KawaseBlur");
        }
        if (m_Settings.blurShader != null && m_Material == null)
        {
            m_Material = CoreUtils.CreateEngineMaterial(m_Settings.blurShader);
        }
        m_RenderPass = new KawaseBlurRenderPass(m_Settings, m_Material);
    }

    // 2. 每帧每个相机调用：决定是否将 Pass 注入渲染队列
    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (m_Material == null) return;

        // 过滤掉预览窗口相机与反射探针相机，仅对 Game 与 Scene 相机生效
        CameraType camType = renderingData.cameraData.cameraType;
        if (camType != CameraType.Game && camType != CameraType.SceneView) return;

        renderer.EnqueuePass(m_RenderPass);
    }

    // 3. 销毁：释放材质与 RTHandle 显存，防止显存泄漏
    protected override void Dispose(bool disposing)
    {
        m_RenderPass?.Dispose();
        CoreUtils.Destroy(m_Material);
    }

    // =====================================================================
    // 内部类：具体执行 GPU 指令录制的 RenderPass
    // =====================================================================
    private class KawaseBlurRenderPass : ScriptableRenderPass
    {
        private const string k_ProfilerTag = "Custom Kawase Blur";
        private static readonly int s_BlurOffsetId = Shader.PropertyToID("_BlurOffset");

        private readonly BlurSettings m_Settings;
        private readonly Material m_Material;
        private readonly ProfilingSampler m_ProfilingSampler;

        // 使用双缓冲 RTHandle 交替读写（Ping-Pong Buffering）
        private RTHandle m_TempRT0;
        private RTHandle m_TempRT1;

        public KawaseBlurRenderPass(BlurSettings settings, Material material)
        {
            m_Settings = settings;
            m_Material = material;
            renderPassEvent = settings.renderPassEvent;
            m_ProfilingSampler = new ProfilingSampler(k_ProfilerTag);
        }

        // 在相机开始渲染该 Pass 前调用：配置临时 RTHandle 分辨率与格式
        public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
        {
            RenderTextureDescriptor desc = renderingData.cameraData.cameraTargetDescriptor;
            desc.depthBufferBits = 0; // 颜色后处理不需要深度缓冲，节省显存带宽
            desc.msaaSamples = 1;
            desc.width  = Mathf.Max(1, desc.width / m_Settings.downsample);
            desc.height = Mathf.Max(1, desc.height / m_Settings.downsample);

            // ReallocateIfNeeded 仅在分辨率或格式变化时重新分配显存，正常帧零开销
            RenderingUtils.ReallocateIfNeeded(ref m_TempRT0, desc, FilterMode.Bilinear,
                TextureWrapMode.Clamp, name: "_KawaseBlurTemp0");
            RenderingUtils.ReallocateIfNeeded(ref m_TempRT1, desc, FilterMode.Bilinear,
                TextureWrapMode.Clamp, name: "_KawaseBlurTemp1");
        }

        // 核心执行阶段：通过 CommandBuffer 录制多次 Ping-Pong Blit
        public override void Execute(ScriptableRenderContext context, ref RenderingData renderingData)
        {
            if (m_Material == null) return;

            RTHandle cameraColor = renderingData.cameraData.renderer.cameraColorTargetHandle;
            if (cameraColor == null || cameraColor.rt == null) return;

            CommandBuffer cmd = CommandBufferPool.Get();
            using (new ProfilingScope(cmd, m_ProfilingSampler))
            {
                // 第 1 步：将相机颜色缓冲区降采样拷贝到 TempRT0
                cmd.SetGlobalFloat(s_BlurOffsetId, 1.0f);
                Blitter.BlitCameraTexture(cmd, cameraColor, m_TempRT0, m_Material, 0);

                // 第 2 步：在 TempRT0 与 TempRT1 之间交替迭代模糊
                RTHandle src = m_TempRT0;
                RTHandle dst = m_TempRT1;
                for (int i = 1; i < m_Settings.iterations; i++)
                {
                    cmd.SetGlobalFloat(s_BlurOffsetId, 1.0f + i * m_Settings.blurSpread);
                    Blitter.BlitCameraTexture(cmd, src, dst, m_Material, 0);
                    (src, dst) = (dst, src); // 交换读写句柄
                }

                // 第 3 步：将最终模糊结果写回相机颜色缓冲区（或设为全局贴图供 UI 背景采样）
                cmd.SetGlobalFloat(s_BlurOffsetId, 1.0f + m_Settings.iterations * m_Settings.blurSpread);
                Blitter.BlitCameraTexture(cmd, src, cameraColor, m_Material, 0);
            }

            context.ExecuteCommandBuffer(cmd);
            CommandBufferPool.Release(cmd);
        }

        public void Dispose()
        {
            m_TempRT0?.Release();
            m_TempRT1?.Release();
        }
    }
}
```

### 3. 工程关键细节解析

1. **为什么使用 `RenderingUtils.ReallocateIfNeeded` 而不是每帧 `GetTemporaryRT`？**
   - `RTHandle` 会持久缓存底层 `RenderTexture`。只要相机分辨率和格式没变，`ReallocateIfNeeded` 直接复用已有句柄，避免了每帧向驱动层申请和释放纹理描述符的 CPU 开销。
2. **为什么要显式设置 `desc.depthBufferBits = 0`？**
   - `cameraTargetDescriptor` 默认带有 24 位或 32 位深度模板缓冲格式。如果直接拿它创建后处理临时 RT，会平白多分配一倍的深度显存，并且在移动端 TBDR GPU 上触发不必要的 Depth Tile Load/Store 带宽开销。
3. **为什么用 `ProfilingScope` 包裹指令？**
   - `using (new ProfilingScope(cmd, m_ProfilingSampler))` 会在生成的 GPU 命令流中自动插入调试标记。打开 **Frame Debugger** 或 **RenderDoc** 时，所有平铺的 `Blit` 调用都会折叠归类在 `Custom Kawase Blur` 层级下，一目了然。

---

## 五、深度与法线纹理请求：`ConfigureInput`

如果自定义的 `ScriptableRenderPass` 需要读取相机深度图（`_CameraDepthTexture`）、法线图（`_CameraNormalsTexture`）或是不透明颜色抓取图（`_CameraOpaqueTexture`），**不要手动在 URP Asset 面板里全局强开这些开关**（因为全局开启后，即使当前场景不需要该特效，管线每帧也会额外跑一遍 CopyDepth / DepthNormals Pass）。

正确做法是在 `OnCameraSetup` 中按需调用 `ConfigureInput`：

```csharp
public override void OnCameraSetup(CommandBuffer cmd, ref RenderingData renderingData)
{
    // 按需声明当前 Pass 依赖深度图与法线图；仅当此 Pass 激活时 URP 才会生成对应纹理
    ConfigureInput(ScriptableRenderPassInput.Depth | ScriptableRenderPassInput.Normal);
}
```

| `ScriptableRenderPassInput` 枚举 | 触发的内置前置动作 | Shader 中可直接采样的全局纹理名 |
| :--- | :--- | :--- |
| `None` | 无额外开销 | — |
| `Depth` | 激活 `DepthOnlyPass` 或 `CopyDepthPass` | `_CameraDepthTexture` |
| `Normal` | 激活 `DepthNormalOnlyPass` | `_CameraNormalsTexture` |
| `Color` | 在不透明物体绘制后执行 `CopyColorPass` | `_CameraOpaqueTexture` |
| `Motion` | 激活运动矢量 `MotionVectorRenderPass` | `_MotionVectorTexture` |

---

## 六、URP 性能调优与排查要点

在实际项目中维护 URP 管线时，重点关注以下四个高频性能陷阱：

1. **控制每次 Blit 的全屏带宽消耗**：
   - 在 2K/4K 移动屏上，全屏 `RGBA16Float`（HDR，每像素 8 字节）的一次读写带宽高达数十 MB。对于模糊、泛光（Bloom）、体积光等低频效果，务必先降采样（`downsample = 2` 或 `4`，像素量减少为 `1/4` 或 `1/16`）再迭代计算。
2. **避免不必要的 `CopyColor` 与 `CopyDepth`**：
   - 在 Frame Debugger 中检查是否意外出现了 `CopyColor` 或 `CopyDepth`。在移动端，将 Tile Memory（片上高速缓存）写回系统主存再作为纹理读取（Resolve/Load），会打断 TBDR 块渲染流水线。如果不需要水体折射或软粒子，确保没有任何激活的 Pass 请求 `ScriptableRenderPassInput.Color`。
3. **Shader 变体剔除（Shader Variant Stripping）**：
   - URP 内置 `Lit.shader` 含有大量 `#pragma multi_compile` 关键字（阴影级联、软阴影、光照贴图、雾效、附加光源等），组合后变体可达数万个，导致打包时间暴涨与运行时内存飙升。
   - **工程对策**：在 URP Asset 中关闭未使用的特性（如 Additional Lights Shadow、Soft Shadows），并实现 `IPreprocessShaders.OnProcessShader` 构建期回调，剔除项目不使用的关键字组合。
4. **善用 Frame Debugger 与 RenderDoc 定位合批打断**：
   - 打开 `Window -> Analysis -> Frame Debugger`，点选 `RenderLoopNewBatcher.Draw` 节点，查看右侧的 **Why this draw call can't be batched with the previous one**。最常见的原因是材质球未满足 `UnityPerMaterial` 布局一致，或穿插了使用 `MaterialPropertyBlock` 的渲染器（注意：**SRP Batcher 不兼容 `MaterialPropertyBlock`**，一旦使用 `MaterialPropertyBlock` 会回退为普通 DrawCall，若需大量同网格差异化属性应改用 GPU Instancing）。
