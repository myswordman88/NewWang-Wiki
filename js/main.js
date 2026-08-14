/* =========================================================
   新王觉醒 官网交互脚本
   - 移动端菜单切换 + 下拉子菜单展开/收起
   - 桌面端下拉菜单 aria-expanded 管理
   - 滚动揭示动画 (IntersectionObserver)
   - 数据数字滚动计数
   - 预约表单校验（纯前端，不收集/外传敏感信息）
   - 页脚年份 & 平滑滚动
   ========================================================= */
(function () {
  "use strict";

  /* ---------- 移动端菜单 + 下拉子菜单 ---------- */
  const toggle = document.getElementById("navToggle");
  const menu = document.getElementById("navMenu");
  const dropdownParents = menu ? menu.querySelectorAll(".has-dropdown") : [];

  function closeMenu() {
    if (!menu || !toggle) return;
    menu.classList.remove("open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "打开菜单");
    dropdownParents.forEach(function (li) {
      li.classList.remove("open");
      const a = li.querySelector("a");
      if (a) a.setAttribute("aria-expanded", "false");
    });
  }

  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      const isOpen = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(isOpen));
      toggle.setAttribute("aria-label", isOpen ? "关闭菜单" : "打开菜单");
      if (!isOpen) {
        dropdownParents.forEach(function (li) {
          li.classList.remove("open");
          const a = li.querySelector("a");
          if (a) a.setAttribute("aria-expanded", "false");
        });
      }
    });

    // 点击菜单项后关闭
    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function (e) {
        const parentLi = this.closest(".has-dropdown");
        // 仅当不是下拉触发器时关闭整菜单
        if (!parentLi || this.getAttribute("href") !== "#") {
          closeMenu();
        }
      });
    });

    // 点击菜单外部关闭
    document.addEventListener("click", function (e) {
      if (!menu.contains(e.target) && !toggle.contains(e.target)) closeMenu();
    });

    // Esc 关闭
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeMenu();
    });

    // 视口放大到桌面尺寸时重置
    window.addEventListener("resize", function () {
      if (window.innerWidth > 768) closeMenu();
    });
  }

  // 移动端下拉子菜单切换（点击父级展开/收起）
  dropdownParents.forEach(function (li) {
    const trigger = li.querySelector("a");
    if (!trigger) return;

    trigger.addEventListener("click", function (e) {
      // 仅在移动端视图下拦截（窗口宽度 <= 768）
      if (window.innerWidth > 768) return;
      e.preventDefault();
      const isOpen = li.classList.toggle("open");
      trigger.setAttribute("aria-expanded", String(isOpen));
      // 关闭同级其他下拉
      dropdownParents.forEach(function (other) {
        if (other !== li) {
          other.classList.remove("open");
          const a = other.querySelector("a");
          if (a) a.setAttribute("aria-expanded", "false");
        }
      });
    });
  });

  // 桌面端 dropdown hover 时 aria-expanded 联动
  dropdownParents.forEach(function (li) {
    const trigger = li.querySelector("a");
    if (!trigger) return;
    li.addEventListener("mouseenter", function () {
      if (window.innerWidth > 768) trigger.setAttribute("aria-expanded", "true");
    });
    li.addEventListener("mouseleave", function () {
      if (window.innerWidth > 768) trigger.setAttribute("aria-expanded", "false");
    });
    li.addEventListener("focusin", function () {
      if (window.innerWidth > 768) trigger.setAttribute("aria-expanded", "true");
    });
    li.addEventListener("focusout", function (e) {
      if (window.innerWidth > 768 && !li.contains(e.relatedTarget)) {
        trigger.setAttribute("aria-expanded", "false");
      }
    });
  });

  /* ---------- 滚动揭示动画 ---------- */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0, rootMargin: "0px 0px -8% 0px" }
    );
    revealEls.forEach(function (el) {
      io.observe(el);
    });
  } else {
    // 不支持时直接显示
    revealEls.forEach(function (el) {
      el.classList.add("is-visible");
    });
  }

  /* ---------- 数字滚动计数 ---------- */
  const counters = document.querySelectorAll(".stat-num[data-target]");
  function animateCount(el) {
    const target = parseFloat(el.getAttribute("data-target")) || 0;
    const suffix = el.getAttribute("data-suffix") || "";
    const duration = 1600;
    const start = performance.now();

    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - p, 3);
      const value = Math.floor(eased * target);
      el.textContent = formatNumber(value) + suffix;
      if (p < 1) {
        requestAnimationFrame(tick);
      } else {
        el.textContent = formatNumber(target) + suffix;
      }
    }
    requestAnimationFrame(tick);
  }

  function formatNumber(n) {
    // 超过一万使用千分位
    return n.toLocaleString("en-US");
  }

  if ("IntersectionObserver" in window && counters.length) {
    const statIO = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animateCount(entry.target);
            statIO.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    counters.forEach(function (c) {
      statIO.observe(c);
    });
  } else {
    counters.forEach(function (c) {
      const t = parseFloat(c.getAttribute("data-target")) || 0;
      c.textContent = formatNumber(t) + (c.getAttribute("data-suffix") || "");
    });
  }

  /* ---------- 平滑滚动（兼容旧浏览器） ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
      const id = this.getAttribute("href");
      if (id === "#" || id.length < 2) return;
      const targetEl = document.querySelector(id);
      if (!targetEl) return;
      e.preventDefault();
      targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  /* ---------- 页脚年份 ---------- */
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());

  /* ---------- 上线倒计时（终点：2026-08-29 09:00 本地时间） ---------- */
  const cdDays = document.getElementById("cdDays");
  const cdHours = document.getElementById("cdHours");
  const cdMins = document.getElementById("cdMins");
  const cdSecs = document.getElementById("cdSecs");
  const COUNTDOWN_TARGET = new Date(2026, 7, 29, 9, 0, 0).getTime(); // 月份 7 = 8月
  function pad2(n) { return String(n).padStart(2, "0"); }
  function tickCountdown() {
    if (!cdDays) return;
    let diff = COUNTDOWN_TARGET - Date.now();
    if (diff < 0) diff = 0;
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    cdDays.textContent = pad2(d);
    cdHours.textContent = pad2(h);
    cdMins.textContent = pad2(m);
    cdSecs.textContent = pad2(s);
  }
  if (cdDays) {
    tickCountdown();
    setInterval(tickCountdown, 1000);
  }
})();
