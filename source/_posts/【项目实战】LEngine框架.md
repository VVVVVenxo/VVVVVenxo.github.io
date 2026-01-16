---
title: 【项目实战】LEngine 框架
toc: true
categories:
  - 项目实战
  - Unity
cover: /img/covers/game2.jpg
date: 2025-01-15
tags:
  - Unity
  - 框架设计
  - CSharp
  - 热更新
  - YooAsset
  - 商业项目
description: LEngine 是一个模块化、可热更新的 Unity 客户端游戏框架，专为中大型商业项目设计，包含三层架构、YooAsset 资源管理、HybridCLR 热更新、状态机、ET 网络等核心模块。
---

## 项目简介

**LEngine** 是一个模块化、可热更新的 Unity 客户端游戏框架，专为中大型商业游戏项目设计。框架采用清晰的分层架构，将代码分为核心层、模块层和热更新层，支持基于 HybridCLR 的代码热更新方案。

> GitHub 地址: [LEngine](https://github.com/VVenox/LEngine)

## 框架特点

- **模块化架构**：清晰的 Core/Module/HotFix 三层分层设计
- **热更新支持**：基于 HybridCLR 的代码热更新方案
- **资源管理**：基于 YooAsset 的资源加载、热更新、对象池管理
- **UI 框架**：分层窗口管理、窗口栈、消息中心、自动资源管理
- **状态机系统**：完整的游戏状态管理、流程控制
- **网络框架**：基于 ET 的高性能网络通信
- **配置表系统**：基于 MemoryPack 的高性能配置表读取

## 框架架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        业务逻辑层 (Game)                          │
│              具体游戏逻辑、UI实现、玩法系统等                        │
├─────────────────────────────────────────────────────────────────┤
│                       热更新层 (HotFix)                           │
│  GameManager | UIManager | GameStateMgr | SConfigMgr | ECCore   │
│  SceneModule | PerfMgr | ETMgr                                  │
├─────────────────────────────────────────────────────────────────┤
│                   模块层 (Stable.Runtime.Module)                  │
│  ResourceModule | FsmModule | AudioModule | TimerModule         │
│  ObjectPoolModule | ProcedureModule | UpdateDriver              │
├─────────────────────────────────────────────────────────────────┤
│                 核心层 (Stable.Runtime.Core/TEngine)              │
│  ModuleSystem | Log | GameEvent | MemoryPool | GameTime         │
├─────────────────────────────────────────────────────────────────┤
│                     网络层 (Stable.ETCore)                        │
│                   基于ET框架的网络通信实现                          │
├─────────────────────────────────────────────────────────────────┤
│                       启动层 (Launcher)                           │
│                 游戏启动流程、资源初始化                             │
└─────────────────────────────────────────────────────────────────┘
```

## 目录结构

```
Assets/
├── Scripts/
│   ├── Stable/                 # 稳定层（不可热更）
│   │   ├── Runtime/            # 运行时核心
│   │   │   ├── Core/           # 核心层（ModuleSystem、Log、GameEvent 等）
│   │   │   └── Module/         # 模块层（Resource、Audio、Timer 等）
│   │   ├── ETCore/             # ET 网络核心
│   │   ├── Procedure/          # 启动流程
│   │   └── Editor/             # 编辑器扩展
│   └── HotFix/                 # 热更新层
│       ├── Framework/          # 框架代码（UIManager、GameStateMgr 等）
│       │   ├── UIMgr/          # UI 管理系统
│       │   ├── GameState/      # 游戏状态管理
│       │   ├── ECCore/         # 实体组件系统
│       │   └── SConfig/        # 配置表系统
│       └── Common/             # 通用工具（单例、工具类等）
├── Launcher/                   # 启动器
└── ThirdParty/                 # 第三方插件
```

## 核心模块详解

### 1. ModuleSystem 模块管理系统

模块管理系统是框架的核心，负责管理所有底层模块的创建、注册和更新。

```csharp
// 通过接口获取模块（自动创建）
var resourceModule = ModuleSystem.GetModule<IResourceModule>();
var fsmModule = ModuleSystem.GetModule<IFsmModule>();
var audioModule = ModuleSystem.GetModule<IAudioModule>();
```

**特点：**
- 通过接口类型获取模块实例
- 支持模块优先级排序
- 自动管理模块生命周期

---

### 2. ResourceModule 资源管理

基于 YooAsset 封装的资源管理模块，支持资源热更新、多运行模式、资源加密。

#### 运行模式

| 模式 | 说明 |
|------|------|
| EditorSimulateMode | 编辑器模拟模式，无需构建资源包 |
| OfflinePlayMode | 离线模式，使用本地资源包 |
| HostPlayMode | 联机模式，支持资源热更新 |
| WebPlayMode | WebGL 模式 |

#### 使用示例

```csharp
// 获取模块
var resourceModule = GameModule.Resource;

// 同步加载
var prefab = resourceModule.LoadAsset<GameObject>("Assets/Prefabs/Player.prefab");

// 异步加载
var prefab = await resourceModule.LoadAssetAsync<GameObject>("Assets/Prefabs/Player.prefab");

// 加载并实例化
var player = resourceModule.LoadGameObject("Assets/Prefabs/Player.prefab");

// 卸载资源
resourceModule.UnloadAsset(asset);
resourceModule.UnloadUnusedAssets();
```

#### 资源热更新

```csharp
// 初始化资源包
await resourceModule.InitPackage("DefaultPackage");

// 检查更新
var versionOp = resourceModule.RequestPackageVersionAsync();
await versionOp;

// 创建下载器并下载
var downloader = resourceModule.CreateResourceDownloader();
if (downloader.TotalDownloadCount > 0)
{
    downloader.BeginDownload();
    await downloader;
}
```

---

### 3. UIManager UI 管理系统

完整的 UI 管理框架，提供分层窗口管理、窗口栈、消息中心等功能。

#### UI 层级

| 层级 | 说明 | OrderInLayer |
|------|------|--------------|
| SceneLayer | 场景 UI 层 | 0 |
| NormalLayer | 普通 UI 层 | 1000 |
| PopupLayer | 弹窗层 | 2000 |
| LoadingLayer | 加载层 | 3000 |
| TopLayer | 顶层 | 4000 |

#### 窗口定义

使用特性标注定义窗口：

```csharp
[UIWindow(
    PrefabPath = "Assets/UI/Prefabs/UILogin.prefab",
    LayerName = UILayersConfig.NormalLayer,
    ScreenType = ScreenType.Full,
    IsStack = true
)]
public class UILogin : UIViewBase
{
    private Button _btnLogin;
    private InputField _inputName;

    public override void OnCreate()
    {
        base.OnCreate();
        _btnLogin = Root.transform.Find("BtnLogin").GetComponent<Button>();
        _inputName = Root.transform.Find("InputName").GetComponent<InputField>();
        _btnLogin.onClick.AddListener(OnLoginClick);
    }

    public override void OnShow(params object[] args)
    {
        base.OnShow(args);
        // 显示时的逻辑
    }

    public override void OnDestroy()
    {
        _btnLogin.onClick.RemoveListener(OnLoginClick);
        base.OnDestroy();
    }

    private void OnLoginClick()
    {
        GameManager.GameStateMgr.ChangeState<PlayingState>();
    }
}
```

#### 窗口操作

```csharp
// 打开窗口
await GameManager.UIManager.OpenWindow<UILogin>();

// 带参数打开
await GameManager.UIManager.OpenWindow<UIShop>(shopType, itemId);

// 关闭窗口（隐藏但不销毁）
GameManager.UIManager.CloseWindow<UILogin>();

// 销毁窗口
GameManager.UIManager.DestroyWindow<UILogin>();

// 获取窗口实例
var loginUI = GameManager.UIManager.GetWindow<UILogin>();
```

#### UIViewBase 生命周期

```
OnCreate()      -> 窗口创建时
    ↓
OnShow(args)    -> 窗口显示时
    ↓
OnUpdate()      -> 每帧更新（需实现 IUIUpdatable）
    ↓
OnHide()        -> 窗口隐藏时
    ↓
OnDestroy()     -> 窗口销毁时
```

#### 消息中心

```csharp
// 注册消息
GameManager.UIManager.Messages.Register("MESSAGE_NAME", OnMessageReceived);

// 发送消息
GameManager.UIManager.Messages.Broadcast("MESSAGE_NAME", data);

// 移除消息
GameManager.UIManager.Messages.Unregister("MESSAGE_NAME", OnMessageReceived);
```

---

### 4. GameStateMgr 游戏状态管理

完整的游戏状态机系统，用于管理游戏的状态切换。

#### 定义状态

```csharp
public class LoginState : GameStateBase
{
    public override string StateName => "Login";

    public override void OnInit()
    {
        // 状态初始化（只调用一次）
    }

    protected override async UniTask OnEnterAsync()
    {
        Log.Info("进入登录状态");
        await GameManager.UIManager.OpenWindow<UILogin>();
    }

    protected override async UniTask OnLeaveAsync()
    {
        GameManager.UIManager.CloseWindow<UILogin>();
        await UniTask.CompletedTask;
    }

    public override void OnUpdate(float deltaTime)
    {
        // 每帧更新
    }
}
```

#### 状态操作

```csharp
// 注册状态
GameManager.GameStateMgr.RegisterState<LoginState>();
GameManager.GameStateMgr.RegisterState<LoadingState>();
GameManager.GameStateMgr.RegisterState<PlayingState>();

// 启动状态机
GameManager.GameStateMgr.Start<LoginState>();

// 切换状态
GameManager.GameStateMgr.ChangeState<PlayingState>();

// 带参数切换
var context = new LoadingContext { SceneName = "GameScene" };
GameManager.GameStateMgr.ChangeState<LoadingState>(context);

// 检查当前状态
if (GameManager.GameStateMgr.IsInState<PlayingState>())
{
    // ...
}
```

#### 状态生命周期

```
RegisterState()  -> 注册状态
    ↓
OnInit()         -> 初始化（只调用一次）
    ↓
OnEnterAsync()   -> 进入状态
    ↓
OnUpdate()       -> 每帧更新
    ↓
OnLeaveAsync()   -> 离开状态
    ↓
OnDestroy()      -> 销毁（游戏退出时）
```

---

### 5. EventSystem 事件系统

灵活的事件系统，支持强类型泛型事件。

#### 基本用法

```csharp
// 注册事件
EventMgr.Dispatcher.AddEventListener("PlayerDead", OnPlayerDead);

// 发送事件
EventMgr.Dispatcher.DispatchEvent("PlayerDead", playerData);

// 移除事件
EventMgr.Dispatcher.RemoveEventListener("PlayerDead", OnPlayerDead);
```

#### 强类型事件（推荐）

```csharp
// 定义事件类型
public class PlayerDeadEvent
{
    public int PlayerId;
    public string PlayerName;
    public Vector3 Position;
}

// 注册
dispatcher.AddEventListener<PlayerDeadEvent>(OnPlayerDead);

// 发送
dispatcher.DispatchEvent(new PlayerDeadEvent {
    PlayerId = 1,
    PlayerName = "Player1",
    Position = Vector3.zero
});

// 处理
private void OnPlayerDead(PlayerDeadEvent evt)
{
    Log.Info($"玩家 {evt.PlayerName} 死亡");
}
```

#### GameEvent 静态事件

```csharp
// 定义事件
public static class GameEvents
{
    public static GameEvent<int> OnScoreChanged = new();
    public static GameEvent<PlayerData> OnPlayerSpawn = new();
}

// 注册
GameEvents.OnScoreChanged.Register(OnScoreChanged);

// 发送
GameEvents.OnScoreChanged.Invoke(100);

// 移除
GameEvents.OnScoreChanged.Unregister(OnScoreChanged);
```

---

### 6. ObjectPoolModule 对象池

高级对象池实现，支持容量管理、过期时间、自动释放。

```csharp
// 获取模块
var objectPoolModule = ModuleSystem.GetModule<IObjectPoolModule>();

// 创建对象池
var pool = objectPoolModule.CreateSingleSpawnObjectPool<MyObject>(
    name: "MyObjectPool",
    capacity: 100,
    expireTime: 60f
);

// 从池中获取对象
var obj = pool.Spawn();

// 归还对象
pool.Unspawn(obj);

// 释放所有未使用的对象
pool.ReleaseAllUnused();
```

#### 自定义可池化对象

```csharp
public class BulletObject : ObjectBase
{
    public static BulletObject Create(GameObject go)
    {
        var obj = MemoryPool.Acquire<BulletObject>();
        obj.Initialize(go);
        return obj;
    }

    protected override void OnSpawn()
    {
        // 从池中取出时调用
    }

    protected override void OnUnspawn()
    {
        // 归还池中时调用
    }

    protected override void Release(bool isShutdown)
    {
        // 释放时调用
    }
}
```

---

### 7. AudioModule 音频管理

完整的音频管理模块，支持 BGM、音效、音量分组控制。

```csharp
// 获取模块
var audioModule = GameModule.Audio;

// 播放背景音乐
audioModule.PlayMusic("MainTheme");
audioModule.PlayMusic("BattleTheme", fadeTime: 1.0f);  // 淡入淡出

// 播放音效
audioModule.PlaySound("ButtonClick");
audioModule.PlaySound("Explosion", volume: 0.8f);
audioModule.PlaySoundAtPosition("Footstep", position);  // 3D 音效

// 音量控制
audioModule.SetMasterVolume(0.8f);
audioModule.SetMusicVolume(0.5f);
audioModule.SetSoundVolume(0.7f);
audioModule.SetMute(true);

// 暂停/恢复/停止
audioModule.PauseMusic();
audioModule.ResumeMusic();
audioModule.StopMusic();
```

---

### 8. TimerModule 定时器

定时器模块，支持延迟调用和重复调用。

```csharp
// 延迟调用
GameModule.Timer.AddTimer(2.0f, () => {
    Log.Info("2秒后执行");
});

// 重复调用
GameModule.Timer.AddTimer(1.0f, () => {
    Log.Info("每秒执行");
}, repeat: -1);  // -1 表示无限重复

// 带 ID 的定时器（方便取消）
var timerId = GameModule.Timer.AddTimer(5.0f, OnTimerComplete);
GameModule.Timer.RemoveTimer(timerId);
```

---

### 9. ProcedureModule 流程管理

游戏启动流程管理，确保资源初始化、热更下载、程序集加载按顺序执行。

```
ProcedureLaunch (启动)
    ↓
ProcedureInitPackage (初始化资源包)
    ↓
ProcedureInitResources (初始化资源)
    ↓
ProcedureClearCache (清理缓存，可选)
    ↓
ProcedureCreateDownloader (创建下载器)
    ↓
ProcedureDownloadFile (下载资源)
    ↓
ProcedureDownloadOver (下载完成)
    ↓
ProcedurePreload (预加载)
    ↓
ProcedureSplash (闪屏)
    ↓
ProcedureLoadAssembly (加载热更程序集)
    ↓
ProcedureStartGame (启动游戏)
    ↓
GameApp.Entrance() (热更入口)
```

---

## LEngine vs GameplayFrameWork 对比

| 对比项 | GameplayFrameWork | LEngine |
|--------|-------------------|---------|
| **定位** | 学习/小型项目 | 中大型商业项目 |
| **架构** | 单层单例模式 | Stable/HotFix 分层架构 |
| **资源管理** | Unity Resources | YooAsset（热更、加密、多模式） |
| **异步支持** | 协程 + 回调 | UniTask async/await |
| **热更新** | 不支持 | HybridCLR 代码热更 |
| **UI 系统** | 4 层简单管理 | 多层级 + 窗口栈 + 消息中心 + 特性标注 |
| **事件系统** | 字符串事件名 | 强类型泛型事件 |
| **对象池** | 简单 Dictionary | 容量、过期时间、自动释放 |
| **状态管理** | 无 | GameStateMgr 完整状态机 |
| **网络** | 无 | ET 高性能网络框架 |
| **配置表** | 无 | SConfig 配置表系统 |
| **实体系统** | 无 | 轻量级 EC 系统 |
| **流程控制** | 无 | ProcedureModule 启动流程 |
| **日志系统** | Debug.Log | 统一 Log 系统 |
| **依赖项** | DOTween | YooAsset + UniTask + DOTween |

---

## 核心升级点详解

### 1. 三层架构分离

**GameplayFrameWork**：所有代码在一起，无法热更新。

**LEngine**：
- **Core 层**：核心功能，不可热更
- **Module 层**：功能模块，不可热更
- **HotFix 层**：业务逻辑，可热更新

这种分层使得业务代码可以在不重新发版的情况下更新。

### 2. YooAsset 资源系统

**GameplayFrameWork**：使用 Resources 文件夹，无法热更资源。

**LEngine**：
- 支持资源热更新
- 多种运行模式（编辑器模拟/离线/联机/WebGL）
- 资源加密保护
- 断点续传下载
- 资源版本管理

### 3. 完整状态机系统

**GameplayFrameWork**：无状态管理，需要手动控制游戏流程。

**LEngine**：
- 完整的状态生命周期（Init/Enter/Update/Leave/Destroy）
- 支持异步状态切换
- 状态间数据传递
- 状态变更事件监听

### 4. 高级 UI 框架

**GameplayFrameWork**：简单的 4 层管理，手动加载预制体。

**LEngine**：
- 特性标注定义窗口
- 自动资源加载/销毁
- 窗口栈管理（返回上一界面）
- 内置消息中心
- 完整的生命周期

### 5. 异步优先设计

**GameplayFrameWork**：协程 + 回调，代码嵌套深。

**LEngine**：
- 全面使用 UniTask
- async/await 语法
- 代码更简洁可读
- 支持取消令牌

### 6. 强类型事件系统

**GameplayFrameWork**：字符串事件名，容易拼写错误。

**LEngine**：
- 泛型事件类型
- 编译期类型检查
- 更好的 IDE 支持
- 静态事件定义

### 7. 商业级功能支持

**LEngine** 额外提供：
- ET 网络框架
- SConfig 配置表系统
- EC 实体组件系统
- 流程管理
- 性能监控（PerfMgr）

---

## 快速开始

### 环境要求

- Unity 2021.3 LTS 或更高版本
- .NET Standard 2.1

### 依赖项

| 依赖 | 说明 | 必需 |
|------|------|------|
| YooAsset | 资源管理 | 是 |
| UniTask | 异步支持 | 是 |
| MemoryPack | 序列化 | 是 |
| HybridCLR | 热更新 | 可选 |
| DOTween | 动画 | 可选 |

### 基本使用

```csharp
public partial class GameApp
{
    private static async void StartGameLogic()
    {
        // 1. 注册基础管理器
        await GameManager.RegisterBaseManagersAsync();
        GameManager.PerfMgr.DoInit();
        
        // 2. 设置扩展状态注册回调（可选，在 GameStateMgr 初始化前设置）
        // GameStateMgr.OnRegisterExtensionStates = RegisterBusinessStates;
        
        // 3. 注册游戏管理器（UIManager、GameStateMgr 等）
        // 注意：GameStateMgr 会自动注册 LoginState、LoadingState、PlayingState
        GameManager.RegisterGameManagers();
        
        // 4. 启动状态机
        GameManager.GameStateMgr.Start<LoginState>();
    }
    
    /// <summary>
    /// 注册业务层自定义状态（由 GameStateMgr 回调）
    /// </summary>
    private static void RegisterBusinessStates(GameStateMgr stateMgr)
    {
        // 注册业务层的自定义状态
        // stateMgr.RegisterState<YourCustomState>();
    }
}
```

### 常用 API 速查

```csharp
// 模块访问
GameModule.Resource.LoadAsset<T>(path);
GameModule.Audio.PlaySound(clipName);
GameModule.Timer.AddTimer(delay, callback);

// UI 操作
await GameManager.UIManager.OpenWindow<UILogin>();
GameManager.UIManager.CloseWindow<UILogin>();
GameManager.UIManager.DestroyWindow<UILogin>();

// 状态切换
GameManager.GameStateMgr.ChangeState<PlayingState>();

// 事件系统
EventMgr.Dispatcher.AddEventListener("EventName", handler);
EventMgr.Dispatcher.DispatchEvent("EventName", data);
```

---

## 总结

**LEngine** 是 **GameplayFrameWork** 的商业级升级版本，主要升级点包括：

- Stable/HotFix 分层架构支持代码热更新
- YooAsset 资源热更新方案
- 完整的游戏状态机（GameStateMgr）
- 高级 UI 框架（窗口栈、消息中心、特性标注）
- UniTask 异步支持
- 强类型事件系统
- ET 网络框架集成
- SConfig 配置表系统
- 性能监控（PerfMgr）

如果你正在开发中大型商业游戏项目，LEngine 提供了更完善的基础设施，让你专注于业务逻辑开发。

---

## 许可协议

本项目采用 [MIT License](LICENSE) 开源协议。
