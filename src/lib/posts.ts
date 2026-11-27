import fs from 'node:fs';
import path from 'node:path';
import matter from 'gray-matter';
import { Marked } from 'marked';
import { createHighlighter, type Highlighter } from 'shiki';

export interface TocHeading {
  depth: number;
  text: string;
  slug: string;
}

export interface PostItem {
  slug: string;
  title: string;
  cleanTitle: string;
  categoryBadge: string;
  dateStr: string;
  dateFormatted: string;
  year: string;
  month: string;
  day: string;
  timestamp: number;
  readingMinutes: number;
  wordCount: number;
  categories: string[];
  tags: string[];
  cover?: string;
  coverThumb?: string;
  description: string;
  url: string;
  rawContent: string;
  htmlContent: string;
  headings: TocHeading[];
}

const POSTS_DIR = path.resolve(process.cwd(), 'source/_posts');
const SOURCE_DIR = path.resolve(process.cwd(), 'source');

let highlighterPromise: Promise<Highlighter> | null = null;

function getShikiHighlighter(): Promise<Highlighter> {
  if (!highlighterPromise) {
    highlighterPromise = createHighlighter({
      themes: ['one-light', 'one-dark-pro'],
      langs: [
        'c',
        'cpp',
        'csharp',
        'lua',
        'python',
        'javascript',
        'typescript',
        'bash',
        'shell',
        'json',
        'yaml',
        'html',
        'css',
        'xml',
        'sql',
        'glsl',
        'hlsl',
        'shaderlab',
        'markdown',
        'ini',
        'diff',
        'text',
      ],
    });
  }
  return highlighterPromise;
}

const LANG_ALIASES: Record<string, string> = {
  'c#': 'csharp',
  cs: 'csharp',
  'c++': 'cpp',
  cxx: 'cpp',
  h: 'cpp',
  hpp: 'cpp',
  sh: 'bash',
  zsh: 'bash',
  shellscript: 'bash',
  js: 'javascript',
  ts: 'typescript',
  py: 'python',
  yml: 'yaml',
  md: 'markdown',
  shader: 'hlsl',
  cg: 'hlsl',
  plaintext: 'text',
  txt: 'text',
};

function normalizeLang(lang?: string): string {
  const raw = (lang || 'text').trim().split(/\s+/)[0].toLowerCase();
  return LANG_ALIASES[raw] || raw || 'text';
}

function slugifyHeading(text: string, used: Map<string, number>): string {
  const clean = text
    .replace(/<[^>]+>/g, '')
    .replace(/&[a-zA-Z0-9#]+;/g, '')
    .trim()
    .toLowerCase()
    .replace(/[\s\u3000]+/g, '-')
    .replace(/[^\w\u4e00-\u9fa5\-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  const base = clean || 'section';
  const count = used.get(base) || 0;
  used.set(base, count + 1);
  return count === 0 ? base : `${base}-${count}`;
}

function stripHtml(html: string): string {
  return html
    .replace(/<[^>]+>/g, '')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .trim();
}

function countWordsAndReadingTime(markdown: string): { wordCount: number; readingMinutes: number } {
  const withoutCode = markdown.replace(/```[\s\S]*?```/g, ' ');
  const cjkMatches = withoutCode.match(/[\u4e00-\u9fa5]/g) || [];
  const latinMatches = withoutCode
    .replace(/[\u4e00-\u9fa5]/g, ' ')
    .match(/[a-zA-Z0-9_\-]+/g) || [];
  const codeLines = (markdown.match(/```[\s\S]*?```/g) || [])
    .join('\n')
    .split('\n').length;
  const wordCount = cjkMatches.length + latinMatches.length + Math.round(codeLines * 3);
  const readingMinutes = Math.max(1, Math.round(wordCount / 320));
  return { wordCount, readingMinutes };
}

function extractDescription(markdown: string, frontmatterDesc?: string): string {
  if (frontmatterDesc && String(frontmatterDesc).trim()) {
    return String(frontmatterDesc).trim();
  }
  const lines = markdown
    .replace(/```[\s\S]*?```/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l && !l.startsWith('#') && !l.startsWith('---') && !l.startsWith('|') && !l.startsWith('>'));
  const joined = lines
    .slice(0, 4)
    .join(' ')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^[-*+\d.]+\s+/, '')
    .trim();
  return joined.slice(0, 180);
}

function parseDateParts(rawFileContent: string, fmDate: unknown): {
  year: string;
  month: string;
  day: string;
  dateStr: string;
  dateFormatted: string;
  timestamp: number;
} {
  const m = rawFileContent.match(/^date:\s*['"]?(\d{4})-(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?/m);
  if (m) {
    const year = m[1];
    const month = m[2].padStart(2, '0');
    const day = m[3].padStart(2, '0');
    const hh = (m[4] || '00').padStart(2, '0');
    const mm = (m[5] || '00').padStart(2, '0');
    const ss = (m[6] || '00').padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;
    const dateFormatted = `${year}年${month}月${day}日`;
    const timestamp = new Date(`${year}-${month}-${day}T${hh}:${mm}:${ss}Z`).getTime();
    return { year, month, day, dateStr, dateFormatted, timestamp };
  }
  const d = fmDate instanceof Date ? fmDate : new Date(String(fmDate || '2025-01-01'));
  const year = String(d.getUTCFullYear());
  const month = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  const dateStr = `${year}-${month}-${day}`;
  const dateFormatted = `${year}年${month}月${day}日`;
  return { year, month, day, dateStr, dateFormatted, timestamp: d.getTime() };
}

function normalizeArray(val: unknown): string[] {
  if (!val) return [];
  if (Array.isArray(val)) {
    return val.flat().map(v => String(v).trim()).filter(Boolean);
  }
  return [String(val).trim()].filter(Boolean);
}

function postProcessHtml(html: string): string {
  // 1. Fix CJK bold edge case where **text（paren）** followed by CJK fails to close in CommonMark
  let out = html;
  if (out.includes('**')) {
    out = out.replace(
      /(<(?:pre|code)\b[^>]*>[\s\S]*?<\/(?:pre|code)>)|\*\*([^\n*]+?)\*\*/gi,
      (match, codeBlock, boldInner) => {
        if (codeBlock) return codeBlock;
        return `<strong>${boldInner}</strong>`;
      }
    );
  }

  // 2. Inject intrinsic width/height on local SVG images and lazy loading on all images
  out = out.replace(
    /<img\b([^>]*\bsrc=["'](\/img\/posts\/[^"']+\.svg)["'][^>]*)>/gi,
    (match, attrs, src) => {
      if (/\bwidth=/i.test(attrs) && /\bheight=/i.test(attrs)) return match;
      try {
        const filePath = path.join(SOURCE_DIR, decodeURIComponent(src).replace(/^\/+/, ''));
        if (!fs.existsSync(filePath)) return match;
        const head = fs.readFileSync(filePath, 'utf8').slice(0, 400);
        const w = head.match(/\bwidth=["'](\d+)["']/);
        const h = head.match(/\bheight=["'](\d+)["']/);
        if (w && h) {
          return `<img width="${w[1]}" height="${h[1]}"${attrs}>`;
        }
      } catch (_) {}
      return match;
    }
  );

  out = out.replace(/<img\b(?![^>]*\bloading=)([^>]*)>/gi, (_match, attrs) => {
    const extra = /\bdecoding=/i.test(attrs) ? ' loading="lazy"' : ' loading="lazy" decoding="async"';
    return `<img${attrs}${extra}>`;
  });

  return out;
}

export async function renderMarkdown(markdown: string): Promise<{ html: string; headings: TocHeading[] }> {
  const highlighter = await getShikiHighlighter();
  const loadedLangs = new Set(highlighter.getLoadedLanguages());
  const headings: TocHeading[] = [];
  const usedSlugs = new Map<string, number>();

  const markedInstance = new Marked();

  markedInstance.use({
    gfm: true,
    breaks: false,
    renderer: {
      heading({ tokens, depth }) {
        const innerHtml = this.parser.parseInline(tokens);
        const plainText = stripHtml(innerHtml);
        const slug = slugifyHeading(plainText, usedSlugs);
        if (depth === 2 || depth === 3) {
          headings.push({ depth, text: plainText, slug });
        }
        return `<h${depth} id="${slug}"><a aria-hidden="true" tabindex="-1" href="#${slug}"><span class="icon icon-link"></span></a>${innerHtml}</h${depth}>\n`;
      },
      code({ text, lang }) {
        const normalized = normalizeLang(lang);
        const finalLang = loadedLangs.has(normalized) ? normalized : 'text';
        const shikiHtml = highlighter.codeToHtml(text, {
          lang: finalLang,
          themes: {
            light: 'one-light',
            dark: 'one-dark-pro',
          },
          defaultColor: false,
        });
        const copyBtn = `<button class="copy-button" type="button" aria-label="复制代码" title="复制代码"><svg class="copy-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg><svg class="check-icon hidden" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg></button>`;
        return `<div class="code-block-wrapper">${copyBtn}${shikiHtml}</div>\n`;
      },
    },
  });

  const rawHtml = await markedInstance.parse(markdown);
  const html = postProcessHtml(rawHtml);
  return { html, headings };
}

let cachedPosts: PostItem[] | null = null;

export async function getAllPosts(): Promise<PostItem[]> {
  if (cachedPosts && import.meta.env.PROD) {
    return cachedPosts;
  }

  const files = fs
    .readdirSync(POSTS_DIR)
    .filter(f => f.endsWith('.md'))
    .sort();

  const posts: PostItem[] = [];

  for (const file of files) {
    const fullPath = path.join(POSTS_DIR, file);
    const rawFile = fs.readFileSync(fullPath, 'utf8');
    const { data, content } = matter(rawFile);

    if (data.published === false) continue;

    const slug = file.replace(/\.md$/, '');
    const rawTitle = String(data.title || slug).trim();

    // Extract optional 【Category】 prefix for cleaner badge presentation if needed
    const prefixMatch = rawTitle.match(/^【([^】]+)】\s*(.+)$/);
    const cleanTitle = prefixMatch ? prefixMatch[2].trim() : rawTitle;
    const categories = normalizeArray(data.categories);
    const tags = normalizeArray(data.tags);
    const categoryBadge = prefixMatch
      ? prefixMatch[1].trim()
      : categories[categories.length - 1] || '技术笔记';

    const { year, month, day, dateStr, dateFormatted, timestamp } = parseDateParts(rawFile, data.date);
    const { wordCount, readingMinutes } = countWordsAndReadingTime(content);
    const description = extractDescription(content, data.description);

    const cover = data.cover ? String(data.cover).trim() : undefined;
    let coverThumb = cover;
    if (cover && cover.includes('/img/covers/gen/') && cover.endsWith('.png')) {
      const candidateThumb = cover.replace(/\.png$/, '-thumb.svg');
      const thumbDiskPath = path.join(SOURCE_DIR, candidateThumb.replace(/^\/+/, ''));
      if (fs.existsSync(thumbDiskPath)) {
        coverThumb = candidateThumb;
      }
    }

    const { html: htmlContent, headings } = await renderMarkdown(content);
    const url = `/${year}/${month}/${day}/${encodeURIComponent(slug)}/`;

    posts.push({
      slug,
      title: rawTitle,
      cleanTitle,
      categoryBadge,
      dateStr,
      dateFormatted,
      year,
      month,
      day,
      timestamp,
      readingMinutes,
      wordCount,
      categories,
      tags,
      cover,
      coverThumb,
      description,
      url,
      rawContent: content,
      htmlContent,
      headings,
    });
  }

  posts.sort((a, b) => {
    if (b.timestamp !== a.timestamp) return b.timestamp - a.timestamp;
    return b.slug.localeCompare(a.slug, 'zh-CN');
  });

  cachedPosts = posts;
  return posts;
}

export function toTermSlug(name: string): string {
  return String(name || '')
    .trim()
    .replace(/C#/gi, 'CSharp')
    .replace(/A\*/gi, 'A-Star')
    .replace(/[*#?:"<>|/\\]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export async function getAllTags(): Promise<{ name: string; slug: string; count: number; posts: PostItem[] }[]> {
  const posts = await getAllPosts();
  const map = new Map<string, { name: string; slug: string; posts: PostItem[] }>();
  for (const post of posts) {
    for (const tag of post.tags) {
      const slug = toTermSlug(tag);
      const existing = map.get(slug);
      if (existing) {
        if (!existing.posts.includes(post)) existing.posts.push(post);
      } else {
        map.set(slug, { name: tag, slug, posts: [post] });
      }
    }
  }
  return Array.from(map.values())
    .map(item => ({ ...item, count: item.posts.length }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-CN'));
}

export async function getAllCategories(): Promise<{ name: string; slug: string; count: number; posts: PostItem[] }[]> {
  const posts = await getAllPosts();
  const map = new Map<string, { name: string; slug: string; posts: PostItem[] }>();
  for (const post of posts) {
    for (const cat of post.categories) {
      const slug = toTermSlug(cat);
      const existing = map.get(slug);
      if (existing) {
        if (!existing.posts.includes(post)) existing.posts.push(post);
      } else {
        map.set(slug, { name: cat, slug, posts: [post] });
      }
    }
  }
  return Array.from(map.values())
    .map(item => ({ ...item, count: item.posts.length }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-CN'));
}
