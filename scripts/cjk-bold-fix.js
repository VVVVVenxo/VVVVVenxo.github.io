'use strict'
const fs = require('fs')
const path = require('path')

// 1. Fix CommonMark CJK bold parsing edge case where **text（paren）** immediately
//    followed by a CJK character fails to close in marked.
// 2. Inject intrinsic width/height on local SVG images in posts so lazy loading
//    reserves the exact layout space upfront and never shifts TOC anchor positions.
hexo.extend.filter.register('after_post_render', data => {
  if (!data || typeof data.content !== 'string') return data

  if (data.content.includes('**')) {
    data.content = data.content.replace(
      /(<(?:pre|code)\b[^>]*>[\s\S]*?<\/(?:pre|code)>)|\*\*([^\n*]+?)\*\*/gi,
      (match, codeBlock, boldInner) => {
        if (codeBlock) return codeBlock
        return `<strong>${boldInner}</strong>`
      }
    )
  }

  data.content = data.content.replace(
    /<img\b([^>]*\bsrc=["'](\/img\/posts\/[^"']+\.svg)["'][^>]*)>/gi,
    (match, attrs, src) => {
      if (/\bwidth=/i.test(attrs) && /\bheight=/i.test(attrs)) return match
      try {
        const filePath = path.join(hexo.source_dir, decodeURIComponent(src).replace(/^\/+/, ''))
        if (!fs.existsSync(filePath)) return match
        const head = fs.readFileSync(filePath, 'utf8').slice(0, 400)
        const w = head.match(/\bwidth=["'](\d+)["']/)
        const h = head.match(/\bheight=["'](\d+)["']/)
        if (w && h) {
          return `<img width="${w[1]}" height="${h[1]}"${attrs}>`
        }
      } catch (_) {}
      return match
    }
  )

  return data
})
