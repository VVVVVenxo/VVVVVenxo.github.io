# VVVVVenxo.github.io — Claude Code 项目规范

详情同 `.cursor/rules`，核心约定如下：

## 架构与目录
- **源码分支**：`source`（唯一工作分支）；`gh-pages` 由 GitHub Actions 自动构建生成，勿手改。
- **文章目录**：`source/_posts/*.md`，分类遵循两级结构（`技术笔记` / `项目实战` / `AI探索` / `随笔杂谈` + 具体技术栈如 `C++`、`C#`、`Unity`、`网络`、`算法`、`数据结构`、`计算机基础`、`图形学`、`AI Coding`、`AI Agent`）。
- **站点视觉与交互定制**：
  - `source/css/site-refinement.css`：纸面青绿编辑部配色（明/暗主题）、代码块样式、本地搜索弹窗、移动端折叠目录样式。
  - `source/css/pace-theme-editorial.css`：顶部加载进度条配色。
  - `source/js/site-refinement.js`：首页编辑部导语与精选混排、文章页移动端折叠目录注入。
- **Hexo 构建插件（`scripts/`）**：
  - `scripts/cover-thumbnails.js`：将列表/卡片中的 `/img/covers/gen/*.png` 自动替换为仅含图解的 `-thumb.svg`，保留正文与 OpenGraph 的完整 PNG。
  - `scripts/local-search-index.js`：构建时生成 `search.json` 供 Butterfly 本地搜索使用。
  - `scripts/seo-feeds.js`：构建时生成 `sitemap.xml` 与 `atom.xml`（RSS 订阅源）。
- **程序化封面工具（`tools/covers/`）**：
  - `tools/covers/gen_covers.py`：根据标题和分类生成 `1200×630` 完整封面 SVG 与 `600×360` 缩略图 `-thumb.svg`。
  - `tools/covers/svg2png.py`：调用本机 Chrome/Chromium/Edge 将完整封面 SVG 渲染为 PNG。
  - `tools/covers/new-cover.sh`：一键生成新文章封面并回填 front-matter（`--all` 重刷全部自动封面，不覆盖手动封面）。

## 常用命令
```bash
# 新文章生成封面（写文章时省略 cover 字段）
bash tools/covers/new-cover.sh

# 运行封面与缩略图测试
python -m unittest discover -s tools/covers -p "test_*.py"
node tools/covers/test_thumbnails.cjs

# 本地构建与预览
npm run build
npm run server
```
