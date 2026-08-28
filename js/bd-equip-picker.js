// BD 构建页：装备选择器（暗金/套装/符文之语，复用现有数据）
// 数据源：window.UNIQUE_ITEMS / window.SET_ITEMS.parts / window.RUNEWORDS / window.BASE_ITEMS / window.WEAPON_ITEMS
// 支持全部装备栏：weapon/helmet/armor/shield/gloves/belt/boots/amulet/ring
(function () {
  "use strict";

  // ---------- 基底装备图片工具 ----------
  function allBases() {
    return [].concat(window.BASE_ITEMS || [], window.WEAPON_ITEMS || []);
  }
  // 'assets/equipment/cap_hat.webp' -> 'cap_hat'（picker 缩略图拼接用文件名）
  function normImg(src) {
    if (!src) return "";
    var m = String(src).match(/([\w\-]+)\.webp\s*$/);
    return m ? m[1] : String(src);
  }
  // 按底材 code 查图（套装部件在套装页即用此底材图）
  function baseImgByCode(code) {
    var arr = allBases();
    for (var i = 0; i < arr.length; i++) {
      if (arr[i] && arr[i].code === code) return normImg(arr[i].img);
    }
    return "";
  }
  // Fisher-Yates 洗牌（首次打开选择器时为符文分配底材图，之后固定）
  function shuffle(arr) {
    var a = arr.slice(), i = a.length;
    while (i) {
      var j = Math.floor(Math.random() * i--);
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  // 符文缩略图固定分配缓存（每部位随机一次后不再变化）
  var rwImgCache = {};

  // ---------- 部位配置 ----------
  // base8：基底装备 8 类（非这 8 类的 category 一律归武器）
  var BASE_CAT8 = { "头盔":1, "铠甲":1, "盾牌":1, "手套":1, "腰带":1, "靴子":1, "项链":1, "戒指":1 };
  var BASE_CAT2SLOT = { "头盔":"helmet", "铠甲":"armor", "盾牌":"shield", "手套":"gloves", "腰带":"belt", "靴子":"boots", "项链":"amulet", "戒指":"ring" };
  // 符文 itypes code：非部位类（武器/头/衣/盾）的为武器类（head 死灵盾/ashd 圣骑盾不算武器）
  var RW_WEAPON_CODES = ["axe","scep","hamm","club","mace","miss","weap","h2h","swor","pole","mele","pala","staf","spea","knif","wand","grim"];
  // 泛化武器类（任意武器/远程/近战/圣骑专用）：不归具体子类按钮，仅"全部"可见
  var RW_GENERIC = { miss: 1, weap: 1, mele: 1, pala: 1 };

  // ---------- 武器子类（与暗金装备页同款：type code → 大类中文 + 展示顺序） ----------
  var TYPE_ZH = {
    axe: "斧", swor: "剑", hamm: "锤", mace: "钉锤", club: "棍棒", knif: "匕首",
    spea: "矛", pole: "长柄武器", scep: "权杖", wand: "魔杖", staf: "法杖",
    h2h: "拳套（爪）", h2h2: "拳套（爪）", grim: "魔典", taxe: "投掷斧", tkni: "投掷刀",
    bow: "弓", abow: "长弓", xbow: "弩", jave: "标枪", ajav: "标枪", aspe: "矛", orb: "法球"
  };
  var TYPE_ORDER = ["axe","swor","hamm","mace","club","knif","spea","pole","scep","wand","staf","h2h2","grim","taxe","tkni","bow","abow","xbow","jave","ajav","aspe","orb"];
  // 从当前武器数据生成子类按钮（按 subtype_zh 去重，排序同暗金页）
  function weaponSubtypes(data) {
    var map = {};
    data.forEach(function (it) {
      var t = it.type, zh = it.subtype_zh;
      if (!t || !zh) return;
      if (!map[zh]) {
        var oi = TYPE_ORDER.indexOf(t);
        map[zh] = { zh: zh, oi: oi < 0 ? 900 : oi };
      }
    });
    return Object.keys(map).map(function (k) { return map[k]; })
      .sort(function (a, b) { return a.oi - b.oi || a.zh.localeCompare(b.zh, "zh-CN"); })
      .map(function (x) { return x.zh; });
  }

  var SLOTS = {
    weapon: {
      label: "武器",
      unique: function (u) { return u.cat === "weapon"; },
      rwCodes: RW_WEAPON_CODES
    },
    helmet: {
      label: "头部",
      unique: function (u) { return u.cat === "helm"; },
      rwCodes: ["helm"]
    },
    armor: {
      label: "护甲",
      unique: function (u) { return u.cat === "armor"; },
      rwCodes: ["tors"]
    },
    shield: {
      label: "盾牌",
      unique: function (u) { return u.cat === "shield"; },
      rwCodes: ["shld"]
    },
    gloves: {
      label: "手套",
      unique: function (u) { return u.cat === "glove"; },
      rwCodes: []            // D2 符文之语不支持手套
    },
    belt: {
      label: "腰带",
      unique: function (u) { return u.cat === "belt"; },
      rwCodes: []            // 不支持腰带
    },
    boots: {
      label: "靴子",
      unique: function (u) { return u.cat === "boot"; },
      rwCodes: []            // 不支持靴子
    },
    amulet: {
      label: "项链",
      unique: function (u) { return u.cat === "jewelry" && /项链/.test(u.cat_zh || ""); },
      rwCodes: []            // 不支持项链
    },
    ring: {
      label: "戒指",
      unique: function (u) { return u.cat === "jewelry" && u.cat_zh === "戒指"; },
      rwCodes: []            // 不支持戒指
    },
    charm: {
      label: "护符",
      unique: function (u) { return u.cat === "charm"; },
      rwCodes: []            // 不支持符文之语
    }
  };

  // 套装部件 → 部位（经底材 category 反查，命中 base 8 类则对应部位，否则归武器）
  function slotOfBaseCat(cat) {
    if (BASE_CAT8[cat]) return BASE_CAT2SLOT[cat];
    return "weapon";
  }
  // 某部位可用的基底图（符文缩略图随机池：武器用全部武器底材图，其余用对应 base 8 类图）
  function slotBaseImgs(slotKey) {
    var out = [];
    allBases().forEach(function (b) {
      if (!b || !b.img) return;
      if (slotKey === "weapon") {
        if (!BASE_CAT8[b.category]) {
          var n = normImg(b.img);
          if (n && out.indexOf(n) === -1) out.push(n);
        }
      } else if (BASE_CAT2SLOT[b.category] === slotKey) {
        var n2 = normImg(b.img);
        if (n2 && out.indexOf(n2) === -1) out.push(n2);
      }
    });
    return out;
  }

  // ---------- 按部位统一提取（暗金/套装/符文） ----------
  function collectBySlot(slotKey) {
    var cfg = SLOTS[slotKey] || SLOTS.helmet;
    var out = [];

    // 暗金
    (window.UNIQUE_ITEMS || []).forEach(function (u) {
      if (!cfg.unique(u)) return;
      out.push({
        kind: "unique",
        _raw: u,
        name: u.name_zh || u.name_en,
        name_en: u.name_en,
        name_zh_tw: u.name_zh_tw || "",
        base: u.base_zh || u.base_en || "",
        img: u.img || baseImgByCode(u.code),   // img 缺失（mod 新增无美术映射）时回退底材图
        tier: u.tier_zh || "",
        cat_zh: u.cat_zh || "",
        req_lvl: u.req_lvl || "",
        qlvl: u.qlvl || "",
        props: u.props || [],
        type: u.type || "",
        subtype_zh: u.subtype_zh || u.type || ""
      });
    });

    // 传奇&混沌（字段同暗金，含 legend 标记；品质筛选归「传奇」按钮）
    (window.LEGEND_ITEMS || []).forEach(function (u) {
      if (!cfg.unique(u)) return;
      out.push({
        kind: "legend",
        _raw: u,
        name: u.name_zh || u.name_en,
        name_en: u.name_en,
        name_zh_tw: u.name_zh_tw || "",
        base: u.base_zh || u.base_en || "",
        img: u.img || baseImgByCode(u.code),
        tier: u.tier_zh || "",
        cat_zh: u.cat_zh || "",
        req_lvl: u.req_lvl || "",
        qlvl: u.qlvl || "",
        props: u.props || [],
        type: u.type || "",
        subtype_zh: u.subtype_zh || u.type || ""
      });
    });

    // 套装（经底材 category 归属部位）
    ((window.SET_ITEMS || {}).parts || []).forEach(function (p) {
      if (!p.item_code) return;
      var b = null;
      var arr = allBases();
      for (var i = 0; i < arr.length; i++) {
        if (arr[i] && arr[i].code === p.item_code) { b = arr[i]; break; }
      }
      if (slotOfBaseCat(b && b.category) !== slotKey) return;
      out.push({
        kind: "set",
        _raw: p,
        name: p.part_zh || p.part_en,
        name_en: p.part_en,
        base: p.item_name_en || "",
        img: b ? normImg(b.img) : "",
        setName: p.set_zh || p.set_en,
        set_zh: p.set_zh || "",
        rarity: p.rarity || "",
        lvl: p.lvl || "",
        lvl_req: p.lvl_req || "",
        self_props: p.self_props || [],
        aprop_props: p.aprop_props || {},
        // 武器子类：底材 type_raw → 大类中文（与暗金页 TYPE_ZH 一致）
        type: b ? (b.type_raw || "") : "",
        subtype_zh: b ? (TYPE_ZH[b.type_raw] || b.category || "") : (p.item_type_zh || "")
      });
    });

    // 符文之语（itypes code 匹配；缩略图随机分配该部位基底图，分配一次后固定）
    var rwList = [];
    (window.RUNEWORDS || []).forEach(function (r) {
      var its = r.itypes || [];
      var hit = its.some(function (x) { return cfg.rwCodes.indexOf(x && x.code) !== -1; });
      if (hit) rwList.push(r);
    });
    var pool = slotBaseImgs(slotKey);
    if (!rwImgCache[slotKey] || rwImgCache[slotKey].length < rwList.length) rwImgCache[slotKey] = shuffle(pool);
    rwList.forEach(function (r, idx) {
      var pool2 = rwImgCache[slotKey];
      // 武器子类：跳过泛化类（miss/weap/mele/pala），取第一个具体武器类 itype → 大类中文；无具体类则归空（仅"全部"可见）
      var firstCode = "", firstName = "";
      (r.itypes || []).some(function (x) {
        if (x && RW_WEAPON_CODES.indexOf(x.code) !== -1 && !RW_GENERIC[x.code]) {
          firstCode = x.code; firstName = x.name || ""; return true;
        }
        return false;
      });
      out.push({
        kind: "rune",
        _raw: r,
        name: r.rw_zh || r.rw_en,
        name_en: r.rw_en,
        base: (r.itypes || []).map(function (x) { return (x && x.name) || ""; }).join(" / "),
        img: pool2.length ? pool2[idx % pool2.length] : "",
        runes: (r.runes || []).map(function (x) { return (x && x.zh) || ""; }).join(" + "),
        req_lvl: r.req_lvl || "",
        sockets: r.sockets || "",
        props: r.props || [],
        type: firstCode,
        subtype_zh: firstCode ? (TYPE_ZH[firstCode] || firstName) : ""   // 泛化符文不归子类
      });
    });

    return out;
  }

  // ---------- 渲染：模态弹窗 ----------
  var modal = null;
  var state = { kind: "all", query: "" };

  function open(slotKey, onSelect) {
    var cfg = SLOTS[slotKey] || SLOTS.helmet;
    var data = collectBySlot(slotKey);
    ensureModal();
    document.body.classList.add("bd-modal-open");   // 弹窗打开时隐藏常驻符文叠加层（避免透过遮罩造成视觉遮挡）
    document.getElementById("bdPickerTitle").textContent = "选择装备：" + cfg.label;
    state = { kind: "all", query: "", subtype: null };
    modal._data = data;
    modal._onSelect = onSelect;
    renderSubBar(slotKey, data);
    renderList();
    modal.style.display = "flex";
    var search = document.getElementById("bdPickerSearch");
    if (search) { search.value = ""; search.focus(); }
  }

  function close() {
    if (modal) modal.style.display = "none";
    document.body.classList.remove("bd-modal-open");   // 关闭弹窗时恢复符文叠加层显示
  }

  function ensureModal() {
    if (modal) return;
    modal = document.createElement("div");
    modal.id = "bdEquipPicker";
    modal.className = "bd-modal";
    modal.innerHTML =
      '<div class="bd-modal-card" role="dialog" aria-label="选择装备">' +
        '<header class="bd-modal-head">' +
          '<h3 class="bd-modal-title" id="bdPickerTitle">选择装备</h3>' +
          '<button type="button" class="bd-modal-close" id="bdPickerClose" aria-label="关闭">×</button>' +
        '</header>' +
        '<div class="bd-modal-body">' +
          '<div class="bd-picker-search-row">' +
            '<span class="bd-picker-search-icon" aria-hidden="true">⌕</span>' +
            '<input type="search" id="bdPickerSearch" placeholder="搜索名称、底材…" autocomplete="off" />' +
          '</div>' +
          '<div class="bd-picker-bar" id="bdPickerBar">' +
            '<span class="bd-picker-bar-label">品质</span>' +
            '<button type="button" class="bd-picker-chip active" data-kind="all">全部</button>' +
            '<button type="button" class="bd-picker-chip" data-kind="unique">暗金</button>' +
            '<button type="button" class="bd-picker-chip" data-kind="set">套装</button>' +
            '<button type="button" class="bd-picker-chip" data-kind="rune">符文之语</button>' +
            '<button type="button" class="bd-picker-chip" data-kind="legend">传奇</button>' +
          '</div>' +
          '<div class="bd-picker-bar bd-picker-bar--sub" id="bdPickerSubBar" hidden></div>' +
          '<p class="bd-picker-count" id="bdPickerCount" aria-live="polite"></p>' +
          '<div class="bd-picker-grid" id="bdPickerGrid"></div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    document.getElementById("bdPickerClose").addEventListener("click", close);
    modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
    var search = document.getElementById("bdPickerSearch");
    search.addEventListener("input", function () {
      state.query = this.value || "";
      renderList();
    });
    document.getElementById("bdPickerBar").addEventListener("click", function (e) {
      var btn = e.target.closest(".bd-picker-chip");
      if (!btn) return;
      Array.prototype.forEach.call(this.querySelectorAll(".bd-picker-chip"), function (b) {
        b.classList.toggle("active", b === btn);
      });
      state.kind = btn.getAttribute("data-kind") || "all";
      renderList();
    });
    // 武器类型筛选行（仅武器槽位显示）
    document.getElementById("bdPickerSubBar").addEventListener("click", function (e) {
      var btn = e.target.closest(".bd-picker-chip--sub");
      if (!btn) return;
      var s = btn.getAttribute("data-subtype");
      state.subtype = state.subtype === s ? null : s;   // 再次点击取消
      Array.prototype.forEach.call(this.querySelectorAll(".bd-picker-chip--sub"), function (b) {
        b.classList.toggle("active", b.getAttribute("data-subtype") === state.subtype);
      });
      renderList();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal.style.display === "flex") close();
    });
  }

  // 武器类型筛选行：仅武器槽位渲染（排序与暗金页一致；「拳套（爪）」前强制换行）
  function renderSubBar(slotKey, data) {
    var bar = document.getElementById("bdPickerSubBar");
    if (!bar) return;
    if (slotKey !== "weapon") { bar.hidden = true; bar.innerHTML = ""; return; }
    var list = weaponSubtypes(data);
    bar.hidden = list.length === 0;
    bar.innerHTML = '<span class="bd-picker-bar-label">类型</span>' + list.map(function (s) {
      var br = s === "拳套（爪）" ? '<span class="bd-picker-break"></span>' : "";
      var active = state.subtype === s ? " active" : "";
      return br + '<button type="button" class="bd-picker-chip bd-picker-chip--sub' + active + '" data-subtype="' + esc(s) + '">' + esc(s) + '</button>';
    }).join("");
  }

  function filter() {
    var q = (state.query || "").toLowerCase().trim();
    return (modal._data || []).filter(function (it) {
      if (state.kind !== "all" && it.kind !== state.kind) return false;
      if (state.subtype && (it.subtype_zh || "") !== state.subtype) return false;
      if (q) {
        var hay = (it.name + " " + (it.name_en || "") + " " + (it.base || "") + " " + (it.setName || "") + " " + (it.runes || "")).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return ({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" })[c];
    });
  }

  function renderList() {
    var list = filter();
    var grid = document.getElementById("bdPickerGrid");
    var count = document.getElementById("bdPickerCount");
    count.textContent = "共 " + list.length + " 件";
    if (!list.length) {
      grid.innerHTML = '<p class="bd-picker-empty">没有匹配的装备，试试调整筛选条件。</p>';
      return;
    }
    grid.innerHTML = list.map(function (it) {
      var imgHtml = it.img
        ? '<img class="bd-picker-thumb" src="assets/equipment/' + esc(it.img) + '.webp" alt="' + esc(it.name) + '" loading="lazy" decoding="async" onerror="this.outerHTML=\'<div class=&quot;bd-picker-thumb-ph&quot;>无图</div>\';" />'
        : '<div class="bd-picker-thumb-ph">无图</div>';
      var sub = it.kind === "set"
        ? it.setName + "（套装）"
        : it.kind === "rune"
          ? (it.runes || "符文之语") + " · Lv" + (it.req_lvl || "?")
          : (it.base || "") + (it.tier ? " · " + it.tier : "");
      return '<button type="button" class="bd-picker-card bd-picker-card--' + it.kind + '" data-idx="' + (modal._data.indexOf(it)) + '">' +
        imgHtml +
        '<span class="bd-picker-name">' + esc(it.name) + '</span>' +
        '<span class="bd-picker-base">' + esc(sub) + '</span>' +
      '</button>';
    }).join("");
    grid.querySelectorAll(".bd-picker-card").forEach(function (card) {
      var idx = parseInt(card.getAttribute("data-idx"), 10);
      card.addEventListener("click", function () {
        var it = modal._data[idx];
        if (!it) return;
        if (typeof modal._onSelect === "function") modal._onSelect(it);
        close();
      });
      // hover 预览：鼠标放到卡片上时显示该装备的属性卡片（复用 BD 构建页 tooltip）
      card.addEventListener("mouseenter", function () {
        var it = modal._data[idx];
        if (it && window.__bdTooltip) window.__bdTooltip.show(card, it);
      });
      card.addEventListener("mouseleave", function () {
        if (window.__bdTooltip) window.__bdTooltip.hide();
      });
    });
  }

  // 暴露 API
  window.bdEquipPicker = { open: open, close: close };
})();
