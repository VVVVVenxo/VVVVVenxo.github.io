---
title: 【图形学】现代渲染管线与Shader编程精要
toc: true
mathjax: true
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
description: 系统梳理现代实时图形渲染管线的完整数据流：从 CPU 应用阶段的剔除与合批、MVP 坐标空间变换矩阵推导、透视除法与重心坐标插值，到 GPU SIMT 架构下的 Shader 编程精要、PBR（Cook-Torrance BRDF）光照模型实现，以及 Early-Z、Overdraw 与分支发散等核心性能调优准则。
---

在游戏客户端开发中，无论是排查一个材质表现异常、编写一个自定义后处理效果，还是定位移动端的 GPU 帧率瓶颈，最终都会回到同一个底层基石——**现代实时渲染管线（Real-Time Rendering Pipeline）与可编程着色器（Shader）**。

很多初学者在写 Shader 时容易陷入「背公式、抄节点」的误区：知道要把顶点乘上 `UNITY_MATRIX_MVP`（或 URP 的 `TransformObjectToHClip`），却不清楚齐次坐标的 $w$ 分量究竟在什么时候发挥作用；知道片元着色器里尽量少写 `if-else`，却不明白 GPU 的 Warp/Wavefront 锁步执行机制为什么会导致耗时翻倍。

本文按 **「硬件管线全链路 → 五大坐标空间与数学推导 → 光栅化与重心插值 → HLSL/URP Shader 编程实战 → 经典光照模型与 PBR → GPU 硬件架构与 Shader 性能优化」** 的工程脉络，将现代渲染管线与 Shader 编程的核心精要彻底讲透。

---

## 一、现代实时渲染管线全貌：从 3D 数据到屏幕像素

在《Real-Time Rendering》的经典划分中，实时渲染管线在宏观上分为三大阶段：**应用阶段（Application Stage）**、**几何阶段（Geometry Stage）** 与 **光栅化阶段（Rasterization Stage）**（现代管线常将逐片元操作独立为第四阶段 **逐片元合并阶段 Output-Merger**）。

```
┌───────────────────────────────────────────────────────────────────────────┐
│ 1. 应用阶段 (CPU 主导)                                                     │
│   场景图遍历 → 视锥体剔除 (Frustum Culling) → 渲染排序 → 打包 CBuffer/DrawCall │
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼ (通过命令缓冲区 CommandBuffer 提交至 GPU)
┌───────────────────────────────────────────────────────────────────────────┐
│ 2. 几何阶段 (GPU 顶点管线)                                                 │
│   输入装配 (IA) → 【顶点着色器 Vertex Shader】 → (曲面细分/几何着色器)       │
│   → 齐次裁剪 (Clipping) → 透视除法 (NDC) → 屏幕视口映射 (Viewport Transform)│
└─────────────────────────────────────┬─────────────────────────────────────┘
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ 3. 光栅化与片元阶段 (GPU 像素管线)                                         │
│   三角形设置与遍历 → 透视校正插值 → Early-Z 提前深度测试                    │
│   → 【片元着色器 Fragment Shader】 → Alpha 测试 / 模板测试 / 深度测试       │
│   → 颜色混合 (Blending) → 写入帧缓冲 (FrameBuffer / RenderTarget)          │
└───────────────────────────────────────────────────────────────────────────┘
```

### 1. 应用阶段（CPU 侧）：决定「画什么」与「怎么交接」

在 GPU 真正开始干活之前，CPU 必须完成一帧的渲染准备工作：

1. **可见性剔除（Culling）**：
   - **视锥体剔除（Frustum Culling）**：利用相机的六个裁剪平面与物体包围盒（AABB / OBB）求交，剔除视野外的物体。
   - **遮挡剔除（Occlusion Culling）**：剔除被墙体或大型建筑完全挡住的物体（预计算 PVS 或 GPU Hi-Z 层次深度剔除）。
2. **渲染状态分类与排序（Sorting）**：
   - **不透明物体（Opaque，Queue $\le$ 2500）**：按 **从前向后（Front-to-Back）** 排序（结合材质/Shader 分组以保证 SRP Batcher 合批），最大化触发 **Early-Z** 剔除被遮挡像素。
   - **半透明物体（Transparent，Queue $>$ 2500）**：关闭深度写入（`ZWrite Off`），严格按 **从后向前（Back-to-Front，画家算法）** 排序，确保 Alpha 混合顺序正确。
3. **数据绑定与 DrawCall 提交**：
   - 将网格顶点数据（VBO/IBO：坐标、法线、切线、UV、顶点色）与常量缓冲区（Constant Buffer / Uniform：材质参数、变换矩阵、光源信息）绑定到显存，向命令队列压入渲染指令（如 `DrawIndexedPrimitive`）。

---

## 二、几何阶段核心：五大坐标空间与矩阵变换推导

顶点着色器（Vertex Shader）最核心的职责，就是把顶点从模型自身的局部坐标系，一步步变换到相机的齐次裁剪空间。理解这 **5 个坐标空间** 与 **4 次变换** 是写好一切空间特效（如世界坐标溶解、屏幕空间 UV、法线贴图、边缘光）的前提。

| 序号 | 坐标空间 | 英文名称 | 变换矩阵 / 操作 | 核心几何意义与工程用途 |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **模型空间** | Object / Model Space | —（建模导出原点） | 以模型自身枢轴为原点；常用于做模型本地顶点动画（如旗帜飘动、呼吸膨胀）。 |
| **2** | **世界空间** | World Space | $\mathbf{M}_{\text{model}}$（缩放 $\to$ 旋转 $\to$ 平移） | 全场景统一坐标系；用于计算世界光照方向、世界高度雾、平面反射、距离场交互。 |
| **3** | **观察空间** | View / Camera Space | $\mathbf{M}_{\text{view}}$（相机逆变换） | 以相机为原点（OpenGL/Unity 观察空间右手系，$-Z$ 为相机正前方）；用于计算视角深度、MatCap 采样。 |
| **4** | **齐次裁剪空间** | Clip Space | $\mathbf{M}_{\text{proj}}$（正交或透视投影） | 顶点着色器输出（`SV_POSITION`）所在空间；利用 $[-w, w]$ 边界直接做图元视锥裁剪。 |
| **5** | **归一化设备坐标** | NDC Space | 透视除法（$(x/w, y/w, z/w)$） | 固定管线自动执行；将可视范围规整到标准立方体（OpenGL 为 $[-1,1]^3$，DirectX/Metal/现代 Unity 深度 $z \in [0,1]$）。 |

### 1. 为什么 3D 渲染必须使用 4D 齐次坐标（Homogeneous Coordinates）？

在三维空间中，$3 \times 3$ 矩阵只能表示**线性变换**（旋转、缩放、切变），无法表示**平移（Translation）**（因为平移是仿射变换 $\mathbf{p}' = \mathbf{R}\mathbf{p} + \mathbf{t}$）。

引入第 4 个分量 $w$ 后：
- **空间点（Position）** 表示为 $(x, y, z, 1)^T$ —— 受平移影响；
- **方向向量（Vector，如法线、切线、光线方向）** 表示为 $(x, y, z, 0)^T$ —— 乘上 $4 \times 4$ 矩阵时平移分量被 $w=0$ 自动清零，只受旋转和缩放影响！

$$
\begin{bmatrix}
r_{00} & r_{01} & r_{02} & t_x \\
r_{10} & r_{11} & r_{12} & t_y \\
r_{20} & r_{21} & r_{22} & t_z \\
0 & 0 & 0 & 1
\end{bmatrix}
\begin{bmatrix}
x \\ y \\ z \\ 1
\end{bmatrix}
=
\begin{bmatrix}
r_{00}x + r_{01}y + r_{02}z + t_x \\
r_{10}x + r_{11}y + r_{12}z + t_y \\
r_{20}x + r_{21}y + r_{22}z + t_z \\
1
\end{bmatrix}
$$

### 2. 法线变换陷阱：为什么法线不能直接乘 $\mathbf{M}_{\text{model}}$？

这是图形学面试与实战的必考题：**当模型发生非均匀缩放（Non-uniform Scaling，例如 $x$ 轴拉伸 2 倍，$y$ 轴不变）时，如果直接用模型矩阵 $\mathbf{M}$ 乘以表面法线 $\mathbf{n}$，变换后的法线将不再垂直于变换后的表面！**

**数学推导**：
设表面切向量为 $\mathbf{t}$，法向量为 $\mathbf{n}$，两者正交，即内积 $\mathbf{t}^T \mathbf{n} = 0$。
经过矩阵 $\mathbf{M}$ 变换后，新切向量为 $\mathbf{t}' = \mathbf{M}\mathbf{t}$。假设法线变换矩阵为 $\mathbf{G}$（即 $\mathbf{n}' = \mathbf{G}\mathbf{n}$），为了保持正交性，必须满足：

$$
(\mathbf{t}')^T \mathbf{n}' = (\mathbf{M}\mathbf{t})^T (\mathbf{G}\mathbf{n}) = \mathbf{t}^T (\mathbf{M}^T \mathbf{G}) \mathbf{n} = 0
$$

要使上式对任意正交的 $\mathbf{t}, \mathbf{n}$ 恒成立，中间项必须为单位矩阵 $\mathbf{I}$：

$$
\mathbf{M}^T \mathbf{G} = \mathbf{I} \implies \mathbf{G} = (\mathbf{M}^{-1})^T
$$

> **核心结论**：法线向量必须乘以模型变换矩阵的**逆转置矩阵（Inverse Transpose Matrix）**。在 HLSL 中，等价技巧是用向量左乘逆矩阵：`mul(normalOS, (float3x3)UNITY_MATRIX_I_M)`（这也是 URP `TransformObjectToWorldNormal` 的内部实现）。只有当模型仅包含旋转和等比缩放（正交矩阵 $\mathbf{M}^T = \mathbf{M}^{-1}$）时，才能直接用 $\mathbf{M}$ 变换法线。

### 3. 透视投影矩阵与 Reversed-Z（反向深度缓冲）

透视投影（Perspective Projection）会产生「近大远小」的视觉效果，其本质是将平截头体（Frustum）挤压成一个长方体，并把观察空间下的深度 $-z_e$ 存入齐次坐标的 $w_{\text{clip}}$ 分量中，供后续硬件做**透视除法（除以 $w_{\text{clip}}$）**。

在现代渲染引擎（包括 Unity 5.5+ 在 DirectX 11/12、Metal、Vulkan 等平台）中，普遍采用了 **Reversed-Z（反向 Z 缓冲）** 技术：
- **传统深度映射**：近裁剪面 $n \to 0$，远裁剪面 $f \to 1$。由于透视除法后深度 $z_{\text{ndc}} = A + B/z_e$ 是典型的反比例函数，90% 以上的深度精度都堆积在离相机极近的区域，远处物体极易发生 **Z-Fighting（深度冲突闪烁）**。
- **Reversed-Z 映射**：将**近裁剪面映射为 $1$，远裁剪面映射为 $0$**（配合 32 位浮点深度缓冲），刚好让反比例曲线的稀疏区与浮点数在接近 $0$ 处的高指数精度相抵消，使整个视锥体内的深度分布精度提升数个数量级！

---

## 三、光栅化阶段：图元装配、透视校正插值与 Early-Z

当顶点着色器输出裁剪空间坐标 `SV_POSITION` 后，硬件固定管线接管并完成以下关键步骤：

1. **齐次裁剪（Clipping）与透视除法**：
   - 在除以 $w$ 之前，硬件先检查顶点是否满足 $-w \le x, y, z \le w$（或 $0 \le z \le w$）。如果有三角形跨过视锥边界，硬件会在齐次空间将其切割成新的小三角形（避免 $w \le 0$ 导致除零或坐标翻转）。
   - 随后硬件执行透视除法 $(x/w, y/w, z/w)$ 得到 NDC 坐标，再根据屏幕宽高像素 `(ScreenWidth, ScreenHeight)` 映射为屏幕像素坐标。
2. **背面剔除（Back-Face Culling）**：
   - 利用屏幕空间三角形三个顶点的二维叉积符号（环绕顺序 Winding Order：顺时针 CW 或逆时针 CCW），直接丢弃背对相机的三角形，瞬间砍掉约一半的网格片元开销。
3. **三角形遍历与重心坐标插值（Barycentric Interpolation）**：
   - 光栅化器扫描被三角形覆盖的像素中心（或 MSAA 子采样点），计算每个像素在三角形内的重心坐标 $(\alpha, \beta, \gamma)$（满足 $\alpha + \beta + \gamma = 1$）。
   - **透视校正插值（Perspective-Correct Interpolation）**：注意！**屏幕空间的二维重心坐标在三维空间中并不是线性的**！如果直接对屏幕空间的 UV 或深度做线性插值，贴图在倾斜表面会出现明显的折痕扭曲。硬件实际执行的是对属性除以观察空间深度 $Z$（即 $1/w$）进行线性插值，再除以插值后的 $1/w$ 还原：

$$
I_p = \frac{\alpha \frac{I_0}{w_0} + \beta \frac{I_1}{w_1} + \gamma \frac{I_2}{w_2}}{\alpha \frac{1}{w_0} + \beta \frac{1}{w_1} + \gamma \frac{1}{w_2}}
$$

4. **Early-Z（提前深度测试）机制与失效场景**：
   - 现代 GPU 会在运行昂贵的片元着色器**之前**，先用光栅化插值出的片元深度与当前深度缓冲（Z-Buffer）做对比。如果该片元已经被前面的不透明物体挡住，硬件直接丢弃该片元，跳过 Fragment Shader！
   - **哪些操作会导致 Early-Z 失效（退化为 Late-Z）？**
     1. 在片元着色器中调用了 `clip()` 或 `discard`（即 **Alpha Test 镂空材质**，如草叶、铁丝网）：因为硬件在跑完 Fragment Shader 之前不知道这个像素会不会被丢弃，无法提前更新深度缓冲。
     2. 在片元着色器中手动修改并输出了 `SV_Depth`。
     3. 开启了 Alpha Blending 半透明混合且乱序绘制。

---

## 四、Shader 编程精要：以 Unity URP (HLSL) 为例

在 Unity URP（Universal Render Pipeline）中，官方全面采用标准的 **HLSL（High-Level Shading Language）** 替代了 Built-in 管线时代的 CG 宏。下面我们拆解一个工程级 URP Shader 的标准骨架与底层通信语义。

### 1. 渲染状态指令与语义绑定（Semantics）

CPU 与 GPU 各个阶段之间通过**语义（Semantics）**进行寄存器绑定：

- **应用阶段 $\to$ 顶点着色器（`Attributes`）**：
  - `POSITION`：模型空间顶点坐标（`float4`）
  - `NORMAL`：模型空间顶点法线（`float3`）
  - `TANGENT`：模型空间顶点切线（`float4`，其中 `w` 分量存储副切线方向 $\pm 1$）
  - `TEXCOORD0 ~ TEXCOORD7`：第 0~7 套 UV 通道或自定义逐顶点数据
  - `COLOR`：顶点颜色（`float4`，常用于烘焙遮罩或风吹摆动权重）
- **顶点着色器 $\to$ 片元着色器（`Varyings`）**：
  - `SV_POSITION`（System Value Position）：**必选**，告诉光栅化器这是齐次裁剪空间坐标。
  - `TEXCOORD0 ~ N`：任意需要经过重心插值传递给片元的变量（世界坐标、世界法线、UV、雾效因子等）。
- **片元着色器 $\to$ 输出合并阶段**：
  - `SV_Target`（或 MRT 多渲染目标下的 `SV_Target0`, `SV_Target1`）：输出最终颜色 `half4` 到颜色缓冲区。

### 2. SRP Batcher 兼容性核心：`CBUFFER_START(UnityPerMaterial)`

在 URP 中，想要让不同材质球但使用同一个 Shader 的物体实现极致的 CPU 提交优化（**SRP Batcher**），必须将所有在 `Properties` 中声明的标量/向量材质属性包裹在名为 `UnityPerMaterial` 的常量缓冲区（Constant Buffer）中：

```hlsl
CBUFFER_START(UnityPerMaterial)
    float4 _BaseMap_ST;
    half4  _BaseColor;
    half   _Metallic;
    half   _Smoothness;
    half   _BumpScale;
CBUFFER_END
```

这样当切换材质时，CPU 无需重新绑定整个 Shader 状态，只需切换指向显存中预存的 `UnityPerMaterial` 缓冲区指针，从而大幅削减 SetPass Call 的 CPU 开销。

### 3. 切线空间（Tangent Space）与法线贴图（Normal Mapping）解码

为什么游戏里的法线贴图整体呈现**蓝紫色**？
- 法线贴图通常存储在**切线空间（TBN Space）**中：以顶点所在表面切线为 $T$（X 轴，红）、副切线为 $B$（Y 轴，绿）、表面法线为 $N$（Z 轴，蓝）。
- 因为绝大多数凹凸法线都朝向表面外侧，即切线空间下法向量主要集中在 $(0, 0, 1)$ 附近。
- 纹理像素只能存储 $[0, 1]$ 范围的无符号值，因此需要将 $[-1, 1]$ 的法向量通过 $\text{Pixel} = \frac{\mathbf{n} + 1}{2}$ 映射存储。于是 $(0, 0, 1)$ 映射后就是 $(0.5, 0.5, 1.0)$——即 RGB 下的蓝紫色！

在 Shader 中采样法线贴图后，需要执行逆映射 $\mathbf{n}_{\text{tangent}} = 2 \cdot \text{Pixel} - 1$，再左乘由顶点法线、切线、副切线构成的 **TBN 正交矩阵**，将其变换回世界空间参与光照计算：

$$
\mathbf{n}_{\text{world}} = \text{normalize}\left(
\begin{bmatrix} \mathbf{T}_w & \mathbf{B}_w & \mathbf{N}_w \end{bmatrix}
\begin{bmatrix} n_x \\ n_y \\ n_z \end{bmatrix}_{\text{tangent}}
\right)
$$

---

## 五、经典经验光照与现代 PBR（基于物理的渲染）完整实现

### 1. 从兰伯特（Lambert）到 Blinn-Phong 经验模型

早期的实时渲染使用经验模型拆解光照：

$$\mathbf{L}_{\text{out}} = \mathbf{L}_{\text{ambient}} + \mathbf{L}_{\text{diffuse}} + \mathbf{L}_{\text{specular}}$$

1. **Lambert 漫反射**：光强与表面法线 $\mathbf{n}$ 和光线方向 $\mathbf{l}$ 的夹角余弦成正比，即 $\max(0, \mathbf{n} \cdot \mathbf{l})$（工程上常用 **Half-Lambert 半兰伯特** $0.5(\mathbf{n} \cdot \mathbf{l}) + 0.5$ 提亮背光暗部，广泛用于二次元卡通渲染）。
2. **Blinn-Phong 高光反射**：引入视线方向 $\mathbf{v}$ 与光线方向 $\mathbf{l}$ 的角平分线——**半程向量（Halfway Vector）** $\mathbf{h} = \text{normalize}(\mathbf{l} + \mathbf{v})$，用 $(\max(0, \mathbf{n} \cdot \mathbf{h}))^{\text{Gloss}}$ 模拟高光斑（比传统 Phong 的反射向量 $\mathbf{r} \cdot \mathbf{v}$ 计算更快且在掠射角无断层）。

然而，Blinn-Phong 不满足**能量守恒（Energy Conservation）**（出射光总能量可能大于入射光，导致高光过曝发飘），也无法真实表现金属与非金属在不同粗糙度下的菲涅尔反射变化。

### 2. 现代 PBR 核心：微平面理论与 Cook-Torrance BRDF

现代游戏引擎（Unity URP Lit、UE5 DefaultLit）均采用基于微平面理论（Microfacet Theory）的 **Cook-Torrance 双向反射分布函数（BRDF）**。渲染方程中的反射项由漫反射 $f_{\text{lambert}}$ 与镜面反射 $f_{\text{cook-torrance}}$ 组成：

$$
f_r(\mathbf{l}, \mathbf{v}) = k_d \frac{\mathbf{c}_{\text{albedo}}}{\pi} + \frac{D(\mathbf{h}) \, F(\mathbf{v}, \mathbf{h}) \, G(\mathbf{l}, \mathbf{v}, \mathbf{h})}{4 (\mathbf{n} \cdot \mathbf{l}) (\mathbf{n} \cdot \mathbf{v})}
$$

其中分子上的 **$D, G, F$ 三大核心函数** 各司其职：

| 项 | 名称 | 常用工业界解析式 | 物理几何含义 |
| :---: | :--- | :--- | :--- |
| **$D(\mathbf{h})$** | **法线分布函数**<br>(Normal Distribution Function) | **Trowbridge-Reitz GGX**：<br>$D_{\text{GGX}} = \frac{\alpha^2}{\pi ((\mathbf{n}\cdot\mathbf{h})^2 (\alpha^2 - 1) + 1)^2}$ | 统计学上朝向恰好与半程向量 $\mathbf{h}$ 一致的微平面比例；粗糙度 $\alpha = \text{roughness}^2$ 越小，高光越锐利集中，且 GGX 拥有极其自然的柔和长尾光晕。 |
| **$G(\mathbf{l},\mathbf{v},\mathbf{h})$** | **几何遮蔽函数**<br>(Geometry Function) | **Smith-Schlick-GGX**：<br>$G = G_1(\mathbf{n},\mathbf{l},k) \cdot G_1(\mathbf{n},\mathbf{v},k)$ | 模拟微平面凹凸之间互相遮挡入射光（Shadowing）或反射光（Masking）导致的能量衰减，防止粗糙表面在掠射角过亮。 |
| **$F(\mathbf{v},\mathbf{h})$** | **菲涅尔方程**<br>(Fresnel Equation) | **Fresnel-Schlick 近似**：<br>$F = F_0 + (1 - F_0)(1 - (\mathbf{h}\cdot\mathbf{v}))^5$ | 描述不同观察角度下的反射率变化：视线越贴近表面（掠射角 $\mathbf{h}\cdot\mathbf{v} \to 0$），反射越强。电介质基础反射率 $F_0 \approx 0.04$，金属则由反照率 $\text{Albedo}$ 决定 $F_0$ 且无漫反射（$k_d = (1 - F)(1 - \text{metallic})$）。 |

### 3. 完整实战：编写一个包含法线贴图、直接光 PBR 与环境光的 URP Shader

下面是一个可以直接放入 Unity URP 工程运行的完整单 Pass PBR Shader，清晰展示了从顶点变换、TBN 矩阵构建到 Cook-Torrance GGX 计算的全过程：

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

            // 遵循 SRP Batcher 规范的材质常量缓冲区
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                half4  _BaseColor;
                half   _BumpScale;
                half   _Metallic;
                half   _Roughness;
            CBUFFER_END

            // 1. 顶点着色器：完成空间变换与 TBN 正交基构建
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

            // --- Cook-Torrance BRDF 三大核心函数 ---
            // D: Trowbridge-Reitz GGX 法线分布
            float DistributionGGX(float NdotH, float roughness)
            {
                float a  = roughness * roughness;
                float a2 = a * a;
                float denom = (NdotH * NdotH * (a2 - 1.0) + 1.0);
                return a2 / max(PI * denom * denom, 1e-6);
            }

            // G: Schlick-GGX 几何遮蔽
            float GeometrySchlickGGX(float NdotV, float roughness)
            {
                float r = roughness + 1.0;
                float k = (r * r) / 8.0; // 直接光下的重映射 k
                return NdotV / max(NdotV * (1.0 - k) + k, 1e-5);
            }

            float GeometrySmith(float NdotV, float NdotL, float roughness)
            {
                return GeometrySchlickGGX(NdotV, roughness) * GeometrySchlickGGX(NdotL, roughness);
            }

            // F: Fresnel-Schlick 近似
            half3 FresnelSchlick(float HdotV, half3 F0)
            {
                return F0 + (1.0h - F0) * pow( saturate(1.0 - HdotV), 5.0 );
            }

            // 2. 片元着色器：法线采样、BRDF 积分与环境球谐光
            half4 frag(Varyings input) : SV_Target
            {
                // 采样反照率与切线空间法线
                half4 albedoSample = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, input.uv) * _BaseColor;
                half3 albedo = albedoSample.rgb;

                half4 packedNormal = SAMPLE_TEXTURE2D(_BumpMap, sampler_BumpMap, input.uv);
                half3 normalTS = UnpackNormalScale(packedNormal, _BumpScale);

                // TBN 矩阵将法线从切线空间变换到世界空间
                half3x3 TBN = half3x3(input.tangentWS, input.bitangentWS, input.normalWS);
                float3 N = normalize(mul(normalTS, TBN));
                float3 V = GetWorldSpaceNormalizeViewDir(input.positionWS);

                // 获取主光源信息与阴影衰减
                float4 shadowCoord = TransformWorldToShadowCoord(input.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                float3 L = normalize(mainLight.direction);
                float3 H = normalize(V + L);

                float NdotL = max(dot(N, L), 0.0);
                float NdotV = max(dot(N, V), 1e-4);
                float NdotH = max(dot(N, H), 0.0);
                float HdotV = max(dot(H, V), 0.0);

                // 计算基础反射率 F0：非金属固定约 0.04，金属使用 Albedo
                half3 F0 = lerp(half3(0.04, 0.04, 0.04), albedo, _Metallic);

                // Cook-Torrance 镜面反射项
                float  D = DistributionGGX(NdotH, _Roughness);
                float  G = GeometrySmith(NdotV, NdotL, _Roughness);
                half3  F = FresnelSchlick(HdotV, F0);

                half3 numerator   = D * G * F;
                float denominator = 4.0 * NdotV * NdotL + 1e-5;
                half3 specular    = numerator / denominator;

                // 能量守恒：漫反射比例 kd = (1 - F) * (1 - metallic)
                half3 kS = F;
                half3 kD = (1.0h - kS) * (1.0h - _Metallic);
                half3 diffuse = kD * albedo * INV_PI;

                // 直接光辐射照度贡献 + 球谐环境光 (SH)
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

## 六、GPU 硬件执行模型与 Shader 性能优化黄金法则

写得出效果只是第一步，在商业项目（尤其是移动端 TBDR 架构 GPU，如 Mali、Adreno、Apple A/M 系列）中，不懂 GPU 硬件特性的 Shader 极易引发严重的帧率跳水与发热降频。

### 1. SIMT 架构（Warp / Wavefront）与动态分支发散

为什么 GPU 能同时处理几百万个像素，却极度害怕复杂的 `if-else`？

- **CPU（MIMD）**：擅长复杂控制流，拥有强大的分支预测器（Branch Predictor）、乱序执行与大容量的 L1/L2/L3 缓存，核心数量少但单核逻辑极强。
- **GPU（SIMT，单指令多线程）**：将大量算术逻辑单元（ALU）编组调度。NVIDIA 将 **32 个线程** 编为一个 **Warp**（AMD 为 64 线程的 Wavefront，移动端 Mali 为 16 线程等）。**同一个 Warp 内的所有线程在同一时钟周期必须执行完全相同的指令（锁步执行 Lock-step）！**

当片元着色器中出现基于采样结果或空间坐标的动态分支时：

```hlsl
// 危险：同一 2x2 像素块或同一个 Warp 内不同像素走向不同分支
if (noiseValue > 0.5) {
    color = ExpensiveBranchA(); // 分支 A
} else {
    color = ExpensiveBranchB(); // 分支 B
}
```

如果同一个 Warp 里的 32 个像素，有 20 个满足 `noiseValue > 0.5`，另外 12 个不满足，就会发生 **分支发散（Branch Divergence）**：
1. GPU 先遮蔽（Mask out）那 12 个线程，让前 20 个线程执行 `ExpensiveBranchA()`（那 12 个线程干等着空转）；
2. 接着再反转掩码，遮蔽前 20 个线程，让后 12 个线程执行 `ExpensiveBranchB()`；
3. **最终整个 Warp 的耗时等于两个分支耗时之和（$T_A + T_B$）！** 不仅如此，为了保存两套分支的临时变量，Shader 占用的通用寄存器（VGPR）数量激增，直接导致 GPU SM 单元能同时驻留的活跃 Warp 数量（**Occupancy 占用率**）断崖式下跌，无法隐藏纹理采样的内存延迟。

> **优化对策**：
> - 用无分支内置代数函数替代简单的 `if-else`：例如用 `step(edge, x)`、`smoothstep()`、`lerp(a, b, t)`、`saturate()`、`abs()`。
> - 如果必须根据材质功能开关走不同逻辑，使用编译期宏 `#pragma shader_feature_local` 生成静态变体，而不是运行时动态分支。

### 2. $2 \times 2$ 像素块（Quad）、偏导数（`ddx` / `ddy`）与 Mipmap 原理

GPU 在光栅化并调度片元着色器时，最小执行粒度并不是 1 个像素，而是 **$2 \times 2$ 的像素块（Quad，共 4 个像素）**。哪怕一个细长三角形只覆盖了 1 个像素，硬件也会生成另外 3 个**辅助片元（Helper Lanes / Ghost Pixels）**凑成 $2 \times 2$ 一起跑完片元着色器（最后丢弃那 3 个辅助像素的结果）。

**为什么硬件非要按 $2 \times 2$ 打包执行？**
为了计算屏幕空间偏导数 `ddx(v)` 和 `ddy(v)`！
- 当 GPU 执行 `SAMPLE_TEXTURE2D` 时，它怎么知道该选哪一层 Mipmap？
- 硬件通过比较同一个 $2 \times 2$ Quad 内左右相邻像素的 UV 差值（$\frac{\partial u}{\partial x}, \frac{\partial v}{\partial x}$）和上下相邻像素的 UV 差值（$\frac{\partial u}{\partial y}, \frac{\partial v}{\partial y}$），算出当前 1 个屏幕像素跨过了多少个纹素（Texel footprint $\rho$），进而通过 $\text{LOD} = \log_2(\rho)$ 自动选出最匹配的 Mipmap 层级！
- **这也解释了为什么「极小三角形（Micro-triangles）」是性能杀手**：当高模网格没有做好 LOD，远处大量三角形面积只有 1~2 个像素时，$2 \times 2$ Quad 中有高达 50%~75% 的算力都浪费在了无用的辅助片元上（称为 **Quad Overdraw**）。

### 3. 客户端 Shader 性能调优 CheckList

在日常客户端 Code Review 与 RenderDoc / Frame Debugger 性能剖析中，遵循以下 5 条铁律可以规避 90% 的 GPU 瓶颈：

1. **能放在顶点着色器（VS）算的，绝不放到片元着色器（FS）**：
   - 通常一个模型的顶点数只有几千，而覆盖的屏幕像素高达几十万。像线性雾效因子、SH 球谐环境光、静态 UV 偏移等低频变化量，在 `vert` 中算好通过插值传给 `frag`，性价比极高。
2. **严格区分浮点数精度（`float` / `half` / `fixed`）**：
   - **`float`（32-bit）**：用于世界空间坐标、顶点位置与高频累加的 UV（若 UV 用 `half`，当坐标较大或大地图滚动时会出现肉眼可见的像素抖动马赛克）。
   - **`half`（16-bit，动态范围 $\pm 65504$）**：用于方向向量（归一化后的 $N, L, V, H$）、HDR 颜色、光照计算与绝大多数片元着色器内部变量。在现代移动 GPU 上，`half` 寄存器带宽减半，ALU 吞吐率往往是 `float` 的 2 倍。
3. **合并纹理通道（Channel Packing），减少纹理采样次数**：
   - 带宽（Bandwidth）与纹理采样等待（Texture Stall）是移动端的头号发热源。将 `Metallic`（R）、`Occlusion`（G）、`Detail Mask`（B）、`Smoothness`（A）打包进同一张 **Mask 贴图**，一次 `SAMPLE_TEXTURE2D` 取出四个物理属性。
4. **警惕函数调用顺序与 MAD（乘加指令）合并**：
   - **标量与向量相乘，先算标量**：`float3 res = (scalarA * scalarB) * vectorC;` 只需 1 次标量乘法 + 1 次向量乘法（共 4 次运算）；若写成 `scalarA * vectorC * scalarB` 则需要 2 次向量乘法（共 6 次运算）。
   - **善用硬件单周期指令**：现代 GPU 的 `saturate()`、`abs()`、负号修饰符通常是**零额外周期开销**（直接在指令读取/写回阶段顺带完成），且 `a * b + c` 会被编译器自动融合为单周期的 **FMA / MAD（Fused Multiply-Add）** 指令。因此把 `(x + a) * b` 改写为展开形式 `x * b + a * b`（当 $a, b$ 为常量时），往往能少用一条指令。
5. **严控半透明 Overdraw 与慎用 `Discard / Clip`**：
   - 在移动端的 **TBDR（Tile-Based Deferred Rendering）** 架构中，硬件内置了极其高效的 **HSR（Hidden Surface Removal，隐藏面消除）**。只要是不透明材质（`Opaque`），哪怕 CPU 没有严格排序，TBDR 硬件也能在片元着色器执行前剔除被遮挡像素；但一旦开启 `Alpha Test (clip)` 或 `Alpha Blend`，HSR 管线就会被打断回退（Flush），引发严重的 Overdraw 与片上内存（Tile Memory）带宽雪崩。

---

## 七、总结

回顾整条现代渲染管线，我们可以用一句话串联起它的设计哲学：

> **渲染管线是一场高度协同的「流水线接力」——CPU 负责宏观的空间剔除与批次组织，顶点着色器将三维几何投射到齐次裁剪空间，硬件光栅化器用重心插值与 Early-Z 架起从离散顶点到连续像素的桥梁，最终由片元着色器在 SIMT 锁步阵列上结合物理光照模型（PBR）点亮每一个屏幕像素。**

掌握了这条从数学推导、管线语义到 GPU 硬件特性的完整链路，无论是进一步深入 **Unity URP 的自定义 `ScriptableRenderFeature` 后处理**、研究 **ShadowMap 软阴影与屏幕空间反射（SSR）**，还是使用 **RenderDoc** 逐指令剖析一帧的渲染耗时，都将真正做到胸有成竹。
