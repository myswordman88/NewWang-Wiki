# -*- coding: utf-8 -*-
import re, html as H
from html.parser import HTMLParser
import zhconv

SRC = 'assets/7.3 重铸与无形化/7mmSWrAUWZ7SkpcUFG1uiN/7.3 重铸与无形化.html'
OUT = 'crafting-reforge.html'

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
    if n.tag == 'svg': return ''
    return ''.join(x if isinstance(x, str) else gt(x) for x in n.mixed)

def find_all(n, cls=None, tag=None):
    out = []
    if isinstance(n, str): return out
    if (cls is None or cls in n.attrs.get('class', '')) or (tag is not None and n.tag == tag):
        out.append(n)
    for it in n.mixed: out += find_all(it, cls, tag)
    return out

b = B(); b.feed(open(SRC, encoding='utf-8').read()); root = b.root

def q(t): return t.replace('“', '「').replace('”', '」')
def clean(t): return q(zhconv.convert(t, 'zh-cn'))
def out(t): return H.escape(clean(t))

blocks = find_all(root, 'wolai-block')
def get_start(prefix):
    for n in blocks:
        t = gt(n).strip()
        if t.startswith(prefix): return t
    return ''

intro_recast   = get_start('重铸本质')
formula_recast = get_start('1件任意 魔法')
note_charm     = get_start('暗金「咒符」暂时不能重铸')
mat_recast     = get_start('新增物品「暗金之尘」')
decompose      = get_start('4件任意 暗金 装备')
intro_ethereal = get_start('现在玩家可以利用合成公式')
formula_ethereal = get_start('1件 任意品质 装备 + 1')
mat_ethereal   = get_start('现在所有「关底BOSS」')

m_recast   = re.findall(r'1件任意 (魔法|稀有|套装|暗金) 装备 / 咒符 / 珠宝\s*\+ (\d+)「暗金之尘」= 重新获得该 \1 装备（属性重新Roll）', formula_recast)
m_decompose= re.findall(r'(\d+)件任意 (暗金|套装) 装备 \+ 1 融冰药水（阿卡拉处购买）= 1 「暗金之尘」\+ 1 融冰药水', decompose)
m_eth      = re.findall(r'1件 任意品质 装备 \+ (\d+) 「英雄旗帜」= 该装备有(\d+)%转化为「无形」装备且保留所有属性', formula_ethereal)
note_arrow = re.search(r'「箭袋」类物品（包括「弓矢」和「弩箭」）均无法转化为「无形」', formula_ethereal)
m_baodi    = re.search(r'【注意】：保底机制它来了！.*?（携带后角色头顶有特殊效果）', formula_ethereal)

L = []
L.append('<article class="feature-section reveal">')
L.append('')
L.append('  <h3 class="feature-section-title">6.3.1 重铸系统</h3>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">重铸简介</h4>')
L.append('    <p class="feature-block-text">%s</p>' % out(intro_recast))
L.append('  </div>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">重铸公式</h4>')
L.append('    <div class="table-scroll">')
L.append('    <table class="feature-table" style="table-layout:fixed; min-width:560px">')
L.append('      <colgroup><col style="width:16%"><col style="width:50%"><col style="width:34%"></colgroup>')
L.append('      <thead><tr><th>底材品质</th><th>重铸配方</th><th>重铸结果</th></tr></thead>')
L.append('      <tbody>')
for (quality, n) in m_recast:
    recipe = '1件任意 %s 装备 / 咒符 / 珠宝 + %s「暗金之尘」' % (quality, n)
    result = '重新获得该 %s 装备（属性重新Roll）' % quality
    L.append('        <tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (out(quality), out(recipe), out(result)))
L.append('      </tbody>')
L.append('    </table>')
L.append('    </div>')
L.append('    <p class="feature-block-text">%s</p>' % out(note_charm))
L.append('  </div>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">重铸材料</h4>')
L.append('    <p class="feature-block-text">%s</p>' % out(re.sub(r'「分解装备」.*$', '', mat_recast)))
L.append('    <div class="table-scroll">')
L.append('    <table class="feature-table" style="table-layout:fixed; min-width:520px">')
L.append('      <colgroup><col style="width:60%"><col style="width:40%"></colgroup>')
L.append('      <thead><tr><th>分解材料</th><th>产物</th></tr></thead>')
L.append('      <tbody>')
for (n, quality) in m_decompose:
    mat = '%s件任意 %s 装备 + 1 融冰药水（阿卡拉处购买）' % (n, quality)
    prod = '1「暗金之尘」+ 1 融冰药水（融冰药水返还）'
    L.append('        <tr><td>%s</td><td>%s</td></tr>' % (out(mat), out(prod)))
L.append('      </tbody>')
L.append('    </table>')
L.append('    </div>')
L.append('  </div>')
L.append('')
L.append('  <h3 class="feature-section-title">6.3.2 装备无形化</h3>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">无形化简介</h4>')
L.append('    <p class="feature-block-text">%s</p>' % out(intro_ethereal))
L.append('  </div>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">无形化公式</h4>')
L.append('    <div class="table-scroll">')
L.append('    <table class="feature-table" style="table-layout:fixed; min-width:560px">')
L.append('      <colgroup><col style="width:44%"><col style="width:12%"><col style="width:44%"></colgroup>')
L.append('      <thead><tr><th>合成配方</th><th>转化几率</th><th>说明</th></tr></thead>')
L.append('      <tbody>')
for (n, pct) in m_eth:
    recipe = '1件 任意品质 装备 + %s「英雄旗帜」' % n
    desc = '该装备转化为「无形」装备且保留所有属性'
    L.append('        <tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (out(recipe), out(pct + '%'), out(desc)))
L.append('      </tbody>')
L.append('    </table>')
L.append('    </div>')
L.append('    <p class="feature-block-text">%s</p>' % out(note_arrow.group(0) if note_arrow else ''))
L.append('    <p class="feature-block-text">%s</p>' % out(m_baodi.group(0) if m_baodi else ''))
L.append('  </div>')
L.append('')
L.append('  <div class="feature-subsection">')
L.append('    <h4 class="feature-subsection-title">无形化材料</h4>')
L.append('    <p class="feature-block-text">%s</p>' % out(mat_ethereal))
L.append('  </div>')
L.append('')
L.append('</article>')

NEW = '\n'.join(L)
content = open(OUT, encoding='utf-8').read()
content = re.sub(r'<article class="feature-section reveal">.*?</article>', NEW, content, flags=re.S)
content = re.sub(r'<p class="section-lead">.*?</p>',
                '<p class="section-lead">重铸刷新属性、无形化提升基础——装备打造的两大核心机制。</p>', content)
open(OUT, 'w', encoding='utf-8').write(content)
print('WROTE', OUT, 'recast=%d decompose=%d eth=%d' % (len(m_recast), len(m_decompose), len(m_eth)))
