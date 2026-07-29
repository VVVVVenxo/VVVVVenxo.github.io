#!/usr/bin/env bash
# 一键：给缺封面的新文章生成封面（C 风格 SVG + PNG）
# 用法：在仓库根目录执行  bash scripts/new-cover.sh
#   加 --all 强制重新生成所有文章封面
set -e
cd "$(dirname "$0")/.."

echo "==> 生成 SVG（仅缺 cover 的文章，--all 则全部）"
python scripts/gen_covers.py "$@"

echo "==> SVG 转 PNG（增量）"
python scripts/svg2png.py

echo "==> 完成。检查改动："
git status --short source/_posts source/img/covers/gen
echo ""
echo "确认无误后提交：git add -A && git commit -m 'xxx' && git push origin source"
