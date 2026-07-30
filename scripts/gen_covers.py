#!/usr/bin/env python3
"""
按分类生成「极光霓虹 + 全息轨道」文章封面。

用法:
  python scripts/gen_covers.py          # 只处理缺 cover 的文章
  python scripts/gen_covers.py --all    # 重绘全部自动生成封面，保留手动封面
  python scripts/gen_covers.py 关键词    # 只处理标题包含关键词的文章

生成 SVG 到 source/img/covers/gen/，并写回 PNG cover 路径。
PNG 由 scripts/svg2png.py 使用 headless Chrome 增量生成。
"""
import glob
import hashlib
import html
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(BASE, "source", "_posts")
GEN = os.path.join(BASE, "source", "img", "covers", "gen")
GENERATED_PREFIX = "/img/covers/gen/"

# 分类 -> (深色背景1, 深色背景2, 霓虹色1, 霓虹色2, 霓虹色3)
PALETTES = {
    "Unity": ("#071b2b", "#160d2c", "#67e8f9", "#60a5fa", "#c084fc"),
    "C++": ("#07142f", "#190c32", "#22d3ee", "#6366f1", "#f052d1"),
    "C#": ("#1d0b35", "#081a2c", "#a78bfa", "#f472b6", "#67e8f9"),
    "网络": ("#042b2c", "#071735", "#34d399", "#22d3ee", "#3b82f6"),
    "算法": ("#2b1705", "#1b0b31", "#fbbf24", "#fb7185", "#8b5cf6"),
    "数据结构": ("#052a2a", "#171038", "#2dd4bf", "#6366f1", "#c084fc"),
    "图形学": ("#2d0a1e", "#091934", "#fb7185", "#e879f9", "#60a5fa"),
    "计算机基础": ("#0b1739", "#20103a", "#67e8f9", "#818cf8", "#d8b4fe"),
    "随笔杂谈": ("#30200b", "#29102d", "#fbbf24", "#fb7185", "#c084fc"),
    "项目实战": ("#2d0c1c", "#101735", "#fb7185", "#8b5cf6", "#22d3ee"),
    "AI Coding": ("#041427", "#120a2c", "#38bdf8", "#22d3ee", "#a855f7"),
    "AI Agent": ("#04121f", "#180a2a", "#5eead4", "#818cf8", "#e879f9"),
}
DEFAULT_PALETTE = ("#101827", "#1e1033", "#67e8f9", "#818cf8", "#f472b6")

# 中景按领域切换，但保留共同的极光、轨道和标题骨架。
VARIANTS = {
    "C++": "orbit",
    "C#": "orbit",
    "Unity": "prism",
    "图形学": "prism",
    "网络": "wave",
    "算法": "nodes",
    "数据结构": "nodes",
    "计算机基础": "circuit",
    "随笔杂谈": "stars",
    "AI Coding": "circuit",
    "AI Agent": "nodes",
}


def get_meta(path):
    text = open(path, encoding="utf-8").read()
    parts = text.split("---")
    if len(parts) < 3:
        raise ValueError(f"invalid front-matter: {path}")
    front_matter = parts[1]
    title_match = re.search(r"^title:\s*(.+)$", front_matter, re.M)
    if not title_match:
        raise ValueError(f"missing title: {path}")
    title = title_match.group(1).strip()
    category_end = front_matter.find("tags:") if "tags:" in front_matter else len(front_matter)
    category_block = front_matter[front_matter.find("categories:"):category_end]
    categories = re.findall(r"^\s+-\s*(.+)$", category_block, re.M)
    top = categories[0].strip() if categories else ""
    sub = categories[-1].strip() if categories else ""
    cover_match = re.search(r"^cover:\s*(.*)$", front_matter, re.M)
    cover = cover_match.group(1).strip() if cover_match else ""
    return text, title, top, sub, cover


def slugify(title):
    return re.sub(r"[^\w一-鿿]+", "-", title).strip("-")


def number(seed, start, end):
    """从标题 hash 稳定映射一个整数，确保同标题每次生成一致。"""
    return start + int(seed[:8], 16) % (end - start + 1)


def esc(value):
    return html.escape(value, quote=True)


def particles(seed, colors):
    dots = []
    for index in range(34):
        digest = hashlib.sha256(f"{seed}:particle:{index}".encode()).hexdigest()
        x = number(digest[0:8], 20, 1180)
        y = number(digest[8:16], 12, 618)
        radius = number(digest[16:24], 8, 28) / 10
        opacity = number(digest[24:32], 18, 68) / 100
        color = colors[index % len(colors)] if index % 5 == 0 else "#ffffff"
        dots.append(
            f'<circle cx="{x}" cy="{y}" r="{radius:.1f}" fill="{color}" opacity="{opacity:.2f}"/>'
        )
    return "".join(dots)


def common_orbits(seed, c1, c2, c3):
    rotation = number(seed[0:8], -12, 12)
    dash1 = number(seed[8:16], 7, 14)
    dash2 = number(seed[16:24], 16, 28)
    return f'''
<g transform="translate(600 315) rotate({rotation})" fill="none" filter="url(#lineGlow)">
  <ellipse rx="350" ry="202" stroke="{c1}" stroke-opacity=".28" stroke-width="1.8" stroke-dasharray="{dash1} 18"/>
  <ellipse rx="412" ry="242" stroke="{c3}" stroke-opacity=".20" stroke-width="1.5" stroke-dasharray="2 {dash2}"/>
  <path d="M-392 -18 A395 218 0 0 1 -175 -190" stroke="{c1}" stroke-width="3.5" opacity=".58"/>
  <path d="M175 190 A395 218 0 0 1 392 18" stroke="{c3}" stroke-width="3.5" opacity=".58"/>
</g>'''


def orbit_variant(seed, c1, c2, c3):
    angle = number(seed[0:8], -18, 18)
    return f'''
<g transform="translate(600 315) rotate({angle})" fill="none" filter="url(#lineGlow)">
  <ellipse rx="285" ry="162" stroke="{c2}" stroke-width="2" stroke-opacity=".24"/>
  <circle cx="-278" cy="-34" r="7" fill="{c1}" stroke="none"/>
  <circle cx="280" cy="42" r="7" fill="{c3}" stroke="none"/>
  <circle cx="-278" cy="-34" r="18" stroke="{c1}" stroke-opacity=".32"/>
  <circle cx="280" cy="42" r="18" stroke="{c3}" stroke-opacity=".32"/>
</g>'''


def prism_variant(seed, c1, c2, c3):
    offset = number(seed[0:8], -45, 45)
    return f'''
<g opacity=".24" filter="url(#softGlow)">
  <polygon points="{95+offset},70 {430+offset},24 {300+offset},305" fill="url(#prismGradient)"/>
  <polygon points="930,35 1180,175 {850+offset//2},310" fill="url(#prismGradient)"/>
  <polygon points="820,445 1145,340 1080,625" fill="url(#prismGradient)"/>
  <path d="M80 520 L335 455 L180 615 Z" fill="none" stroke="{c1}" stroke-opacity=".32"/>
</g>'''


def wave_variant(seed, c1, c2, c3):
    phase = number(seed[0:8], -45, 45)
    paths = []
    colors = (c1, c2, c3)
    for index in range(12):
        y = 418 + index * 10
        lift = 335 - index * 3 + phase
        end = 420 + index * 5
        paths.append(
            f'<path d="M-40 {y} C230 {lift} 430 {520+index*2} 675 {405-index*2} '
            f'S1000 {350+index*3} 1240 {end}" fill="none" stroke="{colors[index % 3]}" '
            f'stroke-width="1.5" opacity="{0.13 + index * 0.018:.2f}"/>'
        )
    return f'<g filter="url(#lineGlow)">{"".join(paths)}</g>'


def nodes_variant(seed, c1, c2, c3):
    nodes = []
    positions = []
    for index in range(9):
        digest = hashlib.sha256(f"{seed}:node:{index}".encode()).hexdigest()
        # 节点放在标题外围，避免遮挡中心。
        side = index % 2
        x = number(digest[0:8], 70, 350) if side == 0 else number(digest[0:8], 850, 1130)
        y = number(digest[8:16], 80, 550)
        positions.append((x, y))
    for index, (x, y) in enumerate(positions):
        nx, ny = positions[(index + 2) % len(positions)]
        color = (c1, c2, c3)[index % 3]
        nodes.append(f'<line x1="{x}" y1="{y}" x2="{nx}" y2="{ny}" stroke="{color}" stroke-opacity=".20"/>' )
        nodes.append(f'<circle cx="{x}" cy="{y}" r="{4 + index % 3}" fill="{color}" opacity=".72"/>' )
        nodes.append(f'<circle cx="{x}" cy="{y}" r="{12 + index % 4 * 2}" fill="none" stroke="{color}" stroke-opacity=".22"/>' )
    return f'<g filter="url(#lineGlow)">{"".join(nodes)}</g>'


def circuit_variant(seed, c1, c2, c3):
    shift = number(seed[0:8], -35, 35)
    return f'''
<g fill="none" stroke-linecap="round" filter="url(#lineGlow)">
  <path d="M40 160 H245 V235 H365" stroke="{c1}" stroke-opacity=".35" stroke-width="2"/>
  <path d="M1160 470 H965 V405 H840" stroke="{c3}" stroke-opacity=".35" stroke-width="2"/>
  <path d="M110 520 H260 V{455+shift} H390" stroke="{c2}" stroke-opacity=".24"/>
  <path d="M1090 110 H930 V{180+shift} H820" stroke="{c2}" stroke-opacity=".24"/>
  <circle cx="245" cy="160" r="6" fill="{c1}" stroke="none"/>
  <circle cx="965" cy="470" r="6" fill="{c3}" stroke="none"/>
  <rect x="338" y="222" width="28" height="28" rx="5" stroke="{c1}" stroke-opacity=".42"/>
  <rect x="834" y="391" width="28" height="28" rx="5" stroke="{c3}" stroke-opacity=".42"/>
</g>'''


def stars_variant(seed, c1, c2, c3):
    angle = number(seed[0:8], -20, 20)
    return f'''
<g transform="rotate({angle} 600 315)" filter="url(#lineGlow)">
  <path d="M100 500 C350 260 750 520 1120 170" fill="none" stroke="{c2}" stroke-width="2" stroke-opacity=".20" stroke-dasharray="2 20"/>
  <path d="M80 460 C390 170 760 490 1140 120" fill="none" stroke="{c1}" stroke-width="1.5" stroke-opacity=".16"/>
  <circle cx="300" cy="315" r="5" fill="{c1}"/><circle cx="905" cy="280" r="5" fill="{c3}"/>
</g>'''


def glass_variant(seed, c1, c2, c3):
    return f'''
<g>
  <rect x="145" y="104" width="910" height="422" rx="38" fill="url(#glassGradient)" stroke="#ffffff" stroke-opacity=".24" stroke-width="1.4"/>
  <path d="M185 150 H340" stroke="{c1}" stroke-width="3" opacity=".78"/>
  <path d="M860 480 H1015" stroke="{c3}" stroke-width="3" opacity=".78"/>
  <circle cx="980" cy="155" r="6" fill="{c1}"/><circle cx="1002" cy="155" r="6" fill="{c2}"/><circle cx="1024" cy="155" r="6" fill="{c3}"/>
</g>'''


def middle_layer(variant, seed, c1, c2, c3):
    if variant == "orbit":
        return orbit_variant(seed, c1, c2, c3)
    if variant == "prism":
        return prism_variant(seed, c1, c2, c3)
    if variant == "wave":
        return wave_variant(seed, c1, c2, c3)
    if variant == "nodes":
        return nodes_variant(seed, c1, c2, c3)
    if variant == "circuit":
        return circuit_variant(seed, c1, c2, c3)
    if variant == "glass":
        return glass_variant(seed, c1, c2, c3)
    return stars_variant(seed, c1, c2, c3)


def make_svg(title, top, sub):
    palette_key = "项目实战" if top == "项目实战" else sub
    bg1, bg2, c1, c2, c3 = PALETTES.get(palette_key, PALETTES.get(sub, DEFAULT_PALETTE))
    variant = "glass" if top == "项目实战" else VARIANTS.get(sub, "stars")
    seed = hashlib.sha256(title.encode()).hexdigest()
    clean_title = re.sub(r"^【.+?】", "", title)
    category_label = top if top == sub else f"{top} / {sub}"
    font_size = 112 if len(clean_title) <= 6 else 92 if len(clean_title) <= 9 else 72 if len(clean_title) <= 13 else 56 if len(clean_title) <= 17 else 44

    y1 = number(seed[0:8], 385, 455)
    y2 = number(seed[8:16], 145, 205)
    y3 = number(seed[16:24], 395, 455)
    y4 = number(seed[24:32], 145, 215)
    y5 = number(seed[32:40], 345, 440)
    particle_svg = particles(seed, (c1, c2, c3))
    orbit_svg = common_orbits(seed, c1, c2, c3)
    middle_svg = middle_layer(variant, seed, c1, c2, c3)

    # 项目卡片内标题略向左，其余封面保持居中。
    if variant == "glass":
        title_x = 600
        title_anchor = "middle"
    else:
        title_x = 600
        title_anchor = "middle"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<defs>
  <radialGradient id="bg" cx="50%" cy="45%" r="82%"><stop stop-color="{bg1}"/><stop offset=".52" stop-color="{bg2}"/><stop offset="1" stop-color="#02030a"/></radialGradient>
  <linearGradient id="auroraA" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{c1}" stop-opacity="0"/><stop offset=".25" stop-color="{c1}" stop-opacity=".82"/><stop offset=".56" stop-color="{c2}" stop-opacity=".70"/><stop offset=".82" stop-color="{c3}" stop-opacity=".72"/><stop offset="1" stop-color="{c3}" stop-opacity="0"/></linearGradient>
  <linearGradient id="auroraB" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{c3}" stop-opacity="0"/><stop offset=".42" stop-color="{c2}" stop-opacity=".56"/><stop offset=".75" stop-color="{c1}" stop-opacity=".58"/><stop offset="1" stop-color="{c1}" stop-opacity="0"/></linearGradient>
  <linearGradient id="neonGradient" x1="0" y1="0" x2="1" y2="0"><stop stop-color="{c1}"/><stop offset=".5" stop-color="{c2}"/><stop offset="1" stop-color="{c3}"/></linearGradient>
  <linearGradient id="titleGradient" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#effcff"/><stop offset=".5" stop-color="#ecebff"/><stop offset="1" stop-color="#fff0fb"/></linearGradient>
  <linearGradient id="prismGradient" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c1}" stop-opacity=".48"/><stop offset=".5" stop-color="{c2}" stop-opacity=".10"/><stop offset="1" stop-color="{c3}" stop-opacity=".44"/></linearGradient>
  <linearGradient id="glassGradient" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff" stop-opacity=".13"/><stop offset=".48" stop-color="#fff" stop-opacity=".035"/><stop offset="1" stop-color="{c2}" stop-opacity=".12"/></linearGradient>
  <filter id="blur48"><feGaussianBlur stdDeviation="48"/></filter>
  <filter id="blur22"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="lineGlow"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="softGlow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="titleGlow" x="-30%" y="-50%" width="160%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
  <radialGradient id="vignette" cx="50%" cy="50%" r="73%"><stop offset=".58" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".70"/></radialGradient>
</defs>
<rect width="1200" height="630" fill="url(#bg)"/>
<path d="M-160 {y1} C100 70 360 520 660 {y2} S1060 90 1360 {y3}" fill="none" stroke="url(#auroraA)" stroke-width="172" filter="url(#blur48)" opacity=".94"/>
<path d="M-100 {y4} C220 500 500 90 800 {y5} S1110 465 1320 140" fill="none" stroke="url(#auroraB)" stroke-width="105" filter="url(#blur22)" opacity=".64"/>
{particle_svg}
{orbit_svg}
{middle_svg}
<rect x="170" y="210" width="860" height="150" rx="75" fill="#02040c" opacity=".18" filter="url(#blur22)"/>
<text x="{title_x}" y="322" font-family="'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif" font-size="{font_size}" font-weight="900" fill="url(#neonGradient)" opacity=".72" text-anchor="{title_anchor}" filter="url(#titleGlow)">{esc(clean_title)}</text>
<text x="{title_x}" y="322" font-family="'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif" font-size="{font_size}" font-weight="900" fill="url(#titleGradient)" stroke="#090b18" stroke-width="1.2" paint-order="stroke" text-anchor="{title_anchor}">{esc(clean_title)}</text>
<rect x="450" y="354" width="300" height="44" rx="22" fill="#070a18" opacity=".64" stroke="{c2}" stroke-opacity=".42"/>
<text x="600" y="383" font-family="'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif" font-size="20" fill="#eef2ff" text-anchor="middle" letter-spacing="5">{esc(category_label)}</text>
<rect width="1200" height="630" fill="url(#vignette)" pointer-events="none"/>
</svg>'''


def write_cover(path, text, title, top, sub):
    slug = slugify(title)
    svg_path = os.path.join(GEN, slug + ".svg")
    open(svg_path, "w", encoding="utf-8").write(make_svg(title, top, sub))
    cover_line = f"cover: {GENERATED_PREFIX}{slug}.png"
    if re.search(r"^cover:.*$", text, re.M):
        text = re.sub(r"^cover:.*$", cover_line, text, count=1, flags=re.M)
    else:
        text = re.sub(r"^(date:.*)$", cover_line + r"\n\1", text, count=1, flags=re.M)
    open(path, "w", encoding="utf-8").write(text)


def main():
    os.makedirs(GEN, exist_ok=True)
    keywords = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    force_all = "--all" in sys.argv
    generated = 0
    skipped_manual = 0

    for path in glob.glob(os.path.join(POSTS, "*.md")):
        text, title, top, sub, cover = get_meta(path)
        if keywords and not any(keyword in title for keyword in keywords):
            continue

        is_generated = cover.startswith(GENERATED_PREFIX)
        if cover and not is_generated:
            skipped_manual += 1
            continue  # 永远尊重手动封面，--all 也不覆盖。
        if cover and not force_all:
            continue

        write_cover(path, text, title, top, sub)
        print(f"[{top}/{sub}] {title}")
        generated += 1

    print(f"generated {generated}, kept manual covers {skipped_manual}")


if __name__ == "__main__":
    main()
