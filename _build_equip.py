import re, glob, os

# 装备详情 8 项：顺序、标题、英文slug、图标、描述
ITEMS = [
    ("装备系统", "system",   "🛡️", "品质、词缀、镶嵌、无形化与耐久机制的深度说明。"),
    ("特等装备", "special",  "⭐", "介于普通与魔法之间的特等品质，入门过渡的优选。"),
    ("魔法&稀有", "magic",   "🔮", "魔法品质（1–2 条随机词缀）与稀有品质（多条随机词缀）装备，构筑流派的核心素材。"),
    ("套装装备", "set",      "👑", "凑齐套装可触发强力觉醒羁绊的主题套装。"),
    ("符文之语", "rune",     "📜", "以符文镶嵌词缀组合，触发隐藏强力的符文之语装备。"),
    ("暗金装备", "unique",   "🟠", "固定词缀、独一无二的暗金品质装备。"),
    ("手工装备", "crafted",  "🔨", "通过配方手工打造、词缀可定制的装备。"),
    ("传奇&混沌", "legend",  "🌟", "超越暗金的传奇品质，以及蕴含混沌之力的特殊品质装备。"),
]

def dropdown_plain():
    lis = "\n".join('              <li><a href="equipment-%s.html">%s</a></li>' % (slug, title)
                    for title, slug, _, _ in ITEMS)
    return '            <ul class="dropdown">\n%s\n            </ul>' % lis

def dropdown_with_current(current_title):
    out = []
    for title, slug, _, _ in ITEMS:
        if title == current_title:
            out.append('              <li><span class="current">%s</span></li>' % title)
        else:
            out.append('              <li><a href="equipment-%s.html">%s</a></li>' % (slug, title))
    return '            <ul class="dropdown">\n%s\n            </ul>' % "\n".join(out)

# 1) 全站替换「装备详情」下拉为 10 项（普通链接，无高亮）
pat = re.compile(r'(<li class="has-dropdown">\s*<a href="[^"]*"[^>]*>装备详情</a>\s*)<ul class="dropdown">.*?</ul>', re.S)
new_dd = dropdown_plain()
updated_dd = []
for f in glob.glob("*.html"):
    s = open(f, encoding="utf-8").read()
    s2 = pat.sub(lambda m: m.group(1) + new_dd, s)
    if s2 != s:
        open(f, "w", encoding="utf-8").write(s2)
        updated_dd.append(f)
print("dropdown updated (%d):" % len(updated_dd), ", ".join(sorted(updated_dd)))

# 2) 首页装备详情卡片区：3 张 article -> 10 张 <a class="card card-link">
cards_html = '\n'.join(
    '          <a class="card card-link reveal" id="equipment-%s" href="equipment-%s.html" aria-label="查看%s详情">\n'
    '            <div class="card-icon" aria-hidden="true">%s</div>\n'
    '            <h3>%s</h3>\n'
    '            <p>%s</p>\n'
    '          </a>' % (slug, slug, title, icon, title, desc)
    for title, slug, icon, desc in ITEMS)
new_block = '        <div class="cards cards-5">\n%s\n        </div>' % cards_html

idx = open("index.html", encoding="utf-8").read()
m = re.search(r'(<div class="cards cards-5">).*?(</div>)\s*(?=</section>)', idx, re.S)
assert m, "homepage equipment cards block not found!"
idx = idx[:m.start()] + new_block + idx[m.end():]
open("index.html", "w", encoding="utf-8").write(idx)
print("homepage cards rewritten")

# 3) 生成 10 个装备详情占位页
NAV = '''    <nav class="nav container" aria-label="主导航">
      <a class="brand" href="index.html" aria-label="新王觉醒首页">
        <span class="brand-text">新王觉醒 | 官方网站</span>
      </a>

      <button class="nav-toggle" id="navToggle" aria-expanded="false" aria-controls="navMenu" aria-label="打开菜单">
        <span></span><span></span><span></span>
      </button>

      <ul class="nav-menu" id="navMenu">
        <li class="has-dropdown">
          <a href="index.html#overview" aria-haspopup="true" aria-expanded="false">模组概览</a>
          <ul class="dropdown">
            <li><a href="feature.html">特色简介</a></li>
            <li><a href="author.html">作者简介</a></li>
            <li><a href="donate.html">赞助详情</a></li>
            <li><a href="download.html">下载地址</a></li>
            <li><a href="changelog.html">更新日志</a></li>
            <li><a href="community.html">讨论社群</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#newbie" aria-haspopup="true" aria-expanded="false">新手专区</a>
          <ul class="dropdown">
            <li><a href="guide.html">安装指南</a></li>
            <li><a href="faq.html">常见问题</a></li>
            <li><a href="beginner.html">新手入门</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#changes" aria-haspopup="true" aria-expanded="false">全新系统</a>
          <ul class="dropdown">
            <li><a href="changes-basic.html">基础改动</a></li>
            <li><a href="changes-awaken.html">觉醒系统</a></li>
            <li><a href="changes-class.html">转职系统</a></li>
            <li><a href="changes-recipe.html">合成配方</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="skills-overview.html" aria-haspopup="true" aria-expanded="false">职业技能</a>
          <ul class="dropdown">
            <li><a href="skills-overview.html">技能总览</a></li>
            <li><a href="skills-sorceress.html">女巫</a></li>
            <li><a href="skills-amazon.html">亚马逊</a></li>
            <li><a href="skills-necro.html">死灵法师</a></li>
            <li><a href="skills-paladin.html">圣骑士</a></li>
            <li><a href="skills-barbarian.html">野蛮人</a></li>
            <li><a href="skills-druid.html">德鲁伊</a></li>
            <li><a href="skills-assassin.html">刺客</a></li>
            <li><a href="skills-warlock.html">术士</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#equipment" aria-haspopup="true" aria-expanded="false">装备详情</a>
__EQUIP_DROPDOWN__
        </li>
        <li class="has-dropdown">
          <a href="index.html#crafting" aria-haspopup="true" aria-expanded="false">装备打造</a>
          <ul class="dropdown">
            <li><a href="index.html#crafting-scroll">强化卷轴系统</a></li>
            <li><a href="index.html#crafting-forge">锻造系统</a></li>
            <li><a href="index.html#crafting-reforge">重铸与无形化</a></li>
            <li><a href="index.html#crafting-inherit">套装继承系统</a></li>
            <li><a href="index.html#crafting-rune">符文共鸣</a></li>
            <li><a href="index.html#crafting-seal">封印词条系统</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#items" aria-haspopup="true" aria-expanded="false">物品和配方</a>
          <ul class="dropdown">
            <li><a href="index.html#items-recipe">合成配方</a></li>
            <li><a href="index.html#items-new">新增物品</a></li>
          </ul>
        </li>
      </ul>
    </nav>'''

TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} | 新王觉醒</title>
  <meta name="description" content="新王觉醒 Mod 装备详情：{title}——{desc}" />
  <meta name="author" content="新王觉醒" />
  <meta name="theme-color" content="#0a0a0f" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700;900&family=Noto+Serif+SC:wght@600;700;900&family=Rajdhani:wght@500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="./css/style.css" />
</head>
<body>
  <a class="skip-link" href="#main">跳到主要内容</a>

  <header class="site-header" id="top">
__NAV__
  </header>

  <main id="main">
    <section class="section detail feature">
      <div class="container">
        <nav class="breadcrumb" aria-label="面包屑">
          <a href="index.html">首页</a><span aria-hidden="true">/</span>
          <a href="index.html#equipment">装备详情</a><span aria-hidden="true">/</span>
          <span class="current">{title}</span>
        </nav>

        <header class="section-head reveal">
          <p class="section-kicker">装备详情 | <span class="kicker-num">5 · {num}</span></p>
          <h2>{title}</h2>
          <p class="section-lead">{desc}</p>
        </header>

        <article class="feature-section reveal">
  <div class="feature-subsection">
    <p class="feature-block-text">本装备页面尚未制作，敬请期待。</p>
  </div>
</article>

        <a class="btn btn-ghost detail-back" href="index.html">← 返回首页</a>
      </div>
    </section>
  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <span class="brand-mark" aria-hidden="true">王</span>
        <span class="brand-text">新王觉醒</span>
        <p class="footer-tag">觉醒之夜已经降临。</p>
      </div>
      <nav class="footer-links" aria-label="页脚导航">
        <a href="index.html#overview">模组概览</a>
        <a href="index.html#newbie">新手专区</a>
        <a href="changelog.html">更新日志</a>
        <a href="index.html#crafting">装备打造</a>
      </nav>
      <p class="footer-copy">© <span id="year">2026</span> 新王觉醒. 保留所有权利.</p>
      <p class="version-badge">当前版本 v1.1.0</p>
    </div>
  </footer>

  <script src="./js/main.js" defer></script>
</body>
</html>
'''

for i, (title, slug, icon, desc) in enumerate(ITEMS, start=1):
    nav = NAV.replace("__EQUIP_DROPDOWN__", dropdown_with_current(title))
    html = TPL.replace("__NAV__", nav).format(title=title, desc=desc, num=i)
    open("equipment-%s.html" % slug, "w", encoding="utf-8").write(html)
    print("created equipment-%s.html (5.%d)" % (slug, i))

print("DONE")
