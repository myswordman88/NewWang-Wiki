// 基底装备 / 武器 筛选数据库：搜索 + 分类/级别筛选 + 排序（纯前端，无后端）
// 视图驱动：防具(armor) 与 武器(weapon) 各一套数据、卡片渲染、排序项、快捷筛选。
(function () {
  "use strict";

  // 图片 onload：根据原图高度归类 c1/c2/c3，并把第一根分割线下移到图片框底边
  var ONLOAD_ATTR = "var t=this.closest('.base-thumb');var c=this.closest('.base-card');"
    + "if(c){var h=this.naturalHeight;var cls=h<=196?'c1':(h<=294?'c2':'c3');c.classList.add(cls);"
    + "var b=c.querySelector('.base-card-body');var d=c.querySelector('.base-divider');"
    + "if(b&&d&&t){b.style.paddingTop='';var cur=d.offsetTop;var gap=t.offsetTop;var tgt=gap+t.offsetHeight+gap;var add=Math.max(0,tgt-cur);d.style.marginTop=add+'px';}}";

  var GRID = document.getElementById("baseGrid");
  var COUNT = document.getElementById("baseCount");
  var EMPTY = document.getElementById("baseEmpty");
  var SEARCH = document.getElementById("baseSearch");
  var CAT = document.getElementById("baseCat");
  var TIER = document.getElementById("baseTier");
  var SORT_CONTROL = document.getElementById("baseSortControl");
  var SORT_DIR = document.getElementById("baseSortDir");
  var SORT_TRIGGER = document.getElementById("baseSortTrigger");
  var SORT_MENU = document.getElementById("baseSortMenu");
  var QUICK = document.getElementById("baseQuickFilters");
  var TABS = document.getElementById("baseTabs");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function uniq(a) {
    return a.filter(function (v, i) { return a.indexOf(v) === i; });
  }

  // ===== 卡片渲染：防具 =====
  function armorCard(it) {
    var dura = it.durability ? (it.durability + " / " + it.durability) : "—";
    var defRange = it.defense_min + "–" + it.defense_max;
    var thumb = (it.name_zh || it.name_en || "?").charAt(0);
    var twName = it.name_zh_tw && it.name_zh_tw !== it.name_zh ? it.name_zh_tw : it.name_zh;
    var hasImg = !!(it.img && it.img.length);
    var thumbCls = "base-thumb" + (hasImg ? " has-img" : "");
    var imgTag = hasImg
      ? '<img src="' + esc(it.img) + '" alt="' + esc(it.name_zh) + '" loading="lazy" onload="' + ONLOAD_ATTR + '" />'
      : '<img src="" alt="" loading="lazy" aria-hidden="true" />';
    var weightHTML = "";
    if (it.type_raw === "tors" || it.type_raw === "shie") {
      var wmap = { 0: ["轻型", "w-light"], 5: ["中型", "w-mid"], 10: ["重型", "w-heavy"] };
      var wv = wmap[it.speed];
      if (wv) {
        weightHTML = '<div class="base-weight"><span class="base-name-label">重量</span> <span class="base-weight-tag ' + wv[1] + '">「' + wv[0] + '」</span></div>';
      }
    }
    return '<article class="base-card' + (hasImg ? " has-img" : "") + '">'
      + '<div class="' + thumbCls + '" aria-hidden="true" data-code="' + esc(it.code) + '">'
      + '<span class="base-thumb-placeholder">' + esc(thumb) + "</span>"
      + imgTag
      + "</div>"
      + '<div class="base-card-body">'
      + '<h3 class="base-name">' + esc(it.name_zh) + "</h3>"
      + '<div class="base-subtitle">'
      + '<span class="base-tier tier-' + esc(it.tier) + '">' + esc(it.tier) + "</span>"
      + '<span class="base-dot" aria-hidden="true">·</span>'
      + '<span class="base-cat">' + esc(it.category) + "</span>"
      + "</div>"
      + '<div class="base-en-name"><span class="base-name-label">英</span> ' + esc(it.name_en) + "</div>"
      + '<div class="base-names-row">'
      + '<span class="base-zh"><span class="base-name-label">简</span> ' + esc(it.name_zh) + "</span>"
      + '<span class="base-tw"><span class="base-name-label">繁</span> ' + esc(twName) + "</span>"
      + "</div>"
      + weightHTML
      + '<hr class="base-divider" />'
      + '<div class="base-stats">'
      + '<div class="base-stat-group base-stat-left">'
      + '<div class="base-stat"><span class="base-stat-label">防御</span><strong class="base-stat-num">' + esc(defRange) + "</strong>" + (it.defense_avg ? '<span class="base-def-avg">（' + esc(it.defense_avg) + "平均）</span>" : "") + "</div>"
      + '<div class="base-stat"><span class="base-stat-label">耐久度</span><strong class="base-stat-num">' + esc(dura) + "</strong></div>"
      + "</div>"
      + '<div class="base-stat-group base-stat-right">'
      + '<div class="base-stat"><span class="base-stat-label">需要等级</span><strong class="base-stat-num base-req-num">' + esc(it.qlvl) + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">需要力量</span><strong class="base-stat-num base-req-num">' + esc(it.reqstr) + "</strong></div>"
      + "</div>"
      + "</div>"
      + '<div class="base-card-bot">'
      + '<span class="base-qlvl">Qlvl <strong>' + esc(it.qlvl) + "</strong></span>"
      + '<span class="base-sockets">最大孔数 <strong>' + esc(it.sockets3 ? it.sockets3.replace(/\//g, " / ") : it.max_sockets) + "</strong></span>"
      + "</div>"
      + "</div>"
      + "</article>";
  }

  // ===== 卡片渲染：武器 =====
  function weaponCard(it) {
    var isOther = it.category === "其他";
    var dura = it.durability ? (it.durability + " / " + it.durability) : "—";
    var dmgRange = it.damage_min + "–" + it.damage_max;
    // 「其他」类（Magic Arrows / Magic Bolts 等弹药）：伤害/耐久/速度 均显示 —
    var dmgHTML = isOther ? "—" : (esc(dmgRange) + (it.damage_avg ? '<span class="base-def-avg">（' + esc(it.damage_avg) + "平均）</span>" : ""));
    var duraDisplay = isOther ? "—" : dura;
    var spdDisplay = isOther ? "—" : esc(it.speed);
    // 顶部「武器速度」行：放在繁体译名下一行，类似于防具重量；负值=快(绿)、0=普通(金)、正值=慢(红)
    var speedVal = isOther ? "—" : it.speed;
    var sf = isOther ? 0 : parseFloat(it.speed);
    var speedCls = sf < 0 ? "w-fast" : (sf > 0 ? "w-slow" : "w-normal");
    var speedHTML = '<div class="base-speed"><span class="base-name-label">武器速度</span>：<span class="base-speed-tag ' + speedCls + '">' + esc(speedVal) + "</span></div>";
    var thumb = (it.name_zh || it.name_en || "?").charAt(0);
    var twName = it.name_zh_tw && it.name_zh_tw !== it.name_zh ? it.name_zh_tw : it.name_zh;
    var hasImg = !!(it.img && it.img.length);
    var thumbCls = "base-thumb" + (hasImg ? " has-img" : "");
    var imgTag = hasImg
      ? '<img src="' + esc(it.img) + '" alt="' + esc(it.name_zh) + '" loading="lazy" onload="' + ONLOAD_ATTR + '" />'
      : '<img src="" alt="" loading="lazy" aria-hidden="true" />';
    return '<article class="base-card' + (hasImg ? " has-img" : "") + '">'
      + '<div class="' + thumbCls + '" aria-hidden="true" data-code="' + esc(it.code) + '">'
      + '<span class="base-thumb-placeholder">' + esc(thumb) + "</span>"
      + imgTag
      + "</div>"
      + '<div class="base-card-body">'
      + '<h3 class="base-name">' + esc(it.name_zh) + "</h3>"
      + '<div class="base-subtitle">'
      + '<span class="base-tier tier-' + esc(it.tier) + '">' + esc(it.tier) + "</span>"
      + '<span class="base-dot" aria-hidden="true">·</span>'
      + '<span class="base-cat">' + esc(it.category) + "</span>"
      + "</div>"
      + '<div class="base-en-name"><span class="base-name-label">英</span> ' + esc(it.name_en) + "</div>"
      + '<div class="base-names-row">'
      + '<span class="base-zh"><span class="base-name-label">简</span> ' + esc(it.name_zh) + "</span>"
      + '<span class="base-tw"><span class="base-name-label">繁</span> ' + esc(twName) + "</span>"
      + "</div>"
      + speedHTML
      + '<hr class="base-divider" />'
      + '<div class="base-stats">'
      + '<div class="base-stat-group base-stat-left">'
      + '<div class="base-stat"><span class="base-stat-label">伤害</span><strong class="base-stat-num">' + dmgHTML + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">耐久度</span><strong class="base-stat-num">' + duraDisplay + "</strong></div>"
      + (it.rangeadder && String(it.rangeadder) !== "0" ? '<div class="base-stat"><span class="base-stat-label">攻击距离加成</span><strong class="base-stat-num">' + esc(it.rangeadder) + "</strong></div>" : "")
      + "</div>"
      + '<div class="base-stat-group base-stat-right">'
      + '<div class="base-stat"><span class="base-stat-label">需要等级</span><strong class="base-stat-num base-req-num">' + esc(it.qlvl) + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">需要力量</span><strong class="base-stat-num base-req-num">' + esc(it.reqstr) + "</strong></div>"
      + '<div class="base-stat"><span class="base-stat-label">需要敏捷</span><strong class="base-stat-num base-req-num">' + esc(it.reqdex) + "</strong></div>"
      + "</div>"
      + "</div>"
      + '<div class="base-card-bot">'
      + '<span class="base-qlvl">Qlvl <strong>' + esc(it.qlvl) + "</strong></span>"
      + '<span class="base-sockets">最大孔数 <strong>' + esc(it.sockets3 ? it.sockets3.replace(/\//g, " / ") : it.max_sockets) + "</strong></span>"
      + "</div>"
      + "</div>"
      + "</article>";
  }

  // ===== 视图配置 =====
  var VIEWS = {
    armor: {
      data: function () { return window.BASE_ITEMS || []; },
      card: armorCard,
      catLabel: { "铠甲": "衣服" },
      quickCats: ["头盔", "铠甲", "盾牌", "腰带", "靴子", "手套"],
      sorts: [
        { key: "default", label: "默认（编号）", dir: "asc" },
        { key: "name", label: "名称", dir: "asc" },
        { key: "def", label: "平均防御", dir: "desc", field: "defense_avg", num: true },
        { key: "str", label: "需求力量", dir: "asc", field: "reqstr", num: true },
        { key: "qlvl", label: "需求等级", dir: "asc", field: "qlvl", num: true },
        { key: "sock", label: "最大孔数", dir: "desc", field: "max_sockets", num: true }
      ]
    },
    weapon: {
      data: function () { return window.WEAPON_ITEMS || []; },
      card: weaponCard,
      catLabel: {},
      quickCats: null,
      sorts: [
        { key: "default", label: "默认（编号）", dir: "asc" },
        { key: "name", label: "名称", dir: "asc" },
        { key: "dam", label: "平均伤害", dir: "desc", field: "damage_avg", num: true },
        { key: "str", label: "需求力量", dir: "asc", field: "reqstr", num: true },
        { key: "dex", label: "需求敏捷", dir: "asc", field: "reqdex", num: true },
        { key: "qlvl", label: "需求等级", dir: "asc", field: "qlvl", num: true },
        { key: "sock", label: "最大孔数", dir: "desc", field: "max_sockets", num: true }
      ]
    }
  };

  var state = { view: "armor", q: "", cat: "", tier: "", sortKey: "default", sortDir: "asc" };

  function curView() { return VIEWS[state.view]; }
  function getData() { return curView().data(); }
  function findSort(key) {
    var s = curView().sorts;
    for (var i = 0; i < s.length; i++) { if (s[i].key === key) return s[i]; }
    return null;
  }

  function initFilters() {
    var data = getData();
    var cats = uniq(data.map(function (d) { return d.category; }));
    var TIER_ORDER = ["普通", "扩展", "精英"];
    var tiers = uniq(data.map(function (d) { return d.tier; })).sort(function (a, b) {
      var ia = TIER_ORDER.indexOf(a), ib = TIER_ORDER.indexOf(b);
      if (ia === -1) ia = 99; if (ib === -1) ib = 99;
      return ia - ib;
    });
    CAT.innerHTML = '<option value="">全部</option>' + cats.map(function (c) {
      return '<option value="' + esc(c) + '">' + esc(c) + "</option>";
    }).join("");
    TIER.innerHTML = '<option value="">全部</option>' + tiers.map(function (t) {
      return '<option value="' + esc(t) + '">' + esc(t) + "</option>";
    }).join("");
  }

  function buildQuickFilters() {
    if (!QUICK) return;
    var v = curView();
    var cats = v.quickCats || uniq(getData().map(function (d) { return d.category; }));
    // 「其他」类置末，符合直觉
    var oi = cats.indexOf("其他");
    if (oi >= 0) { cats.splice(oi, 1); cats.push("其他"); }
    QUICK.innerHTML = '<button class="base-chip active" data-cat="" data-tier="">全部</button>' + cats.map(function (c) {
      var label = v.catLabel[c] || c;
      return '<button class="base-chip" data-cat="' + esc(c) + '" data-tier="">' + esc(label) + "</button>";
    }).join("");
    setActiveQuick(state.cat, state.tier);
  }

  function buildSortMenu() {
    if (!SORT_MENU) return;
    var v = curView();
    SORT_MENU.innerHTML = v.sorts.map(function (o) {
      return '<button type="button" class="base-sort-option" role="menuitem" data-key="' + o.key + '" data-dir="' + o.dir + '">' + esc(o.label) + "</button>";
    }).join("");
  }

  function apply() {
    var q = state.q.trim().toLowerCase();
    var list = getData().filter(function (d) {
      if (state.cat && d.category !== state.cat) return false;
      if (state.tier && d.tier !== state.tier) return false;
      if (q) {
        var hay = (d.name_zh + " " + d.name_zh_tw + " " + d.name_en + " " + d.code).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
    if (state.sortKey !== "default") {
      var opt = findSort(state.sortKey);
      var dir = state.sortDir === "desc" ? -1 : 1;
      if (opt && opt.key === "name") {
        list.sort(function (a, b) { return a.name_zh.localeCompare(b.name_zh, "zh") * dir; });
      } else if (opt && opt.num) {
        list.sort(function (a, b) {
          var va = parseFloat(a[opt.field]) || 0, vb = parseFloat(b[opt.field]) || 0;
          return (va - vb) * dir;
        });
      }
    }
    GRID.innerHTML = list.map(curView().card).join("");
    COUNT.innerHTML = "共计 <strong>" + list.length + "</strong> 条数据";
    EMPTY.hidden = list.length !== 0;
    setActiveQuick(state.cat, state.tier);
    updateSortUI();
  }

  function setActiveQuick(cat, tier) {
    if (!QUICK) return;
    QUICK.querySelectorAll("button[data-cat]").forEach(function (chip) {
      var c = chip.getAttribute("data-cat") || "";
      var t = chip.getAttribute("data-tier") || "";
      chip.classList.toggle("active", (c === cat && t === tier));
    });
  }

  function updateSortUI() {
    if (!SORT_TRIGGER || !SORT_DIR || !SORT_MENU) return;
    var isDefault = state.sortKey === "default";
    var opt = findSort(state.sortKey);
    var label = isDefault ? "排序" : (opt ? opt.label : "排序");
    SORT_TRIGGER.querySelector(".base-sort-label").textContent = label;
    SORT_TRIGGER.querySelector(".base-sort-arrow").textContent = isDefault ? "▼" : (state.sortDir === "desc" ? "▼" : "▲");

    SORT_DIR.classList.toggle("active", !isDefault);
    SORT_DIR.classList.remove("asc", "desc");
    var dirIcon = SORT_DIR.querySelector(".base-sort-dir-icon");
    if (isDefault) {
      dirIcon.textContent = "↕";
    } else {
      SORT_DIR.classList.add(state.sortDir);
      dirIcon.textContent = state.sortDir === "desc" ? "↓" : "↑";
    }

    SORT_MENU.querySelectorAll(".base-sort-option").forEach(function (o) {
      var key = o.getAttribute("data-key");
      var active = key === state.sortKey;
      o.classList.toggle("active", active);
      if (active) o.setAttribute("data-dir", state.sortDir);
      else o.setAttribute("data-dir", o.getAttribute("data-dir") || "asc");
    });
  }

  function setSortMenu(open) {
    if (!SORT_MENU || !SORT_TRIGGER) return;
    SORT_MENU.hidden = !open;
    SORT_TRIGGER.setAttribute("aria-expanded", String(open));
  }

  function bind() {
    SEARCH.addEventListener("input", function () { state.q = this.value; apply(); });
    CAT.addEventListener("change", function () { state.cat = this.value; apply(); });
    TIER.addEventListener("change", function () { state.tier = this.value; apply(); });

    if (TABS) {
      TABS.addEventListener("click", function (e) {
        var btn = e.target.closest(".base-tab");
        if (!btn) return;
        var nv = btn.getAttribute("data-view");
        if (!nv || nv === state.view) return;
        state.view = nv;
        state.cat = ""; state.tier = ""; state.sortKey = "default"; state.sortDir = "asc";
        CAT.value = ""; TIER.value = "";
        TABS.querySelectorAll(".base-tab").forEach(function (b) {
          var on = b.getAttribute("data-view") === nv;
          b.classList.toggle("active", on);
          b.setAttribute("aria-selected", String(on));
        });
        initFilters();
        buildQuickFilters();
        buildSortMenu();
        updateSortUI();
        apply();
      });
    }

    if (SORT_DIR) {
      SORT_DIR.addEventListener("click", function () {
        if (state.sortKey === "default") return;
        state.sortDir = state.sortDir === "desc" ? "asc" : "desc";
        updateSortUI();
        apply();
      });
    }

    if (SORT_TRIGGER && SORT_MENU) {
      SORT_TRIGGER.addEventListener("click", function (e) {
        e.stopPropagation();
        setSortMenu(SORT_MENU.hidden);
      });
      SORT_MENU.addEventListener("click", function (e) {
        var opt = e.target.closest(".base-sort-option");
        if (!opt) return;
        var key = opt.getAttribute("data-key");
        var dir = opt.getAttribute("data-dir") || "asc";
        state.sortKey = key;
        state.sortDir = key === "default" ? "asc" : dir;
        setSortMenu(false);
        updateSortUI();
        apply();
      });
      document.addEventListener("click", function (e) {
        if (!SORT_CONTROL.contains(e.target)) setSortMenu(false);
      });
    }

    if (QUICK) {
      QUICK.addEventListener("click", function (e) {
        var target = e.target.closest("button");
        if (!target) return;
        var cat = target.getAttribute("data-cat") || "";
        var tier = target.getAttribute("data-tier") || "";
        state.cat = cat;
        state.tier = tier;
        CAT.value = cat;
        TIER.value = tier;
        setActiveQuick(cat, tier);
        apply();
      });
    }
  }

  initFilters();
  buildQuickFilters();
  buildSortMenu();
  bind();
  updateSortUI();
  apply();
})();
