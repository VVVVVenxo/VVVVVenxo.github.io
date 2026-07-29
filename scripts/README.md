# 文章封面自动生成

按文章分类程序化生成统一风格的封面（深底 + 细网格 + 分类强调色）。

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

## 配色规则

每个二级分类一个低饱和强调色，见 `scripts/gen_covers.py` 里的 `ACCENT`。
新增分类时在那里加一行即可，未定义的分类用默认灰蓝。

## 依赖

- Python 3
- 本地安装了 Chrome / Chromium / Edge（脚本自动探测，或设 `CHROME_BIN` 环境变量）
