'use strict'

// Fix CommonMark CJK bold parsing edge case where **text（paren）** immediately
// followed by a CJK character fails to close in marked.
hexo.extend.filter.register('after_post_render', data => {
  if (!data || typeof data.content !== 'string' || !data.content.includes('**')) {
    return data
  }
  data.content = data.content.replace(
    /(<(?:pre|code)\b[^>]*>[\s\S]*?<\/(?:pre|code)>)|\*\*([^\n*]+?)\*\*/gi,
    (match, codeBlock, boldInner) => {
      if (codeBlock) return codeBlock
      return `<strong>${boldInner}</strong>`
    }
  )
  return data
})
