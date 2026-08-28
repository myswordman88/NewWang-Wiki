/* =========================================================
   新王觉醒 · 重置密码回调页逻辑
   - 依赖 window.sbClient（由 shared.js 自动加载 auth 链）
   - 两种入口：
       * 带 ?code=xxx（PKCE 流）或 #access_token=（旧式隐式流）
         → 自动换取 session，显示「设置新密码」表单
       * 无 token → 显示「输入邮箱申请重置」表单
   ========================================================= */
(function () {
  'use strict';

  var wrap = document.getElementById('resetWrap');

  function showRequest(msg) {
    wrap.innerHTML =
      '<h3 class="auth-title">重置密码</h3>' +
      '<p class="auth-hint">输入你的注册邮箱，我们会发送一封重置密码邮件。</p>' +
      '<form id="rpForm" class="auth-form">' +
        '<label>邮箱<input type="email" id="rpEmail" autocomplete="email" required></label>' +
        '<p class="auth-err" id="rpErr" role="alert"></p>' +
        '<button type="submit" class="btn btn-primary" id="rpSubmit">发送重置邮件</button>' +
      '</form>' +
      '<p class="auth-switch"><a href="./index.html">返回首页</a></p>';
    if (msg) document.getElementById('rpErr').textContent = msg;
    document.getElementById('rpForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var email = document.getElementById('rpEmail').value.trim();
      var err = document.getElementById('rpErr');
      err.textContent = '';
      if (!email) { err.textContent = '请填写邮箱。'; return; }
      window.sbClient.auth.resetPasswordForEmail(email, {
        redirectTo: location.origin + '/reset-password.html'
      }).then(function () {
        wrap.innerHTML =
          '<h3 class="auth-title">邮件已发送</h3>' +
          '<p class="auth-hint">重置密码链接已发送至 ' + email + '，请查收邮件（若未收到，请检查垃圾邮件）。</p>' +
          '<p class="auth-switch"><a href="./index.html">返回首页</a></p>';
      }).catch(function (e) {
        err.textContent = (e && e.message) || '发送失败，请重试。';
      });
    });
  }

  function showUpdate() {
    wrap.innerHTML =
      '<h3 class="auth-title">设置新密码</h3>' +
      '<p class="auth-hint">请输入你的新密码（至少 6 位）。</p>' +
      '<form id="rpForm" class="auth-form">' +
        '<label>新密码<input type="password" id="rpPwd" autocomplete="new-password" minlength="6" required></label>' +
        '<p class="auth-err" id="rpErr" role="alert"></p>' +
        '<button type="submit" class="btn btn-primary" id="rpSubmit">更新密码</button>' +
      '</form>';
    document.getElementById('rpForm').addEventListener('submit', function (e) {
      e.preventDefault();
      var pwd = document.getElementById('rpPwd').value;
      var err = document.getElementById('rpErr');
      err.textContent = '';
      if (pwd.length < 6) { err.textContent = '密码至少 6 位。'; return; }
      window.sbClient.auth.updateUser({ password: pwd }).then(function () {
        wrap.innerHTML =
          '<h3 class="auth-title">密码已更新</h3>' +
          '<p class="auth-hint">密码修改成功，现在可以用新密码登录了。</p>' +
          '<p class="auth-switch"><a href="./index.html">返回首页登录</a></p>';
      }).catch(function (e) {
        err.textContent = (e && e.message) || '更新失败，请重试。';
      });
    });
  }

  // 合并 search 与 hash 参数，便于统一读取
  function allParams() {
    var s = (location.search ? location.search.slice(1) : '') + '&' +
            (location.hash ? location.hash.slice(1) : '');
    return new URLSearchParams(s);
  }

  // 判断当前 URL 是否携带重置回调令牌（兼容 PKCE 的 ?code= 与 implicit 的 #access_token=）
  function hasToken() {
    var p = allParams();
    return p.get('code') || p.get('access_token') ||
           p.get('token_type') === 'recovery' || p.get('type') === 'recovery';
  }

  // Supabase 回调失败时返回 #error=...&error_code=...&error_description=...
  function parseCallbackError() {
    var p = allParams();
    if (!p.get('error') && !p.get('error_code')) return null;
    var desc = decodeURIComponent(p.get('error_description') || '').replace(/\+/g, ' ');
    return desc || p.get('error_code') || '重置链接无效';
  }

  function start() {
    if (!window.sbClient) {
      wrap.innerHTML =
        '<h3 class="auth-title">服务未连接</h3>' +
        '<p class="auth-hint">登录服务未初始化，请确认 js/config.js 已正确配置 Supabase。</p>';
      return;
    }
    // 先查本地已有会话（例如恢复后刷新页面），再处理 URL 里的令牌
    window.sbClient.auth.getSession().then(function (res) {
      if (res.data && res.data.session) { showUpdate(); return; }
      var err = parseCallbackError();
      if (err) {
        showRequest('链接错误：' + err + '。请重新申请一封重置邮件。');
        return;
      }
      if (!hasToken()) { showRequest(); return; }
      // getSessionFromUrl 自动识别 PKCE(code) 与 implicit(access_token) 两种流
      window.sbClient.auth.getSessionFromUrl().then(function (r) {
        if (r.data && r.data.session) { showUpdate(); return; }
        showRequest('重置链接已失效或已被使用，请重新申请。');
      }).catch(function () {
        showRequest('重置链接已失效或已被使用，请重新申请。');
      });
    });
  }

  // 等待 shared.js 的 auth 链把 window.sbClient 初始化完成
  var tries = 0;
  (function wait() {
    if (window.sbClient) { start(); return; }
    if (tries++ > 50) {
      wrap.innerHTML =
        '<h3 class="auth-title">服务加载超时</h3>' +
        '<p class="auth-hint">登录服务未能及时加载，请刷新页面重试。</p>';
      return;
    }
    setTimeout(wait, 100);
  })();
})();
