/* 魔法&稀有词缀总表：客户端渲染
 * 依赖：js/magic-rare.js (window.MAGIC_RARE)
 * 设计：
 *  - 默认不渲染词条（避免 1476 行一次性卡顿）；点击顶部「装备类型」筛选按钮后才渲染。
 *  - 词条按暗金装备风格显示为可读中文（如「法力 1 - 5」「增强伤害 60 - 70%」），不再展开原始代码列。
 *  - itype/etype 仅用于筛选，不在列表中显示。
 */
(function () {
  "use strict";

  // 列定义（合并后 8 列）：类型 / 名称(中文+Name) / 稀有度(rare 标签) / 等级 / 需求等级 / 掉落频率 / 组 / 词条(合并 mod1~3)
  // cn/en 分开，渲染时英文换行显示在中文下方
  var COLS = [
    { id: "type", cn: "类型", en: "Type", cls: "col-type", kind: "badge" },
    { id: "name", cn: "名称", en: "Name", cls: "col-name", kind: "combined" },
    { id: "rare", cn: "稀有度", en: "Rare", kind: "raretags" },
    { id: "level", cn: "等级", en: "Alvl", kind: "num" },
    { id: "levelreq", cn: "需求等级", en: "Levelreq", kind: "num" },
    { id: "frequency", cn: "掉落频率", en: "Frequency", kind: "num" },
    { id: "group", cn: "组", en: "group", kind: "num" },
    { id: "mods", cn: "词条", en: "Mod code", kind: "modtext", path: ["mods"] }
  ];

  // 装备类型分类（用于顶部筛选按钮折叠）
  var EQ_CATS = [
    { key: "weapon", label: "武器", codes: ["weap", "mele", "miss", "swor", "axe", "mace", "hamm", "club", "blun", "pole", "spea", "aspe", "knif", "thro", "tkni", "h2h", "abow", "mboq", "mxbq", "orb", "staff", "staf", "wand", "rod", "scep", "grim", "pelt"] },
    { key: "armor", label: "护甲", codes: ["armo", "tors", "circ", "helm", "phlm", "ashd", "shld", "glov", "boot", "belt"] },
    { key: "jewelry", label: "首饰", codes: ["amul", "ring", "jewl"] },
    { key: "charm", label: "咒符", codes: ["scha", "mcha", "lcha"] },
    { key: "class", label: "职业专用", codes: ["amaz", "head"] }
  ];

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  // 数字（含范围/百分号）高亮，沿用暗金装备页风格
  function colorizeProp(text) {
    var safe = esc(text);
    return safe.replace(/(\d+(?:\s*-\s*\d+)?%?)/g, '<span class="prop-num">$1</span>');
  }

  function getPath(r, p) {
    var v = r;
    for (var k = 0; k < p.length; k++) {
      if (v == null) return null;
      v = v[p[k]];
    }
    return v;
  }

  function renderCell(r, c) {
    if (c.kind === "badge") {
      return '<td class="col-type"><span class="affix-badge ' + r.type + '">' +
        (r.type === "prefix" ? "前缀" : "后缀") + "</span></td>";
    }
    if (c.kind === "combined") {
      // 名称列：中文（Name）—— 例：虚无之（Blank）；中文缺失时只显示 Name
      var cn = r.nameCn || "";
      var nm = r.name || "";
      var txt = cn ? cn + "（" + nm + "）" : nm;
      if (!txt) return '<td class="' + (c.cls || "") + ' cell-empty"></td>';
      return '<td class="' + (c.cls || "") + '">' + esc(txt) + "</td>";
    }
    if (c.kind === "modtext") {
      var mods = getPath(r, c.path) || [];
      var parts = [];
      mods.forEach(function (m) { if (m && m.text) parts.push(m.text); });
      if (!parts.length) return '<td class="cell-modtext cell-empty"></td>';
      // 多个词条用「 / 」分隔，分隔符加粗绿色高亮
      var html = parts.map(function (p) { return colorizeProp(p); })
        .join('<span class="mod-sep"> / </span>');
      return '<td class="cell-modtext">' + html + "</td>";
    }
    if (c.kind === "raretags") {
      var isRare = (r.rare === "1");
      var tagHtml = '<span class="affix-rare-tag magic">魔法</span>';
      if (isRare) tagHtml += '<span class="affix-rare-tag rare">稀有</span>';
      return '<td class="cell-rare"><span class="affix-rare-tags">' + tagHtml + "</span></td>";
    }
    var v = r[c.id] != null ? String(r[c.id]) : "";
    var cls = c.cls || "";
    if (v === "") {
      cls += " cell-empty";
      return '<td class="' + cls.trim() + '"></td>';
    }
    return '<td class="' + cls.trim() + '">' + esc(v) + "</td>";
  }

  function buildTable(rows) {
    var thead = "<thead><tr>" + COLS.map(function (c) {
      // 词条列例外：中文（英文）单行；其余列中文在上、英文小字换行在下（带括号）
      var enCls = (c.id === "mods") ? "h-en-inline" : "h-en";
      return '<th class="' + (c.cls || "") + '"><span class="h-cn">' + esc(c.cn) +
        '</span><span class="' + enCls + '">（' + esc(c.en) + "）</span></th>";
    }).join("") + "</tr></thead>";
    var tbody = "<tbody>" + rows.map(function (r) {
      return "<tr>" + COLS.map(function (c) { return renderCell(r, c); }).join("") + "</tr>";
    }).join("") + "</tbody>";
    return '<table class="affix-table">' + thead + tbody + "</table>";
  }

  var DATA = null;
  var state = { eqType: null, typeFilter: "all", rareFilter: "all", q: "" };

  // 计算数据中出现的装备类型（按 itype，排除 etype 互斥），返回 [{code,cn,count}]
  function collectEqTypes() {
    var map = {};
    DATA.list.forEach(function (r) {
      var exc = r.etypes.map(function (t) { return t.code; }).filter(Boolean);
      r.itypes.forEach(function (t) {
        if (!t.code || exc.indexOf(t.code) !== -1) return;
        if (!map[t.code]) map[t.code] = { code: t.code, cn: t.cn || t.code, count: 0 };
        map[t.code].count++;
      });
    });
    return Object.keys(map).map(function (k) { return map[k]; })
      .sort(function (a, b) { return b.count - a.count || a.cn.localeCompare(b.cn, "zh"); });
  }

  function matchesEq(r, code) {
    if (!code) return true;
    var inc = r.itypes.some(function (t) { return t.code === code; });
    var exc = r.etypes.some(function (t) { return t.code === code; });
    return inc && !exc;
  }

  function applyFilter() {
    var q = state.q.trim().toLowerCase();
    return DATA.list.filter(function (r) {
      if (!matchesEq(r, state.eqType)) return false;
      if (state.typeFilter !== "all" && r.type !== state.typeFilter) return false;
      // 装备品质筛选（对应 rare 列）：魔法=rare 为空/0；稀有=rare=1
      if (state.rareFilter === "magic" && r.rare === "1") return false;
      if (state.rareFilter === "rare" && r.rare !== "1") return false;
      if (q && r.name.toLowerCase().indexOf(q) === -1 &&
        (r.nameCn || "").toLowerCase().indexOf(q) === -1) return false;
      return true;
    });
  }

  function render() {
    var countEl = document.getElementById("affixCount");
    var wrap = document.getElementById("affixTableWrap");
    var hintEl = document.getElementById("affixHint");
    var expandRow = document.getElementById("affixExpandRow");
    if (!wrap) return;

    if (!state.eqType) {
      wrap.innerHTML = "";
      if (hintEl) hintEl.style.display = "";
      if (countEl) countEl.innerHTML = "请选择上方装备类型，查看对应词缀";
      if (expandRow) expandRow.style.display = "none";
      return;
    }
    if (hintEl) hintEl.style.display = "none";

    var rows = applyFilter();
    if (!rows.length) {
      wrap.innerHTML = '<p class="affix-empty">没有匹配的词缀，试试调整筛选或搜索关键词。</p>';
      if (countEl) countEl.innerHTML = "共 <strong>0</strong> 条";
      if (expandRow) expandRow.style.display = "none";
      return;
    }
    var np = rows.filter(function (r) { return r.type === "prefix"; }).length;
    var ns = rows.filter(function (r) { return r.type === "suffix"; }).length;
    if (countEl) countEl.innerHTML = "共 <strong>" + rows.length + "</strong> 条（前缀 " + np + " / 后缀 " + ns + "）";
    if (expandRow) expandRow.style.display = "";
    wrap.innerHTML = buildTable(rows);
  }

  function buildEqButtons() {
    var bar = document.getElementById("affixEqBar");
    if (!bar) return;
    var types = collectEqTypes();
    var byCode = {};
    types.forEach(function (t) { byCode[t.code] = t; });
    var categorized = {};
;
    var html = EQ_CATS.map(function (cat) {
      var items = cat.codes.map(function (c) { return byCode[c]; }).filter(Boolean)
        .sort(function (a, b) { return b.count - a.count; });
      items.forEach(function (t) { categorized[t.code] = true; });
      if (!items.length) return "";
      var total = items.reduce(function (s, t) { return s + t.count; }, 0);
      var btns = items.map(function (t) {
        return '<button type="button" class="affix-eq-btn" data-eq="' + esc(t.code) +
          '" data-cn="' + esc(t.cn) + '" title="' + esc(t.code) + '">' + esc(t.cn) +
          '<span class="affix-eq-count">' + t.count + "</span></button>";
      }).join("");
      return '<details class="affix-eq-cat"><summary>' + esc(cat.label) +
        '<span class="affix-cat-count">' + total + '</span></summary>' +
        '<div class="affix-eq-bar">' + btns + "</div></details>";
    }).join("");

    // 兜底：未归入上述分类的装备类型
    var others = types.filter(function (t) { return !categorized[t.code]; });
    if (others.length) {
      var ob = others.map(function (t) {
        return '<button type="button" class="affix-eq-btn" data-eq="' + esc(t.code) +
          '" data-cn="' + esc(t.cn) + '" title="' + esc(t.code) + '">' + esc(t.cn) +
          '<span class="affix-eq-count">' + t.count + "</span></button>";
      }).join("");
      html += '<details class="affix-eq-cat"><summary>其他' +
        '<span class="affix-cat-count">' + others.reduce(function (s, t) { return s + t.count; }, 0) +
        '</span></summary><div class="affix-eq-bar">' + ob + "</div></details>";
    }
    bar.innerHTML = html;
  }

  function bind() {
    var eqBtns = document.querySelectorAll(".affix-eq-btn");
    eqBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        var code = b.getAttribute("data-eq") || "";
        var already = state.eqType === code;
        state.eqType = already ? null : code;
        eqBtns.forEach(function (x) { x.classList.remove("active"); });
        if (!already) b.classList.add("active");
        var label = document.getElementById("affixEqLabel");
        if (label) label.textContent = already ? "" : (b.getAttribute("data-cn") || "");
        render();
      });
    });
    var typeBtns = document.querySelectorAll("[data-typefilter]");
    typeBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        state.typeFilter = b.getAttribute("data-typefilter") || "all";
        typeBtns.forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        render();
      });
    });
    var rareBtns = document.querySelectorAll("[data-rarefilter]");
    rareBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        var rf = b.getAttribute("data-rarefilter");
        // 再次点击同一按钮 -> 取消该品质筛选
        state.rareFilter = (state.rareFilter === rf) ? "all" : rf;
        rareBtns.forEach(function (x) { x.classList.remove("active"); });
        if (state.rareFilter !== "all") b.classList.add("active");
        render();
      });
    });
    var search = document.getElementById("affixSearch");
    if (search) {
      search.addEventListener("input", function () {
        state.q = search.value || "";
        render();
      });
    }
    // 展开全部 / 收起滚动 切换
    var expandBtn = document.getElementById("affixExpandBtn");
    if (expandBtn) {
      expandBtn.addEventListener("click", function () {
        var wrap = document.getElementById("affixTableWrap");
        if (!wrap) return;
        var expanded = wrap.classList.toggle("affix-expand");
        expandBtn.classList.toggle("active", expanded);
        expandBtn.textContent = expanded ? "收起滚动" : "展开全部";
      });
    }
  }

  function init() {
    DATA = window.MAGIC_RARE;
    if (!DATA || !DATA.list) {
      var wrap = document.getElementById("affixTableWrap");
      if (wrap) wrap.innerHTML = '<p class="affix-empty">词缀数据未能加载（js/magic-rare.js）。</p>';
      return;
    }
    buildEqButtons();
    bind();
    render();
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
