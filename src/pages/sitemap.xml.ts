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
  const posts = await getAllPosts();
  const latestIso = posts.length ? new Date(posts[0].timestamp).toISOString() : new Date().toISOString();

  const urls = [
    { loc: `${siteUrl}/`, lastmod: latestIso },
    { loc: `${siteUrl}/blog/`, lastmod: latestIso },
    { loc: `${siteUrl}/archives/`, lastmod: latestIso },
    { loc: `${siteUrl}/categories/`, lastmod: latestIso },
    { loc: `${siteUrl}/tags/`, lastmod: latestIso },
    { loc: `${siteUrl}/about/`, lastmod: latestIso },
    ...posts.map(post => ({
      loc: `${siteUrl}${post.url}`,
      lastmod: new Date(post.timestamp).toISOString(),
    })),
  ];

  const xml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...urls.map(item => `  <url><loc>${xmlEscape(item.loc)}</loc><lastmod>${item.lastmod}</lastmod></url>`),
    '</urlset>',
  ].join('\n');

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/xml; charset=utf-8',
    },
  });
};
