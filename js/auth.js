/* =========================================================
   新王觉醒 · 登录 / 注册 / 登出（邮箱 + 密码）
   ---------------------------------------------------------
   暴露全局 window.Auth：
     Auth.ready        Promise<user|null>  —— 客户端与初始会话就绪后 resolve
     Auth.getUser()    → 当前 user 或 null
     Auth.getSession() → 当前 session 或 null
     Auth.isLoggedIn() → bool
     Auth.onChange(cb) → 登录态变化回调（用于页面刷新列表）
     Auth.signIn(e,p) / signUp(e,p) / signOut()
     Auth.openModal()  → 打开登录弹窗
   依赖：window.sbClient（supabase-client.js 初始化）
   ========================================================= */
(function () {
  'use strict';

  var Auth = {};
  Auth._user = null;
  Auth._session = null;
  Auth._subs = [];

  function escapeHtml(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // 等待 sbClient 与其初始会话检查完成后 resolve（无论成败都 resolve，避免卡死页面）
  Auth.ready = new Promise(function (resolve) {
    function go() {
      if (!window.sbClient) {
        Auth._user = null;
        Auth._session = null;
        resolve(null);
        return;
      }
      try {
        window.sbClient.auth.onAuthStateChange(function (_event, session) {
          Auth._session = session;
          Auth._user = session ? session.user : null;
          Auth._render();
          Auth._subs.forEach(function (cb) { try { cb(Auth._user); } catch (e) {} });
        });
      } catch (e) { /* ignore */ }

      window.sbClient.auth.getSession().then(function (res) {
        Auth._session = res.data && res.data.session;
        Auth._user = Auth._session ? Auth._session.user : null;
        resolve(Auth._user);
      }).catch(function () { resolve(null); });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', go);
    else go();
  });

  Auth.onChange = function (cb) { if (typeof cb === 'function') Auth._subs.push(cb); };
  Auth.getSession = function () { return Auth._session; };
  Auth.getUser = function () { return Auth._user; };
  Auth.isLoggedIn = function () { return !!Auth._user; };

  Auth.signUp = function (email, password) {
    return window.sbClient.auth.signUp({ email: email, password: password }).then(function (r) {
      if (r.error) throw r.error;
      return r.data;
    });
  };
  Auth.signIn = function (email, password) {
    return window.sbClient.auth.signInWithPassword({ email: email, password: password }).then(function (r) {
      if (r.error) throw r.error;
      return r.data;
    });
  };
  Auth.signOut = function () {
    return window.sbClient.auth.signOut().then(function (r) { if (r.error) throw r.error; });
  };
  Auth.resetPassword = function (email) {
    return window.sbClient.auth.resetPasswordForEmail(email, {
      redirectTo: location.origin + '/reset-password.html'
    }).then(function (r) {
      if (r.error) throw r.error;
      return r.data;
    });
  };

  /* ---------- 导航登录区渲染 ---------- */
  Auth._render = function () {
    var mount = document.getElementById('navAuth');
    if (!mount) return;
    if (Auth._user) {
      var email = (Auth._user.email || '');
      var name = email.split('@')[0] || '用户';
      mount.innerHTML =
        '<button class="nav-auth-btn" id="navUserBtn" type="button" aria-haspopup="true">' + escapeHtml(name) + ' ▾</button>' +
        '<div class="nav-auth-menu" id="navAuthMenu" hidden>' +
          '<a href="bd-my.html">我的 BD</a>' +
          '<button type="button" id="navSignOut">退出登录</button>' +
        '</div>';
      var ub = document.getElementById('navUserBtn');
      var menu = document.getElementById('navAuthMenu');
      ub.addEventListener('click', function (e) { e.stopPropagation(); menu.hidden = !menu.hidden; });
      document.getElementById('navSignOut').addEventListener('click', function () {
        Auth.signOut().then(function () { menu.hidden = true; });
      });
      document.addEventListener('click', function () { menu.hidden = true; });
    } else {
      mount.innerHTML = '<button class="nav-auth-btn" id="navLoginBtn" type="button">登录 / 注册</button>';
      document.getElementById('navLoginBtn').addEventListener('click', Auth.openModal);
    }
  };

  /* ---------- 登录 / 注册弹窗 ---------- */
  var modalEl = null;
  var mode = 'signin';

  function setMode(md) {
    mode = md;
    var pwdLabel = document.getElementById('authPwd') ? document.getElementById('authPwd').parentNode : null;
    if (md === 'forgot') {
      document.getElementById('authTitle').textContent = '重置密码';
      document.getElementById('authSubmit').textContent = '发送重置邮件';
      document.getElementById('authToggle').textContent = '返回登录';
      document.querySelector('.auth-switch').firstChild.textContent = '想起了？';
      if (pwdLabel) pwdLabel.style.display = 'none';
      document.getElementById('authErr').textContent = '';
      return;
    }
    if (pwdLabel) pwdLabel.style.display = '';
    document.getElementById('authTitle').textContent = md === 'signin' ? '登录' : '注册';
    document.getElementById('authSubmit').textContent = md === 'signin' ? '登 录' : '注册';
    document.getElementById('authToggle').textContent = md === 'signin' ? '去注册' : '去登录';
    document.querySelector('.auth-switch').firstChild.textContent = md === 'signin' ? '还没有账号？' : '已有账号？';
    document.getElementById('authErr').textContent = '';
  }

  Auth.openModal = function () {
    if (!window.sbClient) {
      alert('登录服务未连接：请先在 js/config.js 填写 Supabase 的 URL 与 anon key。');
      return;
    }
    if (!modalEl) buildModal();
    modalEl.hidden = false;
    document.body.classList.add('modal-open');
    var em = document.getElementById('authEmail');
    if (em) em.focus();
  };

  function closeModal() {
    if (modalEl) { modalEl.hidden = true; document.body.classList.remove('modal-open'); }
  }

  function buildModal() {
    var m = document.createElement('div');
    m.className = 'auth-modal-mask';
    m.id = 'authModal';
    m.hidden = true;
    m.innerHTML =
      '<div class="auth-modal" role="dialog" aria-modal="true" aria-label="登录或注册">' +
        '<button class="auth-modal-close" id="authClose" aria-label="关闭">×</button>' +
        '<h3 id="authTitle">登录</h3>' +
        '<form id="authForm" class="auth-form" autocomplete="on">' +
          '<label>邮箱<input type="email" id="authEmail" autocomplete="email" required></label>' +
          '<label>密码<input type="password" id="authPwd" autocomplete="current-password" minlength="6" required></label>' +
          '<p class="auth-err" id="authErr" role="alert"></p>' +
          '<a href="#" id="authForgot" class="auth-forgot">忘记密码？</a>' +
          '<button type="submit" class="btn btn-primary" id="authSubmit">登 录</button>' +
        '</form>' +
        '<p class="auth-switch">还没有账号？<a href="#" id="authToggle">去注册</a></p>' +
        '<p class="auth-hint">注册后若开启邮箱验证，请查收验证邮件激活后再登录。</p>' +
      '</div>';
    document.body.appendChild(m);
    modalEl = m;

    document.getElementById('authClose').addEventListener('click', closeModal);
    m.addEventListener('click', function (e) { if (e.target === m) closeModal(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modalEl.hidden) closeModal(); });
    document.getElementById('authToggle').addEventListener('click', function (e) {
      e.preventDefault();
      if (mode === 'forgot') setMode('signin');
      else setMode(mode === 'signin' ? 'signup' : 'signin');
    });
    var forgotLink = document.getElementById('authForgot');
    if (forgotLink) forgotLink.addEventListener('click', function (e) {
      e.preventDefault(); setMode('forgot');
    });
    document.getElementById('authForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = document.getElementById('authEmail').value.trim();
      var pwd = document.getElementById('authPwd').value;
      var err = document.getElementById('authErr');
      err.textContent = '';
      if (mode === 'forgot') {
        if (!email) { err.textContent = '请填写邮箱。'; return; }
        Auth.resetPassword(email).then(function () {
          closeModal();
          alert('重置密码邮件已发送，请查收邮箱（若未收到，请检查垃圾邮件）。');
        }).catch(function (e) { err.textContent = (e && e.message) || '发送失败，请重试。'; });
        return;
      }
      if (!email || pwd.length < 6) { err.textContent = '请填写邮箱，密码至少 6 位。'; return; }
      (mode === 'signin' ? Auth.signIn(email, pwd) : Auth.signUp(email, pwd)).then(function () {
        closeModal();
        if (mode === 'signup') alert('注册成功！若开启了邮箱验证，请先查收激活邮件再登录。');
      }).catch(function (e) { err.textContent = (e && e.message) || '操作失败，请重试。'; });
    });
  }

  // 初始渲染 + 页面切换后重渲染
  Auth.ready.then(function () { Auth._render(); });
  window.addEventListener('hashchange', function () { Auth._render(); });
  window.addEventListener('DOMContentLoaded', function () { Auth._render(); });

  window.Auth = Auth;
})();
