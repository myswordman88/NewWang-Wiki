// 基底装备筛选数据库：搜索 + 分类/级别筛选 + 排序（纯前端，无后端）
(function () {
  "use strict";
  var DATA = window.BASE_ITEMS || [];
  var grid = document.getElementById("baseGrid");
  var countEl = document.getElementById("baseCount");
  var emptyEl = document.getElementById("baseEmpty");
  var searchEl = document.getElementById("baseSearch");
  var catEl = document.getElementById("baseCat");
  var tierEl = document.getElementById("baseTier");
  var sortEl = document.getElementById("baseSort");
  var toggleEl = document.getElementById("baseToggleEn");
  var dbEl = document.getElementById("baseDb");

  var state = { q: "", cat: "", tier: "", sort: "default", showExtra: true };

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function uniq(arr) {
    return arr.filter(function (v, i) { return arr.indexOf(v) === i; });
  }

  function initFilters() {
    var cats = uniq(DATA.map(function (d) { return d.category; }));
    var TIER_ORDER = ["普通", "扩展", "精英"];
    var tiers = uniq(DATA.map(function (d) { return d.tier; })).sort(function (a, b) {
      var ia = TIER_ORDER.indexOf(a), ib = TIER_ORDER.indexOf(b);
      if (ia === -1) ia = 99; if (ib === -1) ib = 99;
      return ia - ib;
    });
    catEl.innerHTML = '<option value="">全部</option>' + cats.map(function (c) {
      return '<option value="' + esc(c) + '">' + esc(c) + "</option>";
    }).join("");
    tierEl.innerHTML = '<option value="">全部</option>' + tiers.map(function (t) {
      return '<option value="' + esc(t) + '">' + esc(t) + "</option>";
    }).join("");
  }

  function cardHTML(it) {
    var dura = it.durability ? (it.durability + " / " + it.durability) : "—";
    var defRange = it.defense_min + "–" + it.defense_max;
    var thumb = (it.name_zh || it.name_en || "?").charAt(0);
    var twName = it.name_zh_tw && it.name_zh_tw !== it.name_zh ? it.name_zh_tw : it.name_zh;
    return '<article class="base-card">'
      + '<div class="base-thumb" aria-hidden="true" data-code="' + esc(it.code) + '">'
      + '<span class="base-thumb-placeholder">' + esc(thumb) + "</span>"
      + '<img src="" alt="" loading="lazy" aria-hidden="true" />'
      + "</div>"
      + '<div class="base-card-body">'
      + '<h3 class="base-name">' + esc(it.name_zh) + "</h3>"
      + '<div class="base-subtitle">'
      + '<span class="base-tier tier-' + esc(it.tier) + '">' + esc(it.tier) + "</span>"
      + '<span class="base-dot" aria-hidden="true">·</span>'
      + '<span class="base-cat">' + esc(it.category) + "</span>"
      + "</div>"
      + '<div class="base-names-row">'
      + '<span class="base-zh"><span class="base-name-label">简</span>' + esc(it.name_zh) + "</span>"
      + '<span class="base-tw base-name-extra"><span class="base-name-label">繁</span>' + esc(twName) + "</span>"
      + "</div>"
      + '<hr class="base-divider" />'
      + '<div class="base-stats">'
      + '<div class="base-stat"><span class="base-stat-label">防御</span><strong class="base-stat-num">' + esc(defRange) + '</strong><span class="base-avg">(' + esc(it.defense_avg) + ' 平均)</span></div>'
      + '<div class="base-stat"><span class="base-stat-label">耐久度</span><strong class="base-stat-num">' + esc(dura) + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">需要等级</span><strong class="base-stat-num base-req-num">' + esc(it.qlvl) + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">需要力量</span><strong class="base-stat-num base-req-num">' + esc(it.reqstr) + "</strong></div>"
      + "</div>"
      + '<div class="base-card-bot">'
      + '<span class="base-qlvl">Qlvl <strong>' + esc(it.qlvl) + "</strong></span>"
      + '<span class="base-sockets">最大孔数 <strong>' + esc(it.max_sockets) + "</strong></span>"
      + "</div>"
      + "</div>"
      + "</article>";
  }

  function apply() {
    var q = state.q.trim().toLowerCase();
    var list = DATA.filter(function (d) {
      if (state.cat && d.category !== state.cat) return false;
      if (state.tier && d.tier !== state.tier) return false;
      if (q) {
        var hay = (d.name_zh + " " + d.name_zh_tw + " " + d.name_en + " " + d.code).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
    switch (state.sort) {
      case "name": list.sort(function (a, b) { return a.name_zh.localeCompare(b.name_zh, "zh"); }); break;
      case "def-desc": list.sort(function (a, b) { return b.defense_avg - a.defense_avg; }); break;
      case "def-asc": list.sort(function (a, b) { return a.defense_avg - b.defense_avg; }); break;
      case "str-asc": list.sort(function (a, b) { return a.reqstr - b.reqstr; }); break;
      case "qlvl-asc": list.sort(function (a, b) { return a.qlvl - b.qlvl; }); break;
      case "sock-desc": list.sort(function (a, b) { return b.max_sockets - a.max_sockets; }); break;
      default: break;
    }
    grid.innerHTML = list.map(cardHTML).join("");
    countEl.innerHTML = "共计 <strong>" + list.length + "</strong> 条数据";
    emptyEl.hidden = list.length !== 0;
  }

  function bind() {
    searchEl.addEventListener("input", function () { state.q = this.value; apply(); });
    catEl.addEventListener("change", function () { state.cat = this.value; apply(); });
    tierEl.addEventListener("change", function () { state.tier = this.value; apply(); });
    sortEl.addEventListener("change", function () { state.sort = this.value; apply(); });
    toggleEl.addEventListener("click", function () {
      state.showExtra = !state.showExtra;
      this.setAttribute("aria-pressed", String(state.showExtra));
      this.textContent = state.showExtra ? "隐藏对照" : "译名对照";
      dbEl.classList.toggle("hide-extra", !state.showExtra);
    });
  }

  initFilters();
  bind();
  apply();
})();
