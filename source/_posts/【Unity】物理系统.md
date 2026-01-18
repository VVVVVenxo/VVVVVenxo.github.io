---
title: 【Unity】物理系统
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - 物理
  - 碰撞检测
  - NavMesh
description: 详解 Unity 物理系统：碰撞检测模式、穿透问题解决方案，以及 NavMesh 导航系统。
---

## 碰撞检测模式

在 Rigidbody 组件中，可以设置不同的碰撞检测模式来解决穿透问题。

### 穿透问题的原因

Unity 每帧更新位置：`newPosition = oldPosition + velocity * deltaTime`

如果速度很快而 `deltaTime` 太大，物体可能**直接跳过障碍物**，碰撞器来不及检测。例如墙体厚度 0.2，每帧移动距离 2，一帧就穿透了。

### Discrete 模式（离散）

| 项目 | 说明 |
|------|------|
| CPU 开销 | 每 1000 次碰撞约 0.6ms |
| 穿透问题 | **会穿透**（帧率有限，检测不到重叠） |
| 适用场景 | 低速物体、静态交互 |

### Continuous 模式（连续）

| 项目 | 说明 |
|------|------|
| CPU 开销 | 每 1000 次碰撞约 1.5ms |
| 穿透问题 | 解决（在两帧之间线性插值轨迹检测） |
| 适用场景 | 快速物体打中**静态**目标 |

### Continuous Dynamic 模式

| 项目 | 说明 |
|------|------|
| CPU 开销 | 每 1000 次碰撞约 1.7ms |
| 穿透问题 | 解决 |
| 适用场景 | 快速物体打中**动态**目标（如移动的敌人） |

### Continuous Speculative 模式

| 项目 | 说明 |
|------|------|
| CPU 开销 | 每 1000 次碰撞约 1.2ms |
| 穿透问题 | 解决（预测性检测，牺牲部分准确性换性能） |
| 适用场景 | Unity 2018+，高效且安全 |

---

## 穿透问题解决方案

| 方案 | 说明 |
|------|------|
| 设置合理的碰撞检测模式 | 快速物体使用 Continuous |
| 增加墙体厚度 | 确保不会被跳过 |
| 提高 Fixed Timestep 精度 | 减小物理更新间隔 |
| 使用射线检测 | 手动射线 + 命中判断 |

### 射线检测方案

对于子弹等高速物体，使用射线更可靠：

```csharp
void Update()
{
    Vector3 movement = velocity * Time.deltaTime;
    
    if (Physics.Raycast(transform.position, velocity.normalized, 
                        out RaycastHit hit, movement.magnitude))
    {
        // 命中目标
        OnHit(hit);
        transform.position = hit.point;
    }
    else
    {
        transform.position += movement;
    }
}
```

---

## NavMesh 导航系统

NavMesh 是 Unity 内置的寻路系统，将场景 **Bake** 成可导航网格。

### 核心组件

| 组件 | 作用 |
|------|------|
| **NavMesh** | 可行走区域的网格数据 |
| **NavMeshAgent** | 控制物体在 NavMesh 上移动 |
| **NavMeshObstacle** | 动态障碍物 |
| **OffMeshLink** | 跳跃点、传送门等特殊连接 |

### 使用流程

1. **烘焙 NavMesh**
   - Window → AI → Navigation
   - 选择静态物体，标记为 Navigation Static
   - 点击 Bake 生成导航网格

2. **添加 NavMeshAgent**
   - 给角色添加 NavMeshAgent 组件
   - 设置速度、加速度、转向速度等参数

3. **控制移动**

```csharp
using UnityEngine.AI;

public class AIController : MonoBehaviour
{
    private NavMeshAgent agent;
    
    void Start()
    {
        agent = GetComponent<NavMeshAgent>();
    }
    
    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            Ray ray = Camera.main.ScreenPointToRay(Input.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit))
            {
                agent.SetDestination(hit.point);  // 设置目标点
            }
        }
    }
}
```

### NavMeshAgent 常用属性

| 属性 | 说明 |
|------|------|
| `speed` | 移动速度 |
| `angularSpeed` | 转向速度 |
| `acceleration` | 加速度 |
| `stoppingDistance` | 停止距离 |
| `remainingDistance` | 剩余距离 |
| `hasPath` | 是否有有效路径 |

### 动态障碍物

```csharp
// 添加 NavMeshObstacle 组件
// 设置 Carve = true 可以在 NavMesh 上"挖洞"
```

---

## 物理系统最佳实践

| 场景 | 建议 |
|------|------|
| 低速物体 | Discrete 模式 |
| 高速物体打静态目标 | Continuous 模式 |
| 高速物体打动态目标 | Continuous Dynamic 模式 |
| 子弹类 | 射线检测 |
| AI 寻路 | NavMesh + NavMeshAgent |
| 物理计算 | 放在 FixedUpdate 中 |
