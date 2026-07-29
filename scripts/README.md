# 文章封面自动生成

按文章分类程序化生成统一风格的封面：三色极光霓虹 + 全息轨道骨架 + 分类专属中景元素。每篇封面还会按标题稳定改变极光曲线、轨道角度和粒子位置，避免同分类撞图。

## 写新文章后，一键生成封面

```bash
bash scripts/new-cover.sh
```

它会：
1. 扫描 `source/_posts/`，给**还没有 `cover:` 字段**的文章生成封面 SVG，并写入 `cover:` 指向生成的 PNG；
2. 把 SVG 转成 PNG（用 headless Chrome）；
3. 打印改动，等你确认后手动 `git commit && git push`。

已有 `cover:` 的文章会被跳过（尊重手动指定的封面，比如项目实战用真实截图）。

## 重新生成全部封面

改了配色 / 风格后，强制刷新所有：

```bash
bash scripts/new-cover.sh --all
```

## 视觉规则

- 每个分类一套三色霓虹调色板，定义在 `scripts/gen_covers.py` 的 `PALETTES`
- 全站统一「极光 + 全息轨道 + 霓虹标题」骨架
- 分类中景：C++/C# 轨道、Unity/图形学棱镜、网络波纹、算法/数据结构节点图、计算机基础电路、随笔星轨、项目实战玻璃面板
- 新增分类时在 `PALETTES` 和 `VARIANTS` 各加一行；未定义分类使用默认蓝紫粉极光
- `--all` 只重绘自动生成的封面，始终保留手动指定的真实项目截图

## 依赖

- Python 3
- 本地安装了 Chrome / Chromium / Edge（脚本自动探测，或设 `CHROME_BIN` 环境变量）
