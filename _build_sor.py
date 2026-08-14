# -*- coding: utf-8 -*-
import os, re, html as ihtml
from html.parser import HTMLParser

SRC = r"F:/Work_Test/WebSite/2026-08-11-22-00-10/assets/5.2 女巫（Sorceress）/sjvV1rpEHjnFpw6V4gmRc2/5.2 女巫（Sorceress）.html"
TEMPLATE = r"F:/Work_Test/WebSite/2026-08-11-22-00-10/skills-overview.html"
OUT = r"F:/Work_Test/WebSite/2026-08-11-22-00-10/skills-sorceress.html"
IMG_BASE = "./images/skills-sorceress/"

SPACE_RE = re.compile(r'(?<=[\u4e00-\u9fff0-9\uff08\uff09\u3010\u3011\u300c\u300d%]) +(?=[\u4e00-\u9fff0-9\uff08\uff09\u3010\u3011\u300c\u300d%])')

def clean(s):
    s = SPACE_RE.sub('', s)
    return s

# ---------- DOM builder (mixed content) ----------
class Node:
    __slots__ = ('tag', 'attrs', 'mixed', 'parent')
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = dict(attrs)
        self.mixed = []  # list of str or Node
        self.parent = None

class DOMBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('root', [])
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        n.parent = self.stack[-1]
        self.stack[-1].mixed.append(n)
        self.stack.append(n)
    def handle_startendtag(self, tag, attrs):
        self.stack[-1].mixed.append(Node(tag, attrs))
    def handle_data(self, d):
        self.stack[-1].mixed.append(d)
    def handle_endtag(self, tag):
        if self.stack[-1].tag == tag:
            self.stack.pop()
        else:
            for i in range(len(self.stack) - 1, 0, -1):
                if self.stack[i].tag == tag:
                    del self.stack[i:]
                    break

def is_node(x):
    return isinstance(x, Node)

def get_text(node):
    if node.tag == 'svg':
        return ''
    t = node.text if False else ''
    out = []
    for it in node.mixed:
        if isinstance(it, str):
            out.append(it)
        else:
            out.append(get_text(it))
    return ''.join(out)

def render_inline(node):
    if node.tag == 'svg':
        return ''
    if node.tag == 'figure':
        return ''  # figures are rendered separately; never inline their caption text
    if node.tag in ('br',):
        return '<br/>'
    parts = []
    for it in node.mixed:
        if isinstance(it, str):
            s = ihtml.escape(it)
            s = SPACE_RE.sub('', s)
            parts.append(s)
        else:
            parts.append(render_inline(it))
    inner = ''.join(parts)
    if node.tag in ('b', 'strong'):
        return '<strong>' + inner + '</strong>'
    if node.tag in ('i', 'em'):
        return '<em>' + inner + '</em>'
    return inner

def render_list(ul_node):
    tag = ul_node.tag if ul_node.tag in ('ol', 'ul') else 'ul'
    cls = 'feature-list'
    out = ['<%s class="%s">' % (tag, cls)]
    for it in ul_node.mixed:
        if is_node(it) and it.tag == 'li':
            out.append(render_list_item(it))
    out.append('</%s>' % tag)
    return ''.join(out)

def render_list_item(li):
    inline_parts = []
    nested = []
    for it in li.mixed:
        if isinstance(it, str):
            s = ihtml.escape(it)
            s = SPACE_RE.sub('', s)
            inline_parts.append(s)
        else:
            if it.tag in ('ul', 'ol'):
                nested.append(it)
            else:
                inline_parts.append(render_inline(it))
    html = '<li>' + ''.join(inline_parts)
    for nl in nested:
        html += render_list(nl)
    html += '</li>'
    return html

def render_table(table_node):
    out = ['<table class="feature-table">']
    for sec in table_node.mixed:
        if not is_node(sec):
            continue
        if sec.tag == 'thead':
            out.append('<thead>' + render_rows(sec) + '</thead>')
        elif sec.tag == 'tbody':
            out.append('<tbody>' + render_rows(sec) + '</tbody>')
    out.append('</table>')
    return ''.join(out)

def render_rows(sec):
    out = []
    for tr in sec.mixed:
        if not is_node(tr) or tr.tag != 'tr':
            continue
        out.append('<tr>')
        for cell in tr.mixed:
            if not is_node(cell):
                continue
            if cell.tag in ('th', 'td'):
                out.append('<%s>%s</%s>' % (cell.tag, render_inline(cell), cell.tag))
        out.append('</tr>')
    return ''.join(out)

def local_src(src):
    if not src:
        return ''
    fn = os.path.basename(src)
    return IMG_BASE + fn

def get_img(node):
    for it in node.mixed:
        if isinstance(it, str):
            continue
        if it.tag == 'img':
            return it
        r = get_img(it)
        if r:
            return r
    return None

def render_figure_single(node, alt):
    img = get_img(node)
    src = img.attrs.get('src', '') if img else ''
    cap = alt if alt else '技能一览'
    return ('<div class="fig-row single"><figure class="feature-figure reveal">'
            '<img src="%s" alt="%s" loading="lazy" decoding="async" />'
            '<figcaption>%s</figcaption></figure></div>' % (local_src(src), ihtml.escape(cap), ihtml.escape(cap)))

def render_fig_row(name, srcs):
    if not srcs:
        return ''
    items = []
    for src in srcs[:2]:
        # awakening panel (orighinal_sor_N_2.png) gets a distinct caption
        cap = (name + ' · 觉醒') if re.search(r'orighinal_sor_\d+_2\.png$', src) else name
        items.append('<figure class="feature-figure reveal"><img src="%s" alt="%s" loading="lazy" decoding="async" /><figcaption>%s</figcaption></figure>'
                     % (local_src(src), ihtml.escape(cap), ihtml.escape(cap)))
    cls = 'two' if len(srcs) >= 2 else 'single'
    return '<div class="fig-row %s">%s</div>' % (cls, ''.join(items))

# ---------- parse ----------
builder = DOMBuilder()
builder.feed(open(SRC, encoding='utf-8').read())
root = builder.root

# collect all figures with 'in_details' flag
def collect_figures(node, in_details, figs):
    for it in node.mixed:
        if isinstance(it, str):
            continue
        nd = in_details or it.tag == 'details'
        if it.tag == 'figure':
            figs.append((it, in_details))
        else:
            collect_figures(it, nd, figs)

all_figs = []
collect_figures(root, False, all_figs)

# Collect BOTH the main panel (orighinal_sor_N.png) and the awakening panel
# (orighinal_sor_N_2.png) per skill name. The 67px icons (_1.png) are skipped.
# Figures inside <details> (the _2 panels) were previously excluded, which is
# why they never rendered — we now include them.
skill_figs = {}   # name -> [src main, src awake]
for fig, in_det in all_figs:
    img = get_img(fig)
    if not img:
        continue
    src = img.attrs.get('src', '')
    if src.endswith('_1.png'):
        continue  # skip 67px skill icons
    raw = (img.attrs.get('alt') or '').strip()
    if not raw:
        continue
    name = raw.split()[0] if raw else ''
    if not name:
        continue
    skill_figs.setdefault(name, [])
    if src not in skill_figs[name]:
        skill_figs[name].append(src)

for name in skill_figs:
    skill_figs[name].sort(key=lambda s: 0 if re.search(r'orighinal_sor_\d+\.png$', s) else 1)

# alias: panel-image alt names may be abbreviated or misspelled vs the skill
# summary name. Merge the variant key's images into the canonical skill name
# and drop the variant key so each skill ends up with [main, awaken] exactly once.
ALIAS = {
    '闪电': '闪电箭', '闪电链': '连锁闪电', '传送': '传送术',
    '寒冰掌握': '冰冷支配', '静态立场': '静电立场', '雷暴': '雷电风暴',
}
for a, s in ALIAS.items():
    if a in skill_figs:
        skill_figs.setdefault(s, [])
        for src in skill_figs[a]:
            if src not in skill_figs[s]:
                skill_figs[s].append(src)
        skill_figs[s].sort(key=lambda x: 0 if re.search(r'orighinal_sor_\d+\.png$', x) else 1)
        del skill_figs[a]

# ---------- render helpers ----------
def cn_name(summary):
    s = summary.strip()
    m = re.match(r'^([\u4e00-\u9fff]+)', s)
    return m.group(1) if m else s

def get_summary_text(det):
    for it in det.mixed:
        if is_node(it) and it.tag == 'summary':
            return clean(get_text(it).strip())
    return ''

def clean_nested_title(s):
    s = re.sub(r'（[^）]*）', '', s)
    return clean(s).strip()

def render_block(node, skill_figs):
    tag = node.tag
    if tag in ('ul', 'ol'):
        return render_list(node)
    if tag == 'table':
        return render_table(node)
    if tag == 'details':
        # skip the wolai "backup" artifact block (duplicated awakening panels)
        if get_summary_text(node).strip() == 'backup':
            return ''
        return render_nested_details(node)
    # skip the global main-image gallery grid; those images are shown per-skill
    if tag == 'div' and 'wolai-simple-table' in node.attrs.get('class', ''):
        return ''
    if tag == 'figure':
        img = get_img(node)
        src = (img.attrs.get('src', '') if img else '')
        if src.endswith('_1.png'):
            return ''  # skip 67px skill-icon
        raw = (img.attrs.get('alt', '') if img else '').strip()
        name = raw.split()[0] if raw else ''
        # main panel + awakening panel are rendered once together via render_fig_row
        if name in skill_figs and (re.search(r'orighinal_sor_\d+\.png$', src) or re.search(r'orighinal_sor_\d+_2\.png$', src)):
            return ''
        alt = clean(raw) if raw else '技能一览'
        return render_figure_single(node, alt)
    if tag in ('aside',):
        txt = clean(get_text(node).strip())
        if txt:
            return '<p class="feature-block-text"><strong>%s</strong></p>' % ihtml.escape(txt)
        return ''
    if tag in ('div', 'p', 'section', 'article'):
        # Always recurse into element children; emit direct text runs as paragraphs.
        # (Previously a text-bearing container short-circuited and dropped figures.)
        has_child = any(is_node(it) for it in node.mixed)
        if not has_child:
            txt = get_text(node).strip()
            if txt:
                return '<p class="feature-block-text">%s</p>' % render_inline(node)
            return ''
        out = []
        buf = []
        for it in node.mixed:
            if isinstance(it, str):
                buf.append(it)
            else:
                t = ''.join(buf)
                if t.strip():
                    out.append('<p class="feature-block-text">%s</p>' % ihtml.escape(SPACE_RE.sub('', t)))
                buf = []
                out.append(render_block(it, skill_figs))
        t = ''.join(buf)
        if t.strip():
            out.append('<p class="feature-block-text">%s</p>' % ihtml.escape(SPACE_RE.sub('', t)))
        return ''.join(out)
    return render_inline(node)

def render_nested_details(node):
    summary = ''
    body = []
    for it in node.mixed:
        if isinstance(it, str):
            continue
        if it.tag == 'summary':
            summary = clean(get_text(it).strip())
        else:
            body.append(it)
    title = clean_nested_title(summary)
    html = '<p class="feature-block-text"><strong>%s</strong></p>\n' % ihtml.escape(title) if title else ''
    for it in body:
        html += render_block(it, skill_figs)
    return html

def render_skill(det, skill_figs):
    summary = ''
    body = []
    for it in det.mixed:
        if isinstance(it, str):
            continue
        if it.tag == 'summary':
            summary = clean(get_text(it).strip())
        else:
            body.append(it)
    name = cn_name(summary)
    html = '<h4 class="feature-subsection-title">%s</h4>\n' % ihtml.escape(summary)
    for it in body:
        html += render_block(it, skill_figs)
    figs = skill_figs.get(name, [])
    html += render_fig_row(name, figs)
    return html

# ---------- chapters ----------
# find first h2 and use its parent container as the chapter stream
h2s = []
def find_h2(node):
    for it in node.mixed:
        if isinstance(it, str):
            continue
        if it.tag == 'h2':
            h2s.append(it)
        find_h2(it)
find_h2(root)

chapters = []
cur = None
if h2s:
    container = h2s[0].parent
    for it in container.mixed:
        if isinstance(it, str):
            continue
        if it.tag == 'h2':
            title = clean(get_text(it).strip())
            title = re.sub(r'^\d+\.\s*', '', title)
            cur = {'title': title, 'blocks': []}
            chapters.append(cur)
        else:
            if cur is not None:
                cur['blocks'].append(it)

NUM = {'通用标签和词缀': '4.2.1', '冰冷系': '4.2.2', '闪电系': '4.2.3', '火焰系': '4.2.4'}

article_parts = []
for ch in chapters:
    title = ch['title']
    num = NUM.get(title, '')
    article_parts.append('<h3 class="feature-section-title">%s %s</h3>' % (num, ihtml.escape(title)))
    article_parts.append('<div class="feature-subsection">')
    for b in ch['blocks']:
        if isinstance(b, str):
            continue
        if is_node(b) and b.tag == 'details' and ('（' in get_summary_text(b) and '【' in get_summary_text(b)):
            article_parts.append(render_skill(b, skill_figs))
        else:
            article_parts.append(render_block(b, skill_figs))
    article_parts.append('</div>')

article_html = '<article class="feature-section reveal">\n' + '\n'.join(article_parts) + '\n</article>'

# ---------- template ----------
tpl = open(TEMPLATE, encoding='utf-8').read()
new = tpl
new = new.replace('技能总览 | 新王觉醒', '女巫 | 新王觉醒')
new = new.replace('职业技能·4·1', '职业技能·4·2')
new = new.replace('<h2>技能总览</h2>', '<h2>女巫</h2>')
new = new.replace('本页汇总「新王觉醒」对技能体系的全局改动，包括技能关联词缀、超凡技艺机制，以及技能与召唤物的伤害计算方式。',
                  '女巫职业技能详解：涵盖冰冷、闪电、火焰三系全部主动与被动技能的基础数值、协同加成、词缀效果，以及各阶觉醒分支一览。')
new = new.replace('<span class="current">技能总览</span>', '<span class="current">女巫</span>')
new = re.sub(r'<article class="feature-section reveal">.*?</article>', article_html, new, flags=re.S)
new = new.replace('当前版本 v1.0.9', '当前版本 v1.1.0')

open(OUT, 'w', encoding='utf-8').write(new)
print("written", OUT, "len", len(new))
print("chapters:", [c['title'] for c in chapters])
print("skill_figs keys sample:", list(skill_figs.keys())[:5])
