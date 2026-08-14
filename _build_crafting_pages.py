# -*- coding: utf-8 -*-
"""装备打造板块：把其余 4 张卡片做成可点击链接卡，并生成对应占位页 + 全站导航同步。"""
import os, re, glob

ROOT = r'F:\Work_Test\WebSite\2026-08-11-22-00-10'

# (slug, 标题, kicker 编号, 卡片描述)
PAGES = [
    ('crafting-forge',   '锻造系统',     '6 · 2', '通过锻造改变装备词缀池，定向打造毕业装备。'),
    ('crafting-reforge', '重铸与无形化', '6 · 3', '重铸不满意的无形装备，保留外观并刷新属性。'),
    ('crafting-rune',    '符文共鸣',     '6 · 4', '特定符文组合可激活隐藏共鸣效果，打造专属流派。'),
    ('crafting-seal',    '封印词条',     '6 · 5', '解锁装备上的封印词条，获得稀有觉醒特效。'),
]
SLUGS = [p[0] for p in PAGES]

TMPL = open(os.path.join(ROOT, 'crafting-scroll.html'), encoding='utf-8').read()

PLACEHOLDER = '''  <article class="feature-section reveal">
  <div class="feature-subsection">
    <p class="feature-block-text">该内容尚未实装，敬请期待。</p>
  </div>
</article>'''

# 1) 生成 4 个占位页
for slug, title, kicker, desc in PAGES:
    html = TMPL
    html = html.replace('<title>强化卷轴 | 新王觉醒</title>', '<title>%s | 新王觉醒</title>' % title)
    html = html.replace('<span class="current">强化卷轴</span>', '<span class="current">%s</span>' % title)
    html = html.replace('<span class="kicker-num">6 · 1</span>', '<span class="kicker-num">%s</span>' % kicker)
    html = html.replace('<h2>强化卷轴</h2>', '<h2>%s</h2>' % title)
    html = html.replace('使用强化卷轴提升装备基础属性，追求极限数值。', desc)
    html = re.sub(r'<article class="feature-section reveal">.*?</article>', PLACEHOLDER, html, flags=re.S)
    for s in SLUGS:
        html = html.replace('index.html#%s' % s, '%s.html' % s)
        html = html.replace('#%s' % s, '%s.html' % s)
    open(os.path.join(ROOT, slug + '.html'), 'w', encoding='utf-8').write(html)
    print('wrote', slug + '.html')

# 2) index.html：4 张卡 article -> a.card-link（保留内部内容）
idx = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
idx = re.sub(
    r'(\s*)<article class="card reveal" id="(crafting-(?:forge|reforge|rune|seal))">(\n.*?)</article>',
    lambda m: m.group(1) + '<a class="card card-link reveal" id="%s" href="%s.html">' % (m.group(2), m.group(2)) + m.group(3) + '</a>',
    idx, flags=re.S)
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(idx)
print('updated index.html cards')

# 3) 全站导航下拉：锚点 -> 链接（含 index.html）
def fix_nav(t):
    for s in SLUGS:
        t = t.replace('index.html#%s' % s, '%s.html' % s)
        t = t.replace('#%s' % s, '%s.html' % s)
    return t

for f in glob.glob(os.path.join(ROOT, '*.html')):
    t = open(f, encoding='utf-8').read()
    orig = t
    t = fix_nav(t)
    if t != orig:
        open(f, 'w', encoding='utf-8').write(t)
        print('nav updated', os.path.basename(f))

print('DONE')
