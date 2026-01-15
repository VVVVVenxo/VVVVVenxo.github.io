---
title: 【项目实战】基于OpenGL的大规模自然场景实时漫游系统
toc: true
categories:
  - 项目实战
  - 图形学
cover: /img/covers/code_dark.jpg
date: 2026-01-15
tags:
  - OpenGL
  - C++
  - 图形学
  - 毕业设计
  - 地形渲染
  - GLSL
description: 基于C++与Modern OpenGL构建的大规模自然场景实时漫游系统，实现了地形渲染、水体仿真、天空盒、日夜循环、LOD优化、视锥体剔除、SSAO等核心功能，是一个具备"游戏级"视觉表现的室外场景漫游系统。
---

## 项目简介

**基于OpenGL的大规模自然场景实时漫游系统** 是一个使用 C++17 与 Modern OpenGL (Core Profile 4.5+) 从零构建的室外场景漫游系统。项目实现了地形渲染、水体仿真、天空盒、日夜循环光照等核心功能，并通过 LOD 和视锥体剔除进行性能优化，具备"游戏级"的视觉表现与实时交互能力。

> GitHub 地址: [RoamingSystem](https://github.com/VVenox/RoamingSystem)

## 项目特点

- **地形渲染**：高度图解析、网格生成、多纹理混合（草地/岩石/雪地）、法线贴图
- **性能优化**：4级LOD系统、视锥体剔除（Frustum Culling）
- **水体仿真**：反射/折射、Fresnel效果、DuDv波浪扭曲、岸边泡沫
- **环境系统**：立方体贴图天空盒、日夜循环动态光照
- **后处理效果**：SSAO屏幕空间环境光遮蔽、距离雾效
- **编辑器系统**：ImGui实时参数调节、设置持久化（INI格式）

## 技术栈

| 类别 | 技术/工具 | 版本 |
|------|----------|------|
| 编程语言 | C++ | 17 |
| 图形API | OpenGL | Core Profile 4.5+ |
| 着色语言 | GLSL | 4.50 |
| 窗口管理 | GLFW | 3.x |
| 数学库 | GLM | - |
| 图像加载 | stb_image | - |
| UI框架 | Dear ImGui | - |
| 开发环境 | Visual Studio | 2022 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│              (main.cpp - 程序入口与Game Loop)                │
├─────────────────────────────────────────────────────────────┤
│                     Editor Layer                            │
│          (ImGui 编辑器 - 参数调节、性能监控)                   │
├───────────────┬─────────────────┬───────────────────────────┤
│   Terrain     │   Water         │   Environment             │
│   System      │   System        │   System                  │
│  (地形渲染)    │  (水体仿真)      │  (天空盒/光照)             │
├───────────────┴─────────────────┴───────────────────────────┤
│                    Core Engine Layer                        │
│    Camera │ Shader │ Texture │ Mesh │ Frustum │ LOD        │
├─────────────────────────────────────────────────────────────┤
│                    Platform Layer                           │
│              GLFW │ GLAD │ GLM │ stb_image                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
RoamingSystem/
├── src/
│   ├── main.cpp                    # 程序入口
│   ├── Application.h/cpp           # 应用框架基类（Game Loop、GLFW、ImGui）
│   ├── RoamingApp.h/cpp            # 主应用类（渲染逻辑）
│   ├── Core/                       # 核心引擎组件
│   │   ├── Camera.h                # 第一人称摄像机
│   │   ├── Shader.h/cpp            # 着色器程序管理
│   │   ├── Texture.h/cpp           # 2D纹理加载
│   │   ├── Cubemap.h/cpp           # 立方体贴图（天空盒）
│   │   └── Mesh.h/cpp              # VAO/VBO/EBO封装
│   ├── Terrain/                    # 地形渲染系统
│   │   ├── HeightmapLoader.h/cpp   # 高度图加载
│   │   ├── Terrain.h/cpp           # 地形主接口（门面类）
│   │   ├── ChunkedTerrain.h/cpp    # 分块管理
│   │   ├── TerrainChunk.h/cpp      # 单个地形块（4级LOD）
│   │   └── Frustum.h/cpp           # 视锥体剔除
│   ├── Water/                      # 水体渲染系统
│   │   ├── Water.h/cpp             # 水面网格与渲染
│   │   └── WaterFramebuffers.h/cpp # 反射/折射FBO
│   ├── Environment/                # 环境系统
│   │   ├── Skybox.h/cpp            # 天空盒渲染
│   │   └── Lighting.h/cpp          # 日夜循环光照系统
│   ├── PostProcess/                # 后处理效果
│   │   └── SSAO.h/cpp              # 环境光遮蔽
│   └── Editor/                     # 场景编辑器
│       └── SceneSettings.h/cpp     # 参数序列化（INI格式）
├── shaders/                        # GLSL着色器
│   ├── terrain.vert/frag           # 地形着色器
│   ├── water.vert/frag             # 水面着色器
│   ├── skybox.vert/frag            # 天空盒着色器
│   ├── gbuffer.vert/frag           # G-Buffer（SSAO用）
│   ├── ssao.vert/frag              # SSAO计算
│   └── ssao_blur.frag              # SSAO模糊
├── assets/                         # 资源文件
│   ├── heightmaps/                 # 高度图
│   ├── textures/                   # 纹理
│   └── skybox/                     # 天空盒
└── scripts/
    └── package.bat                 # 打包脚本
```

---

## 核心模块详解

### 1. 地形渲染系统 (Terrain System)

地形系统是项目中最复杂的模块，负责从高度图生成可渲染的3D地形，支持多纹理混合和法线贴图。

#### 1.1 高度图加载

**原理**：读取灰度PNG图像，每个像素的灰度值 (0-255) 映射为高度值。

- 使用 `stb_image` 加载图像
- 遍历像素，将灰度值归一化到 [0, 1]
- 支持双线性插值获取任意坐标高度

#### 1.2 网格生成

根据高度图尺寸创建顶点网格，每个顶点包含：位置、法线、纹理坐标、切线（用于法线贴图）。

**顶点数据结构**：
```cpp
// 每个顶点包含 11 个 float
// Position (3) + Normal (3) + TexCoord (2) + Tangent (3)
vertices.push_back(worldX);      // 位置 X
vertices.push_back(worldY);      // 位置 Y（高度）
vertices.push_back(worldZ);      // 位置 Z
vertices.push_back(normal.x);    // 法线
vertices.push_back(normal.y);
vertices.push_back(normal.z);
vertices.push_back(u);           // 纹理坐标
vertices.push_back(v);
vertices.push_back(tangent.x);   // 切线（TBN矩阵用）
vertices.push_back(tangent.y);
vertices.push_back(tangent.z);
```

#### 1.3 法线计算（中心差分法）

使用相邻顶点的高度差计算法线向量：

```cpp
glm::vec3 TerrainChunk::calculateNormal(const HeightmapLoader& heightmap,
                                        int x, int z, float cellSize, float maxHeight)
{
    int width = heightmap.getWidth();
    int height = heightmap.getGridHeight();
    
    // 采样四个相邻点的高度
    float hL = heightmap.getHeight(std::max(0, x - 1), z) * maxHeight;  // 左
    float hR = heightmap.getHeight(std::min(width - 1, x + 1), z) * maxHeight;  // 右
    float hD = heightmap.getHeight(x, std::max(0, z - 1)) * maxHeight;  // 下
    float hU = heightmap.getHeight(x, std::min(height - 1, z + 1)) * maxHeight;  // 上
    
    // 中心差分公式：N = normalize(hL - hR, 2Δ, hD - hU)
    glm::vec3 normal(hL - hR, 2.0f * cellSize, hD - hU);
    return glm::normalize(normal);
}
```

#### 1.4 多纹理混合

基于 **高度 + 坡度** 的混合策略，使用 `smoothstep` 实现平滑过渡：

| 纹理 | 混合条件 |
|------|---------|
| 草地 (Grass) | 低海拔 + 平坦区域 |
| 岩石 (Rock) | 中等海拔 + 陡峭坡度 |
| 雪地 (Snow) | 高海拔区域 |

**着色器实现**：
```glsl
// 计算坡度（0 = 平坦, 1 = 垂直）
float slope = 1.0 - dot(geometryNormal, vec3(0.0, 1.0, 0.0));

// 归一化高度
float normalizedHeight = vHeight / uMaxHeight;

// 计算混合权重
float grassWeight = smoothstep(uGrassMaxHeight + 0.1, uGrassMaxHeight - 0.1, normalizedHeight);
grassWeight *= smoothstep(uSlopeThreshold + 0.1, uSlopeThreshold - 0.1, slope);

float snowWeight = smoothstep(uRockMaxHeight - 0.1, uRockMaxHeight + 0.1, normalizedHeight);

float rockWeight = 1.0 - grassWeight - snowWeight;
rockWeight = max(rockWeight, smoothstep(uSlopeThreshold - 0.1, uSlopeThreshold + 0.2, slope));

// 归一化权重
float totalWeight = grassWeight + rockWeight + snowWeight + 0.001;
grassWeight /= totalWeight;
rockWeight /= totalWeight;
snowWeight /= totalWeight;

// 混合纹理
vec3 albedo = grassColor * grassWeight + rockColor * rockWeight + snowColor * snowWeight;
```

#### 1.5 法线贴图

使用 TBN 矩阵（Tangent-Bitangent-Normal）将切线空间法线转换到世界空间：

```glsl
if (uUseNormalMaps)
{
    // 采样并混合法线贴图
    vec3 grassNormal = texture(uGrassNormalMap, tiledUV).rgb * 2.0 - 1.0;
    vec3 rockNormal = texture(uRockNormalMap, tiledUV).rgb * 2.0 - 1.0;
    vec3 snowNormal = texture(uSnowNormalMap, tiledUV).rgb * 2.0 - 1.0;
    
    vec3 tangentNormal = grassNormal * grassWeight + 
                         rockNormal * rockWeight + 
                         snowNormal * snowWeight;
    
    // 应用法线贴图强度
    tangentNormal.xy *= uNormalMapStrength;
    tangentNormal = normalize(tangentNormal);
    
    // TBN矩阵变换到世界空间
    normal = normalize(vTBN * tangentNormal);
}
```

---

### 2. LOD系统 (Level of Detail)

根据摄像机距离动态选择不同精度的网格，大幅减少远处地形的渲染开销。

#### 2.1 分块架构

```
ChunkedTerrain
    ├── Frustum (视锥体剔除)
    └── TerrainChunk[] (N×N 个地形块)
            └── LOD Meshes[4] (每块 4 级精度)
```

#### 2.2 LOD级别参数

| LOD | 顶点步长 | 相对三角形数 | 适用距离 |
|-----|---------|-------------|----------|
| 0 | 1 | 100% | 0-100m |
| 1 | 2 | 25% | 100-200m |
| 2 | 4 | 6.25% | 200-400m |
| 3 | 8 | 1.56% | 400m+ |

#### 2.3 LOD网格生成

通过步长控制顶点采样密度：

```cpp
void TerrainChunk::generateLODMesh(/* ... */, int lodLevel)
{
    // LOD0=1, LOD1=2, LOD2=4, LOD3=8
    int step = 1 << lodLevel;
    
    // 按步长采样顶点
    for (int z = startZ; z <= startZ + chunkSize && z < hmHeight; z += step)
    {
        for (int x = startX; x <= startX + chunkSize && x < hmWidth; x += step)
        {
            // 生成顶点...
        }
    }
}
```

#### 2.4 LOD选择算法

基于块中心到摄像机的距离选择合适的LOD级别：

```cpp
int ChunkedTerrain::calculateLOD(float distance) const
{
    // m_lodDistances = { 100.0f, 200.0f, 400.0f, 800.0f }
    for (int i = 0; i < 4; i++)
    {
        if (distance < m_lodDistances[i])
        {
            return i;
        }
    }
    return 3;  // 最低精度
}
```

---

### 3. 视锥体剔除 (Frustum Culling)

跳过摄像机看不到的地形块，进一步提升渲染性能。

#### 3.1 平面提取（Gribb/Hartmann方法）

从 ViewProjection 矩阵直接提取6个裁剪平面：

```cpp
void Frustum::update(const glm::mat4& vp)
{
    // Left plane
    m_planes[LEFT].x = vp[0][3] + vp[0][0];
    m_planes[LEFT].y = vp[1][3] + vp[1][0];
    m_planes[LEFT].z = vp[2][3] + vp[2][0];
    m_planes[LEFT].w = vp[3][3] + vp[3][0];
    
    // Right plane
    m_planes[RIGHT].x = vp[0][3] - vp[0][0];
    m_planes[RIGHT].y = vp[1][3] - vp[1][0];
    m_planes[RIGHT].z = vp[2][3] - vp[2][0];
    m_planes[RIGHT].w = vp[3][3] - vp[3][0];
    
    // Bottom, Top, Near, Far 类似...
    
    // 归一化平面
    for (int i = 0; i < COUNT; i++)
    {
        normalizePlane(m_planes[i]);
    }
}
```

#### 3.2 AABB可见性测试

使用 P-Vertex 方法快速判断包围盒是否在视锥体内：

```cpp
bool Frustum::isBoxVisible(const glm::vec3& min, const glm::vec3& max) const
{
    for (int i = 0; i < COUNT; i++)
    {
        const glm::vec4& plane = m_planes[i];
        
        // 找到离平面最近的点 (p-vertex)
        glm::vec3 pVertex;
        pVertex.x = (plane.x >= 0.0f) ? max.x : min.x;
        pVertex.y = (plane.y >= 0.0f) ? max.y : min.y;
        pVertex.z = (plane.z >= 0.0f) ? max.z : min.z;
        
        // 如果最近点在平面外侧，整个AABB不可见
        float distance = glm::dot(glm::vec3(plane), pVertex) + plane.w;
        if (distance < 0.0f)
        {
            return false;
        }
    }
    return true;
}
```

#### 3.3 性能提升数据

| 场景 | 无优化 | 有剔除+LOD | 提升 |
|------|--------|------------|------|
| 512×512 全可见 | 520K三角形 | ~150K | 3.5× |
| 512×512 部分可见 | 520K三角形 | ~80K | 6.5× |

---

### 4. 水体渲染系统 (Water System)

实现了游戏级的逼真水面效果，包括反射、折射、Fresnel效果和动态波浪。

#### 4.1 反射与折射原理

水面效果需要两次额外的场景渲染：

```
┌──────────────────┐     ┌──────────────────┐
│   反射渲染        │     │   折射渲染        │
│  翻转摄像机      │     │  正常摄像机       │
│  裁剪水面以下     │     │  裁剪水面以上     │
│  结果：倒影      │     │  结果：水下场景   │
└──────────────────┘     └──────────────────┘
```

#### 4.2 裁剪平面技术

使用 `gl_ClipDistance` 实现硬件级裁剪：

```glsl
// 顶点着色器
uniform vec4 uClipPlane;
gl_ClipDistance[0] = dot(worldPos, uClipPlane);

// 反射时: uClipPlane = vec4(0, 1, 0, -waterHeight)  // 裁剪水下
// 折射时: uClipPlane = vec4(0, -1, 0, waterHeight)  // 裁剪水上
```

#### 4.3 Fresnel效果

视线与水面夹角越小，反射越强：

```glsl
// Fresnel效果 - 掠射角更多反射
vec3 viewVector = normalize(vToCamera);
float refractiveFactor = dot(viewVector, vec3(0.0, 1.0, 0.0));
refractiveFactor = pow(refractiveFactor, 0.5);
refractiveFactor = clamp(refractiveFactor, 0.0, 1.0);

// 混合反射和折射
FragColor = mix(reflectColor, refractColor, refractiveFactor);
```

#### 4.4 DuDv波浪扭曲

使用 DuDv 贴图对纹理坐标进行偏移，产生动态波纹效果：

```glsl
// 动画纹理坐标
float moveFactor = uTime * waveSpeed;
vec2 distortedTexCoord = texture(uDudvMap, vec2(vTexCoord.x + moveFactor, vTexCoord.y)).rg * 0.1;
distortedTexCoord = vTexCoord + vec2(distortedTexCoord.x, distortedTexCoord.y + moveFactor);

// 采样DuDv贴图获取扭曲
vec2 totalDistortion = (texture(uDudvMap, distortedTexCoord).rg * 2.0 - 1.0) * uWaveStrength;

// 应用扭曲到纹理坐标
reflectTexCoord += totalDistortion;
refractTexCoord += totalDistortion;
```

#### 4.5 岸边泡沫

基于深度差计算水深，浅水区域显示泡沫：

```glsl
// 计算水深
float floorDistance = /* 地面深度 */;
float waterDistance = /* 水面深度 */;
float waterDepth = floorDistance - waterDistance;

// 泡沫强度基于深度
float foamFactor = 1.0 - clamp(waterDepth / uFoamDepth, 0.0, 1.0);

// 程序化泡沫噪声（带动画）
float foamNoise = /* 噪声计算 */;
float foam = foamFactor * smoothstep(0.3, 0.7, foamNoise * foamFactor + foamFactor * 0.5);

// 混合泡沫颜色
FragColor.rgb = mix(FragColor.rgb, uFoamColor, foam * uFoamIntensity);
```

---

### 5. 天空盒系统 (Skybox System)

#### 5.1 实现原理

1. 使用立方体贴图 (Cubemap) 存储6个方向的天空图像
2. 渲染一个包围摄像机的立方体
3. 移除视图矩阵的平移分量，确保天空盒始终"无限远"

#### 5.2 深度测试技巧

```glsl
// 顶点着色器
void main()
{
    vTexCoord = aPos;
    
    vec4 pos = uProjection * uView * vec4(aPos, 1.0);
    
    // 将深度设为1.0（最远），z = w，透视除法后 z/w = 1.0
    gl_Position = pos.xyww;
}
```

渲染时使用 `GL_LEQUAL` 深度测试：
```cpp
glDepthFunc(GL_LEQUAL);  // 允许深度=1.0的片段通过
```

#### 5.3 动态颜色混合

天空盒颜色随日夜循环变化：

```glsl
uniform vec3 uSkyColor;
uniform float uBlendFactor;
vec3 finalColor = mix(cubemapColor, uSkyColor, uBlendFactor);
```

---

### 6. 动态光照系统 (Lighting System)

实现了完整的日夜循环系统。

#### 6.1 日夜循环时间模型

| 时间 | 太阳角度 | 效果 |
|------|----------|------|
| 6:00 | 0° (地平线) | 日出，暖橙色光 |
| 12:00 | 90° (正上方) | 正午，白色强光 |
| 18:00 | 180° (地平线) | 日落，金橙色光 |
| 0:00 | -90° (地下) | 午夜，微弱蓝光 |

#### 6.2 太阳位置计算

```cpp
glm::vec3 Lighting::getSunDirection() const
{
    // 时间转角度：6点=0°，12点=90°，18点=180°
    float angle = (m_timeOfDay - 6.0f) / 12.0f * glm::pi<float>();
    
    // 太阳从东向西移动
    return glm::normalize(glm::vec3(
        cos(angle),   // x: 东西方向
        sin(angle),   // y: 高度
        -0.3f         // z: 略微偏移
    ));
}
```

#### 6.3 动态颜色计算

根据太阳高度插值不同时段的颜色：

```cpp
glm::vec3 Lighting::getSunColor() const
{
    float sunHeight = getSunHeight();
    
    glm::vec3 noonColor = glm::vec3(1.0f, 1.0f, 0.95f);      // 正午：暖白色
    glm::vec3 sunsetColor = glm::vec3(1.0f, 0.6f, 0.3f);     // 日落：暖橙色
    glm::vec3 nightColor = glm::vec3(0.2f, 0.2f, 0.4f);      // 夜晚：冷蓝色
    
    if (sunHeight > 0.3f)
        return noonColor;                                     // 白天
    else if (sunHeight > 0.0f)
        return glm::mix(sunsetColor, noonColor, sunHeight / 0.3f);  // 日出/日落
    else if (sunHeight > -0.3f)
        return glm::mix(nightColor, sunsetColor, (sunHeight + 0.3f) / 0.3f);  // 黄昏
    else
        return nightColor;                                    // 夜晚
}
```

---

### 7. SSAO后处理 (Screen Space Ambient Occlusion)

屏幕空间环境光遮蔽，增强场景立体感，让角落和缝隙产生柔和阴影。

#### 7.1 算法流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  G-Buffer    │ --> │  SSAO Calc   │ --> │  Blur        │ --> │  Apply       │
│  Pass        │     │  Pass        │     │  Pass        │     │  Pass        │
├──────────────┤     ├──────────────┤     ├──────────────┤     ├──────────────┤
│ 渲染场景到    │     │ 在半球内采样  │     │ 4x4盒式模糊   │     │ 应用到环境光 │
│ 位置+法线纹理 │     │ 计算遮蔽因子  │     │ 去除噪点     │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

#### 7.2 核心参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| radius | 0.5 | 采样半径，越大影响范围越广 |
| bias | 0.025 | 深度偏移，防止自遮挡伪影 |
| intensity | 1.0 | 遮蔽强度，控制暗化程度 |
| kernelSize | 32 | 采样点数量，越多越平滑但越慢 |

#### 7.3 应用到地形着色器

```glsl
// 获取SSAO因子
float ssaoFactor = 1.0;
if (uSSAOEnabled)
{
    vec2 screenUV = gl_FragCoord.xy / vec2(textureSize(uSSAOTexture, 0));
    float ssao = texture(uSSAOTexture, screenUV).r;
    ssaoFactor = mix(1.0, ssao, uSSAOIntensity);
}

// 环境光乘以遮蔽因子
vec3 ambient = uAmbientColor * albedo * ssaoFactor;
```

---

## 渲染管线

每帧渲染的完整流程：

```
1. 更新逻辑 (deltaTime)
   ├── 处理输入
   ├── 更新摄像机位置
   └── 更新日夜循环时间

2. G-Buffer Pass (SSAO预渲染)
   └── 输出位置和法线纹理

3. SSAO Pass
   ├── 半球采样计算遮蔽因子
   └── 4x4盒式模糊去噪

4. 水体预渲染 (如果启用水体)
   ├── 绑定反射FBO
   │   ├── 计算反射摄像机位置（Y轴镜像）
   │   ├── 设置裁剪平面（裁剪水下）
   │   └── 渲染场景（天空盒、地形）
   │
   └── 绑定折射FBO
       ├── 设置裁剪平面（裁剪水上）
       └── 渲染场景（地形）

5. 主场景渲染
   ├── 渲染天空盒
   ├── 渲染地形（含SSAO、雾效）
   └── 渲染水面（使用反射/折射纹理）

6. UI渲染
   └── ImGui面板
```

---

## 代码统计

| 模块 | 文件数 | 代码行数 |
|------|--------|----------|
| Application | 6 | ~944 |
| Core | 11 | ~863 |
| Terrain | 10 | ~809 |
| Water | 4 | ~371 |
| Environment | 4 | ~346 |
| PostProcess | 2 | ~300 |
| Editor | 2 | ~177 |
| **C++ 小计** | **39** | **~3,510** |
| GLSL 着色器 | 12 | ~306 |
| **项目总计** | **51** | **~3,816** |

---

## 操作说明

| 按键 | 功能 |
|------|------|
| W/A/S/D | 前后左右移动 |
| Shift | 加速移动（3倍速度） |
| 鼠标移动 | 视角旋转 |
| 滚轮 | 调整视野 (FOV) |
| Space | 切换鼠标捕获 |
| F1 | 切换线框模式 |
| ESC | 退出程序 |

---

## 编辑器界面

基于 ImGui 实现的实时参数调节面板：

| 面板 | 功能 |
|------|------|
| **Performance** | FPS、帧时间、顶点数、三角形数、GPU信息 |
| **Camera** | 位置显示、移动速度、地面行走模式 |
| **Terrain** | 纹理平铺、混合参数、法线贴图强度 |
| **Water** | 水面高度、波浪参数、颜色、泡沫设置 |
| **Lighting** | 时间控制、日夜循环开关、光照强度 |
| **Settings** | 保存/加载设置（INI格式） |

---

## 效果展示

> 待补充：运行程序后截取效果图，建议包含以下场景：
> - 正午阳光下的地形全景
> - 日落/日出时的天空颜色变化
> - 水面反射与波浪效果
> - SSAO开启/关闭对比
> - 编辑器界面展示

<!-- 
将截图放入 source/img/posts/ 目录，然后取消下方注释：
![地形全景](/img/posts/roaming-terrain.jpg)
![水体效果](/img/posts/roaming-water.jpg)
![日落效果](/img/posts/roaming-sunset.jpg)
![编辑器界面](/img/posts/roaming-editor.jpg)
-->

---

## 总结

本项目从零实现了一个完整的大规模自然场景实时漫游系统，主要技术成果包括：

**核心功能**：
- 基于高度图的地形生成与多纹理混合
- 4级LOD系统与视锥体剔除优化
- 逼真的水体渲染（反射/折射/Fresnel/波浪/泡沫）
- 天空盒与日夜循环动态光照
- SSAO屏幕空间环境光遮蔽

**技术难点与收获**：
- 深入理解 OpenGL 渲染管线与着色器编程
- 掌握大规模场景的性能优化技术（LOD、剔除）
- 学习了多种图形学算法的实际应用

**可扩展方向**：
- 植被系统（草地、树木的实例化渲染）
- 天气系统（雨、雪、云的动态效果）
- 阴影系统（级联阴影贴图 CSM）

---

## 许可协议

本项目采用 MIT License 开源协议。
