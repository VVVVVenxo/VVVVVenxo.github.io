#!/usr/bin/env python3
"""
按分类程序化生成文章封面（C 风格：深底 + 细网格 + 线框图标）。

用法:
  python gen_covers.py            # 只给缺 cover 的文章生成（CI 用）
  python gen_covers.py --all      # 强制全部重新生成
  python gen_covers.py 关键词      # 只处理标题含关键词的文章（调试用）

生成 SVG 到 source/img/covers/gen/，并把文章 front-matter 的 cover 指向它。
SVG 转 PNG 由 svg2png 步骤完成（headless Chrome）。
"""
import os, re, glob, sys

BASE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(BASE, "source", "_posts")
GEN   = os.path.join(BASE, "source", "img", "covers", "gen")

# 分类 -> 强调色（低饱和，深底上通透）
ACCENT = {
    "Unity":     "#c8ccd4",  # 冷银
    "C++":       "#6ea8fe",  # 柔蓝
    "C#":        "#b18cf0",  # 柔紫
    "网络":       "#6fd0a8",  # 薄荷绿
    "算法":       "#f0b866",  # 琥珀
    "数据结构":   "#5ec8c8",  # 青
    "图形学":     "#f08a80",  # 珊瑚红
    "计算机基础":  "#8fa0e8",  # 靛
    "随笔杂谈":   "#c9b79c",  # 暖沙
    "项目实战":   "#f0968a",  # 砖红
}
DEFAULT_ACCENT = "#8fa3bf"

def get_meta(path):
    txt = open(path, encoding="utf-8").read()
    parts = txt.split("---")
    fm = parts[1]
    title = re.search(r"title:\s*(.+)", fm).group(1).strip()
    end = fm.find("tags:") if "tags:" in fm else len(fm)
    cats = re.findall(r"^\s+-\s*(.+)$", fm[fm.find("categories:"):end], re.M)
    top = cats[0].strip() if cats else ""
    sub = cats[-1].strip() if cats else ""
    has_cover = bool(re.search(r"^cover:\s*\S", fm, re.M))
    return title, top, sub, has_cover

def slugify(title):
    return re.sub(r"[^\w一-鿿]+", "-", title).strip("-")

def make_svg(title, top, sub):
    acc = ACCENT.get(sub, ACCENT.get(top, DEFAULT_ACCENT))
    clean = re.sub(r"^【.+?】", "", title)
    # 标题过长自动缩小字号
    fs = 76 if len(clean) <= 9 else (64 if len(clean) <= 13 else 52)
    grid = ""
    for x in range(0, 1200, 48):
        grid += f'<line x1="{x}" y1="0" x2="{x}" y2="630" stroke="{acc}" stroke-width="1" opacity="0.04"/>'
    for y in range(0, 630, 48):
        grid += f'<line x1="0" y1="{y}" x2="1200" y2="{y}" stroke="{acc}" stroke-width="1" opacity="0.04"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <radialGradient id="bg" cx="0.3" cy="0.4" r="0.9">
      <stop offset="0" stop-color="#1a1e26"/><stop offset="1" stop-color="#0c0e13"/>
    </radialGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  {grid}
  <rect x="100" y="238" width="44" height="44" rx="8" fill="none" stroke="{acc}" stroke-width="2" opacity="0.8"/>
  <circle cx="122" cy="260" r="6" fill="{acc}"/>
  <text x="100" y="370" font-family="'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
        font-size="{fs}" font-weight="700" fill="#eef1f6">{clean}</text>
  <text x="102" y="424" font-family="'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
        font-size="23" fill="{acc}" opacity="0.85" letter-spacing="3">{top} / {sub}</text>
</svg>'''

def main():
    os.makedirs(GEN, exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    force_all = "--all" in sys.argv
    n = 0
    for p in glob.glob(os.path.join(POSTS, "*.md")):
        title, top, sub, has_cover = get_meta(p)
        if args and not any(k in title for k in args):
            continue
        if has_cover and not force_all:
            continue  # 已有 cover，跳过（尊重手动指定）
        slug = slugify(title)
        svg_path = os.path.join(GEN, slug + ".svg")
        open(svg_path, "w", encoding="utf-8").write(make_svg(title, top, sub))
        # 写回 front-matter 的 cover（PNG 路径，转换后生成）
        cover_line = f"cover: /img/covers/gen/{slug}.png"
        txt = open(p, encoding="utf-8").read()
        if re.search(r"^cover:.*$", txt, re.M):
            txt = re.sub(r"^cover:.*$", cover_line, txt, count=1, flags=re.M)
        else:
            # 插到 date 行前，没有就插到第二个 --- 前
            txt = re.sub(r"^(date:.*)$", cover_line + r"\n\1", txt, count=1, flags=re.M)
        open(p, "w", encoding="utf-8").write(txt)
        print(f"[{sub or top}] {title}")
        n += 1
    print(f"generated {n}")

if __name__ == "__main__":
    main()
