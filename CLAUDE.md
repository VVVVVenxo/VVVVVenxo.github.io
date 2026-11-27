# VVVVVenxo.github.io — Claude Code 项目规范

详情同 `.cursor/rules`，核心约定如下：

## 架构与目录
- **源码分支**：`source`（唯一工作分支）；`gh-pages` 由 GitHub Actions 自动构建生成，勿手改。
- **文章目录**：`source/_posts/*.md`，分类遵循两级结构（`技术笔记` / `项目实战` / `AI探索` / `随笔杂谈` + 具体技术栈如 `C++`、`C#`、`Unity`、`网络`、`算法`、`数据结构`、`计算机基础`、`图形学`、`AI Coding`、`AI Agent`）。
- **Astro + Tailwind v4 平铺编辑部前端架构（`src/`）**：
  - `astro.config.mjs`：Astro 站点配置，通过 `sourceAssetsBridge` 将 `source/img` 映射为静态资源并输出构建产物至 `./public`。
  - `src/styles/global.css`：暖米纸 + 陶土红棕（`#f7f5ef` / `#9b442a`，暗黑模式 `#201f1c` / `#e6a082`）平铺编辑部样式与 Shiki 双主题代码样式。
  - `src/layouts/BaseLayout.astro`：全局顶栏、页脚、明暗主题切换、代码块一键复制与全站 `Ctrl+K` 搜索弹窗。
  - `src/lib/posts.ts`：读取 `source/_posts/*.md`，基于 Marked + Shiki 双主题高亮渲染 Markdown，保持 `/:year/:month/:day/:slug/` 原永久链接兼容。
  - `src/pages/`：首页（`index.astro`）、博客列表（`blog/index.astro`）、文章详情页（`[year]/[month]/[day]/[slug]/index.astro`）、分类/标签页、关于页以及 `search.json.ts` / `atom.xml.ts` / `sitemap.xml.ts`。
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
