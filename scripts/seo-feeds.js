'use strict';

function xmlEscape(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function toIsoDate(val) {
  if (!val) return new Date().toISOString();
  if (typeof val.toISOString === 'function') return val.toISOString();
  const d = new Date(val);
  return isNaN(d.getTime()) ? new Date().toISOString() : d.toISOString();
}

hexo.extend.generator.register('site_sitemap_and_rss', locals => {
  const siteUrl = String(hexo.config.url || 'https://VVVVVenxo.github.io').replace(/\/+$/, '');
  const siteTitle = hexo.config.title || "VVVVVenxo's Blog";
  const siteDesc = hexo.config.description || hexo.config.subtitle || '';
  const author = hexo.config.author || 'VVVVVenxo';

  const posts = locals.posts
    .sort('-date')
    .filter(post => post.published !== false && post.title);

  const sitemapUrls = [
    { loc: `${siteUrl}/`, lastmod: posts.length ? toIsoDate(posts.first().updated || posts.first().date) : toIsoDate() },
    { loc: `${siteUrl}/archives/`, lastmod: toIsoDate() },
    { loc: `${siteUrl}/categories/`, lastmod: toIsoDate() },
    { loc: `${siteUrl}/tags/`, lastmod: toIsoDate() },
    { loc: `${siteUrl}/about/`, lastmod: toIsoDate() },
  ];

  posts.forEach(post => {
    const relPath = '/' + String(post.path || '').replace(/^\/+/, '');
    sitemapUrls.push({
      loc: `${siteUrl}${encodeURI(relPath)}`,
      lastmod: toIsoDate(post.updated || post.date)
    });
  });

  const sitemapXml = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...sitemapUrls.map(item => `  <url><loc>${xmlEscape(item.loc)}</loc><lastmod>${item.lastmod}</lastmod></url>`),
    '</urlset>'
  ].join('\n');

  const rssItems = posts.limit(20).map(post => {
    const relPath = '/' + String(post.path || '').replace(/^\/+/, '');
    const fullUrl = `${siteUrl}${encodeURI(relPath)}`;
    const summary = post.description || '';
    return [
      '    <item>',
      `      <title>${xmlEscape(post.title)}</title>`,
      `      <link>${xmlEscape(fullUrl)}</link>`,
      `      <guid>${xmlEscape(fullUrl)}</guid>`,
      `      <pubDate>${new Date(toIsoDate(post.date)).toUTCString()}</pubDate>`,
      `      <description>${xmlEscape(summary)}</description>`,
      '    </item>'
    ].join('\n');
  }).join('\n');

  const atomXml = [
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
    '</rss>'
  ].join('\n');

  return [
    { path: 'sitemap.xml', data: sitemapXml },
    { path: 'atom.xml', data: atomXml }
  ];
});
