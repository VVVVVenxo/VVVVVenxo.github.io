'use strict';

function stripText(value) {
  return String(value || '')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

hexo.extend.generator.register('local_search_json', locals => {
  const searchConfig = hexo.config.search || {};
  const outputPath = searchConfig.path || 'search.json';
  const root = (hexo.config.root || '/').replace(/\/+$/, '');

  const posts = locals.posts
    .sort('-date')
    .filter(post => post.published !== false && post.indexing !== false && post.title)
    .map(post => {
      const categories = post.categories && post.categories.length
        ? post.categories.map(item => item.name).join(' ')
        : '';
      const tags = post.tags && post.tags.length
        ? post.tags.map(item => item.name).join(' ')
        : '';
      const body = stripText(post.content || post.raw || '');
      const content = [categories, tags, body].filter(Boolean).join(' ');
      const relPath = '/' + String(post.path || '').replace(/^\/+/, '');

      return {
        title: String(post.title).trim(),
        url: (root + relPath).replace(/\/{2,}/g, '/'),
        content
      };
    });

  return {
    path: outputPath,
    data: JSON.stringify(posts)
  };
});