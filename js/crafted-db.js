// 手工装备页面：系列筛选 + 关键词搜索 + 卡片渲染
// 卡片复用基底/套装装备的 .base-card 结构，词条着色规则对齐套装页（range 数字淡黄、其余随文字色）
(function () {
  "use strict";

  var DATA = window.CRAFTED_ITEMS || [];

  // 基底装备代码 -> 图片（来自 window.BASE_ITEMS；护身符/戒指/武器大类用替代表）
  var BASE_MAP = {};
  (window.BASE_ITEMS || []).forEach(function (b) { BASE_MAP[b.code] = b.img; });
  var BASE_FALLBACK = {
    "amul": "assets/equipment/amulet1.webp",
    "ring": "assets/equipment/ring1.webp",
    "blun": "assets/equipment/club.webp",
    "axe": "assets/equipment/axe.webp",
    "spea": "assets/equipment/spear.webp",
    "rod": "assets/equipment/wand.webp"
  };
  function baseImg(code) {
    if (BASE_MAP[code]) return BASE_MAP[code];
    return BASE_FALLBACK[code] || "";
  }

  // ---- 状态 ----
  var state = { series: "all", part: "all", q: "" };

  // ---- 工具 ----
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // 词条着色：变量（数字/范围，含 -，如 25 - 50、5%）用淡黄高亮；其余文字 #6c6cff
  function colorize(text) {
    if (!text) return "";
    var parts = text.split(/([+-]?\d+(?:\s*-\s*[+-]?\d+)?%?)/);
    return parts.map(function (part) {
      if (/^[+-]?\d+(?:\s*-\s*[+-]?\d+)?%?$/.test(part)) {
        return '<span class="prop-num">' + esc(part) + "</span>";
      }
      return '<span class="prop-text">' + esc(part) + "</span>";
    }).join("");
  }

  // 搜索索引串
  function haystack(it) {
    return [
      it.series, it.series_en, it.result_zh, it.result_en,
      it.base_zh, it.base_code, it.part, it.quality,
      (it.materials || []).map(function (m) { return m.zh || ""; }).join(" "),
      (it.mods || []).join(" ")
    ].join(" ").toLowerCase();
  }

  // ---- DOM ----
  var TABS = document.getElementById("craftedTabs");
  var PART_TABS = document.getElementById("craftedPartTabs");
  var SEARCH = document.getElementById("craftedSearch");
  var GRID = document.getElementById("craftedGrid");
  var COUNT = document.getElementById("craftedCount");
  var EMPTY = document.getElementById("craftedEmpty");

  // ---- 单卡渲染 ----
  function cardHtml(it) {
    var bimg = baseImg(it.base_code);
    var isJewel = (it.base_code === "amul" || it.base_code === "ring");
    var imgHtml = bimg
      ? '<div class="base-thumb' + (isJewel ? " jewel" : "") + '">'
        + '<img src="' + esc(bimg) + '" alt="' + esc(it.base_zh) + '" loading="lazy" />'
        + "</div>"
      : "";
    var hasImgCls = bimg ? " has-img" : "";
    var mats = (it.materials || []).map(function (m) {
      var img = m.img
        ? '<img class="mat-img" src="' + esc(m.img) + '" alt="' + esc(m.zh) + '" loading="lazy" />'
        : "";
      return '<span class="mat-item">' + img + '<span class="mat-name">' + esc(m.zh) + "</span></span>";
    }).join("");
    var mods = (it.mods || []).map(function (m) {
      return "<li>" + colorize(m) + "</li>";
    }).join("");

    var qHtml = "";
    if (it.qual_magic) qHtml += '<span class="qual-magic">魔法品质</span>';
    if (it.qual_upg) qHtml += '<span class="qual-upg">（可升级）</span>';

    var baseCodeHtml = it.base_code
      ? '<span class="crafted-code">「' + esc(it.base_code) + '」</span>'
      : "";

    return '<article class="base-card crafted-card series-' + esc(it.series) + hasImgCls + '">'
      + imgHtml
      + '<div class="base-card-body">'
      // ---- 顶部区域：名称 + 系列标签 + 部位标签 + 基底装备 + 品质要求 ----
      + '<div class="crafted-top">'
      + '<div class="crafted-head">'
      + '<h3 class="base-name">' + esc(it.result_zh) + "</h3>"
      + '<span class="crafted-series">' + esc(it.series) + "</span>"
      + "</div>"
      + '<p class="base-en-name">' + esc(it.result_en) + "</p>"
      + '<div class="crafted-block">'
      + '<span class="crafted-label">基底装备</span>'
      + '<span class="crafted-value">' + esc(it.base_zh) + baseCodeHtml + "</span>"
      + "</div>"
      + (qHtml ? '<div class="crafted-block">'
      + '<span class="crafted-label">品质要求</span>'
      + '<span class="crafted-value">' + qHtml + "</span>"
      + "</div>" : "")
      + "</div>"
      // ---- 中部区域：合成材料 ----
      + '<hr class="base-divider" />'
      + '<div class="crafted-mid">'
      + '<div class="crafted-block">'
      + '<span class="crafted-label">合成材料</span>'
      + '<span class="crafted-value crafted-materials">' + mats + "</span>"
      + "</div>"
      + "</div>"
      // ---- 底部区域：固定词条 ----
      + '<hr class="base-divider" />'
      + '<div class="crafted-bot">'
      + '<div class="crafted-block crafted-mods-block">'
      + '<span class="crafted-label">固定词条</span>'
      + '<ul class="crafted-mods">' + mods + "</ul>"
      + "</div>"
      + "</div>"
      + "</div>"
      + "</article>";
  }

  // ---- 渲染 ----
  function render() {
    var q = state.q.trim().toLowerCase();
    var list = DATA.filter(function (it) {
      if (state.series !== "all" && it.series !== state.series) return false;
      if (state.part !== "all" && it.part !== state.part) return false;
      if (q && haystack(it).indexOf(q) === -1) return false;
      return true;
    });

    GRID.innerHTML = list.map(cardHtml).join("");
    var bits = [];
    if (state.series !== "all") bits.push(esc(state.series) + "系列");
    if (state.part !== "all") bits.push(esc(state.part));
    COUNT.innerHTML = "共 <strong>" + list.length + "</strong> 个手工装备配方"
      + (bits.length ? "（" + bits.join(" · ") + "）" : "");
    EMPTY.hidden = list.length !== 0;
  }

  // ---- 事件 ----
  function bind() {
    if (TABS) {
      TABS.addEventListener("click", function (e) {
        var btn = e.target.closest(".base-tab");
        if (!btn) return;
        state.series = btn.getAttribute("data-series");
        TABS.querySelectorAll(".base-tab").forEach(function (b) {
          var on = b === btn;
          b.classList.toggle("active", on);
          b.setAttribute("aria-selected", on ? "true" : "false");
        });
        render();
      });
    }
    if (PART_TABS) {
      PART_TABS.addEventListener("click", function (e) {
        var btn = e.target.closest(".base-tab");
        if (!btn) return;
        state.part = btn.getAttribute("data-part");
        PART_TABS.querySelectorAll(".base-tab").forEach(function (b) {
          var on = b === btn;
          b.classList.toggle("active", on);
          b.setAttribute("aria-selected", on ? "true" : "false");
        });
        render();
      });
    }
    if (SEARCH) {
      SEARCH.addEventListener("input", function () { state.q = this.value; render(); });
    }
  }

  // ---- 初始化 ----
  if (GRID) {
    bind();
    render();
  }
})();
