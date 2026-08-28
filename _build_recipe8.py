import os, re, html as H
from html.parser import HTMLParser

ROOT = 'F:/Work_Test/WebSite/2026-08-11-22-00-10'
SRC = os.path.join(ROOT, 'assets', '8.1 合成配方', 'aSFuCg2zoCFFgrxXPLaMN8', '8.1 合成配方.html')

class N:
    __slots__ = ('tag', 'attrs', 'mixed', 'parent')
    def __init__(s, t, a):
        s.tag = t; s.attrs = dict(a); s.mixed = []; s.parent = None

class B(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True)
        s.root = N('root', []); s.stack = [s.root]
    def handle_starttag(s, t, a):
        n = N(t, a); n.parent = s.stack[-1]; s.stack[-1].mixed.append(n); s.stack.append(n)
    def handle_startendtag(s, t, a):
        n = N(t, a); n.parent = s.stack[-1]; s.stack[-1].mixed.append(n)
    def handle_data(s, d): s.stack[-1].mixed.append(d)
    def handle_endtag(s, t):
        if s.stack[-1].tag == t: s.stack.pop()
        else:
            for i in range(len(s.stack)-1, 0, -1):
                if s.stack[i].tag == t: del s.stack[i:]; break

def gt(n):
    if isinstance(n, str): return n
    if n.tag == 'svg': return ''
    return ''.join(gt(x) for x in n.mixed)

def cls_of(n): return n.attrs.get('class', '') if not isinstance(n, str) else ''

def find_all(n, cls):
    out = []
    if not isinstance(n, str):
        if cls in cls_of(n): out.append(n)
        for it in n.mixed: out += find_all(it, cls)
    return out

def find_tag(n, tag):
    if isinstance(n, str): return None
    if n.tag == tag: return n
    for it in n.mixed:
        r = find_tag(it, tag)
        if r: return r
    return None

b = B(); b.feed(open(SRC, encoding='utf-8').read()); root = b.root
tbls = find_all(root, 'wolai-simple-table')

def rows_of(tbl):
    inner = find_tag(tbl, 'table')
    tb = find_tag(inner, 'tbody')
    out = []
    for tr in tb.mixed:
        if isinstance(tr, str) or tr.tag != 'tr': continue
        cells = [gt(c).strip() for c in tr.mixed if not isinstance(c, str) and c.tag in ('th', 'td')]
        out.append(cells)
    return out

tbl1 = rows_of(tbls[0])   # 改动配方 3 行
tbl2 = rows_of(tbls[1])   # 新增配方

# 过滤表2空行（两列皆空）
tbl2 = [r for r in tbl2 if not (len(r) == 2 and r[0] == '' and r[1] == '')]

def esc(t):
    return H.escape(t).replace('\n', '<br>')

L = []
L.append('          <h3 class="feature-section-title">8.1.1 原版配方</h3>')
L.append('          <div class="feature-subsection">')
L.append('            <p class="feature-block-text">详情查询游戏内「凯恩之书」。</p>')
L.append('          </div>')

L.append('')
L.append('          <h3 class="feature-section-title">8.1.2 改动配方</h3>')
L.append('          <div class="feature-subsection">')
L.append('            <p class="feature-block-text">Mod 对部分原版配方进行了调整，以下是改动前后的对比：</p>')
L.append('            <table class="feature-table recipe-first">')
L.append('              <thead><tr><th>配方内容</th><th>原版配方</th><th>Mod 改动配方</th></tr></thead>')
L.append('              <tbody>')
for c1, c2, c3 in tbl1:
    L.append('                <tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(c1), esc(c2), esc(c3)))
L.append('              </tbody>')
L.append('            </table>')
L.append('          </div>')

L.append('')
L.append('          <h3 class="feature-section-title">8.1.3 新增配方</h3>')
L.append('          <div class="feature-subsection">')
L.append('            <p class="feature-block-text">Mod 新增了大量合成公式，利用赫拉迪克方块即可打造传说级道具：</p>')
L.append('            <table class="feature-table recipe-first">')
L.append('              <thead><tr><th>配方内容</th><th>配方公式</th></tr></thead>')
L.append('              <tbody>')
for row in tbl2:
    c1 = esc(row[0]); c2 = esc(row[1])
    L.append('                <tr><td>%s</td><td>%s</td></tr>' % (c1, c2))
L.append('              </tbody>')
L.append('            </table>')
L.append('          </div>')

ARTICLE = '\n'.join(L)

TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>合成配方 | 新王觉醒</title>
  <meta name="description" content="新王觉醒 Mod 合成配方：按类别整理的全部赫拉迪克方块配方，检索方便。" />
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
    <nav class="nav container" aria-label="主导航">
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
          <ul class="dropdown">
            <li><a href="equipment-system.html">装备系统</a></li>
            <li><a href="equipment-special.html">特等装备</a></li>
            <li><a href="equipment-magic.html">魔法&稀有</a></li>
            <li><a href="equipment-set.html">套装装备</a></li>
            <li><a href="equipment-rune.html">符文之语</a></li>
            <li><a href="equipment-unique.html">暗金装备</a></li>
            <li><a href="equipment-crafted.html">手工装备</a></li>
            <li><a href="equipment-legend.html">传奇&混沌</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#crafting" aria-haspopup="true" aria-expanded="false">装备打造</a>
          <ul class="dropdown">
            <li><a href="crafting-scroll.html">强化卷轴</a></li>
            <li><a href="crafting-forge.html">锻造系统</a></li>
            <li><a href="crafting-reforge.html">重铸与无形化</a></li>
            <li><a href="crafting-rune.html">符文共鸣</a></li>
            <li><a href="crafting-seal.html">封印词条</a></li>
          </ul>
        </li>
        <li class="has-dropdown">
          <a href="index.html#items" aria-haspopup="true" aria-expanded="false">物品和配方</a>
          <ul class="dropdown">
            <li><a href="items-recipe.html">合成配方</a></li>
            <li><a href="items-new.html">新增物品</a></li>
          </ul>
        </li>
      </ul>
    </nav>
  </header>

  <main id="main">
    <section class="section detail feature">
      <div class="container">
        <nav class="breadcrumb" aria-label="面包屑">
          <a href="index.html">首页</a><span aria-hidden="true">/</span>
          <a href="index.html#items">物品和配方</a><span aria-hidden="true">/</span>
          <span class="current">合成配方</span>
        </nav>

        <header class="section-head reveal">
          <p class="section-kicker">物品和配方 | <span class="kicker-num">8 · 1</span></p>
          <h2>合成配方</h2>
          <p class="section-lead">按类别整理的全部赫拉迪克方块配方，检索方便。</p>
        </header>

        <article class="feature-section reveal recipe-page">
__ARTICLE__
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
      <p class="version-badge">当前版本 v1.0.8</p>
    </div>
  </footer>

  <script src="./js/main.js" defer></script>
</body>
</html>
'''

html = TEMPLATE.replace('__ARTICLE__', ARTICLE)
with open(os.path.join(ROOT, 'items-recipe.html'), 'w', encoding='utf-8') as f:
    f.write(html)
print('items-recipe.html 生成完成 | 表1=%d行 表2=%d行' % (len(tbl1), len(tbl2)))
