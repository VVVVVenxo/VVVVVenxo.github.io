---
title: 【Unity】内存与资源管理
toc: true
categories:
  - 技术笔记
  - Unity
cover: /img/covers/game.jpg
date: 2025-06-05
tags:
  - 资源加载
  - 对象池
  - GC
  - 热更新
description: 详解 Unity 内存与资源管理：资源加载、对象池、GC 原理与优化、AB 包热更新。
---

## Resources 资源加载

通过代码动态加载 `Resources` 文件夹下指定路径的资源。

### 同步加载

```csharp
TextAsset ta = Resources.Load<TextAsset>("Tex/TextJPG");
```

**注意**：预设体加载后**必须实例化**：

```csharp
GameObject prefab = Resources.Load<GameObject>("Prefabs/Enemy");
GameObject enemy = Instantiate(prefab);  // 实例化
```

### 异步加载

同步加载大资源会造成程序卡顿。异步加载内部新开线程，不阻塞主线程。

#### 方式一：事件监听

```csharp
void Start()
{
    ResourceRequest rq = Resources.LoadAsync<Texture>("Tex/TextJPG");
    rq.completed += LoadOver;
}

private void LoadOver(AsyncOperation rq)
{
    Texture tex = (rq as ResourceRequest).asset as Texture;
}
```

#### 方式二：协程

```csharp
IEnumerator LoadResource()
{
    ResourceRequest rq = Resources.LoadAsync<Texture>("Tex/TextJPG");
    yield return rq;
    
    Texture tex = rq.asset as Texture;
}
```

---

## ScriptableObject

ScriptableObject 是一种**轻量级数据容器**，用于共享配置数据或资源。

| 特点 | 说明 |
|------|------|
| 不挂载到 GameObject | 减少场景内存占用 |
| 数据持久化 | 修改后数据会保存 |
| 多处共享 | 多个对象引用同一份数据 |

### 使用场景

- 配置表（技能参数、关卡数据）
- 共享资源（物品数据库）
- 事件通道（ScriptableObject Event）

```csharp
[CreateAssetMenu(fileName = "SkillData", menuName = "Data/Skill")]
public class SkillData : ScriptableObject
{
    public string skillName;
    public int damage;
    public float cooldown;
}
```

---

## 对象池（Object Pool）

对象池通过**重复利用已创建的对象**，减少频繁的实例化和销毁。

### 适用场景

- 子弹、敌人、特效
- 其他频繁生成销毁的对象

### 实现示例

```csharp
public class GameObjectPool : MonoBehaviour
{
    [SerializeField] private GameObject prefab;
    private Queue<GameObject> pool = new Queue<GameObject>();
    
    public GameObject Get()
    {
        GameObject obj;
        if (pool.Count > 0)
        {
            obj = pool.Dequeue();
            obj.SetActive(true);
        }
        else
        {
            obj = Instantiate(prefab);
        }
        return obj;
    }
    
    public void Return(GameObject obj)
    {
        obj.SetActive(false);
        pool.Enqueue(obj);
    }
}
```

**注意**：对象池不能解决实例化卡顿，只是把卡顿**提前**到预热阶段。

---

## AB 包与热更新

AB 包是**特定于平台的资产压缩包**，包括模型、贴图、预设体等。

| 作用 | 说明 |
|------|------|
| 减小包体 | 资源按需下载 |
| 热更新 | 无需重新发布即可更新资源 |
| 按需加载 | 只加载需要的资源 |

### 加载示例

```csharp
AssetBundle bundle = AssetBundle.LoadFromFile(path);
GameObject prefab = bundle.LoadAsset<GameObject>("EnemyPrefab");
bundle.Unload(false);  // 不卸载已加载的资源
```

---

## GC 概述

作为游戏程序员，需要了解三种 GC：

| GC 类型 | 说明 |
|---------|------|
| Unity GC（Mono Runtime GC） | Unity 使用的 GC |
| C# GC（CLR GC） | .NET 标准 GC |
| Lua GC | Lua 脚本的 GC |

### GC 与堆内存的关系

Unity 的托管堆内存由 Mono 分配和管理。**"托管"** 意味着 Mono 可以自动调整堆大小、适时调用 GC。

> **优化 GC = 优化堆内存 = 减少堆内存分配 + 及时回收**

---

## GC 触发时机

### 被动触发

GC 会不时自动运行（频率因平台而异）。

### 主动触发

| 接口 | 说明 |
|------|------|
| `Resources.UnloadUnusedAssets()` | Mono GC，内部会调用 `GC.Collect()` |
| `GC.Collect()` | C# GC |
| `Resources.UnloadAsset()` | 强制卸载资源（无论是否在使用） |

---

## 分代回收原理

CLR 为每个托管堆对象定义**代数（Generation）**：

| 代 | 说明 | 预算容量 |
|----|------|----------|
| 第 0 代 | 新创建的对象 | 256KB - 4MB |
| 第 1 代 | 经历过 1 次 GC 未被回收 | 512KB - 4MB |
| 第 2 代 | 经历过 2 次以上 GC 未被回收 | 不受限制 |

**优势**：优先回收第 0 代（大部分新对象生命周期短），避免直接清理整个堆导致的卡顿。

---

## GC 优化方法

### 一、字符串操作

使用 `StringBuilder` 并重用：

```csharp
private readonly StringBuilder _builder = new StringBuilder();

public string Concatenate(string a, string b)
{
    _builder.Clear();
    _builder.Append(a).Append(b);
    return _builder.ToString();
}
```

### 二、集合与循环

预分配集合并重用：

```csharp
private readonly List<int> _list = new List<int>(100);

private void Update()
{
    _list.Clear();  // 重用而非重新创建
    for (int i = 0; i < 100; i++)
        _list.Add(i);
}
```

对 `List` 或数组使用 `for` 循环（`foreach` 遍历 Dictionary 可能产生 GC）。

### 三、委托与 Lambda

Lambda 捕获局部变量会产生闭包分配：

```csharp
// 避免：捕获局部变量产生 GC
int count = 0;
InvokeAction(() => { count++; });

// 建议：使用静态方法
InvokeAction(StaticMethod);
```

### 四、装箱（Boxing）

使用泛型约束避免装箱：

| 场景 | 优化 |
|------|------|
| `String.Format("{0}", cost)` | 使用 `$"{cost}"` 或 `ToString()` |
| `yield return 0` | 使用 `yield return null` |
| LINQ 和正则表达式 | 热点代码中尽量少用 |

### 五、Unity API 优化

| 原写法 | 优化写法 |
|--------|----------|
| `gameObject.tag == "Player"` | `gameObject.CompareTag("Player")` |
| `GetComponent<T>()` 每帧调用 | 缓存引用 |

---

## GC 优化总结

| 类别 | 优化方法 |
|------|----------|
| 字符串 | 使用 `StringBuilder`，避免拼接 |
| 集合 | 预分配、`Clear()` 重用 |
| 循环 | 用 `for` 代替 `foreach` |
| 委托 | 避免 Lambda 捕获变量 |
| 装箱 | 使用泛型，避免值类型转 `object` |
| 对象 | 使用对象池 |
| 时机 | 在 Loading 时手动触发 GC |
| 缓存 | 缓存组件引用、减少 API 调用 |

---

## Mono 与 IL2CPP

| 特性 | Mono | IL2CPP |
|------|------|--------|
| 编译方式 | JIT（即时编译） | AOT（预先编译） |
| 运行效率 | 较低 | 较高 |
| 包体大小 | 较小 | 较大 |
| 热更新 | 支持 | 需要特殊处理 |

---

## 资源管理最佳实践

| 场景 | 建议 |
|------|------|
| 小型资源、原型开发 | `Resources.Load` |
| 大型项目、需要热更新 | AssetBundle 或 Addressables |
| 频繁创建销毁的对象 | 对象池 |
| 共享配置数据 | ScriptableObject |
| 大资源加载 | 异步加载 + Loading 界面 |
| GC 优化 | 在 Loading 时手动触发 |
