// 套装装备页面：套装列表 -> 点击进入套装详情 -> 显示套装加成 + 部件卡片
// 参考交互：首页为套装名称网格，详情页上方为部分/全部套装加成，下方为各部件图片与属性
(function () {
  "use strict";

  var DATA = window.SET_ITEMS || { parts: [], sets: [] };
  // 过滤构建产物里的空行（无部件名且无套装名的脏记录）
  DATA.parts = (DATA.parts || []).filter(function (p) { return (p.part_zh || p.set_zh); });

  // ---- 预计算关联 ----
  var setByZh = {};
  DATA.sets.forEach(function (s) { setByZh[s.set_zh] = s; });

  var partsOfSet = {};
  DATA.parts.forEach(function (p) {
    (partsOfSet[p.set_zh] = partsOfSet[p.set_zh] || []).push(p);
  });

  // 从 base / weapon 数据中查找图片与基础属性
  var baseMap = {}, weapMap = {};
  (window.BASE_ITEMS || []).forEach(function (x) { if (x.code) baseMap[x.code] = x; });
  (window.WEAPON_ITEMS || []).forEach(function (x) { if (x.code) weapMap[x.code] = x; });
  function findBase(code) { return baseMap[code] || weapMap[code] || null; }

  // 截图所示的【职业套装】名单（其余归一般套装）
  var CLASS_SET_EN = [
    "Aldur's Watchtower",
    "Griswold's Legacy",
    "Horazon's Splendor",
    "Immortal King",
    "M'avina's Battle Hymn",
    "Natalya's Odium",
    "Tal Rasha's Wrappings",
    "Trang-Oul's Avatar"
  ];

  // 图片 onload：根据原图高度归类 c1/c2/c3，并把第一根分割线下移到图片框底边（与基底装备一致）
  var ONLOAD_ATTR = "var t=this.closest('.base-thumb');var c=this.closest('.base-card');"
    + "if(c){var h=this.naturalHeight;var cls=h<=196?'c1':(h<=294?'c2':'c3');c.classList.add(cls);"
    + "var b=c.querySelector('.base-card-body');var d=c.querySelector('.base-divider');"
    + "if(b&&d&&t){b.style.paddingTop='';var cur=d.offsetTop;var gap=t.offsetTop;var tgt=gap+t.offsetHeight+gap;var add=Math.max(0,tgt-cur);d.style.marginTop=add+'px';}}";

  DATA.sets.forEach(function (s) {
    var ps = partsOfSet[s.set_zh] || [];
    s.__pieces = ps.length;
    // 职业套装按截图名单判定，不依赖 ui_class
    s.__isClass = CLASS_SET_EN.indexOf(s.set_en) !== -1;
    s.__hay = [s.set_zh, s.set_en].concat(ps.map(function (p) { return p.part_zh + " " + p.part_en; })).join(" ").toLowerCase();
  });

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function num(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }

  // ---- 属性文本着色 ----
  // mode: 'range' = 中间词条：仅「范围型数字」(含 -，如 20 - 30%) 用淡黄，普通数字随文字色
  //       'plain' = 顶部套装加成：数字不单独着色，与文字同色（淡蓝）
  function colorizeProp(text, mode) {
    if (!text) return '';
    var plain = mode === "plain";
    // 拆分数字部分（支持 +/-、范围、百分号）与非数字部分
    var parts = text.split(/([+-]?\d+(?:\s*-\s*[+-]?\d+)?%?)/);
    return parts.map(function (part) {
      if (/^[+-]?\d+(?:\s*-\s*[+-]?\d+)?%?$/.test(part)) {
        var isRange = part.indexOf("-") !== -1;
        if (plain || !isRange) {
          return '<span class="prop-text">' + esc(part) + '</span>';
        }
        return '<span class="prop-num">' + esc(part) + '</span>';
      }
      return '<span class="prop-text">' + esc(part) + '</span>';
    }).join('');
  }

  // ---- DOM ----
  var LIST_VIEW = document.getElementById("setListView");
  var DETAIL_VIEW = document.getElementById("setDetailView");
  var SEARCH = document.getElementById("setSearch");
  var LIST_GRID = document.getElementById("setListGrid");
  var LIST_COUNT = document.getElementById("setListCount");
  var LIST_EMPTY = document.getElementById("setListEmpty");

  var DETAIL_BACK = document.getElementById("setDetailBack");
  var DETAIL_HEAD = document.getElementById("setDetailHead");
  var PARTS_GRID = document.getElementById("setPartsGrid");
  var PARTS_COUNT = document.getElementById("setPartsCount");
  var DETAIL_BONUS = document.getElementById("setDetailBonus");

  // ---- 渲染：套装列表 ----
  function renderList(query) {
    query = (query || "").trim().toLowerCase();
    var sets = DATA.sets.filter(function (s) {
      return !query || s.__hay.indexOf(query) !== -1 || s.set_zh.indexOf(query) !== -1 || s.set_en.toLowerCase().indexOf(query) !== -1;
    });

    // 分组：职业套装 / 一般套装
    var classSets = sets.filter(function (s) { return s.__isClass; });
    var normalSets = sets.filter(function (s) { return !s.__isClass; });

    var html = "";
    if (classSets.length) {
      html += '<h3 class="set-group-title">职业套装</h3>'
        + '<div class="set-name-grid">' + classSets.map(setNameCard).join("") + '</div>';
    }
    if (normalSets.length) {
      html += '<h3 class="set-group-title">一般套装</h3>'
        + '<div class="set-name-grid">' + normalSets.map(setNameCard).join("") + '</div>';
    }

    LIST_GRID.innerHTML = html || "";
    LIST_COUNT.innerHTML = "共 <strong>" + sets.length + "</strong> 套套装";
    LIST_EMPTY.hidden = sets.length !== 0;

    // 绑定卡片点击
    LIST_GRID.querySelectorAll(".set-name-card").forEach(function (card) {
      card.addEventListener("click", function () {
        var setZh = card.getAttribute("data-set");
        openDetail(setZh);
      });
    });
  }

  function setNameCard(s) {
    return '<article class="set-name-card" tabindex="0" role="button" data-set="' + esc(s.set_zh) + '" aria-label="' + esc(s.set_zh) + " " + esc(s.set_en) + '">'
      + '<h3 class="set-name-zh">' + esc(s.set_zh) + '</h3>'
      + '<p class="set-name-en">' + esc(s.set_en) + '</p>'
      + '</article>';
  }

  // ---- 渲染：套装详情 ----
  function openDetail(setZh) {
    var s = setByZh[setZh];
    if (!s) return;
    var ps = partsOfSet[setZh] || [];

    // 标题区
    var pieceTags = ps.map(function (p) {
      return '<span class="set-piece-tag">' + esc(p.part_zh) + '</span>';
    }).join("");

    DETAIL_HEAD.innerHTML = '<button type="button" class="set-back" id="setDetailBackBtn">← 套装列表</button>'
      + '<div class="set-detail-title">'
      + '<h2 class="set-detail-name">' + esc(s.set_zh) + '</h2>'
      + '<p class="set-detail-en">' + esc(s.set_en) + '</p>'
      + '<div class="set-detail-meta">'
      + '<span class="set-meta-chip version-' + esc(s.version) + '">' + esc(s.version) + '</span>'
      + '<span class="set-meta-chip">' + esc(s.ui_class || "通用") + '</span>'
      + '<span class="set-meta-chip">' + esc(s.__pieces) + ' 件</span>'
      + '</div>'
      + '<div class="set-piece-tags">' + pieceTags + '</div>'
      + '</div>';

    // 顶部统一显示：部分套装加成 + 全部套装加成（双栏），不放入每张卡片
    var partialHtml = renderPartialBonus(s);
    var fullHtml = renderFullBonus(s);
    if (DETAIL_BONUS) {
      DETAIL_BONUS.innerHTML = '<div class="set-bonus-col">'
        + '<h4 class="set-bonus-title">部分套装加成</h4>'
        + (partialHtml || '<p class="set-bonus-empty">无部分套装加成</p>')
        + '</div>'
        + '<div class="set-bonus-col">'
        + '<h4 class="set-bonus-title">全部套装加成</h4>'
        + (fullHtml || '<p class="set-bonus-empty">无全部套装加成</p>')
        + '</div>';
    }

    // 部件卡片（仅含名称/图片/词条，套装奖励属性统一在顶部显示）
    PARTS_GRID.innerHTML = ps.map(function (p) { return partDetailCard(p, s); }).join("");
    PARTS_COUNT.innerHTML = "共 <strong>" + ps.length + "</strong> 件套装部件";

    // 切换视图
    LIST_VIEW.hidden = true;
    DETAIL_VIEW.hidden = false;
    DETAIL_VIEW.scrollTop = 0;
    window.scrollTo({ top: 0, behavior: "smooth" });

    // 绑定返回按钮
    document.getElementById("setDetailBackBtn").addEventListener("click", backToList);

    // 更新 hash（不触发路由）
    history.replaceState(null, "", "#set=" + encodeURIComponent(setZh));
  }

  function backToList() {
    DETAIL_VIEW.hidden = true;
    LIST_VIEW.hidden = false;
    window.scrollTo({ top: 0, behavior: "smooth" });
    history.replaceState(null, "", window.location.pathname + window.location.search);
  }

  function renderPartialBonus(s) {
    var order = ["2", "3", "4", "5"];
    var html = "";
    order.forEach(function (k) {
      var arr = (s.partial && s.partial[k]) || [];
      if (!arr.length) return;
      var lis = arr.map(function (pr) { return "<li>" + colorizeProp(pr.text || "", "plain") + "</li>"; }).join("");
      html += '<div class="set-bonus-item"><span class="set-bonus-piece">' + esc(k) + ' 套装物品</span>'
        + '<ul class="set-bonus-list">' + lis + "</ul></div>";
    });
    return html;
  }

  function renderFullBonus(s) {
    var arr = s.full || [];
    if (!arr.length) return "";
    return '<ul class="set-bonus-list">' + arr.map(function (pr) { return "<li>" + colorizeProp(pr.text || "", "plain") + "</li>"; }).join("") + "</ul>";
  }

  // ---- 部件详情卡片（对齐基底装备：上=名称+图片 / 中=词条 / 下=套装奖励属性）----
  function partDetailCard(p, s) {
    var base = findBase(p.item_code);
    var hasImg = !!(base && base.img && base.img.length);
    var thumbChar = (p.part_zh || p.part_en || "?").charAt(0);
    // 简/繁 均显示套装装备名：简=简体(part_zh)，繁=繁体(part_zh_tw，缺失时回退底材繁体名 base.name_zh_tw)
    var twName = p.part_zh_tw || (base && base.name_zh_tw ? base.name_zh_tw : p.part_zh);

    var reqLines = [];
    if (p.lvl_req) reqLines.push('需要等级 <strong>' + esc(p.lvl_req) + '</strong>');
    var strReq = base && (base.str_req != null) ? base.str_req : (p.str_req != null ? p.str_req : "");
    var dexReq = base && (base.dex_req != null) ? base.dex_req : (p.dex_req != null ? p.dex_req : "");
    if (strReq) reqLines.push('需要力量 <strong>' + esc(strReq) + '</strong>');
    if (dexReq) reqLines.push('需要敏捷 <strong>' + esc(dexReq) + '</strong>');

    // 上部图片（右上，绝对定位，载入后按高度归 c1/c2/c3）
    var thumbCls = "base-thumb" + (hasImg ? " has-img" : "");
    var imgTag = hasImg
      ? '<img src="' + esc(base.img) + '" alt="' + esc(p.part_zh) + '" loading="lazy" onload="' + ONLOAD_ATTR + '" />'
      : '<img src="" alt="" loading="lazy" aria-hidden="true" />';

    // 中部：基础属性（不应用着色）+ 固定属性 + 套装件数附加属性
    var baseStats = [];
    if (base) {
      if (base.defense_min != null && base.defense_max != null)
        baseStats.push('防御: <strong>' + esc(base.defense_min) + "-" + esc(base.defense_max) + "</strong>");
      if (base.damage_min != null && base.damage_max != null)
        baseStats.push('单手伤害: <strong>' + esc(base.damage_min) + "-" + esc(base.damage_max) + "</strong>");
      if (base.two_hand_min != null && base.two_hand_max != null)
        baseStats.push('双手伤害: <strong>' + esc(base.two_hand_min) + "-" + esc(base.two_hand_max) + "</strong>");
      if (base.durability != null)
        baseStats.push('耐久度: <strong>' + esc(base.durability) + " / " + esc(base.durability) + "</strong>");
    }
    var selfList = (p.self_props || []).map(function (pr) {
      return "<li>" + colorizeProp(pr.text || "", "range") + "</li>";
    }).join("");
    var apropGroups = p.aprop_props || {};
    var apropHtml = "";
    ["2", "3", "4", "5", "6"].forEach(function (k) {
      var arr = apropGroups[k];
      if (!arr || !arr.length) return;
      var lis = arr.map(function (pr) { return "<li>" + colorizeProp(pr.text || "", "range") + "</li>"; }).join("");
      apropHtml += '<div class="part-aprop-group">'
        + '<span class="part-aprop-piece">' + esc(k) + ' 套装物品</span>'
        + '<ul class="part-aprop-list">' + lis + "</ul></div>";
    });
    var midHtml = (baseStats.length ? '<div class="part-base-stats">' + baseStats.map(function (x) { return "<div>" + x + "</div>"; }).join("") + "</div>" : "")
      + (selfList ? '<ul class="part-props">' + selfList + "</ul>" : "")
      + (apropHtml ? '<div class="part-aprop">' + apropHtml + '</div>' : "");

    // 下部：仅当该物品既无「2 套装物品」、也无任何更高档位加成(3/4/5/6)时，
    // 才补一行占位（分割线 + 2套装物品 / 无）。已拥有更高档位加成的物品不再补（中部已显示其属性）。
    var hasTwoPiece = !!(apropGroups["2"] && apropGroups["2"].length);
    var hasHigherPiece = ["3", "4", "5", "6"].some(function (k) { return apropGroups[k] && apropGroups[k].length; });
    var missBlock = (hasTwoPiece || hasHigherPiece) ? "" :
      '<hr class="base-divider base-divider--dashed" />'
      + '<div class="part-aprop-group">'
      + '<span class="part-aprop-piece">2 套装物品</span>'
      + '<ul class="part-aprop-list"><li class="part-aprop-none">无</li></ul>'
      + '</div>';

    return '<article class="base-card' + (hasImg ? " has-img" : "") + '">'
      + '<div class="' + thumbCls + '" aria-hidden="true" data-code="' + esc(p.item_code) + '">'
      + '<span class="base-thumb-placeholder">' + esc(thumbChar) + "</span>"
      + imgTag
      + "</div>"
      + '<div class="base-card-body">'
      + '<h3 class="base-name">' + esc(p.part_zh) + "</h3>"
      + '<div class="base-subtitle">'
      + (base && base.tier ? '<span class="base-tier tier-' + esc(base.tier) + '">' + esc(base.tier) + "</span>" : "")
      + '<span class="base-dot" aria-hidden="true">·</span>'
      + '<span class="base-cat">' + esc(p.item_type_zh || "—") + "</span>"
      + "</div>"
      + '<div class="base-en-name"><span class="base-name-label">英</span> ' + esc(p.part_en) + "</div>"
      + '<div class="base-names-row">'
      + '<span class="base-zh"><span class="base-name-label">简</span> ' + esc(p.part_zh) + "</span>"
      + '<span class="base-tw"><span class="base-name-label">繁</span> ' + esc(twName) + "</span>"
      + "</div>"
      + (reqLines.length ? '<div class="part-reqs">' + reqLines.map(function (x) { return "<span>" + x + "</span>"; }).join("") + "</div>" : "")
      + '<hr class="base-divider" />'
      + '<div class="set-part-mid">' + midHtml + "</div>"
      + missBlock
      + "</div>"
      + "</article>";
  }

  // 暴露部件渲染函数：供 BD 构建页等第三方调用（s 套装上下文可选，传入 null 亦可）
  window.__setPartCardRender = partDetailCard;

  // ---- 事件绑定 ----
  function bind() {
    if (SEARCH) {
      SEARCH.addEventListener("input", function () { renderList(this.value); });
    }
    if (DETAIL_BACK) {
      DETAIL_BACK.addEventListener("click", backToList);
    }
  }

  function initFromHash() {
    var h = window.location.hash;
    var m = h.match(/^#set=(.+)$/);
    if (m) {
      var name = decodeURIComponent(m[1]);
      if (setByZh[name]) {
        openDetail(name);
        return;
      }
    }
    backToList();
  }

  // ---- 初始化 ----
  // 页面守卫：仅当本页网格存在时才执行初始化（BD 构建页等加载本文件仅用渲染函数）
  if (document.getElementById("setListGrid")) {
    bind();
    renderList("");
    initFromHash();
  }
})();
