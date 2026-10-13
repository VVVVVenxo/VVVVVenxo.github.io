const assert = require('node:assert/strict');
const path = require('node:path');
let render;
global.hexo = {
  source_dir: path.resolve(__dirname, '../../source'),
  extend: { filter: { register: (name, callback) => { render = callback; } } }
};
require('../../scripts/cover-thumbnails.js');
const cover = '/img/covers/gen/C-%E5%86%85%E5%AD%98%E7%AE%A1%E7%90%86.png';
assert.equal(render(`<img src="${cover}" alt="memory">`), `<img src="${cover.replace('.png','-thumb.svg')}" alt="memory">`);
assert.equal(render('<img src="/img/manual.png">'), '<img src="/img/manual.png">');
assert.equal(render('<img src="/img/covers/gen/missing.png">'), '<img src="/img/covers/gen/missing.png">');
assert.equal(render(`<meta property="og:image" content="${cover}">`), `<meta property="og:image" content="${cover}">`);
assert.equal(render(`<section class="site-design-preview__originals"><img src="${cover}"></section>`), `<section class="site-design-preview__originals"><img src="${cover}"></section>`);
console.log('5 thumbnail filter checks passed');
