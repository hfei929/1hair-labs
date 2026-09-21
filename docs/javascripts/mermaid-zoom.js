(function () {
  var sourceByHost = new WeakMap(); // div.mermaid → 源码文本
  var bound = new WeakSet();

  function openOverlay(svgMarkup) {
    var overlay = document.createElement('div');
    overlay.className = 'mermaid-zoom-overlay';
    var holder = document.createElement('div');
    holder.className = 'mermaid-zoom-holder';
    holder.innerHTML = svgMarkup;
    var svg = holder.querySelector('svg');
    if (svg) {
      svg.style.maxWidth = 'none';
      svg.style.width = '100%';
      svg.style.height = 'auto';
    }
    overlay.appendChild(holder);
    function esc(e) { if (e.key === 'Escape') close(); }
    function close() {
      overlay.remove();
      document.removeEventListener('keydown', esc);
    }
    overlay.addEventListener('click', close);
    document.addEventListener('keydown', esc);
    document.body.appendChild(overlay);
  }

  function bindHost(host, source) {
    if (bound.has(host)) return;
    bound.add(host);
    host.style.cursor = 'zoom-in';
    host.addEventListener('click', function () {
      // 兼容旧版 Material：SVG 直接在正常 DOM 里
      var svg = host.querySelector('svg');
      if (svg) { openOverlay(svg.outerHTML); return; }
      // 新版 Material：SVG 在 closed shadow root 里 → 重新渲染全宽版
      if (!source || typeof mermaid === 'undefined') return;
      mermaid.render('mmd-zoom-' + Date.now(), source)
        .then(function (r) { openOverlay(r.svg); })
        .catch(function (err) { console.error('[mermaid-zoom]', err); });
    });
  }

  function scan(records) {
    // Material 把 pre.mermaid 替换成 div.mermaid 的瞬间，成对捕获源码
    if (records) {
      records.forEach(function (rec) {
        var pre = Array.prototype.find.call(rec.removedNodes, function (n) {
          return n.nodeType === 1 && n.tagName === 'PRE' && n.classList.contains('mermaid');
        });
        var host = Array.prototype.find.call(rec.addedNodes, function (n) {
          return n.nodeType === 1 && n.classList.contains('mermaid');
        });
        if (pre && host) sourceByHost.set(host, pre.textContent);
      });
    }
    Array.prototype.forEach.call(document.querySelectorAll('.mermaid'), function (n) {
      bindHost(n, sourceByHost.get(n));
    });
  }

  scan();
  // 观察整个 documentElement：覆盖 Material 的 DOM 变换和 instant navigation 换页
  new MutationObserver(function (records) { scan(records); })
    .observe(document.documentElement, { childList: true, subtree: true });
})();
