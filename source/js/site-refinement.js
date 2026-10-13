(() => {
  const isEditorialHome = () => {
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    return path === '/' || /^\/page\/\d+$/.test(path);
  };

  const makeSection = (title, note) => {
    const section = document.createElement('div');
    section.className = 'site-refinement-section';
    section.innerHTML = `<h2>${title}</h2><span>${note}</span>`;
    return section;
  };

  const applyHomeRefinements = () => {
    if (!document.body) return;
    const pageHeader = document.querySelector('#page-header');
    const recentPosts = document.querySelector('#recent-posts');

    if (!isEditorialHome()) {
      document.body.classList.remove('site-editorial-home');
      document.querySelector('.site-refinement-intro')?.remove();
      document.querySelectorAll('.site-refinement-section').forEach(section => section.remove());
      document.querySelector('.site-refinement-featured')?.classList.remove('site-refinement-featured');
      if (recentPosts) delete recentPosts.dataset.editorial;
      return;
    }

    document.body.classList.add('site-editorial-home');
    if (!pageHeader || !recentPosts) return;

    if (!document.querySelector('.site-refinement-intro')) {
      const intro = document.createElement('section');
      intro.className = 'site-refinement-intro';
      intro.setAttribute('aria-label', '站点介绍');
      intro.innerHTML = `
        <div class="site-refinement-mast"><span>VVVVVenxo</span><small>ENGINEERING NOTEBOOK / EST. 2024</small></div>
        <div class="site-refinement-intro__copy">
          <p class="site-refinement-intro__eyebrow">GAME CLIENT ENGINEERING</p>
          <h1>游戏客户端<br>工程手记</h1>
          <p class="site-refinement-intro__lead">从语言、引擎到实时系统。这里记录实现过程、关键原理，以及工程中的真实取舍。</p>
          <div class="site-refinement-intro__topics"><span>C++ / C#</span><span>Unity</span><span>网络同步</span><span>图形渲染</span></div>
        </div>
        <div class="site-refinement-intro__diagram">
          <svg viewBox="0 0 480 290" role="img" aria-labelledby="site-refinement-diagram-title">
            <title id="site-refinement-diagram-title">游戏客户端系统关系</title>
            <g class="flow-lines"><path d="M85 78H200V135H330M85 215H200V160H330M200 135V160M330 135V160H410"/></g>
            <g class="flow-boxes"><rect x="44" y="57" width="82" height="42"/><rect x="44" y="194" width="82" height="42"/><rect x="164" y="119" width="100" height="55"/><rect x="310" y="115" width="84" height="43"/><rect x="390" y="143" width="58" height="34"/></g>
            <g class="flow-labels"><text x="85" y="83">INPUT</text><text x="85" y="220">STATE</text><text x="214" y="150">GAME LOOP</text><text x="352" y="141">RENDER</text><text x="419" y="164">GPU</text></g>
            <circle cx="200" cy="135" r="4"/><circle cx="330" cy="160" r="4"/>
          </svg>
        </div>`;
      pageHeader.insertAdjacentElement('afterend', intro);
    }

    if (!recentPosts.dataset.editorial) {
      const list = recentPosts.querySelector('.recent-post-items');
      const items = list ? Array.from(list.querySelectorAll(':scope > .recent-post-item:not(.ads-wrap)')) : [];
      if (list && items.length) {
        list.insertBefore(makeSection('精选文章', 'CURATED NOTES'), items[0]);
        items[0].classList.add('site-refinement-featured');
        if (items[1]) list.insertBefore(makeSection('最近更新', 'RECENT ENTRIES'), items[1]);
        recentPosts.dataset.editorial = 'true';
      }
    }

    const announcement = document.querySelector('#aside-content .card-announcement');
    if (announcement && !announcement.dataset.refined) {
      announcement.dataset.refined = 'true';
      const heading = announcement.querySelector('.item-headline');
      const content = announcement.querySelector('.announcement_content');
      if (heading) heading.innerHTML = '<i class="fas fa-book-open"></i><span>写作主题</span>';
      if (content) content.innerHTML = '<ul class="site-refinement-topics"><li>C++ 与 C# 基础</li><li>Unity 客户端架构</li><li>网络同步与实时系统</li><li>图形渲染与工程实践</li></ul>';
    }
  };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', applyHomeRefinements, { once: true });
  else applyHomeRefinements();
  document.addEventListener('pjax:complete', applyHomeRefinements);
})();
