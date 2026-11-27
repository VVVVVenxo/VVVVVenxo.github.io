import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const MIME_TYPES = {
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
};

function sourceAssetsBridge() {
  return {
    name: 'source-assets-bridge',
    hooks: {
      'astro:server:setup': ({ server }) => {
        server.middlewares.use((req, res, next) => {
          if (!req.url) return next();
          const cleanUrl = decodeURIComponent(req.url.split('?')[0]);
          if (cleanUrl.startsWith('/img/') || cleanUrl.startsWith('/cover-preview/')) {
            let filePath = path.join(__dirname, 'source', cleanUrl);
            if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
              filePath = path.join(filePath, 'index.html');
            }
            if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
              const ext = path.extname(filePath).toLowerCase();
              res.setHeader('Content-Type', MIME_TYPES[ext] || 'application/octet-stream');
              res.setHeader('Cache-Control', 'no-cache');
              fs.createReadStream(filePath).pipe(res);
              return;
            }
          }
          next();
        });
      },
      'astro:build:done': () => {
        const pairs = [
          [path.join(__dirname, 'source', 'img'), path.join(__dirname, 'public', 'img')],
          [path.join(__dirname, 'source', 'cover-preview'), path.join(__dirname, 'public', 'cover-preview')],
        ];
        for (const [srcDir, destDir] of pairs) {
          if (fs.existsSync(srcDir)) {
            fs.cpSync(srcDir, destDir, { recursive: true, force: true });
          }
        }
      },
    },
  };
}

export default defineConfig({
  site: 'https://VVVVVenxo.github.io',
  outDir: './public',
  publicDir: './static',
  trailingSlash: 'ignore',
  integrations: [sourceAssetsBridge()],
  vite: {
    plugins: [tailwindcss()],
  },
});
