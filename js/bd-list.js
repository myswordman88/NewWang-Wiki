/* =========================================================
   新王觉醒 · BD 公开展示页逻辑（bd-list.html）
   读取 is_public = true 的 BD 并渲染卡片列表（无需登录）
   ========================================================= */
(function () {
  'use strict';

  var listEl = document.getElementById('bdList');

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function classZh(c) {
    var m = {
      amazon: '亚马逊', sorceress: '女巫', necromancer: '死灵法师', paladin: '圣骑士',
      barbarian: '野蛮人', druid: '德鲁伊', assassin: '刺客', warlock: '术士'
    };
    return m[c] || c || '未知';
  }

  function render(rows) {
    if (!rows || !rows.length) {
      listEl.innerHTML = '<p class="bd-list-empty">还没有公开的 BD，快去「BD构建」页发布第一套吧！</p>';
      return;
    }
    listEl.innerHTML = rows.map(function (r) {
      var d = r.data || {};
      // 装备存在 data.player.equip / data.merc.equip（兼容旧版顶层 data.equip）
      var pd = d.player || {};
      var md = d.merc || {};
      var eq = (pd.equip || d.equip || []).concat(md.equip || []).filter(function (e) { return e && !e.empty; }).length;
      var pts = Object.keys(d.points || {}).length;
      return '<a class="bd-card" href="bd-build.html?id=' + encodeURIComponent(r.id) + '&view=1">' +
        '<div class="bd-card-top"><span class="bd-card-class">' + classZh(r.class) + '</span>' +
        (r.is_public ? '<span class="bd-card-public">公开</span>' : '') + '</div>' +
        '<h3 class="bd-card-title">' + esc(r.title || '未命名 BD') + '</h3>' +
        '<div class="bd-card-meta">作者 ' + esc(r.author_name || '匿名') + ' · ' + eq + ' 件装备 · ' + pts + ' 技能</div>' +
        '<div class="bd-card-time">' + (r.created_at ? new Date(r.created_at).toLocaleDateString() : '') + '</div>' +
        '</a>';
    }).join('');
  }

  function load() {
    if (!window.sbClient) {
      listEl.innerHTML = '<p class="bd-list-empty">展示服务未配置（请在 js/config.js 填写 Supabase 信息）。</p>';
      return;
    }
    window.sbClient.from('bds').select('*').eq('is_public', true)
      .order('created_at', { ascending: false })
      .then(function (res) {
        if (res.error) throw res.error;
        render(res.data);
      })
      .catch(function (e) {
        listEl.innerHTML = '<p class="bd-list-empty">加载失败：' + esc((e && e.message) || e) + '</p>';
      });
  }

  // 等待 Supabase 客户端初始化（由 shared.js 异步串联加载）后再读取
  function whenClient(cb) {
    if (window.sbClient) cb();
    else setTimeout(function () { whenClient(cb); }, 120);
  }
  whenClient(load);
})();
