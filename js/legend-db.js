// 传奇&混沌装备页面：搜索 + 分类/子类筛选 + 排序 + 译名对照 + 卡片网格
(function () {
  "use strict";

  var DATA = window.LEGEND_ITEMS || [];

  // ---------- 分类定义（基于 item.cat 精确匹配） ----------
  var CATEGORIES = [
    { key: 'all',     label: '全部' },
    { key: 'weapon',  label: '武器' },
    { key: 'shield',  label: '盾牌' },
    { key: 'helm',    label: '头盔' },
    { key: 'armor',   label: '衣服' },
    { key: 'glove',   label: '手套' },
    { key: 'boot',    label: '鞋子' },
    { key: 'belt',    label: '腰带' },
    { key: 'ring',    label: '戒指' },
    { key: 'amulet',  label: '项链' },
    { key: 'jewel',   label: '珠宝' },
    { key: 'charm',   label: '护符' },
    { key: 'ammo',     label: '箭袋' }
  ];

  // 武器子类：从数据动态生成，按中文标签 subtype_zh 去重（同一类武器的不同品质档共享中文名，如 弓/标枪），
  //            筛选时按 subtype_zh 匹配，点击即命中该类全部品质档
  var SUBTYPES = (function () {
    var order = ['axe','swor','hamm','mace','club','knif','spea','pole','scep','wand','staf','h2h2','grim','taxe','tkni','bow','abow','xbow','jave','ajav','aspe','orb'];
    var map = {};  // label -> { label, orderIdx }
    DATA.forEach(function (r) {
      if (r.cat === 'weapon' && r.type) {
        var label = r.subtype_zh || r.type;
        if (!Object.prototype.hasOwnProperty.call(map, label)) {
          var oi = order.indexOf(r.type);
          map[label] = { label: label, orderIdx: oi < 0 ? 900 : oi };
        }
      }
    });
    var arr = Object.keys(map).map(function (k) { return map[k]; });
    arr.sort(function (a, b) {
      return a.orderIdx - b.orderIdx || a.label.localeCompare(b.label, 'zh-CN');
    });
    return arr.map(function (x) { return { key: x.label, label: x.label }; });
  })();

  // ---------- 排序选项（与基底装备页一致：默认(编号) / 名称 / 需要等级 / 品质等级） ----------
  var SORTS = [
    { key: 'default', label: '默认（编号）', dir: 'asc' },
    { key: 'name',    label: '名称',         dir: 'asc' },
    { key: 'req_lvl', label: '需要等级', dir: 'asc', num: true, field: 'req_lvl' },
    { key: 'qlvl',    label: '品质等级', dir: 'asc', num: true, field: 'qlvl' }
  ];
  function findSort(key) {
    for (var i = 0; i < SORTS.length; i++) if (SORTS[i].key === key) return SORTS[i];
    return SORTS[0];
  }
  function num(v) { var n = parseInt(v, 10); return isNaN(n) ? 0 : n; }

  // ---------- DOM ----------
  var SEARCH = document.getElementById("uniqueSearch");
  var FILTER_TOGGLE = document.getElementById("uniqueFilterToggle");
  var FILTER_PANEL = document.getElementById("uniqueFilterPanel");
  var CATEGORY_FILTER = document.getElementById("uniqueCategoryFilter");
  var SUBTYPE_FILTER = document.getElementById("uniqueSubtypeFilter");
  var TIER_FILTER = document.getElementById("uniqueTier");
  var SORT_CONTROL = document.getElementById("uniqueSortControl");
  var SORT_DIR = document.getElementById("uniqueSortDir");
  var SORT_TRIGGER = document.getElementById("uniqueSortTrigger");
  var SORT_MENU = document.getElementById("uniqueSortMenu");
  var PROP_SORT_BTN = document.getElementById("uniquePropSortBtn");
  var GRID = document.getElementById("uniqueGrid");
  var COUNT = document.getElementById("uniqueListCount");
  var EMPTY = document.getElementById("uniqueListEmpty");

  // ---------- 状态 ----------
  var state = {
    query: "",
    category: "all",
    subtype: null,
    tier: "",               // 级别筛选：普通 / 扩展 / 精英 / 任务（空=全部）
    sponsoredOnly: false,    // 仅显示「冠名赞助」装备
    sortKey: "default",      // 默认（编号）：保持数据原始顺序
    sortDir: "asc",
    showNames: true,          // 译名对照固定显示 EN/简/繁
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

  // 属性文本着色：range 模式——仅「数字 - 数字」才是范围(金色)，前导负号是普通负数(蓝色)
  function colorizeProp(text, mode) {
    if (!text) return '';
    var plain = mode === "plain";
    var parts = text.split(/([+-]?\d+(?:\s*-\s*[+-]?\d+)?%?)/);
    return parts.map(function (part) {
      if (/^[+-]?\d+(?:\s*-\s*[+-]?\d+)?%?$/.test(part)) {
        var isRange = /^\d+\s*-\s*[+-]?\d+%?$/.test(part);
        if (plain || !isRange) {
          return '<span class="prop-text">' + esc(part) + '</span>';
        }
        return '<span class="prop-num">' + esc(part) + '</span>';
      }
      return '<span class="prop-text">' + esc(part) + '</span>';
    }).join('');
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

  // ---------- 渲染筛选按钮 ----------
  function renderFilters() {
    CATEGORY_FILTER.innerHTML = CATEGORIES.map(function (c) {
      var active = state.category === c.key ? ' active' : '';
      return '<button type="button" class="unique-chip-btn' + active + '" data-cat="' + c.key + '">'
        + esc(c.label) + '</button>';
    }).join('')
    // 冠名赞助：单一开关按钮，置于「箭袋」右侧，点击仅显示含「冠名赞助」区块的装备
    + '<button type="button" class="unique-chip-btn unique-chip-sponsor'
      + (state.sponsoredOnly ? ' active' : '') + '" data-sponsored="1">冠名赞助</button>';

    // 武器子类：仅在武器/全部主类下显示；非武器主类时整行隐藏并清空高亮残留
    var showSub = state.category === 'weapon' || state.category === 'all';
    SUBTYPE_FILTER.hidden = !showSub || SUBTYPES.length === 0;
    SUBTYPE_FILTER.innerHTML = SUBTYPES.map(function (s) {
      var active = state.subtype === s.key ? ' active' : '';
      // 在「拳套（爪）」处强制换行：其前插入占满整行的 break 元素，武器子类两行显示
      var br = s.key === '拳套（爪）' ? '<span class="unique-sub-break"></span>' : '';
      return br + '<button type="button" class="unique-chip-btn' + active + '" data-sub="' + s.key + '">'
        + esc(s.label) + '</button>';
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
      r.name_zh, r.name_en, r.name_zh_tw,
      r.base_zh, r.base_en,
      r.cat_zh, r.type, r.subtype_zh,
      r.props.map(function (p) { return p.text; }).join(' ')
    ].join(' ').toLowerCase();
    return hay.indexOf(q) !== -1;
  }

  function getFiltered() {
    var q = state.query.toLowerCase();
    var list = DATA.filter(function (r) {
      if (!matchesQuery(r, q)) return false;

      // 主分类
      if (state.category === 'ring') {
        // 戒指：按中文分类精确匹配
        if (r.cat_zh !== '戒指') return false;
      } else if (state.category === 'amulet') {
        // 项链：按中文分类匹配（含毒蛇项链等同子类）
        if (!/项链/.test(r.cat_zh || '')) return false;
      } else if (state.category === 'jewel') {
        // 珠宝：保卫者/守卫者/守护者 系列碎片与彩虹刻面等，按中文分类精确匹配
        if (r.cat_zh !== '珠宝') return false;
      } else if (state.category !== 'all' && r.cat !== state.category) {
        return false;
      }

      // 武器子类（按中文标签 subtype_zh 匹配，命中同类的全部品质档）
      if (state.subtype && (r.subtype_zh || r.type) !== state.subtype) return false;

      // 级别（普通/扩展/精英/任务），按 tier_zh 精确匹配
      if (state.tier && (r.tier_zh || "") !== state.tier) return false;

      // 仅显示「冠名赞助」装备
      if (state.sponsoredOnly && !r.sponsored) return false;

      return true;
    });

    // 排序：若按当前搜索词临时排序则按属性数值，否则按所选排序字段
    if (state.propSortQuery) {
      var pdir = state.propSortDir === "asc" ? 1 : -1;
      list.sort(function (a, b) {
        var va = extractPropNum(a, state.propSortQuery);
        var vb = extractPropNum(b, state.propSortQuery);
        if (isNaN(va) && isNaN(vb)) return 0;
        if (isNaN(va)) return 1;
        if (isNaN(vb)) return -1;
        return (va - vb) * pdir || a.name_zh.localeCompare(b.name_zh, "zh-CN");
      });
    } else {
      var opt = findSort(state.sortKey);
      var dir = state.sortDir === "desc" ? -1 : 1;
      if (!opt || opt.key === "default") {
        // 默认（编号）：保持数据原始顺序，不排序
      } else if (opt.key === "name") {
        list.sort(function (a, b) {
          return a.name_zh.localeCompare(b.name_zh, "zh-CN") * dir;
        });
      } else if (opt.num) {
        list.sort(function (a, b) {
          return (num(a[opt.field]) - num(b[opt.field])) * dir
            || a.name_zh.localeCompare(b.name_zh, "zh-CN");
        });
      }
    }

    return list;
  }

  // ---------- 排序按钮 UI（分体：左箭头逆序 / 右下拉选需要等级/品质等级） ----------
  function buildSortMenu() {
    if (!SORT_MENU) return;
    SORT_MENU.innerHTML = SORTS.map(function (o) {
      return '<button type="button" class="unique-sort-option" role="menuitem" data-key="' + o.key + '" data-dir="' + o.dir + '">'
        + esc(o.label) + '</button>';
    }).join("");
  }

  function updateSortUI() {
    if (!SORT_TRIGGER || !SORT_DIR || !SORT_MENU) return;
    var opt = findSort(state.sortKey);
    var isDefault = state.sortKey === "default";
    // 与基底装备页一致：默认（编号）时按钮文案显示「排序」，选中具体项时显示该项名称
    SORT_TRIGGER.querySelector(".unique-sort-label").textContent = isDefault ? "排序" : (opt ? opt.label : "排序");
    SORT_TRIGGER.querySelector(".unique-sort-arrow").textContent = isDefault ? "▼" : (state.sortDir === "desc" ? "▼" : "▲");

    SORT_DIR.classList.toggle("active", true);
    SORT_DIR.classList.remove("asc", "desc");
    SORT_DIR.classList.add(state.sortDir);
    SORT_DIR.querySelector(".unique-sort-dir-icon").textContent = state.sortDir === "desc" ? "↓" : "↑";

    SORT_MENU.querySelectorAll(".unique-sort-option").forEach(function (o) {
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

  // ---------- 混沌专属分区（混沌词条 T1-T5 / 固定词条 / 随机词条 / 获取方式） ----------
  function renderChaosAffix(r) {
    var a = r.chaos_affix;
    if (!a) return '';
    // 整个混沌词条块做成可折叠内部小卡片，默认折叠
    var html = '<details class="unique-chaos">';

    // 混沌词条（具名 T1-T5）：emph 首条或 name 上提至标题行，与【混沌词条】同一行显示（空 2 格、加粗）
    var emphText = '';
    var tiers = a.tiers || [];
    if (tiers[0] && typeof tiers[0] === 'object' && tiers[0].emph) {
      emphText = tiers[0].text;
      tiers = tiers.slice(1);
    } else if (a.name) {
      emphText = a.name;
    }
    var headRight = emphText ? '<span class="unique-chaos-emph-inline">　「' + esc(emphText) + '」</span>' : '';
    // 折叠卡片标题行（summary）
    html += '<summary class="unique-chaos-summary">';
    html += '<span class="unique-chaos-head unique-chaos-head--plain">混沌词条' + headRight + '</span>';
    html += '<span class="unique-chaos-chevron" aria-hidden="true"></span>';
    html += '</summary>';
    html += '<div class="unique-chaos-body">';
    html += '<div class="unique-chaos-sec">';
    if (tiers && tiers.length) {
      html += '<ul class="unique-chaos-tiers">'
        + tiers.map(function (t) {
            if (t && typeof t === 'object') {
              var label = t.emph ? '「' + esc(t.text) + '」' : esc(t.text);
              return '<li' + (t.emph ? ' class="unique-chaos-tier-emph"' : '') + '>' + label + '</li>';
            }
            return '<li>' + esc(t) + '</li>';
          }).join('') + '</ul>';
    } else {
      html += '<div class="unique-chaos-note">混沌词条 T1~T5 待补充</div>';
    }
    html += '</div>';

    // 固定词条（升级 / 洗词条配方）
    if (a.fixed && a.fixed.length) {
      html += '<div class="unique-chaos-sec"><div class="unique-chaos-head">固定词条</div>'
        + '<ul class="unique-chaos-list">'
        + a.fixed.map(function (f) { return '<li>' + esc(f) + '</li>'; }).join('') + '</ul></div>';
    }

    // 随机词条（淬炼属性 + 淬炼配方）
    if (a.random) {
      html += '<div class="unique-chaos-sec"><div class="unique-chaos-head">随机词条</div>'
        + '<div class="unique-chaos-note">' + esc(a.random) + '</div></div>';
    }

    html += '</div>';
    html += '</details>';

    // 获取方式（合成配方）：始终显示，不放入折叠卡片（上方分割线，标题紫色）
    if (a.craft) {
      html += '<hr class="unique-chaos-divider" />';
      html += '<div class="unique-chaos-craft">';
      html += '<div class="unique-chaos-sec"><div class="unique-chaos-head craft-head">获取方式</div>'
        + '<div class="unique-chaos-note">' + esc(a.craft) + '</div></div>';
      html += '</div>';
    }
    return html;
  }

  // ---------- 传奇专属分区（传奇词条：可折叠内部小卡片，橙色区别于混沌词条品红） ----------
  function renderLegendAffix(r) {
    var a = r.legend_affix;
    if (!a) return '';
    var headRight = a.name ? '<span class="unique-legend-emph-inline">「' + esc(a.name) + '」</span>' : '';
    var classTag = a.class_zh ? ' <span class="unique-legend-class' + (a.class_color ? ' unique-legend-class--' + esc(a.class_color) : '') + '">&lt; ' + esc(a.class_zh) + ' &gt;</span>' : '';
    var html = '<details class="unique-legend">';
    html += '<summary class="unique-legend-summary">';
    html += '<span class="unique-legend-head">传奇词条' + headRight + classTag + '</span>';
    html += '<span class="unique-legend-chevron" aria-hidden="true"></span>';
    html += '</summary>';
    html += '<div class="unique-legend-body">';
    if (a.desc) {
      html += '<p class="unique-legend-desc">' + esc(a.desc) + '</p>';
    }
    if (a.rows && a.rows.length) {
      html += '<ul class="unique-legend-list">';
      a.rows.forEach(function (row) {
        if (typeof row === 'string') {
          html += '<li>' + esc(row) + '</li>';
        } else {
          html += '<li>' + esc(row.text || '');
          if (row.children && row.children.length) {
            html += '<ul class="unique-legend-sublist">'
              + row.children.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul>';
          }
          html += '</li>';
        }
      });
      html += '</ul>';
    }
    html += '</div>';
    html += '</details>';
    return html;
  }

  // ---------- 渲染卡片（三段式：顶部 名称+图片 / 中间 属性 / 底部 Qlvl） ----------
  function renderCard(r) {
    // 中文名缺失时回退英文，避免标题空白
    var zhs = r.name_zh || r.name_en;

    // 译名行：EN / 简 / 繁 / 底材 四行，首字对齐、统一字号（无【】符号，底材无冒号）
    var names = '<div class="unique-name-meta">'
      + '<span class="nm-line"><span class="label">EN</span>' + esc(r.name_en) + '</span>'
      + '<span class="nm-line"><span class="label">简</span>' + esc(zhs) + '</span>'
      + '<span class="nm-line"><span class="label">繁</span>' + esc(r.name_zh_tw) + '</span>'
      + (r.base_zh ? '<span class="nm-line"><span class="label">底材</span>' + esc(r.base_zh) + '</span>' : '')
      + '</div>';

    // 装备图（传奇美术或底材图；无则占位）—— 顶部右角
    var imgHtml;
    if (r.img) {
      imgHtml = '<img class="unique-thumb" src="assets/equipment/' + esc(r.img) + '.webp" alt="'
        + esc(zhs) + '" loading="lazy" decoding="async" '
        + 'onerror="this.outerHTML=\'<div class=&quot;unique-thumb-ph&quot;>无图</div>\';" />';
    } else {
      imgHtml = '<div class="unique-thumb-ph">无图</div>';
    }

    // 档位 · 分类 标签：复用基底装备页同款 .base-subtitle / .base-tier / .base-cat，保证两端格式统一
    var tierBadge = r.tier_zh
      ? '<span class="base-tier tier-' + esc(r.tier_zh) + '">' + esc(r.tier_zh) + '</span>'
      : '';
    var catBadge = '<span class="base-cat">' + esc(r.cat_zh) + '</span>';
    var dot = tierBadge ? '<span class="base-dot" aria-hidden="true">·</span>' : '';
    // 品质标签：传奇 / 混沌（橙色 / 品红），形成 【档位】·【分类】·【品质】 三段
    var qualityBadge = '';
    if (r.legend) {
      qualityBadge = '<span class="base-dot" aria-hidden="true">·</span><span class="base-tier tier-传奇">传奇</span>';
    } else if (r.chaos) {
      qualityBadge = '<span class="base-dot" aria-hidden="true">·</span><span class="base-tier tier-混沌">混沌</span>';
    }
    var tagline = '<div class="base-subtitle">' + tierBadge + dot + catBadge + qualityBadge + '</div>';
    // 属性（命中搜索词的那一行高亮，便于一眼定位）
    var q = (state.query || '').trim().toLowerCase();
    var isMara = r.name_en === "Mara's Kaleidoscope";
    var props = r.props.map(function (x) {
      var text = x.text || "";
      var hit = q && text.toLowerCase().indexOf(q) !== -1;
      // Mara 的【施法速度】【经验值】为 mod 新增词条：描述用亮淡绿、数字不变
      var isNewProp = isMara && /施法速度|经验值/.test(text);
      var cls = [];
      if (hit) cls.push('unique-prop-hl');
      if (isNewProp) cls.push('unique-prop-new');
      if (x.eu) cls.push('unique-prop-eu');
      if (x.strike) cls.push('unique-prop-strike');
      if (x.green) cls.push('unique-prop-green');
      if (x.lightblue) cls.push('unique-prop-lightblue');
      var clsAttr = cls.length ? ' class="' + cls.join(' ') + '"' : '';
      return '<li' + clsAttr + '>' + colorizeProp(text, "range") + '</li>';
    }).join('');

    // 冠名赞助区块：混沌装备置于【获取方式】之下、需求等级之上；非混沌（传奇）置于【属性】与【需求等级】之间（仅 sponsored 标记的物品渲染）
    var sponsor = '';
    if (r.sponsored && r.sponsor_info) {
      sponsor = '<div class="unique-sponsor">'
        + '<div class="unique-sponsor-title">冠名赞助</div>'
        + '<div class="unique-sponsor-line">「赞助人」：' + esc(r.sponsor_info.sponsor) + '</div>'
        + '<div class="unique-sponsor-line unique-sponsor-desc">“' + esc(r.sponsor_info.desc) + '”</div>'
        + '</div>';
    }

    // 底部：需求等级 + Qlvl，均用黑底徽章（同符文之语风格），整体加粗
    var reqVal = r.req_lvl ? esc(r.req_lvl) : '—';
    var bot = '<div class="unique-card-bot">'
      + '<span class="unique-req">需求等级 <strong>' + reqVal + '</strong></span>'
      + (r.qlvl ? '<span class="unique-req">Qlvl <strong>' + esc(r.qlvl) + '</strong></span>' : '')
      + '</div>';

    return '<article class="unique-card">'
      + '<div class="unique-card-head">'
      + '<div class="unique-name-wrap">'
      + '<h3 class="unique-name' + (r.legend ? ' legend-name' : (r.chaos ? ' chaos-name' : '')) + '">' + esc(zhs) + '</h3>'
      + tagline
      + names
      + '</div>'
      + '<div class="unique-img-wrap' + (r.cat === 'jewelry' ? ' jewel' : '') + (r.img === 'charm_small' || r.img === 'charm_quark' ? ' charm-shrink' : '') + (r.img === 'mephisto_soul_stone' ? ' anni-img' : '') + (r.img === 'torch' ? ' torch-fixed' : '') + '">' + imgHtml + '</div>'
      + '</div>'
      + '<hr class="base-divider' + (r.chaos ? ' base-divider--chaos' : '') + '" />'
      + (props ? '<ul class="unique-props">' + props + '</ul>' : '')
      + (r.chaos ? renderChaosAffix(r) : '') + (r.legend ? renderLegendAffix(r) : '')
      + sponsor
      + bot
      + '</article>';
  }

  // 暴露渲染函数：供 BD 构建页等第三方调用（需与本页或装载页面共用）
  window.__legendCardRender = renderCard;

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
        PROP_SORT_BTN.querySelector(".unique-propsort-label").textContent = "按【" + state.query.trim() + "】排序";
        PROP_SORT_BTN.querySelector(".unique-propsort-dir").textContent = state.propSortDir === "asc" ? "↑" : "↓";
      }
    }
  }

  // ---------- 事件绑定 ----------
  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, ctx = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  function bind() {
    if (SEARCH) {
      var onSearch = debounce(function () { render(); }, 120);
      SEARCH.addEventListener("input", function () {
        state.query = this.value;
        state.propSortQuery = "";   // 新搜索重置按属性排序
        onSearch();
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

    if (TIER_FILTER) {
      TIER_FILTER.addEventListener("change", function () {
        state.tier = this.value;
        render();
      });
    }

    if (CATEGORY_FILTER) {
      // 冠名赞助开关按钮已并入主分类行（箭袋右侧），故监听挂在该行
      CATEGORY_FILTER.addEventListener("click", function (e) {
        var btn = e.target.closest('[data-sponsored]');
        if (!btn) return;
        state.sponsoredOnly = !state.sponsoredOnly;
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
        var opt = e.target.closest(".unique-sort-option");
        if (!opt) return;
        var key = opt.getAttribute("data-key");
        var dir = opt.getAttribute("data-dir") || "asc";
        state.sortKey = key;
        state.sortDir = dir;
        state.propSortQuery = "";   // 选排序字段即取消按属性排序
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
  if (document.getElementById("uniqueGrid")) {
    buildSortMenu();
    updateSortUI();
    renderFilters();
    bind();
    render();
  }
})();
