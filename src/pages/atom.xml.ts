import type { APIRoute } from 'astro';
import { getAllPosts } from '../lib/posts';

function xmlEscape(str: string): string {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export const GET: APIRoute = async () => {
  const siteUrl = 'https://VVVVVenxo.github.io';
  const siteTitle = "VVVVVenxo's Blog";
  const siteDesc = '专注游戏客户端开发，记录 C++、C#、Unity 架构、网络同步、实时渲染与 AI 工程实践。';
  const author = 'VVVVVenxo';

  const posts = await getAllPosts();
  const rssItems = posts
    .slice(0, 25)
    .map(post => {
      const fullUrl = `${siteUrl}${post.url}`;
      return [
        '    <item>',
        `      <title>${xmlEscape(post.title)}</title>`,
        `      <link>${xmlEscape(fullUrl)}</link>`,
        `      <guid>${xmlEscape(fullUrl)}</guid>`,
        `      <pubDate>${new Date(post.timestamp).toUTCString()}</pubDate>`,
        `      <description>${xmlEscape(post.description)}</description>`,
        '    </item>',
      ].join('\n');
    })
    .join('\n');

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
    '  <channel>',
    `    <title>${xmlEscape(siteTitle)}</title>`,
    `    <link>${xmlEscape(siteUrl)}/</link>`,
    `    <description>${xmlEscape(siteDesc)}</description>`,
    '    <language>zh-CN</language>',
    `    <managingEditor>${xmlEscape(author)}</managingEditor>`,
    `    <atom:link href="${xmlEscape(siteUrl)}/atom.xml" rel="self" type="application/rss+xml"/>`,
    rssItems,
    '  </channel>',
    '</rss>',
  ].join('\n');

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
