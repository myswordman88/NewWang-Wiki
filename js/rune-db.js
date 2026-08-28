// 符文之语页面：搜索 + 分类/孔数筛选 + 排序 + 译名对照 + 卡片网格
(function () {
  "use strict";

  var DATA = window.RUNEWORDS || [];

  // ---------- 分类定义 ----------
  var WEAPON_CODES = ['axe','club','grim','h2h','hamm','knif','mace','mele','miss','pala','pole','scep','spea','staf','swor','wand','weap'];
  var SHIELD_CODES = ['shld','ashd','head'];
  var ARMOR_CODES  = ['helm','tors'];          // helm / tors 作为独立主类显示

  var CATEGORIES = [
    { key: 'all',    label: '全部', codes: null },
    { key: 'weapon', label: '武器', codes: WEAPON_CODES },
    { key: 'shield', label: '盾牌', codes: SHIELD_CODES },
    { key: 'helm',   label: '头盔', codes: ['helm'] },
    { key: 'armor',  label: '衣服', codes: ['tors'] },
    { key: 'glove',  label: '手套', codes: ['glov'] },
    { key: 'boot',   label: '鞋子', codes: ['boot'] },
    { key: 'belt',   label: '腰带', codes: ['belt'] },
    { key: 'quiv',   label: '箭袋', codes: ['bowq', 'xboq'] },
  ];

  var SUBTYPES = [
    { key: 'axe',   label: '斧',       codes: ['axe'] },
    { key: 'swor',  label: '剑',       codes: ['swor'] },
    { key: 'hamm',  label: '锤',       codes: ['hamm'] },
    { key: 'mace',  label: '钉锤',     codes: ['mace'] },
    { key: 'club',  label: '棍棒',     codes: ['club'] },
    { key: 'knif',  label: '匕首',     codes: ['knif'] },
    { key: 'spea',  label: '矛',       codes: ['spea'] },
    { key: 'pole',  label: '长柄武器', codes: ['pole'] },
    { key: 'scep',  label: '权杖',     codes: ['scep'] },
    { key: 'wand',  label: '手杖',     codes: ['wand'] },
    { key: 'staf',  label: '法杖',     codes: ['staf'] },
    { key: 'h2h',   label: '爪子',     codes: ['h2h'] },
    { key: 'grim',  label: '魔典',     codes: ['grim'] },
    { key: 'mele',  label: '近战武器', codes: ['mele'] },
    { key: 'miss',  label: '远程武器', codes: ['miss'] },
    { key: 'pala',  label: '圣骑士专用', codes: ['pala'] },
    { key: 'weap',  label: '所有武器', codes: ['weap'] },
  ];

  var SOCKETS = [2, 3, 4, 5, 6];

  // ---------- DOM ----------
  var SEARCH = document.getElementById("runeSearch");
  var FILTER_TOGGLE = document.getElementById("runeFilterToggle");
  var FILTER_PANEL = document.getElementById("runeFilterPanel");
  var CATEGORY_FILTER = document.getElementById("runeCategoryFilter");
  var SUBTYPE_FILTER = document.getElementById("runeSubtypeFilter");
  var SOCKET_FILTER = document.getElementById("runeSocketFilter");
  var SORT_CONTROL = document.getElementById("runeSortControl");
  var SORT_DIR = document.getElementById("runeSortDir");
  var SORT_TRIGGER = document.getElementById("runeSortTrigger");
  var SORT_MENU = document.getElementById("runeSortMenu");
  var PROP_SORT_BTN = document.getElementById("runePropSortBtn");
  var GRID = document.getElementById("runeGrid");
  var COUNT = document.getElementById("runeListCount");
  var EMPTY = document.getElementById("runeListEmpty");

  // ---------- 排序选项（仅需等级一种） ----------
  var SORTS = [
    { key: 'req_lvl', label: '需要等级', dir: 'asc', num: true, field: 'req_lvl' }
  ];
  function findSort(key) {
    for (var i = 0; i < SORTS.length; i++) if (SORTS[i].key === key) return SORTS[i];
    return SORTS[0];
  }

  // ---------- 状态 ----------
  var state = {
    query: "",
    category: "all",
    subtype: null,
    socket: null,
    sortKey: "req_lvl",
    sortDir: "asc",
    showNames: true,          // 译名对照按钮已移除，固定显示 EN/繁/原
    propSortQuery: "",        // 按当前搜索词临时排序的词
    propSortDir: "desc",      // 默认降序（数值大在前）
    filtersOpen: window.innerWidth > 720   // 桌面默认展开，移动端折叠
  };

  // ---------- 工具函数 ----------
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function runeNumber(code) {
    var m = String(code).match(/^(?:r)?(\d+)$/i);
    return m ? parseInt(m[1], 10) : 0;
  }

  // 符文图 <img>：输出路径 assets/runes/rNN.webp
  function runeImg(r) {
    return '<img class="rune-stone" src="assets/runes/' + esc(r.code) + '.webp" alt="'
      + esc(r.zh) + '符文" loading="lazy" decoding="async" />';
  }

  // 属性文本着色：range 模式——仅「数字 - 数字」才是范围(金色)，前导负号是普通负数(蓝色)
  function colorizeProp(text, mode) {
    if (!text) return '';
    var plain = mode === "plain";
    var parts = text.split(/([+-]?\d+(?:\s*-\s*[+-]?\d+)?%?)/);
    return parts.map(function (part) {
      if (/^[+-]?\d+(?:\s*-\s*[+-]?\d+)?%?$/.test(part)) {
        // 范围须为「数字 连字符 数字」，前导负号(负数)不算范围
        var isRange = /^\d+\s*-\s*[+-]?\d+%?$/.test(part);
        if (plain || !isRange) {
          return '<span class="prop-text">' + esc(part) + '</span>';
        }
        return '<span class="prop-num">' + esc(part) + '</span>';
      }
      return '<span class="prop-text">' + esc(part) + '</span>';
    }).join('');
  }

  function hasCode(r, codes) {
    if (!codes) return true;
    return r.itypes.some(function (t) { return codes.indexOf(t.code) !== -1; });
  }

  // 从属性中提取“含搜索词那行”的数值，用于按词条排序（取所有匹配行中最大数值）
  function extractPropNum(r, q) {
    q = (q || "").trim().toLowerCase();
    if (!q) return NaN;
    var best = NaN;
    for (var i = 0; i < r.props.length; i++) {
      var t = (r.props[i].text || "").toLowerCase();
      if (t.indexOf(q) === -1) continue;
      var nums = t.match(/[+-]?\d+(?:\.\d+)?/g);
      if (!nums) continue;
      var mx = nums.map(Number).reduce(function (a, b) { return Math.max(a, b); }, -Infinity);
      if (isNaN(best) || mx > best) best = mx;
    }
    return best;
  }

  function countBy(fn) {
    var map = {};
    DATA.forEach(function (r) { map[r.rw_key] = true; });
    return Object.keys(map).length; // placeholder if needed
  }

  // ---------- 渲染筛选按钮 ----------
  function renderFilters() {
    // 主分类
    CATEGORY_FILTER.innerHTML = CATEGORIES.map(function (c) {
      var active = state.category === c.key ? ' active' : '';
      return '<button type="button" class="rune-chip-btn' + active + '" data-cat="' + c.key + '">'
        + esc(c.label) + '</button>';
    }).join('');

    // 武器子类（仅在武器/全部主类下显示；非武器主类时整行隐藏）。
    // 无论是否显示都重渲染 innerHTML，使高亮始终与 state.subtype 一致——
    // 否则切到非武器主类后旧的高亮按钮仍残留在 DOM 中（bug 修复）。
    var showSub = state.category === 'weapon' || state.category === 'all';
    SUBTYPE_FILTER.hidden = !showSub;
    SUBTYPE_FILTER.innerHTML = SUBTYPES.map(function (s) {
      var active = state.subtype === s.key ? ' active' : '';
      return '<button type="button" class="rune-chip-btn' + active + '" data-sub="' + s.key + '">'
        + esc(s.label) + '</button>';
    }).join('');

    // 孔数
    SOCKET_FILTER.innerHTML = '<button type="button" class="rune-chip-btn' + (state.socket === null ? ' active' : '') + '" data-sock="">全部</button>'
      + SOCKETS.map(function (n) {
          var active = state.socket === n ? ' active' : '';
          return '<button type="button" class="rune-chip-btn' + active + '" data-sock="' + n + '">'
            + n + '孔</button>';
        }).join('');
  }

  function updateFilterPanel() {
    FILTER_PANEL.hidden = !state.filtersOpen;
    FILTER_TOGGLE.setAttribute("aria-expanded", String(state.filtersOpen));
  }

  // ---------- 过滤与排序 ----------
  function matchesQuery(r, q) {
    if (!q) return true;
    var hay = [
      r.rw_zh, r.rw_en, r.rw_zh_tw,
      r.runes.map(function (x) { return x.zh + ' ' + x.en + ' ' + x.code; }).join(' '),
      r.itypes.map(function (t) { return t.name + ' ' + t.name_en + ' ' + t.code; }).join(' '),
      r.props.map(function (p) { return p.text; }).join(' ')
    ].join(' ').toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  function getFiltered() {
    var q = state.query.toLowerCase();
    var list = DATA.filter(function (r) {
      if (!matchesQuery(r, q)) return false;

      // 主分类
      var cat = state.category;
      if (cat !== 'all') {
        var catCodes = (CATEGORIES.find(function (c) { return c.key === cat; }) || {}).codes;
        if (!hasCode(r, catCodes)) return false;
      }

      // 子类（优先级高于主分类；选中子类时只看子类 code）
      if (state.subtype) {
        var sub = SUBTYPES.find(function (s) { return s.key === state.subtype; });
        if (sub && !hasCode(r, sub.codes)) return false;
      }

      // 孔数
      if (state.socket !== null && r.sockets !== state.socket) return false;

      return true;
    });

    // 排序：若按当前搜索词临时排序则按属性数值，否则按需要等级
    if (state.propSortQuery) {
      var pdir = state.propSortDir === "asc" ? 1 : -1;
      list.sort(function (a, b) {
        var va = extractPropNum(a, state.propSortQuery);
        var vb = extractPropNum(b, state.propSortQuery);
        if (isNaN(va) && isNaN(vb)) return 0;
        if (isNaN(va)) return 1;
        if (isNaN(vb)) return -1;
        return (va - vb) * pdir || a.rw_zh.localeCompare(b.rw_zh, "zh-CN");
      });
    } else {
      var opt = findSort(state.sortKey);
      var dir = state.sortDir === "desc" ? -1 : 1;
      if (opt && opt.num) {
        list.sort(function (a, b) {
          return ((a[opt.field] || 0) - (b[opt.field] || 0)) * dir
            || a.rw_zh.localeCompare(b.rw_zh, "zh-CN");
        });
      }
    }

    return list;
  }

  // ---------- 排序按钮 UI（分体：左箭头逆序 / 右下拉选需要等级） ----------
  function buildSortMenu() {
    if (!SORT_MENU) return;
    SORT_MENU.innerHTML = SORTS.map(function (o) {
      return '<button type="button" class="rune-sort-option" role="menuitem" data-key="' + o.key + '" data-dir="' + o.dir + '">'
        + esc(o.label) + '</button>';
    }).join("");
  }

  function updateSortUI() {
    if (!SORT_TRIGGER || !SORT_DIR || !SORT_MENU) return;
    var opt = findSort(state.sortKey);
    SORT_TRIGGER.querySelector(".rune-sort-label").textContent = opt.label;
    SORT_TRIGGER.querySelector(".rune-sort-arrow").textContent = state.sortDir === "desc" ? "▼" : "▲";

    SORT_DIR.classList.toggle("active", true);
    SORT_DIR.classList.remove("asc", "desc");
    SORT_DIR.classList.add(state.sortDir);
    SORT_DIR.querySelector(".rune-sort-dir-icon").textContent = state.sortDir === "desc" ? "↓" : "↑";

    SORT_MENU.querySelectorAll(".rune-sort-option").forEach(function (o) {
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

  // ---------- 渲染卡片 ----------
  function renderCard(r) {
    var req = r.req_lvl ? '需要等级 ' + r.req_lvl : '';

    // 译名行：固定显示 EN / 简 / 繁 三行（按钮已移除）
    var names = '<div class="rune-name-meta">'
      + '<span class="label">EN</span> ' + esc(r.rw_en)
      + ' <span class="label">简</span> ' + esc(r.rw_zh)
      + ' <span class="label">繁</span> ' + esc(r.rw_zh_tw)
      + '</div>';

    // 副标题：2孔 · 剑 / 斧 / 钉锤
    var typeStr = r.itypes.map(function (t) { return esc(t.name); }).join(' / ');
    var subtitle = '<span class="sockets">' + r.sockets + '孔</span>'
      + (typeStr ? ' · <span class="types">' + typeStr + '</span>' : '');

    // 符文图 + 名称
    var runes = r.runes.map(function (x) {
      return '<div class="rune-slot">'
        + runeImg(x)
        + '<span class="rune-slot-name">' + esc(x.zh) + '</span>'
        + '<span class="rune-slot-meta">' + esc(x.en) + ' ' + runeNumber(x.code) + '#</span>'
        + '</div>';
    }).join('');

    // 属性（命中搜索词的那一行高亮，便于一眼定位）
    var q = (state.query || '').trim().toLowerCase();
    var props = r.props.map(function (x) {
      var text = x.text || "";
      var hit = q && text.toLowerCase().indexOf(q) !== -1;
      return '<li' + (hit ? ' class="rune-prop-hl"' : '') + '>'
        + colorizeProp(text, "range") + '</li>';
    }).join('');

    // 符文共鸣占位（内容未来补充）
    var reson = '<div class="rune-reson">'
      + '<h4 class="rune-reson-title">「符文共鸣」待实装</h4>'
      + '<p class="rune-reson-body"></p>'
      + '</div>';

    return '<article class="rune-card">'
      + '<div class="rune-card-head">'
      + '<div class="rune-name-wrap">'
      + '<h3 class="rune-name">' + esc(r.rw_zh) + '</h3>'
      + names
      + '</div>'
      + (req ? '<span class="rune-req">需要等级 <strong>' + r.req_lvl + '</strong></span>' : '')
      + '</div>'
      + '<p class="rune-subtitle">' + subtitle + '</p>'
      + '<div class="rune-combo">' + runes + '</div>'
      + '<hr class="base-divider" />'
      + (props ? '<ul class="rune-props">' + props + '</ul>' : '')
      + (props ? '<hr class="base-divider base-divider--dashed rune-reson-divider" />' : '')
      + reson
      + '</article>';
  }

  // 暴露渲染函数：供 BD 构建页等第三方调用
  window.__runeCardRender = renderCard;

  function render() {
    var list = getFiltered();
    GRID.innerHTML = list.map(renderCard).join("");
    COUNT.innerHTML = "共计 <strong>" + list.length + "</strong> 条数据";
    EMPTY.hidden = list.length !== 0;

    // 按搜索词临时排序按钮：搜索词非空即显示（入口）；点击后才激活排序（高亮）
    if (PROP_SORT_BTN) {
      var hasQuery = !!state.query && state.query.trim().length > 0;
      PROP_SORT_BTN.hidden = !hasQuery;
      if (hasQuery) {
        var active = state.propSortQuery === state.query;
        PROP_SORT_BTN.classList.toggle("active", active);
        PROP_SORT_BTN.setAttribute("aria-pressed", String(active));
        PROP_SORT_BTN.querySelector(".rune-propsort-label").textContent = "按【" + state.query.trim() + "】排序";
        PROP_SORT_BTN.querySelector(".rune-propsort-dir").textContent = state.propSortDir === "asc" ? "↑" : "↓";
      }
    }
  }

  // ---------- 事件绑定 ----------
  function bind() {
    if (SEARCH) {
      SEARCH.addEventListener("input", function () {
        state.query = this.value;
        state.propSortQuery = "";   // 新搜索重置按属性排序
        render();
      });
    }

    if (FILTER_TOGGLE && FILTER_PANEL) {
      FILTER_TOGGLE.addEventListener("click", function () {
        state.filtersOpen = !state.filtersOpen;
        updateFilterPanel();
      });
      updateFilterPanel();
    }

    if (CATEGORY_FILTER) {
      CATEGORY_FILTER.addEventListener("click", function (e) {
        var btn = e.target.closest('[data-cat]');
        if (!btn) return;
        state.category = btn.getAttribute('data-cat');
        if (state.category !== 'weapon' && state.category !== 'all') {
          state.subtype = null; // 非武器主分类时清除子类
        }
        renderFilters();
        render();
      });
    }

    if (SUBTYPE_FILTER) {
      SUBTYPE_FILTER.addEventListener("click", function (e) {
        var btn = e.target.closest('[data-sub]');
        if (!btn) return;
        var key = btn.getAttribute('data-sub');
        state.subtype = state.subtype === key ? null : key;
        if (state.subtype) state.category = 'weapon';
        renderFilters();
        render();
      });
    }

    if (SOCKET_FILTER) {
      SOCKET_FILTER.addEventListener("click", function (e) {
        var btn = e.target.closest('[data-sock]');
        if (!btn) return;
        var v = btn.getAttribute('data-sock');
        state.socket = v === '' ? null : parseInt(v, 10);
        renderFilters();
        render();
      });
    }

    if (SORT_DIR) {
      SORT_DIR.addEventListener("click", function () {
        state.sortDir = state.sortDir === "desc" ? "asc" : "desc";
        updateSortUI();
        render();
      });
    }

    if (SORT_TRIGGER && SORT_MENU) {
      SORT_TRIGGER.addEventListener("click", function (e) {
        e.stopPropagation();
        setSortMenu(SORT_MENU.hidden);
      });
      SORT_MENU.addEventListener("click", function (e) {
        var opt = e.target.closest(".rune-sort-option");
        if (!opt) return;
        var key = opt.getAttribute("data-key");
        var dir = opt.getAttribute("data-dir") || "asc";
        state.sortKey = key;
        state.sortDir = dir;
        state.propSortQuery = "";   // 选需要等级即取消按属性排序
        setSortMenu(false);
        updateSortUI();
        render();
      });
      // 点击页面其它区域关闭菜单
      document.addEventListener("click", function (e) {
        if (SORT_CONTROL && !SORT_CONTROL.contains(e.target)) setSortMenu(false);
      });
    }

    // 按当前搜索词临时排序按钮
    if (PROP_SORT_BTN) {
      PROP_SORT_BTN.addEventListener("click", function () {
        if (!state.query) return;
        if (state.propSortQuery !== state.query) {
          state.propSortQuery = state.query;   // 首次启用，默认降序
          state.propSortDir = "desc";
        } else {
          state.propSortDir = state.propSortDir === "desc" ? "asc" : "desc";  // 再次点击切换方向
        }
        render();
      });
    }
  }

  // ---------- 初始化 ----------
  // 页面守卫：仅当本页网格存在时才执行初始化（BD 构建页等加载本文件仅用渲染函数）
  if (document.getElementById("runeGrid")) {
    buildSortMenu();
    updateSortUI();
    renderFilters();
    bind();
    render();
  }
})();
