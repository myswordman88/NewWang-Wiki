# -*- coding: utf-8 -*-
import re, html as H
from html.parser import HTMLParser
import zhconv

SRC = 'assets/7.2 锻造系统/pcgBXVABFGcXc8RScjG15t/7.2 锻造系统.html'
OUT = 'crafting-forge.html'

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
    if n.tag in ('svg',): return ''
    return ''.join(x if isinstance(x, str) else gt(x) for x in n.mixed)

b = B(); b.feed(open(SRC, encoding='utf-8').read()); root = b.root

def find_all(n, cls=None, tag=None):
    out = []
    if isinstance(n, str): return out
    if (cls is None or cls in n.attrs.get('class', '')) or (tag is not None and n.tag == tag):
        out.append(n)
    for it in n.mixed:
        if not isinstance(it, str): out.extend(find_all(it, cls, tag))
    return out

def z2s(t):
    return zhconv.convert(t, 'zh-cn')

def esc(t):
    return H.escape(t)

def q(t):
    # 弯引号 "" 统一改为中文直角引号「」
    return t.replace('“', '「').replace('”', '」')

def fix_eq(t):
    t = t.strip()
    if 'STAR BREAKER' in t and not t.endswith(')'):
        t = t + ')'
    return t

tbls = find_all(root, cls='wolai-simple-table')

# ---------- TABLE 1: 稀有·锻造石 ----------
tes1 = [gt(c).strip() for c in find_all(tbls[0], cls='wolai-te')]
rows1 = [tes1[3:][i:i+3] for i in range(0, len(tes1[3:]), 3)]

# ---------- TABLE 2: 传奇·锻造石 ----------
tes2 = [gt(c).strip() for c in find_all(tbls[1], cls='wolai-te')]
rows2 = [tes2[8:][i:i+7] for i in range(0, len(tes2[8:]), 7)]
tblocks2 = [gt(bl).strip() for bl in find_all(tbls[1], cls='wolai-block')
            if gt(bl).strip().startswith('T级详细数据（点击箭头展开）')]

# ---------- TABLE 3: 混沌词条 (hand-built from verified source text) ----------
tb3 = [gt(bl).strip() for bl in find_all(tbls[2], cls='wolai-block')
       if gt(bl).strip().startswith('T级详细数据（点击箭头展开）')]
# tb3[0]=节奏大师, tb3[1]=战魂双生 (order in DOM)
TABLE3 = [
    ('1', '「混沌·正义之怒」', '周期性降下毁灭性闪电攻击附近敌人', '待补充（目前仅T1级别）', '6.2赞助装备', '☑️'),
    ('2', '「混沌·时间沙漏」', '冷却减少词条生效上限提高至100%', '仅T1级别', '', '❎'),
    ('3', '「混沌·节奏大师」', '触发连击所需的攻击次数减少', tb3[0], '6.2赞助装备', '☑️'),
    ('4', '「混沌·原初之识」', '无视传奇词条对职业的限制', '仅T1级别', '', '❎'),
    ('5', '「混沌·战魂双生」', '「身经百战」提供的加成额外被算作物理伤害总增', tb3[1], '「混沌·李奥瑞克的手骨」', '☑️'),
]

def tdetail(raw):
    t = q(z2s(raw))
    t = re.sub(r'T级详细数据（点击箭头展开）', '', t)
    t = re.sub(r'(T\d(?:（[^）]*）)?：)', r'\n\1', t).lstrip('\n')
    t = H.escape(t)
    t = re.sub(r'(T\d(?:（[^）]*）)?：)', r'<span class="tlvl">\1</span>', t)
    return t.replace('\n', '<br>')

L = []
L.append('<article class="feature-section reveal">')

# ===== 6.2.1 简介 =====
L.append('  <h3 class="feature-section-title">6.2.1 锻造系统简介</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <p class="feature-block-text">「魔王降临」中的所有装备都可以进行锻造，来增强装备的属性或者获得更强力的词条。</p>')
L.append('    <h4 class="feature-subsection-title">锻造方法</h4>')
L.append('    <ul class="feature-list">')
L.append('      <li>第一步：将装备单独放入「赫拉迪姆方块」进行合成。</li>')
L.append('      <li>第二步：合成成功后装备上会显示：「锻造潜能」：剩余 XX 点。</li>')
L.append('      <li>第三步：怪物和 Boss 都会随机掉落各种「锻造石」。</li>')
L.append('      <li>第四步：将「锻造潜能」≥1 的装备与「锻造石」一起放入「赫拉迪姆方块」进行合成。</li>')
L.append('      <li>第五步：装备属性获得增强，同时「锻造潜能」减少。</li>')
L.append('      <li>第六步：重复上述步骤，直到装备上的「锻造潜能」耗尽。</li>')
L.append('    </ul>')
L.append('    <p class="feature-block-text">「隔壁大王的建议」：先锻造一些消耗比较少的「锻造石」，当剩余「锻造潜能」较少的时候，再锻造一个消耗较大的「锻造石」比较划算！</p>')
L.append('    <h4 class="feature-subsection-title">传奇词条升级方法</h4>')
L.append('    <ul class="feature-list">')
L.append('      <li>首先使用「传奇·锻造石」为拥有「锻造潜能」的装备附加「传奇词条」。</li>')
L.append('      <li>然后将多余的「传奇·锻造石」单独放入「赫拉迪姆方块」进行合成，获得「传奇·结晶」。</li>')
L.append('      <li>将拥有传奇词条的装备和「传奇·结晶」一起放入「赫拉迪姆方块」进行合成，传奇词条的阶级 +1。</li>')
L.append('    </ul>')
L.append('  </div>')

# ===== 6.2.2 稀有·锻造石一览 =====
L.append('  <h3 class="feature-section-title">6.2.2 稀有·锻造石一览</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <table class="feature-table">')
L.append('      <thead><tr><th>编号</th><th>锻造属性</th><th>消耗锻造潜能</th></tr></thead>')
L.append('      <tbody>')
for num, attr, cost in rows1:
    L.append('        <tr><td>%s</td><td>%s</td><td>%s</td></tr>' % (esc(num), esc(q(z2s(attr))), esc(z2s(cost))))
L.append('      </tbody>')
L.append('    </table>')
L.append('  </div>')

# ===== 6.2.3 传奇·锻造石一览 =====
L.append('  <h3 class="feature-section-title">6.2.3 传奇·锻造石一览</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <div class="table-scroll table-breakout">')
L.append('    <table class="feature-table feature-table--center" style="table-layout:fixed; min-width:1080px">')
L.append('      <colgroup><col style="width:66px"><col style="width:102px"><col style="width:98px"><col style="width:132px"><col style="width:320px"><col style="width:158px"><col style="width:112px"><col></colgroup>')
L.append('      <thead><tr><th>序号</th><th>职业</th><th>技能</th><th>锻造石名称</th><th>锻造石效果</th><th>传奇装备</th><th>消耗锻造潜能</th><th>不同T级详细数据</th></tr></thead>')
L.append('      <tbody>')
for ri, (seq, prof, skill, name, eff, eq, cost) in enumerate(rows2):
    td = tdetail(tblocks2[ri]) if ri < len(tblocks2) else ''
    eqd = fix_eq(z2s(eq))
    eqd = q(eqd)
    eqd = esc(eqd)
    eqd = re.sub(r'」\s*\(', '」<br>(', eqd)
    L.append('        <tr><td class="c-c">%s</td><td class="c-c">%s</td><td class="c-c">%s</td><td>%s</td><td>%s</td><td>%s</td><td class="c-c">%s</td><td>%s</td></tr>'
             % (esc(z2s(seq)), esc(z2s(prof)), esc(z2s(skill)), esc(q(z2s(name))),
                esc(q(z2s(eff))), eqd, esc(z2s(cost)), td))
L.append('      </tbody>')
L.append('    </table>')
L.append('    </div>')
L.append('  </div>')

# ===== 6.2.4 混沌词条一览 =====
L.append('  <h3 class="feature-section-title">6.2.4 混沌词条一览</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <div class="table-scroll">')
L.append('    <table class="feature-table feature-table--center" style="table-layout:fixed; min-width:820px">')
L.append('      <colgroup><col style="width:8%"><col style="width:22%"><col style="width:28%"><col style="width:26%"><col style="width:12%"><col style="width:4%"></colgroup>')
L.append('      <thead><tr><th>序号</th><th>词条名称</th><th>词条效果</th><th>不同T级详细数据</th><th>混沌装备</th><th>实装</th></tr></thead>')
L.append('      <tbody>')
for seq, name, eff, td, eq, inst in TABLE3:
    L.append('        <tr><td class="c-c">%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class="c-c">%s</td></tr>'
             % (esc(seq), esc(q(z2s(name))), esc(q(z2s(eff))), tdetail(td), esc(q(z2s(eq))), esc(inst)))
L.append('      </tbody>')
L.append('    </table>')
L.append('    </div>')
L.append('  </div>')

L.append('</article>')

NEW = '\n'.join(L)

content = open(OUT, encoding='utf-8').read()
new_content = re.sub(r'<article class="feature-section reveal">.*?</article>', NEW, content, flags=re.S)
open(OUT, 'w', encoding='utf-8').write(new_content)
print('WROTE', OUT, 'table1=%d table2=%d table3=%d' % (len(rows1), len(rows2), len(TABLE3)))
