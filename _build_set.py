import re, html as H
from html.parser import HTMLParser

SRC = "assets/6.3 「套装」品质装备/ftyuzXwkgg9NWsshbjK5Lk/6.3 「套装」品质装备.html"
PAGE = "equipment-set.html"

# ---------- DOM ----------
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

# ---------- collect wolai-col (each = one 部位) ----------
cols = []
def find_cols(n):
    for it in n.mixed:
        if isinstance(it, str):
            continue
        if 'wolai-col' in it.attrs.get('class', ''):
            cols.append(it)
        find_cols(it)
find_cols(root)

def clean_affix(t):
    # wolai drops the space before 点/% and after % — restore for readability
    t = re.sub(r'(\d)(点|%)', r'\1 \2', t)
    t = re.sub(r'%([一-鿿])', r'% \1', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

parts = []  # (title, [affixes])
for col in cols:
    title = ''; affixes = []
    for child in col.mixed:
        if isinstance(child, str):
            continue
        cls = child.attrs.get('class', '')
        if 'bg-' in cls and 'wolai-block' in cls and not title:
            title = get_text(child).strip()
        if child.tag == 'ul' and 'wolai-block' in cls:
            for li in child.mixed:
                if isinstance(li, str):
                    continue
                if li.tag == 'li':
                    a = clean_affix(get_text(li))
                    if a:
                        affixes.append(a)
    if title and affixes:
        parts.append((title, affixes))

print("parsed 部位 count:", len(parts))
for t, a in parts:
    print("  %s (%d 词缀)" % (t, len(a)))

# ---------- change overview (cleaned) ----------
OVERVIEW = ('现在所有「套装」品质的装备部件，除了固定词条外，都有几率获得随机词条，'
            '且随机词条与「套装」的部位相关联。')

# ---------- build article HTML ----------
def esc(t):
    return H.escape(t)

L = []
L.append('  <h3 class="feature-section-title">5.6.1「套装」改动总览</h3>')
L.append('  <div class="feature-subsection">')
L.append('    <p class="feature-block-text">%s</p>' % esc(OVERVIEW))
L.append('  </div>')
L.append('')
L.append('  <h3 class="feature-section-title">5.6.2 套装随机词条一览</h3>')
for title, affixes in parts:
    L.append('  <div class="feature-subsection">')
    L.append('    <h4 class="feature-subsection-title">%s</h4>' % esc(title))
    L.append('    <ul class="feature-list">')
    for a in affixes:
        L.append('      <li>%s</li>' % esc(a))
    L.append('    </ul>')
    L.append('  </div>')
article = '\n'.join(L)

# ---------- replace placeholder article in page ----------
s = open(PAGE, encoding='utf-8').read()
marker = '<article class="feature-section reveal">'
start = s.index(marker) + len(marker)
end = s.index('</article>')
s = s[:start] + '\n' + article + '\n' + s[end:]
open(PAGE, 'w', encoding='utf-8').write(s)
print("wrote", PAGE)
