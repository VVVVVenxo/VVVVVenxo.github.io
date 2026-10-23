---
title: 【图形学】现代渲染管线与Shader编程精要
toc: true
categories:
  - 技术笔记
  - 图形学
cover: /img/covers/gen/图形学-现代渲染管线与Shader编程精要.png
date: 2026-10-21
tags:
  - 图形学
  - 渲染管线
  - Shader
  - HLSL
  - URP
  - PBR
description: 梳理实时渲染管线的完整流程：从 CPU 剔除与渲染排序、MVP 坐标空间变换、光栅化插值与 Early-Z，到 Unity URP HLSL 结构、PBR（Cook-Torrance BRDF）光照实现及 GPU 硬件层面的 Shader 性能优化。
---

本文梳理现代实时渲染管线（Real-Time Rendering Pipeline）的完整数据流，包含坐标空间变换原理、光栅化细节、Unity URP（HLSL）PBR 着色器实现，以及基于 GPU 硬件架构的性能优化规范。

---

## 一、渲染管线全流程

实时渲染管线分为三个主要阶段：**应用阶段（CPU）**、**几何阶段（GPU 顶点管线）** 与 **光栅化及逐片元阶段（GPU 像素管线）**。

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. 应用阶段 (CPU)                                                       │
│   视锥剔除 (Frustum Culling) → 渲染排序 (Sorting) → 提交 DrawCall        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼ (CommandBuffer)
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. 几何阶段 (GPU)                                                       │
│   输入装配 (IA) → 顶点着色器 (Vertex Shader) → 齐次裁剪 (Clipping)        │
│   → 透视除法 (NDC) → 视口变换 (Viewport Transform)                       │
└────────────────────────────────────┬────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. 光栅化与逐片元阶段 (GPU)                                             │
│   图元装配与背面剔除 → 三角形遍历与插值 → Early-Z 测试                    │
│   → 片元着色器 (Fragment Shader) → Alpha/模板/深度测试 → 混合 (Blending) │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. 应用阶段（CPU 侧）

在向 GPU 提交绘制指令前，CPU 完成以下工作：

1. **可见性剔除（Culling）**：
   - **视锥体剔除（Frustum Culling）**：判断物体包围盒（AABB / OBB）是否与相机视锥体相交，剔除视野外的物体。
   - **遮挡剔除（Occlusion Culling）**：剔除被其他不透明物体完全挡住的物体。
2. **渲染顺序排序（Sorting）**：
   - **不透明物体（Opaque，Queue <= 2500）**：按**从前向后（Front-to-Back）**排序（结合材质分组以保证合批），配合 GPU 的 **Early-Z** 提前剔除被遮挡的片元。
   - **半透明物体（Transparent，Queue > 2500）**：关闭深度写入（`ZWrite Off`），按**从后向前（Back-to-Front）**排序，保证 Alpha 混合结果正确。
3. **数据绑定与提交**：
   - 将顶点缓冲（VBO）、索引缓冲（IBO）和常量缓冲区（Constant Buffer / CBuffer）绑定到显存，向命令队列提交绘制调用（DrawCall）。

---

## 二、几何阶段：五大坐标空间与矩阵变换

顶点着色器（Vertex Shader）的核心任务是将顶点从模型局部空间变换到齐次裁剪空间。

| 序号 | 坐标空间 | 英文名称 | 变换操作 | 核心用途 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **模型空间** | Object Space | — | 模型自身原点；用于本地顶点偏移（如模型膨胀、旗帜摆动）。 |
| **2** | **世界空间** | World Space | 模型矩阵 `M_model` | 场景统一坐标系；用于计算世界光照方向、高度雾、世界坐标溶解。 |
| **3** | **观察空间** | View Space | 观察矩阵 `M_view` | 以相机为原点；用于计算视角深度、MatCap 采样。 |
| **4** | **齐次裁剪空间** | Clip Space | 投影矩阵 `M_proj` | 顶点着色器输出（`SV_POSITION`）；硬件利用 `[-w, w]` 范围做视锥裁剪。 |
| **5** | **归一化设备坐标** | NDC Space | 透视除法 `(x/w, y/w, z/w)` | 固定管线执行；将坐标映射到标准立方体（DirectX/Metal/现代 Unity 中 `z ∈ [0, 1]`）。 |

### 1. 4D 齐次坐标的作用

三维空间中的 `3x3` 矩阵只能表示旋转和缩放（线性变换），无法表示平移（仿射变换 `p' = R * p + t`）。引入第 4 个分量 `w` 后，可以用统一的 `4x4` 矩阵完成变换：

```text
┌ r00  r01  r02  tx ┐   ┌ x ┐   ┌ r00*x + r01*y + r02*z + tx ┐
│ r10  r11  r12  ty │ * │ y │ = │ r10*x + r11*y + r12*z + ty │
│ r20  r21  r22  tz │   │ z │   │ r20*x + r21*y + r22*z + tz │
└  0    0    0    1 ┘   └ w ┘   └             w              ┘
```

- **空间点（Position）**：设为 `(x, y, z, 1)`，受平移分量 `(tx, ty, tz)` 影响。
- **方向向量（Vector，如法线、切线、光方向）**：设为 `(x, y, z, 0)`，平移分量被 `w = 0` 清零，仅受旋转与缩放影响。

### 2. 法线变换：为什么要乘逆转置矩阵？

当模型发生**非均匀缩放**（例如 X 轴缩放 2 倍，Y 轴不变）时，如果直接用模型矩阵 `M` 乘表面法线 `n`，变换后的法线将不再垂直于表面。

**推导过程**：
设表面切向量为 `t`，法向量为 `n`，两者垂直，满足点积 `transpose(t) * n = 0`。
经过矩阵 `M` 变换后，新切向量为 `t' = M * t`。设法线变换矩阵为 `G`（即 `n' = G * n`），要保持垂直关系：

```text
transpose(t') * n' = transpose(M * t) * (G * n)
                   = transpose(t) * (transpose(M) * G) * n = 0
```

要使上式恒成立，需满足 `transpose(M) * G = I`，即：

```text
G = transpose(inverse(M))
```

- **结论**：法线向量必须乘以模型矩阵的**逆转置矩阵**。
- **代码实现**：在 HLSL 中，列向量右乘转置矩阵等价于行向量左乘原矩阵，因此通常写作 `mul(normalOS, (float3x3)UNITY_MATRIX_I_M)`（即 URP 中 `TransformObjectToWorldNormal` 的内部实现）。仅当模型只含旋转与等比缩放时，才能直接用 `M` 变换法线。

### 3. 透视投影与 Reversed-Z（反向深度缓冲）

透视投影矩阵将视锥体（Frustum）挤压为规则长方体，并将观察空间深度 `-z_view` 写入裁剪坐标的 `w` 分量，供后续硬件执行透视除法。

现代图形 API（DirectX 11/12、Metal、Vulkan）在 Unity 中默认启用 **Reversed-Z**：
- **传统方式**：近平面映射为 `0`，远平面映射为 `1`。由于透视除法后深度 `z_ndc = A + B / z_view` 与距离成反比，绝大部分精度集中在相机极近处，远景容易产生 **Z-Fighting（深度闪烁）**。
- **Reversed-Z**：将**近平面映射为 `1`，远平面映射为 `0`**，配合浮点深度缓冲。浮点数越接近 `0` 指数精度越高，刚好抵消 `1/z` 在远处的精度衰减，大幅提升远景深度精度。

---

## 三、光栅化阶段：透视校正插值与 Early-Z

顶点着色器输出 `SV_POSITION` 后，硬件固定管线依次执行以下步骤：

1. **齐次裁剪与透视除法**：
   - 硬件在除以 `w` 之前，检查顶点是否满足 `-w <= x, y <= w` 且 `0 <= z <= w`。跨边界的三角形会被切割成新的小三角形。
   - 随后硬件执行透视除法 `(x/w, y/w, z/w)` 得到 NDC 坐标，再映射为屏幕像素坐标。
2. **背面剔除（Back-Face Culling）**：
   - 根据屏幕空间三角形三个顶点的环绕顺序（顺时针 CW 或逆时针 CCW），计算二维叉积符号，直接丢弃背向相机的三角形。
3. **重心坐标与透视校正插值**：
   - 光栅化器遍历三角形覆盖的像素，计算像素在三角形内的重心坐标 `(α, β, γ)`（满足 `α + β + γ = 1`）。
   - **透视校正插值**：三维空间中的线性属性投影到二维屏幕后不再是线性的。若直接在屏幕空间对 UV 做线性插值，倾斜表面会出现贴图扭曲。硬件实际对 `属性 / w` 和 `1 / w` 分别做线性插值，再相除还原真实值：

```text
         α * (I0 / w0) + β * (I1 / w1) + γ * (I2 / w2)
I_real = ─────────────────────────────────────────────
         α * (1 / w0)  + β * (1 / w1)  + γ * (1 / w2)
```

4. **Early-Z（提前深度测试）**：
   - 硬件在执行片元着色器**之前**，先对比当前片元深度与深度缓冲（Z-Buffer）。若被前景遮挡则直接丢弃，避免无谓的 Fragment Shader 计算。
   - **导致 Early-Z 失效的操作**：
     1. 片元着色器中使用了 `clip()` 或 `discard`（Alpha Test 镂空材质），硬件无法预先确定该像素是否写入深度；
     2. 片元着色器手动修改并输出了 `SV_Depth`；
     3. 开启 Alpha Blending 半透明混合。

---

## 四、Unity URP (HLSL) 编程结构

Unity URP 使用标准 HLSL 编写着色器，核心结构与底层机制如下：

### 1. 常用寄存器语义（Semantics）

- **顶点输入（`Attributes`）**：
  - `POSITION`：模型空间顶点坐标（`float4`）
  - `NORMAL`：模型空间法线（`float3`）
  - `TANGENT`：模型空间切线（`float4`，`w` 分量存储副切线方向 `±1`）
  - `TEXCOORD0 ~ 7`：UV 通道或自定义顶点数据
  - `COLOR`：顶点色（`float4`）
- **顶点输出 / 片元输入（`Varyings`）**：
  - `SV_POSITION`：齐次裁剪空间坐标（必需）
  - `TEXCOORD0 ~ N`：需插值传递给片元的变量
- **片元输出**：
  - `SV_Target`：写入颜色缓冲区的最终颜色（`half4`）

### 2. SRP Batcher 兼容规范：`UnityPerMaterial`

要让使用相同 Shader、不同材质球的物体支持 **SRP Batcher** 合批，必须将材质属性集中声明在 `UnityPerMaterial` 常量缓冲区中：

```hlsl
CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST;
    half4  _BaseColor;
    half   _Metallic;
    half   _Roughness;
    half   _BumpScale;
CBUFFER_END
```

开启 SRP Batcher 后，材质参数常驻显存 CBuffer。切换材质时 CPU 只需修改缓冲区偏移指针，无需重复绑定 Shader 状态，大幅降低 SetPass Call 开销。

### 3. 切线空间（TBN）与法线贴图解码

法线贴图通常保存在**切线空间（Tangent Space）**中：以表面切线为 X（红）、副切线为 Y（绿）、表面法线为 Z（蓝）。
- 默认法线垂直于表面，即 `(0, 0, 1)`。
- 贴图只能保存 `[0, 1]` 的无符号值，因此存储时按 `pixel = normal * 0.5 + 0.5` 编码，`(0, 0, 1)` 编码后为 `(0.5, 0.5, 1.0)`（呈蓝紫色）。
- 片元着色器采样后，先按 `normalTS = pixel * 2.0 - 1.0` 解码，再乘以由世界空间切线、副切线、法线组成的 **TBN 矩阵**，转回世界空间参与光照计算。

---

## 五、光照模型与 URP PBR 完整实现

### 1. 经验模型与 PBR 模型对比

- **Blinn-Phong 经验模型**：
  - 漫反射：`Lambert = max(0, dot(N, L))`（半兰伯特：`0.5 * dot(N, L) + 0.5`）。
  - 高光反射：引入视线 `V` 与光方向 `L` 的半程向量 `H = normalize(L + V)`，计算 `pow(max(0, dot(N, H)), Gloss)`。
  - **局限**：不满足能量守恒（出射光能量可能超过入射光），无法准确区分金属与非金属的反射特性。

- **Cook-Torrance PBR 微平面模型**：
  基于物理的渲染（PBR）将反射分为漫反射项与镜面反射项，满足能量守恒：

```text
               c_albedo       D(H) * F(V, H) * G(L, V, H)
f(L, V) = kd * ──────── + ─────────────────────────────────
                  π          4 * dot(N, L) * dot(N, V)
```

其中镜面反射分子由 **`D`、`G`、`F` 三个核心函数** 构成：

| 项 | 函数名称 | 工程常用模型 | 作用说明 |
| :---: | :--- | :--- | :--- |
| **`D`** | **法线分布函数**<br>(Normal Distribution) | **Trowbridge-Reitz GGX** | 计算朝向与半程向量 `H` 一致的微平面比例，决定高光光斑的集中程度与边缘衰减。 |
| **`G`** | **几何遮蔽函数**<br>(Geometry Function) | **Smith-Schlick-GGX** | 计算微平面相互遮挡导致的反射能量损耗，避免粗糙表面在掠射角过亮。 |
| **`F`** | **菲涅尔方程**<br>(Fresnel Equation) | **Fresnel-Schlick 近似** | 计算不同视线角度下的反射率（视线越平缓反射越强）。非金属基础反射率 `F0 ≈ 0.04`，金属使用 `Albedo` 作为 `F0` 且漫反射系数 `kd = 0`。 |

### 2. URP 直接光 PBR + 法线贴图完整 Shader

以下代码可直接放入 Unity URP 工程使用，包含完整的顶点变换、TBN 法线解码、Cook-Torrance GGX 直接光与球谐环境光（SH）：

```hlsl
Shader "Custom/URP_DirectPBR_Lit"
{
    Properties
    {
        [MainTexture] _BaseMap("Albedo (RGB)", 2D) = "white" {}
        [MainColor]   _BaseColor("Base Color", Color) = (1, 1, 1, 1)
        [NoScaleOffset] _BumpMap("Normal Map", 2D) = "bump" {}
        _BumpScale("Normal Scale", Range(0.0, 2.0)) = 1.0
        _Metallic("Metallic", Range(0.0, 1.0)) = 0.0
        _Roughness("Roughness", Range(0.04, 1.0)) = 0.5
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Opaque"
            "Queue" = "Geometry"
        }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }

            Cull Back
            ZWrite On
            ZTest LEqual

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS   : NORMAL;
                float4 tangentOS  : TANGENT;
                float2 uv         : TEXCOORD0;
            };

            struct Varyings
            {
                float4 positionCS  : SV_POSITION;
                float2 uv          : TEXCOORD0;
                float3 positionWS  : TEXCOORD1;
                half3  normalWS    : TEXCOORD2;
                half3  tangentWS   : TEXCOORD3;
                half3  bitangentWS : TEXCOORD4;
            };

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            TEXTURE2D(_BumpMap); SAMPLER(sampler_BumpMap);

            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4  _BaseColor;
                half   _BumpScale;
                half   _Metallic;
                half   _Roughness;
            CBUFFER_END

            Varyings vert(Attributes input)
            {
                Varyings output;
                VertexPositionInputs posInputs = GetVertexPositionInputs(input.positionOS.xyz);
                VertexNormalInputs normInputs  = GetVertexNormalInputs(input.normalOS, input.tangentOS);

                output.positionCS  = posInputs.positionCS;
                output.positionWS  = posInputs.positionWS;
                output.uv          = TRANSFORM_TEX(input.uv, _BaseMap);
                output.normalWS    = normInputs.normalWS;
                output.tangentWS   = normInputs.tangentWS;
                output.bitangentWS = normInputs.bitangentWS;
                return output;
            }

            // D: GGX 法线分布函数
            float DistributionGGX(float NdotH, float roughness)
            {
                float a  = roughness * roughness;
                float a2 = a * a;
                float denom = NdotH * NdotH * (a2 - 1.0) + 1.0;
                return a2 / max(PI * denom * denom, 1e-6);
            }

            // G: Schlick-GGX 几何遮蔽函数
            float GeometrySchlickGGX(float NdotV, float roughness)
            {
                float r = roughness + 1.0;
                float k = (r * r) / 8.0;
                return NdotV / max(NdotV * (1.0 - k) + k, 1e-5);
            }

            float GeometrySmith(float NdotV, float NdotL, float roughness)
            {
                return GeometrySchlickGGX(NdotV, roughness) * GeometrySchlickGGX(NdotL, roughness);
            }

            // F: Fresnel-Schlick 近似
            half3 FresnelSchlick(float HdotV, half3 F0)
            {
                return F0 + (1.0h - F0) * pow(saturate(1.0 - HdotV), 5.0);
            }

            half4 frag(Varyings input) : SV_Target
            {
                half4 albedoSample = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;
                half3 albedo = albedoSample.rgb;

                half4 packedNormal = SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, input.uv);
                half3 normalTS = UnpackNormalScale(packedNormal, _BumpScale);

                half3x3 TBN = half3x3(input.tangentWS, input.bitangentWS, input.normalWS);
                float3 N = normalize(mul(normalTS, TBN));
                float3 V = GetWorldSpaceNormalizeViewDir(input.positionWS);

                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                float3 L = normalize(mainLight.direction);
                float3 H = normalize(V + L);

                float NdotL = max(dot(N, L), 0.0);
                float NdotV = max(dot(N, V), 1e-4);
                float NdotH = max(dot(N, H), 0.0);
                float HdotV = max(dot(H, V), 0.0);

                half3 F0 = lerp(half3(0.04, 0.04, 0.04), albedo, _Metallic);

                float D = DistributionGGX(NdotH, _Roughness);
                float G = GeometrySmith(NdotV, NdotL, _Roughness);
                half3 F = FresnelSchlick(HdotV, F0);

                half3 specular = (D * G * F) / (4.0 * NdotV * NdotL + 1e-5);

                half3 kS = F;
                half3 kD = (1.0h - kS) * (1.0h - _Metallic);
                half3 diffuse = kD * albedo * INV_PI;

                half3 radiance = mainLight.color * (mainLight.distanceAttenuation * mainLight.shadowAttenuation);
                half3 directLighting = (diffuse + specular) * radiance * NdotL;
                half3 ambientSH = SampleSH(N) * albedo * kD;

                return half4(directLighting + ambientSH, 1.0h);
            }
            ENDHLSL
        }
    }
}
```

---

## 六、GPU 硬件执行特性与 Shader 优化规范

### 1. SIMT 架构与动态分支发散（Branch Divergence）

GPU 采用 **SIMT（单指令多线程）** 架构，将 32 个线程（NVIDIA Warp）或 64 个线程（AMD Wavefront）编为一组，**同一组线程在同一时钟周期必须执行相同的指令**。

```hlsl
// 动态分支：同一 Warp 内不同像素可能进入不同分支
if (noiseValue > 0.5) {
    color = BranchA();
} else {
    color = BranchB();
}
```

如果同一个 Warp 内的线程条件判断不一致（部分为真、部分为假）：
1. 硬件先屏蔽不满足条件的线程，执行 `BranchA()`；
2. 再反转掩码，执行 `BranchB()`；
3. **总耗时等于两个分支耗时之和**，且双分支所需的寄存器数量增加，导致 GPU SM 单元能同时驻留的活跃 Warp 数量（Occupancy）下降。

**优化方式**：
- 简单条件逻辑用内置函数替代：`step()`、`smoothstep()`、`lerp()`、`saturate()`、`abs()`。
- 材质静态功能开关使用 `#pragma shader_feature_local` 编译期宏变体。

### 2. `2x2` 像素块（Quad）与 Mipmap 偏导数

片元着色器的最小调度单位不是单个像素，而是 **`2x2` 像素块（Quad）**。如果一个三角形只覆盖了 1 个像素，硬件仍会补齐 3 个辅助像素（Helper Lanes）一起执行片元着色器，最后丢弃辅助像素的结果。

- **原因**：硬件需要通过同一个 `2x2` Quad 内相邻像素的 UV 差值，计算屏幕空间偏导数 `ddx(uv)` 和 `ddy(uv)`，从而确定当前像素对应的纹素跨度，自动选择正确的 **Mipmap 层级**。
- **工程影响**：当高模未做 LOD、在远景形成大量面积仅有 1~2 像素的**极小三角形（Micro-triangles）**时，高达 50%~75% 的片元算力会浪费在辅助像素上（即 **Quad Overdraw**）。

### 3. 工程优化清单

1. **计算前移至顶点着色器**：顶点数通常远少于片元数。低频变化量（如线性雾效因子、顶点球谐光、固定 UV 偏移）应在 `vert` 中计算并通过插值传给 `frag`。
2. **合理选择数据类型精度**：
   - `float`（32-bit）：用于空间位置坐标和 UV 坐标（防止大坐标或 UV 滚动时出现精度抖动）。
   - `half`（16-bit，范围 `±65504`）：用于单位方向向量、颜色、光照计算。移动端 GPU 上 `half` 占用一半寄存器带宽，ALU 吞吐率更高。
3. **合并纹理通道（Channel Packing）**：将 `Metallic`（R）、`AO`（G）、`Detail`（B）、`Smoothness`（A）合并到一张贴图的四个通道中，将 4 次纹理采样降为 1 次，减少带宽消耗。
4. **指令层面的代数优化**：
   - **标量与向量连乘时先乘标量**：`(scalarA * scalarB) * vector3C` 只需 4 次乘法，而 `scalarA * vector3C * scalarB` 需要 6 次乘法。
   - **利用 MAD（乘加融合）指令**：GPU 支持单周期完成 `a * b + c`，因此将 `(x + a) * b` 展开为 `x * b + a * b`（当 `a, b` 为常量时）可减少指令数。
5. **移动端 TBDR 架构避坑**：移动 GPU（Mali、Adreno、Apple GPU）普遍采用 **TBDR（Tile-Based Deferred Rendering）** 架构，内置硬件级隐藏面消除（HSR）。对不透明物体应避免滥用 `clip() / discard`，否则会打断 HSR 提前剔除流程，导致管线回退与发热。
