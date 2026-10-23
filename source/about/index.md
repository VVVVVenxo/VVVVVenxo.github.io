---
title: 关于与知识图谱
date: 2024-01-01 00:00:00
type: "about"
comments: false
---

## 关于我

你好，我是 **VVVVVenxo**！

一名软件工程专业背景的游戏开发者，目前在 **上海某游戏大厂** 担任游戏客户端开发。这个博客是我的**游戏客户端工程手记**，用来沉淀从编程语言底层、游戏引擎核心机制、客户端架构设计到实时图形与 AI 工具链的工程思考。

> *To be a rock and not to roll.*

- **主力方向**：Unity 商业项目客户端开发、底层性能优化、框架与工具链研发
- **技术兴趣**：游戏客户端架构 / 网络同步 / 计算机图形学与实时渲染 / AI Agent 工程实践
- **常用语言与引擎**：C#、C++、Lua、Python · Unity、Unreal Engine

---

## 知识图谱与阅读路线

站点目前已收录 **38 篇** 体系化文章。如果你第一次来到这里，可以按下面的专题脉络检索阅读：

<div class="site-roadmap-grid">
  <div class="site-roadmap-card">
    <div class="site-roadmap-card__eyebrow">01 · ENGINE &amp; RUNTIME</div>
    <h3>Unity 引擎核心与性能优化</h3>
    <p>从生命周期、协程/多线程、UI 源码到合批渲染、内存管理与 xLua 热更新机制。</p>
    <ul>
      <li><a href="/2026/10/22/%E3%80%90Unity%E3%80%91URP%E6%B8%B2%E6%9F%93%E7%AE%A1%E7%BA%BF%E6%9E%B6%E6%9E%84%E4%B8%8ERenderFeature%E5%AE%9E%E6%88%98/">URP 渲染管线架构与 RenderFeature 后处理实战</a></li>
      <li><a href="/2026/10/20/%E3%80%90Unity%E3%80%91Lua%E7%BC%96%E7%A8%8B%E4%B8%8ExLua%E7%83%AD%E6%9B%B4%E6%96%B0%E6%9C%BA%E5%88%B6/">Lua 编程与 xLua 热更新机制</a></li>
      <li><a href="/2026/07/29/%E3%80%90Unity%E3%80%91UGUI%E6%BA%90%E7%A0%81%E8%A7%A3%E8%AF%BB/">UGUI 源码解读：Canvas、Layout 与事件</a></li>
      <li><a href="/2026/07/28/%E3%80%90Unity%E3%80%91DrawCall%E4%B8%8E%E5%90%88%E6%89%B9%E4%BC%98%E5%8C%96/">DrawCall 与合批优化（SRP Batcher / GPU Instancing）</a></li>
      <li><a href="/2026/07/28/%E3%80%90Unity%E3%80%91GC%E5%8E%9F%E7%90%86%E4%B8%8E%E4%BC%98%E5%8C%96/">Boehm GC 原理与零 GC 编码优化</a></li>
      <li><a href="/2026/07/28/%E3%80%90Unity%E3%80%91%E8%B5%84%E6%BA%90%E5%8A%A0%E8%BD%BD%E4%B8%8E%E7%83%AD%E6%9B%B4%E6%96%B0/">资源加载体系与 AssetBundle 热更新</a></li>
      <li><a href="/2025/06/05/%E3%80%90Unity%E3%80%91%E5%86%85%E5%AD%98%E4%B8%8E%E8%B5%84%E6%BA%90%E7%AE%A1%E7%90%86/">内存分布与资源生命周期管理</a></li>
      <li><a href="/2025/06/05/%E3%80%90Unity%E3%80%91UI%E4%B8%8E%E6%B8%B2%E6%9F%93%E4%BC%98%E5%8C%96/">UI 重建与渲染管线性能调优</a></li>
      <li><a href="/2025/06/05/%E3%80%90Unity%E3%80%91%E5%8D%8F%E7%A8%8B%E4%B8%8E%E5%A4%9A%E7%BA%BF%E7%A8%8B/">协程状态机与多线程同步机制</a></li>
      <li><a href="/2025/06/05/%E3%80%90Unity%E3%80%91%E5%8A%A8%E7%94%BB%E7%B3%BB%E7%BB%9F/">Animator、Playables 与动画系统</a> · <a href="/2025/06/05/%E3%80%90Unity%E3%80%91%E7%89%A9%E7%90%86%E7%B3%BB%E7%BB%9F/">物理系统</a> · <a href="/2025/06/05/%E3%80%90Unity%E3%80%91%E7%94%9F%E5%91%BD%E5%91%A8%E6%9C%9F%E5%87%BD%E6%95%B0/">生命周期</a></li>
    </ul>
  </div>

  <div class="site-roadmap-card">
    <div class="site-roadmap-card__eyebrow">02 · LANGUAGES &amp; MEMORY</div>
    <h3>C++ 与 C# 语言底层机制</h3>
    <p>剖析对象内存模型、虚表、移动语义、STL 容器实现，以及 .NET CLR / IL2CPP 运行时。</p>
    <ul>
      <li><a href="/2025/06/05/%E3%80%90C++%E3%80%91%E6%95%B4%E4%BD%93%E6%A1%86%E6%9E%B6/">【C++】语言核心知识整体框架</a></li>
      <li><a href="/2025/06/05/%E3%80%90C++%E3%80%91%E5%86%85%E5%AD%98%E7%AE%A1%E7%90%86/">【C++】内存管理、智能指针与分配器</a></li>
      <li><a href="/2025/06/05/%E3%80%90C++%E3%80%91%E8%99%9A%E5%87%BD%E6%95%B0/">【C++】虚函数表（vtable）与多态对象布局</a></li>
      <li><a href="/2025/06/05/%E3%80%90C++%E3%80%91%E5%80%BC%E8%AF%AD%E4%B9%89%E4%B8%8E%E7%A7%BB%E5%8A%A8/">【C++】左值/右值、移动语义与完美转发</a></li>
      <li><a href="/2026/07/28/%E3%80%90C++%E3%80%91STL%E4%B8%8E%E5%AE%B9%E5%99%A8%E5%BA%95%E5%B1%82/">【C++】STL 容器底层数据结构与扩容策略</a></li>
      <li><a href="/2025/06/05/%E3%80%90C++%E3%80%91%E5%85%B3%E9%94%AE%E5%AD%97/">【C++】核心关键字</a> · <a href="/2025/06/05/%E3%80%90C++%E3%80%91%E7%B1%BB%E5%9E%8B%E8%BD%AC%E6%8D%A2/">四大类型转换</a></li>
      <li><a href="/2025/06/05/%E3%80%90CSharp%E3%80%91.NET%E5%B9%B3%E5%8F%B0/">【C#】.NET 平台、CLR、CIL 与 JIT/AOT</a></li>
      <li><a href="/2025/06/05/%E3%80%90CSharp%E3%80%91%E7%B1%BB%E5%9E%8B%E4%B8%8E%E5%8F%82%E6%95%B0%E4%BC%A0%E9%80%92/">【C#】值类型/引用类型、拆装箱与参数传递</a></li>
      <li><a href="/2025/06/05/%E3%80%90CSharp%E3%80%91%E5%8F%8D%E5%B0%84%E4%B8%8E%E5%A7%94%E6%89%98/">【C#】反射与委托</a> · <a href="/2025/06/05/%E3%80%90CSharp%E3%80%91%E8%BF%AD%E4%BB%A3%E5%99%A8/">yield 迭代器状态机</a></li>
    </ul>
  </div>

  <div class="site-roadmap-card">
    <div class="site-roadmap-card__eyebrow">03 · ARCHITECTURE &amp; PROJECTS</div>
    <h3>项目实战、图形学与客户端架构</h3>
    <p>现代实时渲染管线与 Shader 编程、大规模自然场景漫游系统与商业级游戏客户端框架。</p>
    <ul>
      <li><a href="/2026/10/21/%E3%80%90%E5%9B%BE%E5%BD%A2%E5%AD%A6%E3%80%91%E7%8E%B0%E4%BB%A3%E6%B8%B2%E6%9F%93%E7%AE%A1%E7%BA%BF%E4%B8%8EShader%E7%BC%96%E7%A8%8B%E7%B2%BE%E8%A6%81/">【图形学】现代渲染管线与 Shader 编程精要（MVP / PBR / GPU 架构）</a></li>
      <li><a href="/2026/01/15/%E3%80%90%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%88%98%E3%80%91OpenGL%E6%BC%AB%E6%B8%B8%E7%B3%BB%E7%BB%9F/">基于 OpenGL 的大规模自然场景实时漫游系统</a></li>
      <li><a href="/2025/01/15/%E3%80%90%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%88%98%E3%80%91LEngine%E6%A1%86%E6%9E%B6/">LEngine 游戏客户端核心框架设计与实现</a></li>
      <li><a href="/2025/01/15/%E3%80%90%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%88%98%E3%80%91GameplayFrameWork%E6%A1%86%E6%9E%B6/">GameplayFramework 模块化战斗与业务框架</a></li>
      <li><a href="/2025/06/05/%E3%80%90%E9%A1%B9%E7%9B%AE%E5%AE%9E%E6%88%98%E3%80%91%E5%93%88%E5%A4%AB%E6%9B%BC%E7%BC%96%E7%A0%81%E5%8E%8B%E7%BC%A9%E7%B3%BB%E7%BB%9F/">哈夫曼编码文件压缩系统设计与实现</a></li>
    </ul>
  </div>

  <div class="site-roadmap-card">
    <div class="site-roadmap-card__eyebrow">04 · NETWORK, ALGORITHMS &amp; AI</div>
    <h3>网络同步、算法与 AI 探索</h3>
    <p>多人实时同步协议、图论寻路与排序算法、操作系统基础，以及 AI Coding 自动化工程。</p>
    <ul>
      <li><a href="/2025/06/05/%E3%80%90%E7%BD%91%E7%BB%9C%E3%80%91%E5%B8%A7%E5%90%8C%E6%AD%A5%E4%B8%8E%E7%8A%B6%E6%80%81%E5%90%8C%E6%AD%A5/">游戏多人网络：帧同步与状态同步深度对比</a></li>
      <li><a href="/2025/06/05/%E3%80%90%E7%BD%91%E7%BB%9C%E3%80%91%E6%B8%B8%E6%88%8F%E5%AE%A2%E6%88%B7%E7%AB%AF%E7%BD%91%E7%BB%9C%E5%9F%BA%E7%A1%80/">游戏客户端网络基础（TCP/UDP/KCP/粘包拆包）</a></li>
      <li><a href="/2026/07/28/%E3%80%90%E8%AE%A1%E7%AE%97%E6%9C%BA%E5%9F%BA%E7%A1%80%E3%80%91%E8%BF%9B%E7%A8%8B%E3%80%81%E5%86%85%E5%AD%98%E4%B8%8E%E7%BD%91%E7%BB%9C/">操作系统核心：进程调度、虚拟内存与网络栈</a></li>
      <li><a href="/2026/07/28/%E3%80%90%E7%AE%97%E6%B3%95%E3%80%91%E5%9B%BE%E4%B8%8E%E6%90%9C%E7%B4%A2%E7%AE%97%E6%B3%95/">图论与搜索算法（DFS/BFS/Dijkstra/A*）</a></li>
      <li><a href="/2026/07/28/%E3%80%90%E7%AE%97%E6%B3%95%E3%80%91%E6%8E%92%E5%BA%8F%E7%AE%97%E6%B3%95%E5%A4%A7%E5%85%A8/">排序算法大全与工程稳定性分析</a> · <a href="/2025/06/05/%E3%80%90%E6%95%B0%E6%8D%AE%E7%BB%93%E6%9E%84%E3%80%91%E5%93%88%E5%B8%8C%E8%A1%A8/">哈希表底层</a></li>
      <li><a href="/2026/07/30/%E3%80%90AI%E6%8E%A2%E7%B4%A2%E3%80%91%E7%94%A8ClaudeCode%E7%BB%B4%E6%8A%A4%E6%8A%80%E6%9C%AF%E5%8D%9A%E5%AE%A2/">【AI 探索】用 Claude Code 维护技术博客</a></li>
      <li><a href="/2026/07/30/%E3%80%90AI%E6%8E%A2%E7%B4%A2%E3%80%91%E8%87%AA%E5%8A%A8%E5%8C%96%E5%B0%81%E9%9D%A2%E7%94%9F%E6%88%90%E7%B3%BB%E7%BB%9F/">【AI 探索】程序化 SVG/PNG 封面生成系统</a></li>
    </ul>
  </div>
</div>

---

## 联系方式

- **GitHub**：[github.com/VVVVVenxo](https://github.com/VVVVVenxo)
- **Email**：[1263147353@qq.com](mailto:1263147353@qq.com)
- **Steam**：[Steam Profile](https://steamcommunity.com/profiles/76561198863443106/)
- **RSS 订阅**：[/atom.xml](/atom.xml)
