# 文章封面自动生成

生成器为每篇文章创建风格统一、主题各异的技术封面：浅灰绿纸面、深色标题，以青绿和少量暖橙强调；左侧排版文章标题与摘要，右侧根据分类绘制主题图解。图解由分类与标题中的主题共同选择；未匹配到具体主题的文章使用对应分类的通用图解。

## 新文章生成封面

在仓库根目录执行：

```bash
bash tools/covers/new-cover.sh
```

脚本会为没有 `cover:` 字段的文章生成 SVG，在 front matter 中写入对应 PNG 路径，再用本机 Chrome/Chromium/Edge 渲染 PNG。已有封面会跳过，方便保留项目截图等手动封面。

## 重新生成自动封面

调整了封面规则后，可强制重绘所有程序生成的封面：

```bash
bash tools/covers/new-cover.sh --all
```

`--all` 不会覆盖 `cover:` 指向其他目录的手动封面。

## 视觉规则

- 保持纸面、深墨、青绿的低饱和基调，暖橙只用于少量重点
- 标题和摘要在左，主题图解在右；图解表达文章核心概念，不用无关装饰填满画面
- 算法文章绘制排序或图搜索过程；C++ 文章绘制内存、虚函数、移动语义或容器结构；Unity 文章绘制生命周期、动画、资源、GC 或渲染流程；网络文章绘制帧同步、状态同步或数据传输时序
- AI Coding 使用电路式的人机协作图；AI Agent 使用规划、工具调用与反馈构成的节点图；封面生成主题展示文章到 SVG/PNG 的处理链路
- 新增主题时，在 `tools/covers/gen_covers.py` 的 `select_variant` 与 `diagram_for` 中添加映射和图解

## 依赖

- Python 3
- 本机安装 Chrome、Chromium 或 Edge（脚本会自动探测；也可设置 `CHROME_BIN`）

## 原图与列表缩略图

- `标题.svg` 与 `标题.png`：1200 × 630，保留标题与摘要，用于完整封面和分享图
- `标题-thumb.svg`：600 × 360，仅展示主题图解，用于首页、侧栏、归档和推荐列表，避免缩小后标题重复或图解被裁切
- Hexo 的 `scripts/cover-thumbnails.js` 在构建时替换有对应缩略图的图片；手动项目截图和分享用的元数据保持不变
- Python 与 shell 工具放在 `tools/covers/`，避免被 Hexo 作为 JavaScript 插件加载

验证生成器：

```bash
python -m unittest discover -s tools/covers -p "test_*.py"
```
