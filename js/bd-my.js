/* =========================================================
   新王觉醒 · 个人中心页逻辑（bd-my.html）
   登录后读取当前用户全部 BD，支持发布/转私有/删除
   ========================================================= */
(function () {
  'use strict';

  var listEl = document.getElementById('bdMyList');
  var loginHint = document.getElementById('bdMyLogin');

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
      listEl.innerHTML = '<p class="bd-list-empty">你还没有保存任何 BD，去「BD构建」页创建第一套吧。</p>';
      return;
    }
    listEl.innerHTML = rows.map(function (r) {
      var d = r.data || {};
      // 装备存在 data.player.equip / data.merc.equip（兼容旧版顶层 data.equip）
      var pd = d.player || {};
      var md = d.merc || {};
      var eq = (pd.equip || d.equip || []).concat(md.equip || []).filter(function (e) { return e && !e.empty; }).length;
      return '<div class="bd-card bd-card--mine" data-id="' + r.id + '">' +
        '<div class="bd-card-top"><span class="bd-card-class">' + classZh(r.class) + '</span>' +
        '<span class="bd-card-status ' + (r.is_public ? 'on' : 'off') + '">' + (r.is_public ? '已公开' : '私有') + '</span></div>' +
        '<h3 class="bd-card-title"><a href="bd-build.html?id=' + r.id + '">' + esc(r.title || '未命名 BD') + '</a></h3>' +
        '<div class="bd-card-meta">' + eq + ' 件装备 · 更新于 ' + new Date(r.updated_at).toLocaleDateString() + '</div>' +
        '<div class="bd-card-actions">' +
          '<button type="button" data-act="toggle" data-id="' + r.id + '" data-pub="' + (r.is_public ? 1 : 0) + '">' + (r.is_public ? '转为私有' : '公开发布') + '</button>' +
          '<button type="button" data-act="del" data-id="' + r.id + '">删除</button>' +
        '</div>' +
      '</div>';
    }).join('');

    listEl.querySelectorAll('button[data-act]').forEach(function (b) {
      b.addEventListener('click', function () { handle(b.dataset.act, b.dataset.id, b.dataset.pub); });
    });

    // 整张卡点击进入编辑（无论公开/私有）；点按钮或标题链接时交给它们自己处理
    listEl.querySelectorAll('.bd-card--mine').forEach(function (card) {
      card.addEventListener('click', function (e) {
        if (e.target.closest('a, button')) return;
        var id = card.getAttribute('data-id');
        if (id) location.href = 'bd-build.html?id=' + encodeURIComponent(id);
      });
    });
  }

  function load() {
    if (!window.sbClient) {
      listEl.innerHTML = '<p class="bd-list-empty">服务未配置（请在 js/config.js 填写 Supabase 信息）。</p>';
      return;
    }
    var user = window.Auth.getUser();
    if (!user) {
      if (loginHint) loginHint.hidden = false;
      listEl.innerHTML = '';
      return;
    }
    if (loginHint) loginHint.hidden = true;
    window.sbClient.from('bds').select('*').eq('user_id', user.id)
      .order('updated_at', { ascending: false })
      .then(function (res) {
        if (res.error) throw res.error;
        render(res.data);
      })
      .catch(function (e) {
        listEl.innerHTML = '<p class="bd-list-empty">加载失败：' + esc((e && e.message) || e) + '</p>';
      });
  }

  function handle(act, id, pub) {
    if (!window.sbClient) return;
    if (act === 'del') {
      if (!confirm('确定删除这套 BD？此操作不可恢复。')) return;
      window.sbClient.from('bds').delete().eq('id', id)
        .then(function (res) { if (res.error) throw res.error; load(); })
        .catch(function (e) { alert('删除失败：' + ((e && e.message) || e)); });
    } else if (act === 'toggle') {
      var next = pub === '1' ? false : true;
      window.sbClient.from('bds').update({ is_public: next }).eq('id', id)
        .then(function (res) { if (res.error) throw res.error; load(); })
        .catch(function (e) { alert('操作失败：' + ((e && e.message) || e)); });
    }
  }

  var loginBtn = document.getElementById('bdMyLoginBtn');
  if (loginBtn) loginBtn.addEventListener('click', function () { if (window.Auth) Auth.openModal(); });

  // 等待 Auth 就绪（shared.js 异步串联加载）后再读取登录态
  function whenAuth(cb) {
    if (window.Auth && window.Auth.ready) { window.Auth.ready.then(cb); }
    else setTimeout(function () { whenAuth(cb); }, 120);
  }
  whenAuth(load);
  whenAuth(function () { window.Auth.onChange(load); });
})();
