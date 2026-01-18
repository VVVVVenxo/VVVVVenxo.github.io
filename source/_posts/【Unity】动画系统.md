---
title: 【Unity】动画系统
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - 动画
  - Animator
  - Animation
description: 详解 Unity 动画系统：Animator 与 Animation 的区别、Mecanim 状态机、Blend Tree 等。
---

## Animator vs Animation

Unity 提供两套动画系统：

| 特性 | Animator | Animation |
|------|----------|-----------|
| 系统 | Mecanim（新） | Legacy（旧） |
| 状态机 | ✅ 支持 | ❌ 不支持 |
| Blend Tree | ✅ 支持 | ❌ 不支持 |
| 层级混合 | ✅ 支持 | ❌ 不支持 |
| 控制复杂度 | 复杂 | 简单 |
| 适用场景 | 角色动作 | UI 动效、简单动画 |

---

## Animator 系统

### Animator Controller

Animator Controller 是动画状态机的核心，定义了：

- 动画状态（State）
- 状态之间的过渡（Transition）
- 过渡条件（Parameters）

### 状态机结构

```
┌─────────────────────────────────────────────────────┐
│              Animator Controller                     │
│                                                     │
│  ┌──────┐      条件触发      ┌──────┐              │
│  │ Idle │ ──────────────────► │ Walk │              │
│  └──────┘ ◄────────────────── └──────┘              │
│      │                            │                 │
│      │         ┌──────┐           │                 │
│      └────────►│ Jump │◄──────────┘                 │
│                └──────┘                             │
└─────────────────────────────────────────────────────┘
```

### 参数类型

| 类型 | 说明 |
|------|------|
| `Float` | 浮点数，用于 Blend Tree |
| `Int` | 整数 |
| `Bool` | 布尔值，持续条件 |
| `Trigger` | 触发器，触发后自动重置 |

### 代码控制

```csharp
public class PlayerAnimator : MonoBehaviour
{
    private Animator animator;
    
    void Start()
    {
        animator = GetComponent<Animator>();
    }
    
    void Update()
    {
        // 设置 Float 参数
        animator.SetFloat("Speed", velocity.magnitude);
        
        // 设置 Bool 参数
        animator.SetBool("IsGrounded", isGrounded);
        
        // 触发 Trigger
        if (Input.GetKeyDown(KeyCode.Space))
        {
            animator.SetTrigger("Jump");
        }
    }
}
```

---

## Blend Tree

Blend Tree 用于**混合多个动画**，实现平滑过渡。

### 类型

| 类型 | 说明 |
|------|------|
| **1D** | 单参数控制（如速度） |
| **2D Simple Directional** | 双参数，简单方向 |
| **2D Freeform Directional** | 双参数，自由方向 |
| **2D Freeform Cartesian** | 双参数，笛卡尔坐标 |

### 1D Blend Tree 示例

```
Speed 参数
    │
    0 ──────► Idle
    │
    0.5 ────► Walk
    │
    1 ──────► Run
```

### 代码控制

```csharp
// 根据速度自动混合 Idle、Walk、Run
float speed = velocity.magnitude / maxSpeed;
animator.SetFloat("Speed", speed);
```

---

## 动画层（Layers）

动画层允许**同时播放多个动画**，实现身体不同部位的独立控制。

### 常见用法

| 层 | 内容 | 权重 |
|----|------|------|
| Base Layer | 移动动画（全身） | 1.0 |
| Upper Body | 射击动画（上半身） | 0.8 |

### Avatar Mask

用于指定动画层影响的身体部位：

- 创建 Avatar Mask 资源
- 选择需要影响的骨骼
- 应用到动画层

---

## Animation 系统（Legacy）

旧版动画系统，适合简单场景：

```csharp
public class SimpleAnimation : MonoBehaviour
{
    private Animation anim;
    
    void Start()
    {
        anim = GetComponent<Animation>();
    }
    
    void PlayAnimation()
    {
        anim.Play("Open");      // 播放动画
        anim.CrossFade("Close", 0.3f);  // 渐变到另一个动画
    }
}
```

### 适用场景

- UI 动效（按钮缩放、面板滑动）
- 简单物体动画（门的开关）
- 不需要复杂状态管理的动画

---

## 动画事件（Animation Events）

在动画特定帧调用脚本方法：

```csharp
public class AttackAnimation : MonoBehaviour
{
    // 在动画编辑器中设置事件调用此方法
    public void OnAttackHit()
    {
        // 攻击命中逻辑
        DealDamage();
    }
    
    public void OnFootstep()
    {
        // 播放脚步声
        PlayFootstepSound();
    }
}
```

### 设置方式

1. 在 Animation 窗口选择动画剪辑
2. 在时间轴上右键 → Add Animation Event
3. 选择要调用的方法

---

## Root Motion

Root Motion 让动画**驱动角色移动**，而非代码。

### 启用方式

1. 在 Animator 组件勾选 `Apply Root Motion`
2. 确保动画剪辑包含位移数据

### 代码控制

```csharp
void OnAnimatorMove()
{
    // 自定义 Root Motion 处理
    Vector3 deltaPosition = animator.deltaPosition;
    transform.position += deltaPosition;
}
```

---

## 动画系统最佳实践

| 场景 | 建议 |
|------|------|
| 角色动作 | Animator + 状态机 |
| 移动混合 | Blend Tree |
| 上下半身分离 | 动画层 + Avatar Mask |
| UI 动效 | Animation（Legacy）或 DOTween |
| 攻击判定 | Animation Events |
| 真实移动感 | Root Motion |
