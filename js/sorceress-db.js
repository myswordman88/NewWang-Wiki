// 职业技能通用渲染页：技能卡片（Tab 筛选 + 搜索 + 展开详情）+ 觉醒区块
// 数据源：window.SKILL_PAGE_DATA（女巫=window.SORCERESS_DATA，亚马逊=window.AMAZON_DATA，其他职业同构）
(function () {
  "use strict";

  var DATA = window.SKILL_PAGE_DATA ||
    window.SORCERESS_DATA || window.AMAZON_DATA || { skills: {}, awakeGroups: [] };

  // ---------- 系别归属兜底（数据中 skills[n].tree 优先） ----------
  var TREE_OF = {};

  // 系别列表：优先数据自带 trees，否则女巫默认
  var TREES = (DATA.trees && DATA.trees.length)
    ? DATA.trees
    : [
        { key: "cold",     label: "冰冷系" },
        { key: "lightning", label: "闪电系" },
        { key: "fire",     label: "火焰系" }
      ];

  var state = { tree: "all", q: "", tag: "" };
  var el = {};

  // ---------- 工具 ----------
  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function num(s) { return '<span class="num">' + esc(s) + "</span>"; }
  function dim(s) { return '<span class="dim">' + esc(s) + "</span>"; }

  // 数字行：含 | 分隔的等级数值序列 → 等宽字体高亮
  function fmtInfoLine(t) {
    if (/\d+\s*\/\s*\d+/.test(t)) {
      return '<div class="sorc-numrow">' + esc(t) + "</div>";
    }
    return esc(t);
  }

  // 标签配色方案（按语义统一调用，详见 css/sorceress.css 的 .sorc-tag.tag--*）
  var TAG_CLASS = {
    "主动": "tag--active",
    "被动": "tag--passive",
    "召唤": "tag--summon",
    "尸体": "tag--corpse",
    "强化": "tag--buff",
    "终极": "tag--ultimate"
  };
  function tagClass(tag) {
    return TAG_CLASS[tag] || "";
  }

  // 筛选按钮中标签的优先排序（其余未知标签按出现顺序追加在后）
  var PREFERRED_TAG_ORDER = [
    "主动", "被动", "召唤", "尸体", "强化", "毒", "骨", "诅咒",
    "终极", "冰冷", "闪电", "火焰", "标枪", "生存", "弓弩", "魔法", "近战", "远程"
  ];

  // ---------- 前置技能解析 ----------
  // 别名：mod 内命名与数据表不一致时映射（如 冰川之枪 = 冰尖柱 Glacial Spike）
  var PRE_ALIAS = { "冰川之枪": "冰尖柱" };
  var PRE_SPLIT = /[\/、,，]+/;   // 多个前置分隔符

  // 按中文名/别名/英文名查找技能数据
  function findSkill(name) {
    name = (name || "").trim();
    if (!name) return null;
    if (DATA.skills[name]) return DATA.skills[name];
    if (PRE_ALIAS[name]) return DATA.skills[PRE_ALIAS[name]] || null;
    var lower = name.toLowerCase();
    var keys = Object.keys(DATA.skills);
    for (var i = 0; i < keys.length; i++) {
      if ((DATA.skills[keys[i]].en || "").toLowerCase() === lower) return DATA.skills[keys[i]];
    }
    return null;
  }

  // 前置技能框（与学习等级框同尺寸：第一行「前置技能」，第二行图标，无名字）
  function renderPrereq(name) {
    var s = findSkill(name);
    var icon = s && s.icon ? '<img src="assets/skills/' + esc(s.icon) + '" alt="' + esc(name) + '" loading="lazy">' : "";
    return '<div class="sorc-prereq">' +
      '<span class="plabel">前置技能</span>' +
      '<div class="picon">' + icon + "</div>" +
    "</div>";
  }

  // ---------- 渲染技能卡片 ----------
  // 可折叠区域块：标题可点击，body 默认展开（open）
  function secBlock(title, bodyHtml, open, extraClass) {
    return '<div class="sorc-sec' + (extraClass ? " " + extraClass : "") + (open ? " open" : "") + '">' +
      '<h5 class="sorc-sec-h">' + esc(title) +
        '<span class="sorc-sec-arrow" aria-hidden="true">▾</span></h5>' +
      '<div class="sorc-sec-body">' + bodyHtml + "</div>" +
    "</div>";
  }

  function renderCard(s) {
    var tree = s.tree || TREE_OF[s.name] || "cold";
    var tags = (s.tags || []).map(function (t) {
      return '<span class="sorc-tag ' + tagClass(t) + '">' + esc(t) + "</span>";
    }).join("");

    // 前置技能框（支持多个）；无前置（空或「无」）则不显示该框
    var prereqHtml = "";
    var hasPrereq = s.prereq && !/^(无|none|null|-|—|－－)?$/i.test(String(s.prereq).trim());
    if (hasPrereq) {
      var rawPre = String(s.prereq).trim();
      // 文字型前置（转职/觉醒门槛，如「一转」「二转」「三转」）：单格纯文字，不拆分、不查图标
      if (/觉醒|[一二三四五六七八九十]转/.test(rawPre)) {
        prereqHtml = '<div class="sorc-prereqs"><div class="sorc-prereq sorc-prereq--text">' +
          '<span class="plabel">前置技能</span>' +
          '<span class="ptext">' + esc(rawPre) + '</span>' +
          '</div></div>';
      } else {
        var preList = rawPre.split(PRE_SPLIT).map(function (x) { return x.trim(); })
          .filter(function (x) { return x && !/^(无|none|null|-|—|－－)?$/i.test(x); });
        if (preList.length) {
          prereqHtml = '<div class="sorc-prereqs">' + preList.map(renderPrereq).join("") + "</div>";
        }
      }
    }
    // 传奇词缀徽章（含传奇词缀的技能在 meta 区最左显示；每个词缀一个独立方框）
    var legBadgeHtml = "";
    if (s.legendary && s.legendary.length) {
      legBadgeHtml = s.legendary.map(function (l) {
        return '<div class="sorc-legbadge">' +
          '<span class="llabel">传奇词缀</span>' +
          '<span class="ln">' + esc(l.name) + "</span>" +
        "</div>";
      }).join("");
    }
    // 学习等级（右上）
    var lvlHtml = s.lvl ? '<span class="sorc-lvl"><span class="l">学习等级</span><span class="v">' + esc(s.lvl) + "</span></span>" : "";
    // 右侧 meta 区：传奇词缀徽章（左）+ 前置框 + 学习等级（右上）
    var meta = (legBadgeHtml || prereqHtml || lvlHtml)
      ? '<div class="sorc-meta">' + legBadgeHtml + prereqHtml + lvlHtml + "</div>"
      : "";

    // 四个区域：可折叠（默认展开），点击标题收起/展开
    var detail = "";

    // ① 技能信息区（含冷却时间 + T 级数据）
    var infoBody = "";
    var infoHtml = "";
    if (s.cd) infoHtml += "<li>冷却时间：" + esc(s.cd) + "</li>";
    if (s.info && s.info.length) {
      infoHtml += s.info.map(function (t) { return "<li>" + fmtInfoLine(t) + "</li>"; }).join("");
    }
    if (!infoHtml) infoHtml = "<li>—</li>";
    infoBody += "<ul>" + infoHtml + "</ul>";
    if (s.tdata && s.tdata.length) {
      infoBody += '<div class="sorc-tdata">' +
        s.tdata.map(function (t) {
          return '<div class="td"><b>T' + t.t + "</b><span>" + esc(t.desc) + "</span></div>";
        }).join("") + "</div>";
    }
    detail += secBlock("技能信息", infoBody, true);

    // ② 属性加成区（原 属性/协同加成）
    var synHtml = (s.synergy && s.synergy.length)
      ? s.synergy.map(function (t) { return "<li>" + fmtInfoLine(t) + "</li>"; }).join("")
      : "<li>—</li>";
    detail += secBlock("属性加成", "<ul>" + synHtml + "</ul>", true);

    // ③ 词缀加成区
    var affHtml = (s.affix && s.affix.length)
      ? s.affix.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("")
      : "<li>—</li>";
    detail += secBlock("词缀加成", "<ul>" + affHtml + "</ul>", true);

    // ④ 传奇词缀区
    if (s.legendary && s.legendary.length) {
      var legHtml = s.legendary.map(function (leg) {
        var tdataHtml = (leg.tdata || []).map(function (t) {
          return '<div class="td"><b>T' + t.t + '</b><span>' + esc(t.desc) + '</span></div>';
        }).join("");
        return '<div class="sorc-leg-card">' +
          '<div class="sorc-leg-card-head">' +
            '<b>' + esc(leg.name) + '</b>' +
            '<span class="sorc-leg-summary">' + esc(leg.summary) + '</span>' +
            '<span class="sorc-arrow">▾</span>' +
          '</div>' +
          '<div class="sorc-leg-card-body">' +
            '<div class="sorc-tdata">' + tdataHtml + '</div>' +
          '</div>' +
        '</div>';
      }).join("");
      detail += secBlock("传奇词缀", '<div class="sorc-leg-grid">' + legHtml + '</div>', true, "sorc-sec--legendary");
    }

    // ⑤ 超凡技艺区
    var masHtml = (s.mastery && s.mastery.length)
      ? s.mastery.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("")
      : "<li>—</li>";
    detail += secBlock("超凡技艺", "<ul>" + masHtml + "</ul>", true);

    var icon = s.icon ? '<img src="assets/skills/' + esc(s.icon) + '" alt="' + esc(s.name) + '" loading="lazy">' : "";
    return '<article class="sorc-card" data-tree="' + tree + '" data-name="' + esc(s.name) + '" data-en="' + esc(s.en || "") + '">' +
      '<div class="sorc-card-head">' +
        (icon ? '<div class="sorc-thumb">' + icon + "</div>" : "") +
        '<div class="sorc-title">' +
          '<div class="sorc-name"><b>' + esc(s.name) + "</b><span class=\"en\">" + esc(s.en || "") + "</span>" +
            '<span class="sorc-tags">' + tags + "</span></div>" +
          (s.desc ? '<p class="sorc-desc">' + esc(s.desc) + "</p>" : "") +
        "</div>" +
        meta +
        '<span class="sorc-arrow">▾</span>' +
      "</div>" +
      '<div class="sorc-detail">' + detail + "</div>" +
    "</article>";
  }

  // ---------- 渲染觉醒 ----------
  function renderAwake(a) {
    var val = a.value ? '<p class="val">' + esc(a.value).replace(/(\d+(?:\.\d+)?%?)/g, function (m) { return '<span class="num">' + m + "</span>"; }) + "</p>" : "";
    var note = a.note ? '<p class="note">注：' + esc(a.note) + "</p>" : "";
    var eff = a.effect ? '<p class="eff">' + esc(a.effect) + "</p>" : "";
    var soon = (!a.effect && !a.value) ? '<p class="soon">（暂未开放）</p>' : "";
    return '<div class="sorc-awake">' +
      '<div class="sorc-awake-head"><span class="sorc-awake-lv sorc-awake-lv-' + a.lvl + '">觉醒 ' + a.lvl + " 阶</span><b>" + esc(a.name) + "</b></div>" +
      eff + val + note + soon +
    "</div>";
  }

  // ---------- 觉醒大卡片（可折叠） ----------
  function renderAwakeCard(g) {
    var awakes = (g.awakes || []).map(renderAwake).join("");
    var guide = g.guide
      ? '<div class="sorc-guide"><h5>觉醒方法指南</h5><p>' + esc(g.guide) + "</p></div>"
      : "";
    return '<article class="sorc-awake-card" data-tree="' + esc(g.tree || "") + '">' +
      '<div class="sorc-awake-card-head">' +
        '<div class="sorc-awake-card-title"><b>' + esc(g.label) + '</b>' +
        '<span class="sorc-awake-card-sub">' + (g.awakes ? g.awakes.length : 0) + " 个觉醒</span></div>" +
        '<span class="sorc-arrow">▾</span>' +
      "</div>" +
      '<div class="sorc-awake-card-body">' + guide +
        '<div class="sorc-awake-grid">' + awakes + "</div>" +
      "</div>" +
    "</article>";
  }

  // ---------- 筛选过滤 ----------
  function filtered() {
    var q = state.q.toLowerCase();
    return Object.keys(DATA.skills).filter(function (name) {
      var s = DATA.skills[name];
      if (state.tree !== "all" && (s.tree || TREE_OF[name] || "cold") !== state.tree) return false;
      if (state.tag && (s.tags || []).indexOf(state.tag) === -1) return false;
      if (!q) return true;
      return (name + " " + (s.en || "")).toLowerCase().indexOf(q) !== -1;
    }).map(function (name) { return DATA.skills[name]; });
  }

  // ---------- 觉醒渲染（随系别 Tab 联动过滤） ----------
  function renderAwakes() {
    if (!el.awakes) return;
    var groups = (DATA.awakeGroups || []).filter(function (g) {
      if (state.tree === "all") return true;
      if (!g.tree) return true;            // 无系别归属的觉醒组（女巫/亚马逊）始终显示，不受 Tab 过滤
      return g.tree === state.tree;
    });
    el.awakes.innerHTML = groups.map(renderAwakeCard).join("");
  }

  // ---------- 渲染 ----------
  function render() {
    var list = filtered();
    var grid = el.grid;
    grid.innerHTML = list.map(renderCard).join("");
    el.count.textContent = "共 " + list.length + " 个技能";

    // 系别标题显隐
    el.titles.forEach(function (t) {
      var key = t.getAttribute("data-tree");
      t.style.display = (state.tree === "all" || state.tree === key) ? "" : "none";
    });

    // 觉醒区随系别过滤：仅显示当前系别的觉醒大卡片
    renderAwakes();
  }

  // ---------- 事件 ----------
  function bind() {
    // Tab
    el.tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        state.tree = tab.getAttribute("data-tree");
        el.tabs.forEach(function (t) { t.classList.toggle("active", t === tab); });
        render();
      });
    });
    // 搜索
    el.search.addEventListener("input", function () {
      state.q = this.value.trim();
      render();
    });
    // 区域标题 / 传奇词缀卡片 / 技能卡片 展开折叠
    el.grid.addEventListener("click", function (e) {
      var head = e.target.closest ? e.target.closest(".sorc-sec-h") : null;
      if (head) {
        var sec = head.parentElement;
        if (sec && sec.classList.contains("sorc-sec")) sec.classList.toggle("open");
        return;
      }
      // 传奇词缀卡片：点击头部展开/折叠，并阻止冒泡触发外层技能卡片
      var legCard = e.target.closest ? e.target.closest(".sorc-leg-card") : null;
      if (legCard) {
        var legHead = e.target.closest ? e.target.closest(".sorc-leg-card-head") : null;
        if (legHead) legCard.classList.toggle("open");
        e.stopPropagation();
        return;
      }
      var card = e.target.closest ? e.target.closest(".sorc-card") : null;
      if (!card) return;
      card.classList.toggle("open");
    });
    // 标签筛选按钮
    if (el.tagbar) {
      el.tagbar.addEventListener("click", function (e) {
        var btn = e.target.closest ? e.target.closest(".sorc-tagbtn") : null;
        if (!btn) return;
        var tag = btn.getAttribute("data-tag");
        state.tag = (state.tag === tag) ? "" : tag;   // 再次点击同一标签 → 取消
        el.tagbtns.forEach(function (b) {
          b.classList.toggle("active", b.getAttribute("data-tag") === (state.tag || ""));
        });
        render();
      });
    }
    // 觉醒大卡片 展开/折叠（仅点击卡片头）
    var awakeWrap = document.getElementById("sorcAwakes");
    if (awakeWrap) {
      awakeWrap.addEventListener("click", function (e) {
        var head = e.target.closest ? e.target.closest(".sorc-awake-card-head") : null;
        if (!head) return;
        var card = head.parentElement;
        if (card && card.classList.contains("sorc-awake-card")) card.classList.toggle("open");
      });
    }
  }

  // ---------- 初始化 ----------
  function init() {
    if (!document.getElementById("sorcApp")) return;   // 页面守卫

    el.toolbar = document.getElementById("sorcToolbar");
    el.grid = document.getElementById("sorcGrid");
    el.count = document.getElementById("sorcCount");
    el.search = document.getElementById("sorcSearch");
    el.titles = document.querySelectorAll(".sorc-tree-title");
    el.awakes = document.getElementById("sorcAwakes");

    // 构建 Tab
    var tabsHtml = '<button type="button" class="sorc-tab active" data-tree="all">全部</button>';
    TREES.forEach(function (t) {
      tabsHtml += '<button type="button" class="sorc-tab" data-tree="' + t.key + '">' + t.label + "</button>";
    });
    document.getElementById("sorcTabs").innerHTML = tabsHtml;
    el.tabs = document.querySelectorAll(".sorc-tab");

    // 系别区块
    var treeHtml = "";
    TREES.forEach(function (t) {
      var nameCls = "sorc-tree-name" + (t.accent ? " " + t.accent : "");
      treeHtml += '<h3 class="sorc-tree-title" data-tree="' + t.key + '">' +
        '<span class="' + nameCls + '">' + t.label + "</span>" +
        ' <span class="cnt">' + Object.keys(DATA.skills).filter(function (n) {
          return (DATA.skills[n].tree || TREE_OF[n]) === t.key;
        }).length + " 个技能</span></h3>";
    });
    el.treeWrap = document.getElementById("sorcTrees");
    if (el.treeWrap) el.treeWrap.innerHTML = treeHtml;
    el.titles = document.querySelectorAll(".sorc-tree-title");

    // 觉醒区：每个系别做成一张可折叠大卡片（由 render() → renderAwakes() 按系别过滤后渲染）
    // 注：此处仅确保容器存在；实际内容在首次 render() 时填充。

    // 标签筛选按钮（搜索栏下方）
    var tagbar = document.getElementById("sorcTagbar");
    if (tagbar) {
      var present = {};
      Object.keys(DATA.skills).forEach(function (n) {
        (DATA.skills[n].tags || []).forEach(function (t) { present[t] = true; });
      });
      var ordered = PREFERRED_TAG_ORDER.filter(function (t) { return present[t]; })
        .concat(Object.keys(present).filter(function (t) { return PREFERRED_TAG_ORDER.indexOf(t) < 0; }));
      var tagHtml = '<button type="button" class="sorc-tagbtn active" data-tag="">全部</button>';
      tagHtml += ordered.map(function (t) {
        return '<button type="button" class="sorc-tagbtn" data-tag="' + esc(t) + '">' +
          '<span class="dot ' + tagClass(t) + '"></span>' + esc(t) + "</button>";
      }).join("");
      tagbar.innerHTML = tagHtml;
      el.tagbar = tagbar;
      el.tagbtns = tagbar.querySelectorAll(".sorc-tagbtn");
    }

    bind();
    render();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
