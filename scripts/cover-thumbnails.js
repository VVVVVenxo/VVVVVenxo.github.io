'use strict';
const fs = require('fs');
const path = require('path');

// Keep full PNG covers for sharing; use diagram-only SVGs in small image slots.
hexo.extend.filter.register('after_render:html', html => {
  if (html.includes('site-design-preview__originals')) return html;
  return html.replace(
    /(<img\b[^>]*\bsrc=")([^"<>]*\/img\/covers\/gen\/[^"<>]+)\.png(")/g,
    (match, before, image, after) => {
      const relative = decodeURIComponent(image.slice(image.indexOf('/img/covers/gen/')));
      const thumbnail = relative + '-thumb.svg';
      return fs.existsSync(path.join(hexo.source_dir, thumbnail.slice(1)))
        ? before + image + '-thumb.svg' + after
        : match;
    }
  );
});
