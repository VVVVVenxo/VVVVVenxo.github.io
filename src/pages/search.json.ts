import type { APIRoute } from 'astro';
import { getAllPosts } from '../lib/posts';

function cleanPlainText(html: string): string {
  return html
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export const GET: APIRoute = async () => {
  const posts = await getAllPosts();
  const entries = posts.map(post => ({
    title: post.title,
    url: post.url,
    date: post.dateStr,
    categories: post.categories,
    tags: post.tags,
    content: cleanPlainText(post.htmlContent).slice(0, 6000),
  }));

  return new Response(JSON.stringify(entries), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
};
