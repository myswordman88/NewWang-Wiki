/* =========================================================
   新王觉醒 · Supabase 客户端初始化
   - 依赖 CDN 全局对象 window.supabase（由 shared.js 自动加载）
   - 依赖 js/config.js（提供 URL / anon key）
   - 初始化后的客户端实例挂在 window.sbClient，全站共用
   - 若未配置，安全降级：仅打印警告，BD 云端功能不可用但站点照常运行
   ========================================================= */
(function () {
  'use strict';

  function init() {
    var c = window.APP_CONFIG;
    var ok = c && c.SUPABASE_URL && c.SUPABASE_URL.indexOf('YOUR-') !== 0 && window.supabase;
    if (!ok) {
      console.warn('[supabase] 未配置或 supabase-js 未加载：请在 js/config.js 填写 SUPABASE_URL / SUPABASE_ANON_KEY。' +
        'BD 云端保存功能将不可用（可继续本地使用）。');
      window.sbClient = null;
      return;
    }
    try {
      window.sbClient = window.supabase.createClient(c.SUPABASE_URL, c.SUPABASE_ANON_KEY);
    } catch (e) {
      console.error('[supabase] 初始化失败', e);
      window.sbClient = null;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
