import os, re, html as H, glob
from html.parser import HTMLParser

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "assets/7.1 强化卷轴系统/scRS3qjhvqCj3xnb9aipP1/7.1 强化卷轴系统.html")
PAGE = "crafting-scroll.html"
TEMPLATE = "equipment-set.html"

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
    def handle_data(s, d):
        s.stack[-1].mixed.append(d)
    def handle_endtag(s, t):
        if s.stack[-1].tag == t:
            s.stack.pop()
        else:
            for i in range(len(s.stack) - 1, 0, -1):
                if s.stack[i].tag == t:
                    del s.stack[i:]; break

def get_text(n):
    if n.tag == 'svg':
        return ''
    out = []
    for x in n.mixed:
        out.append(x if isinstance(x, str) else get_text(x))
    return ''.join(out)

b = B(); b.feed(open(SRC, encoding='utf-8').read()); root = b.root

# ---- 7.1.1 简介 ----
blocks = []
def collect_blocks(n):
    if isinstance(n, str):
        return
    if 'wolai-block' in n.attrs.get('class', ''):
        blocks.append(n)
    for it in n.mixed:
        if not isinstance(it, str):
            collect_blocks(it)
collect_blocks(root)
intro_text = ''
for i, blk in enumerate(blocks):
    if get_text(blk).strip() == '7.1.1 强化卷轴系统简介':
        for j in range(i + 1, len(blocks)):
            txt = get_text(blocks[j]).strip()
            if txt and not txt.startswith('7.1.'):
                intro_text = txt
                break
        break

# ---- 表格 ----
def find_table(n):
    if isinstance(n, str):
        return None
    if 'wolai-simple-table' in n.attrs.get('class', ''):
        return n
    for it in n.mixed:
        if not isinstance(it, str):
            r = find_table(it)
            if r:
                return r
    return None

def find_tbody(n):
    if isinstance(n, str):
        return None
    if n.tag == 'tbody':
        return n
    for it in n.mixed:
        if not isinstance(it, str):
            r = find_tbody(it)
            if r:
                return r
    return None

t = find_table(root)
tbody = find_tbody(t)
data = {'普通强化卷轴': {'武器': [], '防具': [], '饰品': []}}
order = ['普通强化卷轴']
cur = '普通强化卷轴'

def get_tds(tr):
    return [it for it in tr.mixed if isinstance(it, N) and it.tag == 'td']

for tr in tbody.mixed:
    if isinstance(tr, str) or tr.tag != 'tr':
        continue
    tds = get_tds(tr)
    if not tds:
        continue
    if any('bg-' in td.attrs.get('class', '') for td in tds):
        name = get_text(tds[0]).strip()
        if name and name not in data:
            data[name] = {'武器': [], '防具': [], '饰品': []}
            order.append(name)
        cur = name
        continue
    def cell(i):
        return get_text(tds[i]).strip() if i < len(tds) else ''
    def add(cat, a, mn, mx, lv):
        if a:
            data[cur][cat].append((a, mn, mx, lv))
    add('武器', cell(2), cell(3), cell(4), cell(5))
    add('防具', cell(7), cell(8), cell(9), cell(10))
    add('饰品', cell(12), cell(13), cell(14), cell(15))

# ---- 生成 article ----
def esc(t):
    return H.escape(t)
L = []
L.append('  <h3 class="feature-section-title">6.1.1 强化卷轴系统简介</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <p class="feature-block-text">%s</p>' % esc(intro_text))
L.append('  </div>')
L.append('')
L.append('  <h3 class="feature-section-title">6.1.2 强化卷轴一览</h3>')
for name in order:
    L.append('  <div class="feature-subsection">')
    L.append('    <h4 class="feature-subsection-title">%s</h4>' % esc(name))
    L.append('    <table class="feature-table">')
    L.append('      <thead><tr><th>适用装备</th><th>强化属性</th><th>数值范围</th><th>等级需求</th></tr></thead>')
    L.append('      <tbody>')
    for ci, cat in enumerate(('武器', '防具', '饰品')):
        for ri, (a, mn, mx, lv) in enumerate(data[name][cat]):
            sep = ' class="row-sep row-sep-green"' if (ci > 0 and ri == 0) else ''
            L.append('        <tr%s><td>%s</td><td>%s</td><td>%s ~ %s</td><td>+%s</td></tr>' % (sep, esc(cat), esc(a), esc(mn), esc(mx), esc(lv)))
    L.append('      </tbody>')
    L.append('    </table>')
    L.append('  </div>')
article = '\n'.join(L)

# ---- 生成 crafting-scroll.html（基于 equipment-set.html 模板） ----
s = open(TEMPLATE, encoding='utf-8').read()
s = s.replace('套装装备 | 新王觉醒', '强化卷轴 | 新王觉醒')
s = s.replace('新王觉醒 Mod 装备详情：套装装备——凑齐套装可触发强力觉醒羁绊的主题套装。',
              '新王觉醒 Mod 装备打造：强化卷轴——使用强化卷轴提升装备基础属性，追求极限数值。')
s = s.replace('<li><span class="current">套装装备</span></li>',
              '<li><a href="equipment-set.html">套装装备</a></li>')
s = s.replace('            <li><a href="index.html#crafting-inherit">套装继承系统</a></li>\n', '')
s = s.replace('<li><a href="index.html#crafting-scroll">强化卷轴系统</a></li>',
              '<li><span class="current">强化卷轴</span></li>')
s = s.replace('<li><a href="index.html#crafting-seal">封印词条系统</a></li>',
              '<li><a href="index.html#crafting-seal">封印词条</a></li>')
s = s.replace('          <a href="index.html#equipment">装备详情</a><span aria-hidden="true">/</span>\n          <span class="current">套装装备</span>',
              '          <a href="index.html#crafting">装备打造</a><span aria-hidden="true">/</span>\n          <span class="current">强化卷轴</span>')
s = s.replace('装备详情 | <span class="kicker-num">5 · 6</span>',
              '装备打造 | <span class="kicker-num">6 · 1</span>')
s = s.replace('>套装装备</h2>', '>强化卷轴</h2>')
s = s.replace('凑齐套装可触发强力觉醒羁绊的主题套装。',
              '使用强化卷轴提升装备基础属性，追求极限数值。')
marker = '<article class="feature-section reveal">'
start = s.index(marker) + len(marker)
end = s.index('</article>')
s = s[:start] + '\n' + article + '\n' + s[end:]
open(PAGE, 'w', encoding='utf-8').write(s)
print('wrote', PAGE)

# ---- 全站导航同步（除 crafting-scroll.html 本身） ----
def patch_file(path, is_index):
    t = open(path, encoding='utf-8').read()
    orig = t
    if is_index:
        t = t.replace('            <li><a href="#crafting-inherit">套装继承系统</a></li>\n', '')
        t = t.replace('<li><a href="#crafting-scroll">强化卷轴系统</a></li>',
                      '<li><a href="crafting-scroll.html">强化卷轴</a></li>')
    else:
        t = t.replace('            <li><a href="index.html#crafting-inherit">套装继承系统</a></li>\n', '')
        t = t.replace('<li><a href="index.html#crafting-scroll">强化卷轴系统</a></li>',
                      '<li><a href="crafting-scroll.html">强化卷轴</a></li>')
    t = t.replace('封印词条系统</a>', '封印词条</a>')
    if t != orig:
        open(path, 'w', encoding='utf-8').write(t)
        print('patched', os.path.basename(path))

for f in glob.glob(os.path.join(BASE, '*.html')):
    bn = os.path.basename(f)
    if bn == PAGE:
        continue
    patch_file(f, bn == 'index.html')

# ---- index.html 卡片区 ----
idx = open('index.html', encoding='utf-8').read()
inherit_block = (
    '          <article class="card reveal" id="crafting-inherit">\n'
    '            <div class="card-icon" aria-hidden="true">🔗</div>\n'
    '            <h3>套装继承系统</h3>\n'
    '            <p>将旧套装的觉醒羁绊继承到新装备，降低毕业成本。</p>\n'
    '          </article>\n'
)
idx = idx.replace(inherit_block, '')
scroll_old = (
    '          <article class="card reveal" id="crafting-scroll">\n'
    '            <div class="card-icon" aria-hidden="true">📜</div>\n'
    '            <h3>强化卷轴系统</h3>\n'
    '            <p>使用强化卷轴提升装备基础属性，追求极限数值。</p>\n'
    '          </article>'
)
scroll_new = (
    '          <a class="card card-link reveal" id="crafting-scroll" href="crafting-scroll.html">\n'
    '            <div class="card-icon" aria-hidden="true">📜</div>\n'
    '            <h3>强化卷轴</h3>\n'
    '            <p>使用强化卷轴提升装备基础属性，追求极限数值。</p>\n'
    '          </a>'
)
idx = idx.replace(scroll_old, scroll_new)
idx = idx.replace('<h3>封印词条系统</h3>', '<h3>封印词条</h3>')
open('index.html', 'w', encoding='utf-8').write(idx)
print('updated index.html cards')
print('DONE')
