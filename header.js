// justalog 共通ヘッダー
// このファイルを変更するだけで全ページのヘッダーが変わります

(function() {
  // ヘッダーのHTML
  const headerHTML = `
    <div class="header-outer">
      <div class="header">
        <a href="https://justalog.jp/" class="header-logo">just<span>a</span>log</a>
        <div class="header-time" id="site-clock"></div>
      </div>
    </div>
  `;

  // ヘッダーのCSS
  const headerCSS = `
    .header-outer { border-bottom: 1px solid #2a2a2a; }
    .header {
      max-width: 960px;
      margin: 0 auto;
      padding: 20px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .header-logo {
      font-family: 'Space Mono', monospace;
      font-size: 26px;
      color: #fff;
      text-decoration: none;
    }
    .header-logo span { color: #3fb950; }
    .header-time {
      font-family: 'Space Mono', monospace;
      font-size: 14px;
      color: #666;
    }
    @media (max-width: 768px) {
      .header { padding: 16px 24px; }
    }
  `;

  // CSSを挿入
  const style = document.createElement('style');
  style.textContent = headerCSS;
  document.head.appendChild(style);

  // ヘッダーを挿入
  const container = document.getElementById('site-header');
  if (container) {
    container.innerHTML = headerHTML;
  }

  // 時計を起動
  function updateClock() {
    const el = document.getElementById('site-clock');
    if (el) {
      el.textContent = new Date().toLocaleTimeString('ja-JP', {
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
    }
  }
  setInterval(updateClock, 1000);
  updateClock();
})();
