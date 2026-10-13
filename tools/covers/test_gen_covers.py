import glob
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

import gen_covers as covers


class CoverTests(unittest.TestCase):
    def test_all_posts_render_full_and_thumbnail_svg(self):
        for path in glob.glob(os.path.join(covers.POSTS, '*.md')):
            with self.subTest(path=path):
                _, title, top, sub, _ = covers.get_meta(path)
                full = ET.fromstring(covers.make_svg(title, top, sub))
                thumb = ET.fromstring(covers.make_thumbnail(title, top, sub))
                self.assertEqual(full.attrib['viewBox'], '0 0 1200 630')
                self.assertEqual(thumb.attrib['viewBox'], '610 230 600 360')
                self.assertNotIn('x="650" y="205"', covers.make_svg(title, top, sub))
                self.assertNotIn('x="78"', covers.make_thumbnail(title, top, sub))

    def test_parameter_diagram_not_generic_architecture(self):
        diagram = covers.diagram_for('parameters')
        self.assertIn('独立副本', diagram)
        self.assertIn('同一对象', diagram)
        self.assertNotIn('业务模块', diagram)

    def test_reflection_notes_not_csharp_reflection(self):
        kind = covers.select_variant('随笔杂谈', '随笔杂谈', '最近的所思所想')
        self.assertEqual(kind, 'reflection-notes')
        self.assertIn('观察', covers.diagram_for(kind))

    def test_ai_categories_have_distinct_diagrams(self):
        coding = covers.select_variant('AI探索', 'AI Coding', '代码工作流')
        agent = covers.select_variant('AI探索', 'AI Agent', 'Agent 任务规划')
        self.assertEqual(coding, 'ai-coding')
        self.assertEqual(agent, 'ai-agent')
        self.assertNotEqual(covers.diagram_for(coding), covers.diagram_for(agent))

    def test_long_title_keeps_all_characters(self):
        title = '给技术博客做一套自动化封面生成系统'
        lines = covers.wrap_title(title)
        self.assertEqual(''.join(lines), title)
        self.assertGreater(len(lines[-1]), 1)

    def test_writing_preserves_crlf_and_body(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(covers, 'GEN', directory):
            path = os.path.join(directory, 'post.md')
            title = '【C++】内存管理'
            cover = f'cover: {covers.PREFIX}{covers.slugify(title)}.png'
            source = f'---\r\ntitle: {title}\r\n{cover}\r\ndate: 2026-10-13\r\n---\r\n正文\r\ncover: 正文示例\r\n'
            covers.write_cover(path, source, title, '技术笔记', 'C++')
            with open(path, encoding='utf-8', newline='') as post:
                self.assertEqual(post.read(), source)
            self.assertTrue(os.path.isfile(os.path.join(directory, covers.slugify(title) + '-thumb.svg')))

    def test_manual_covers_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'post.md')
            source = '---\ntitle: 项目\ncover: /img/manual.png\ndate: 2026-10-13\n---\n正文\n'
            with open(path, 'w', encoding='utf-8') as post:
                post.write(source)
            with patch.object(covers, 'POSTS', directory), patch.object(covers, 'GEN', os.path.join(directory, 'gen')), patch.object(covers.sys, 'argv', ['gen_covers.py', '--all']):
                covers.main()
            with open(path, encoding='utf-8') as post:
                self.assertEqual(post.read(), source)
            self.assertEqual(os.listdir(os.path.join(directory, 'gen')), [])


if __name__ == '__main__':
    unittest.main()
