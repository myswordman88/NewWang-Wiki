/* =========================================================
   新王觉醒 · 共享导航/页脚注入
   - 所有页面的导航栏与页脚由本文件统一生成，消除重复 HTML
   - 改导航结构改 NAV；改版本号改 SITE_VERSION；改页脚外链改 FOOTER_LINKS
   - 本文件须以 defer 引入，且必须排在 js/main.js 之前（main.js 依赖注入后的 #navToggle/#navMenu）
   ========================================================= */
(function () {
  "use strict";

  /* ===== 站点版本号（备份时只改这里，全站自动同步） ===== */
  var SITE_VERSION = "1.9.10";

  /* ===== 导航数据 =====
     home  : 在 index.html（首页）中该链接使用的 href
     other : 在其他页面中该链接使用的 href
     所有顶层锚点项首页用 #锚点、详情页用 index.html#锚点
     "玩法构筑"下的 BD 子项：首页用 #锚点、详情页用真实 .html 页 */
  var NAV = [
    {
      name: "模组概览", home: "#overview", other: "index.html#overview",
      items: [
        { name: "特色简介", home: "feature.html", other: "feature.html" },
        { name: "作者简介", home: "author.html", other: "author.html" },
        { name: "赞助详情", home: "donate.html", other: "donate.html" },
        { name: "下载地址", home: "download.html", other: "download.html" },
        { name: "更新日志", home: "changelog.html", other: "changelog.html" },
        { name: "讨论社群", home: "community.html", other: "community.html" },
        { name: "特别鸣谢", home: "thanks.html", other: "thanks.html" },
        { name: "开发规划", home: "plan.html", other: "plan.html" }
      ]
    },
    {
      name: "新手专区", home: "#newbie", other: "index.html#newbie",
      items: [
        { name: "安装指南", home: "guide.html", other: "guide.html" },
        { name: "便利功能", home: "faq.html", other: "faq.html" },
        { name: "启动器相关", home: "launcher.html", other: "launcher.html" },
        { name: "视频教程", home: "video.html", other: "video.html" },
        { name: "模组制作", home: "modmaking.html", other: "modmaking.html" }
      ]
    },
    {
      name: "全新系统", home: "#changes", other: "index.html#changes",
      items: [
        { name: "基础改动", home: "changes-basic.html", other: "changes-basic.html" },
        { name: "觉醒系统", home: "changes-awaken.html", other: "changes-awaken.html" },
        { name: "转职系统", home: "changes-class.html", other: "changes-class.html" },
        { name: "合成配方", home: "changes-recipe.html", other: "changes-recipe.html" },
        { name: "新增物品", home: "items-new.html", other: "items-new.html" },
        { name: "终局玩法", home: "endgame.html", other: "endgame.html" },
        { name: "赛季旅程", home: "season.html", other: "season.html" }
      ]
    },
    {
      name: "职业技能", home: "#skills", other: "index.html#skills",
      items: [
        { name: "技能总览", home: "skills-overview.html", other: "skills-overview.html" },
        { name: "女巫", home: "skills-sorceress.html", other: "skills-sorceress.html" },
        { name: "亚马逊", home: "skills-amazon.html", other: "skills-amazon.html" },
        { name: "死灵法师", home: "skills-necro.html", other: "skills-necro.html" },
        { name: "圣骑士", home: "skills-paladin.html", other: "skills-paladin.html" },
        { name: "野蛮人", home: "skills-barbarian.html", other: "skills-barbarian.html" },
        { name: "德鲁伊", home: "skills-druid.html", other: "skills-druid.html" },
        { name: "刺客", home: "skills-assassin.html", other: "skills-assassin.html" },
        { name: "术士", home: "skills-warlock.html", other: "skills-warlock.html" },
        { name: "通用技能", home: "skills-common.html", other: "skills-common.html" }
      ]
    },
    {
      name: "装备详情", home: "#equipment", other: "index.html#equipment",
      items: [
        { name: "装备系统", home: "equipment-system.html", other: "equipment-system.html" },
        { name: "基底装备", home: "equipment-special.html", other: "equipment-special.html" },
        { name: "魔法&稀有", home: "equipment-magic.html", other: "equipment-magic.html" },
        { name: "套装装备", home: "equipment-set.html", other: "equipment-set.html" },
        { name: "符文之语", home: "equipment-rune.html", other: "equipment-rune.html" },
        { name: "暗金装备", home: "equipment-unique.html", other: "equipment-unique.html" },
        { name: "手工装备", home: "equipment-crafted.html", other: "equipment-crafted.html" },
        { name: "传奇&混沌", home: "equipment-legend.html", other: "equipment-legend.html" }
      ]
    },
    {
      name: "装备打造", home: "#crafting", other: "index.html#crafting",
      items: [
        { name: "强化卷轴", home: "crafting-scroll.html", other: "crafting-scroll.html" },
        { name: "锻造系统", home: "crafting-forge.html", other: "crafting-forge.html" },
        { name: "重铸与无形化", home: "crafting-reforge.html", other: "crafting-reforge.html" },
        { name: "套装继承", home: "crafting-inherit.html", other: "crafting-inherit.html" },
        { name: "符文共鸣", home: "crafting-rune.html", other: "crafting-rune.html" },
        { name: "封印词条", home: "crafting-seal.html", other: "crafting-seal.html" }
      ]
    },
    {
      name: "怪物&盟友", home: "#allies", other: "index.html#allies",
      items: [
        { name: "佣兵信息", home: "mercenary.html", other: "mercenary.html" },
        { name: "怪物图鉴", home: "monster.html", other: "monster.html" },
        { name: "BOSS 介绍", home: "boss.html", other: "boss.html" }
      ]
    },
    {
      name: "玩法构筑", home: "#items", other: "index.html#items",
      items: [
        { name: "BD展示", home: "bd-list.html", other: "bd-list.html" },
        { name: "BD构建", home: "bd-build.html", other: "bd-build.html" },
        { name: "我的BD", home: "bd-my.html", other: "bd-my.html" },
        { name: "攻略心得", home: "strategy.html", other: "strategy.html" },
        { name: "Bug反馈", home: "bug.html", other: "bug.html" }
      ]
    }
  ];

  /* ===== 页脚外链（5 个资料站链接） ===== */
  var FOOTER_LINKS = [
    { name: "赞助链接", href: "https://ifdian.net/a/bigwang" },
    { name: "新王觉醒", href: "https://www.wolai.com/v7XJECzma8UnWS71iAgKXP" },
    { name: "魔王降临", href: "https://www.wolai.com/h64uqLTn4dD6d9RcpVWUKr" },
    { name: "王者归来", href: "https://www.wolai.com/vooPs6mcQEAFmWxBWR8e43" },
    { name: "Mod小站", href: "https://www.wolai.com/gJs5pYFZmbv8Ka356rkbk8" }
  ];

  function currentPage() {
    var p = location.pathname.split("/").pop();
    return (!p || p === "index.html") ? "index.html" : p;
  }

  function buildNav(isHome, cur) {
    var items = NAV.map(function (top) {
      var subs = top.items.map(function (it) {
        var href = isHome ? it.home : it.other;
        if (href === cur) {
          return '<li><span class="current">' + it.name + "</span></li>";
        }
        return '<li><a href="' + href + '">' + it.name + "</a></li>";
      }).join("");
      var topHref = isHome ? top.home : top.other;
      return '<li class="has-dropdown">' +
        '<a href="' + topHref + '" aria-haspopup="true" aria-expanded="false">' + top.name + "</a>" +
        '<ul class="dropdown">' + subs + "</ul>" +
      "</li>";
    }).join("");
    var brandHref = isHome ? "#top" : "index.html";
    return '<header class="site-header" id="top">' +
      '<nav class="nav container" aria-label="主导航">' +
        '<a class="brand" href="' + brandHref + '" aria-label="新王觉醒首页">' +
          '<span class="brand-text">新王觉醒 | 官方网站</span>' +
        "</a>" +
        '<button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="navMenu" aria-label="打开菜单">' +
          "<span></span><span></span><span></span>" +
        "</button>" +
        '<ul class="nav-menu" id="navMenu">' + items + '<li class="nav-auth-item" id="navAuth"></li>' + "</ul>" +
      "</nav>" +
    "</header>";
  }

  function buildFooter(version) {
    var links = FOOTER_LINKS.map(function (l) {
      return '<a href="' + l.href + '" target="_blank" rel="noopener">' + l.name + "</a>";
    }).join("");
    return '<footer class="site-footer">' +
      '<div class="container footer-inner">' +
        '<div class="footer-brand">' +
          '<div class="brand-line">' +
            '<span class="brand-mark" aria-hidden="true">王</span>' +
            '<span class="brand-text">新王觉醒</span>' +
          "</div>" +
          '<p class="visitor-counter">' +
            '<span id="busuanzi_container_site_pv">总访问 <span id="busuanzi_value_site_pv"></span> 次</span>' +
            '<span class="counter-sep">·</span>' +
            '<span id="busuanzi_container_site_uv">独立访客 <span id="busuanzi_value_site_uv"></span> 人</span>' +
          "</p>" +
        "</div>" +
        '<div class="footer-row">' +
          '<nav class="footer-links" aria-label="资料站链接">' +
            '<span class="footer-links-label">资料站链接</span>' + links +
          "</nav>" +
          '<p class="footer-copy">By 隔壁大王</p>' +
          '<p class="version-badge">网站版本 v&nbsp;&nbsp;' + version + "</p>" +
        "</div>" +
      "</div>" +
    "</footer>";
  }

  /* ===== 返回顶部浮动按钮 =====
     右下角固定，滚动超过 SHOW_AT 后淡入，点击平滑回到顶部 */
  var SHOW_AT = 400;
  function injectBackToTop() {
    var btn = document.createElement("button");
    btn.id = "backToTop";
    btn.className = "back-to-top";
    btn.type = "button";
    btn.setAttribute("aria-label", "返回顶部");
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" ' +
      'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>';
    document.body.appendChild(btn);

    function onScroll() {
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      btn.classList.toggle("is-visible", y > SHOW_AT);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    btn.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  function inject() {
    var cur = currentPage();
    var isHome = cur === "index.html";
    var navMount = document.getElementById("site-nav");
    if (navMount) navMount.innerHTML = buildNav(isHome, cur);
    var footMount = document.getElementById("site-footer");
    if (footMount) footMount.innerHTML = buildFooter(SITE_VERSION);

    // 返回顶部浮动按钮（右下角，滚动一段距离后出现）
    injectBackToTop();

    // 不蒜子访问计数（本地预览 localhost/127.0.0.1/file:// 不加载，避免外网请求拖慢）
    var h = location.hostname;
    if (!(h === "localhost" || h === "127.0.0.1" || h === "")) {
      var s = document.createElement("script");
      s.async = true;
      s.src = "//busuanzi.ibruce.info/busuanzi/2.3/busuanzi.pure.mini.js";
      document.head.appendChild(s);
    }
    bootstrapAuth();
  }

  /* 按顺序串联加载 Supabase 相关脚本（全站自动启用登录系统，无需逐页改 script 标签） */
  function loadSeq(urls, done) {
    var i = 0;
    (function next() {
      if (i >= urls.length) { if (done) done(); return; }
      var s = document.createElement("script");
      s.src = urls[i++];
      s.onload = next;
      s.onerror = next;
      document.head.appendChild(s);
    })();
  }
  function bootstrapAuth() {
    if (window.__authBooted) return;
    window.__authBooted = true;
    loadSeq([
      "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2",
      "./js/config.js",
      "./js/supabase-client.js",
      "./js/auth.js"
    ]);
  }

  inject();
})();
