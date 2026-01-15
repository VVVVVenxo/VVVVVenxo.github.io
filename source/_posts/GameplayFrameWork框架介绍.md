---
title: Unity游戏开发框架 - GameplayFrameWork
toc: true
categories:
  - 项目实战
  - Unity
cover: /img/covers/game2.jpg
date: 2025-01-15
tags:
  - Unity
  - 框架设计
  - C#
  - 设计模式
  - 单例模式
  - 对象池
description: GameplayFrameWork 是一个轻量级 Unity 游戏开发框架，包含事件中心、资源管理、对象池、UI 管理、音频管理、A* 寻路等核心模块，采用单例模式架构实现模块解耦。
---

## 项目简介

**GameplayFrameWork** 是一个轻量级、模块化的 Unity 游戏开发基础框架。该框架采用单例模式作为核心架构，封装了游戏开发中最常用的功能模块，帮助开发者快速搭建游戏项目的基础设施，专注于业务逻辑开发。

> GitHub 地址: [GameplayFrameWork](https://github.com/VVenox/GameplayFrameWork)

## 框架特点

- **模块化设计**：各模块高度解耦，可按需使用
- **单例模式架构**：统一的管理器访问方式
- **异步加载支持**：资源、场景均支持异步加载
- **事件驱动**：基于观察者模式的事件中心，实现系统间解耦通信
- **对象池优化**：减少频繁创建销毁带来的性能开销
- **开箱即用**：集成 DOTween 动画库、Input System 等常用插件

## 框架架构

```
GameplayFrameWork/
├── Assets/
│   ├── Scripts/
│   │   ├── ProjectBase/           # 框架核心模块
│   │   │   ├── Base/              # 单例模式基类
│   │   │   ├── Event/             # 事件中心
│   │   │   ├── Mono/              # Mono管理器
│   │   │   ├── Res/               # 资源管理
│   │   │   ├── Pool/              # 对象池
│   │   │   ├── UI/                # UI管理
│   │   │   ├── Scenes/            # 场景管理
│   │   │   ├── Music/             # 音频管理
│   │   │   ├── Input/             # 输入管理
│   │   │   └── AStar/             # A*寻路
│   │   └── Test/                  # 测试示例
│   └── Resources/                 # 资源文件夹
└── ...
```

## 核心模块详解

### 1. 单例模式基类 (Base)

框架提供了三种单例模式实现，满足不同场景需求：

#### BaseManager - 普通单例基类

```csharp
public class BaseManager<T> where T : new()
{
    private static T instance;

    public static T GetInstance()
    {
        if (instance == null)
            instance = new T();
        return instance;
    }
}
```

适用于：不需要继承 MonoBehaviour 的管理类。

#### SingletonAutoMono - 自动创建型 Mono 单例

```csharp
public class SingletonAutoMono<T> : MonoBehaviour where T : MonoBehaviour
{
    private static T instance;

    public static T GetInstance()
    {
        if (instance == null)
        {
            GameObject obj = new GameObject();
            obj.name = typeof(T).ToString();
            DontDestroyOnLoad(obj);
            instance = obj.AddComponent<T>();
        }
        return instance;
    }
}
```

适用于：需要自动创建且跨场景存在的 MonoBehaviour 单例。

---

### 2. 事件中心 (EventCenter)

基于**观察者模式**实现的事件系统，支持泛型参数传递，是模块间解耦通信的核心。

#### 核心 API

| 方法 | 说明 |
|------|------|
| `AddEventListener<T>(string name, UnityAction<T> action)` | 添加带参数的事件监听 |
| `AddEventListener(string name, UnityAction action)` | 添加无参数的事件监听 |
| `RemoveEventListener<T>(string name, UnityAction<T> action)` | 移除带参数的事件监听 |
| `EventTrigger<T>(string name, T info)` | 触发带参数的事件 |
| `EventTrigger(string name)` | 触发无参数的事件 |
| `Clear()` | 清空所有事件（场景切换时使用） |

#### 使用示例

```csharp
// 注册事件监听
EventCenter.GetInstance().AddEventListener<int>("PlayerDamaged", OnPlayerDamaged);

// 触发事件
EventCenter.GetInstance().EventTrigger("PlayerDamaged", 50);

// 回调处理
private void OnPlayerDamaged(int damage)
{
    Debug.Log($"玩家受到 {damage} 点伤害");
}
```

---

### 3. 资源管理 (ResMgr)

封装了 Unity 的 Resources 加载方式，支持同步和异步加载，自动处理 GameObject 实例化。

#### 核心 API

```csharp
// 同步加载 - GameObject 会自动实例化
T Load<T>(string name) where T : Object

// 异步加载 - 通过回调返回
void LoadAsync<T>(string name, UnityAction<T> callback) where T : Object
```

#### 使用示例

```csharp
// 同步加载预制体
GameObject enemy = ResMgr.GetInstance().Load<GameObject>("Prefabs/Enemy");

// 异步加载音频
ResMgr.GetInstance().LoadAsync<AudioClip>("Audio/BGM", (clip) =>
{
    audioSource.clip = clip;
    audioSource.Play();
});
```

---

### 4. 对象池 (PoolMgr)

高效的对象池实现，通过复用对象减少 GC 开销，提升游戏性能。

#### 核心 API

| 方法 | 说明 |
|------|------|
| `GetObj(string name, UnityAction<GameObject> callBack)` | 从池中获取对象，池空则自动加载创建 |
| `PushObj(string name, GameObject obj)` | 将对象归还到池中 |
| `Clear()` | 清空对象池（场景切换时调用） |

#### 使用示例

```csharp
// 获取子弹对象
PoolMgr.GetInstance().GetObj("Prefabs/Bullet", (bullet) =>
{
    bullet.transform.position = firePoint.position;
    bullet.GetComponent<Rigidbody>().velocity = direction * speed;
});

// 归还子弹到对象池
PoolMgr.GetInstance().PushObj("Prefabs/Bullet", bulletObj);
```

---

### 5. UI 管理 (UIManager)

完整的 UI 面板管理系统，支持多层级管理和事件绑定。

#### UI 层级

| 层级 | 用途 |
|------|------|
| `Bot` | 底层 UI（背景等） |
| `Mid` | 中层 UI（主界面） |
| `Top` | 上层 UI（提示框） |
| `System` | 系统层 UI（加载遮罩） |

#### 核心 API

```csharp
// 显示面板
void ShowPanel<T>(string panelName, E_UI_Layer layer, UnityAction<T> callBack)

// 隐藏面板
void HidePanel(string panelName)

// 获取已显示的面板
T GetPanel<T>(string name)

// 添加 UI 事件监听
static void AddCustomEventListener(UIBehaviour control, EventTriggerType type, 
    UnityAction<BaseEventData> callBack)
```

#### 使用示例

```csharp
// 显示设置面板
UIManager.GetInstance().ShowPanel<SettingsPanel>("SettingsPanel", E_UI_Layer.Top, 
    (panel) =>
{
    panel.Init();
});

// 为按钮添加点击事件
UIManager.AddCustomEventListener(button, EventTriggerType.PointerClick, 
    (data) =>
{
    Debug.Log("按钮被点击");
});
```

---

### 6. 音频管理 (MusicMgr)

统一管理背景音乐和音效，支持音量控制和音效的自动回收。

#### 核心功能

- **背景音乐**：播放、暂停、停止、音量调节
- **音效**：支持循环音效、自动清理已播放完的音效
- **异步加载**：音频资源采用异步加载，不阻塞主线程

#### 使用示例

```csharp
// 播放背景音乐
MusicMgr.GetInstance().PlayBkMusic("MainTheme");

// 播放音效
MusicMgr.GetInstance().PlaySound("Explosion", false);

// 调节音量
MusicMgr.GetInstance().ChangeBKValue(0.5f);
MusicMgr.GetInstance().ChangeSoundValue(0.8f);
```

---

### 7. Mono 管理器 (MonoMgr)

让非 MonoBehaviour 类也能使用 Unity 的生命周期功能。

#### 核心功能

- 提供 Update 事件订阅
- 提供协程启动能力

#### 使用示例

```csharp
// 添加帧更新监听
MonoMgr.GetInstance().AddUpdateListener(MyUpdate);

// 启动协程
MonoMgr.GetInstance().StartCoroutine(MyCoroutine());

private void MyUpdate()
{
    // 每帧执行的逻辑
}

private IEnumerator MyCoroutine()
{
    yield return new WaitForSeconds(1f);
    Debug.Log("协程执行完毕");
}
```

---

### 8. A* 寻路 (AStarMgr)

经典的 A* 寻路算法实现，支持八方向寻路。

#### 使用示例

```csharp
// 初始化地图 (20x20 的网格)
AStarMgr.GetInstance().InitMapInfo(20, 20);

// 寻路
List<AStarNode> path = AStarMgr.GetInstance().FindPath(
    new Vector2(0, 0),   // 起点
    new Vector2(15, 15)  // 终点
);

if (path != null)
{
    foreach (var node in path)
    {
        Debug.Log($"路径点: ({node.x}, {node.y})");
    }
}
```

---

## 设计模式应用

该框架充分运用了多种设计模式：

| 设计模式 | 应用场景 |
|----------|----------|
| **单例模式** | 所有管理器类的基础架构 |
| **观察者模式** | 事件中心的事件订阅与分发 |
| **对象池模式** | PoolMgr 的对象复用机制 |
| **工厂模式** | ResMgr 的资源加载与实例化 |

---

## 快速开始

### 1. 导入框架

将 `ProjectBase` 文件夹复制到你的 Unity 项目的 Scripts 目录下。

### 2. 配置 Resources

确保在 `Resources` 文件夹下有以下预制体：
- `UI/Canvas` - UI 画布预制体（包含 Bot/Mid/Top/System 四个层级）
- `UI/EventSystem` - 事件系统预制体

### 3. 开始使用

```csharp
using UnityEngine;

public class GameManager : MonoBehaviour
{
    void Start()
    {
        // 注册事件
        EventCenter.GetInstance().AddEventListener("GameStart", OnGameStart);
        
        // 显示主菜单
        UIManager.GetInstance().ShowPanel<MainMenuPanel>("MainMenuPanel", E_UI_Layer.Mid);
        
        // 播放背景音乐
        MusicMgr.GetInstance().PlayBkMusic("MainTheme");
    }
    
    private void OnGameStart()
    {
        Debug.Log("游戏开始！");
    }
}
```

---

## 总结

**GameplayFrameWork** 是我在学习 Unity 游戏开发过程中总结的一套基础框架。它涵盖了游戏开发中最核心的几个系统：

- 资源加载与管理
- 对象池优化
- UI 系统管理
- 事件驱动架构
- 音频管理
- 场景切换
- 寻路系统

通过使用这套框架，可以让开发者更专注于游戏的核心玩法，而不用重复造轮子。希望这个框架能对正在学习 Unity 的朋友有所帮助！

---

## 许可协议

本项目采用 [MIT License](LICENSE) 开源协议。
