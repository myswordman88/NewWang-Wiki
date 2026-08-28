# -*- coding: utf-8 -*-
"""
符文之语数据生成（沿用 _build_set_data.py 框架）
输入:
  resource/excel/runes.txt        符文之语定义(Name=RunewordN, *Rune Name, itype1-6, *RunesUsed, Rune1-6, T1Code1-7+Param/Min/Max)
  resource/excel/itemtypes.txt   itype code -> ItemType 英文显示(适用装备类型，仅英文)
  resource/String/item-names.json  RunewordN -> 中文名(zhCN 第2行)
  resource/mod/objects.json        r01-r33 -> 符文中文名(去色码 ÿcX 与装饰符)
  resource/excel/properties.txt / itemstatcost.txt / item-modifiers.json / skills.* (属性中文管线，复用套装)
输出:
  resource/mod/runewords_zh.csv  (utf-8-sig)
  js/runewords-items.js          (window.RUNEWORDS = [...])
"""
import json, csv, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))

def p(*a): return os.path.join(ROOT, *a)

# ---------- 加载映射 ----------
OBJ = json.load(open(p('resource/mod/objects.json'), encoding='utf-8-sig'))
code2zh_obj = {}
for x in OBJ:
    k = str(x.get('Key', '')).lower()
    if k:
        code2zh_obj[k] = x.get('zhCN', '')

MODS = json.load(open(p('resource/String/item-modifiers.json'), encoding='utf-8'))
modkey2zh = {x['Key']: x.get('zhCN', '') for x in MODS}

NAMES = json.load(open(p('resource/String/item-names.json'), encoding='utf-8'))
name2zh = {x['Key']: x.get('zhCN', '') for x in NAMES}
name2zh_tw = {x['Key']: x.get('zhTW', '') for x in NAMES}

prop_rows = list(csv.DictReader(open(p('resource/excel/properties.txt'), encoding='utf-8'), delimiter='\t'))
prop2stat = {r['code']: r['stat1'] for r in prop_rows}
prop2tip = {r['code']: r.get('*Tooltip', '') for r in prop_rows}

stat2desc = {}
for r in csv.DictReader(open(p('resource/excel/itemstatcost.txt'), encoding='utf-8'), delimiter='\t'):
    stat2desc[r['Stat']] = (r.get('descstrpos'), r.get('descstrneg'))

# ---------- 技能名 -> 中文（oskill/skill/aura 等属性引用的技能）----------
SK_ROWS = list(csv.DictReader(open(p('resource/excel/skills.txt'), encoding='utf-8'), delimiter='\t'))
SK_NAME2SD = {}
SK_ID2NAME = {}
for _r in SK_ROWS:
    _nm = (_r.get('skill') or '').strip()
    _sd = (_r.get('skilldesc') or '').strip()
    _sid = (_r.get('*Id') or '').strip()
    if _nm:
        SK_NAME2SD[_nm] = _sd
        if _sid:
            SK_ID2NAME[_sid] = _nm
SD_ROWS = list(csv.DictReader(open(p('resource/excel/skilldesc.txt'), encoding='utf-8'), delimiter='\t'))
SK_SD2ALT = {}
for _r in SD_ROWS:
    _k = (_r.get('skilldesc') or '').strip()
    _a = (_r.get('str alt') or '').strip()
    if _k:
        SK_SD2ALT[_k] = _a
SK_JSON = json.load(open(p('resource/String/skills.json'), encoding='utf-8'))
SK_KEY2ZH = {x['Key']: (x.get('zhCN') or '').strip() for x in SK_JSON}
SK_NAME2SD_LC = {k.lower(): v for k, v in SK_NAME2SD.items()}
SK_KEY2ZH_LC = {k.lower(): v for k, v in SK_KEY2ZH.items()}

def skill_zh(par):
    if not par:
        return None
    par = str(par).strip()
    if par.isdigit() and par in SK_ID2NAME:
        par = SK_ID2NAME[par]
    # 尝试原值 / 小写 / 去 Old 后缀，兼容 par 大小写与 Frozen OrbOld 这类旧版技能名
    cands = [par, par.lower()]
    if par.endswith('Old'):
        cands += [par[:-3], par[:-3].lower()]
    for c in cands:
        sd = SK_NAME2SD.get(c) or SK_NAME2SD_LC.get(c.lower())
        if sd:
            alt = SK_SD2ALT.get(sd)
            if alt and SK_KEY2ZH.get(alt):
                return SK_KEY2ZH[alt]
    for c in cands:
        if SK_KEY2ZH.get(c) or SK_KEY2ZH_LC.get(c.lower()):
            return SK_KEY2ZH.get(c) or SK_KEY2ZH_LC.get(c.lower())
    return None

# ---------- 符文名 -> 中文（objects.json 的 r01-r33）----------
def clean_rune(s):
    if not s:
        return ''
    s = re.sub(r'ÿc.', '', s)               # 去色码 ÿcX
    s = s.replace('ㅪ', '').replace('★', '').replace('-', '')
    s = re.sub(r'\s+', '', s)               # 去空白/换行
    m = re.search(r'符文：([^A-Za-z]+)', s)  # 取「符文：」后、英文前的汉字
    return m.group(1) if m else s

code2rune = {}
for x in OBJ:
    k = str(x.get('Key', ''))
    if re.match(r'^r\d+$', k):
        en = re.search(r'([A-Za-z]+)\s*Rune', x.get('enUS', ''))
        code2rune[k.lower()] = {
            'zh': clean_rune(x.get('zhCN', '')),
            'zh_tw': clean_rune(x.get('zhTW', '')),
            'en': en.group(1) if en else '',
        }

# ---------- 符文需求等级（经典 D2，用于计算符文之语需要等级）----------
RUNE_LEVELS = {
    'r01': 11, 'r02': 11, 'r03': 13, 'r04': 13, 'r05': 15, 'r06': 15,
    'r07': 17, 'r08': 19, 'r09': 21, 'r10': 23, 'r11': 25, 'r12': 27,
    'r13': 29, 'r14': 31, 'r15': 33, 'r16': 35, 'r17': 37, 'r18': 39,
    'r19': 41, 'r20': 43, 'r21': 45, 'r22': 47, 'r23': 49, 'r24': 51,
    'r25': 53, 'r26': 55, 'r27': 57, 'r28': 59, 'r29': 61, 'r30': 63,
    'r31': 65, 'r32': 67, 'r33': 69,
}

# ---------- 适用装备类型 -> 英文显示（itemtypes.txt，仅英文）----------
IT_ROWS = list(csv.DictReader(open(p('resource/excel/itemtypes.txt'), encoding='utf-8'), delimiter='\t'))
code2type = {}
for r in IT_ROWS:
    c = (r.get('Code') or '').strip()
    if c:
        code2type[c] = (r.get('ItemType') or '').strip()

# 装备类型中文覆盖层（优先于英文；缺失则回退英文）
# 用户已确认：ashd/head/helm/shld/tors（5 项，2026-08-16）
# 其余（axe..weap）为初稿草稿，待用户校对
CODE2TYPE_ZH = {
    'ashd': '圣骑士盾牌',     # 已确认
    'head': '死灵盾牌',       # 已确认
    'helm': '头盔',           # 已确认
    'shld': '盾牌',           # 已确认
    'tors': '衣服',           # 已确认
    'axe': '斧',             # 草稿
    'club': '棍棒',           # 草稿
    'grim': '魔典',           # 草稿
    'h2h': '拳套（爪）',       # 草稿
    'hamm': '锤',            # 草稿
    'knif': '匕首',           # 草稿
    'mace': '钉锤',           # 草稿
    'mele': '近战武器',        # 草稿
    'miss': '远程武器',        # 草稿
    'pala': '圣骑士专用',       # 草稿
    'pole': '长柄武器',        # 草稿
    'scep': '权杖',           # 草稿
    'spea': '矛',            # 草稿
    'staf': '法杖',           # 草稿
    'swor': '剑',            # 草稿
    'wand': '魔杖',           # 草稿
    'weap': '武器',           # 草稿
}

# D2 特例：ModStr 取不到正确中文的属性
SPECIAL_ZH = {
    'res-all': '所有抗性 (Resist All) %+d%%',
    'res-all-max': '所有抗性上限 (Resist All Max) %+d%%',
    'dmg-min': '最小伤害 (Min Dmg) %+d',
    'dmg-max': '最大伤害 (Max Dmg) %+d',
    'dmg%': '增强伤害 (ED) %+d%%',
    'dur': '耐久度 (Dur) %d / %d',
    'cold-len': '冰冻持续时间 (CLen) %d',
    'pois-len': '中毒持续时间 (PLen) %d',
    'fade': '消散 (Fade) %+d',
    'regen-stam': '体力恢复 (Stam) %+d%%',
    'sock': '已镶嵌 (Sockets) %d',
    'fireskill': '火焰技能等级 (Fire Skills) %+d',
    'stamdrain': '体力消耗 (Stamina) %+d%%',
    'ethereal': '无形 (Ethereal)',
    'indestruct': '不可破坏 (Indestructible)',
}
STATE_ZH = {'fullsetgeneric': '完整套装', 'monsterset': '怪物套装'}

# ---------- 文本清洗 ----------
def has_cjk(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s))

def clean_name_zh(zh):
    if not zh:
        return ''
    zh = re.sub(r'ÿc.', '', zh)
    cand = [s.strip() for s in zh.split('\n') if s.strip()]
    for line in cand:
        if has_cjk(line) and not line.startswith('['):
            return line
    if len(cand) >= 2:
        return cand[1]
    return cand[0] if cand else ''

def format_desc(zh, mn, mx):
    if mn in (None, ''):
        mn = 0
    if mx in (None, ''):
        mx = 0
    mn, mx = int(mn), int(mx)
    phs = re.findall(r'%[-+]?\d*\.?\d*[di]', zh)
    if len(phs) == 1:
        val = str(mn) if mn == mx else '%d - %d' % (mn, mx)
        zh = zh.replace(phs[0], val, 1)
    elif len(phs) == 2:
        zh = zh.replace(phs[0], str(mn), 1).replace(phs[1], str(mx), 1)
    zh = zh.replace('%%', '%')
    if '#' in zh:
        if mn == mx:
            val = str(mn)
        else:
            val = '%d - %d' % (mn, mx)
        head, rest = zh.split('#', 1)
        zh = head + val + rest.replace('#', str(mx))
    return zh.strip()

def stat_zh(code, par, mn, mx):
    if code is None or code == '':
        return None
    code = code.strip()
    if code.startswith('Set-'):
        return None
    if code in ('RunesID',):
        return None
    if code in CLASS_SKILL:
        try:
            lvl = int(mx) if mx not in (None, '') else 0
        except (ValueError, TypeError):
            lvl = 0
        return '%s技能等级 +%d (%s Skill Lvls)' % (CLASS_SKILL[code], lvl, CLASS_SKILL_EN[code])
    try:
        mn = int(mn) if mn not in (None, '') else 0
    except (ValueError, TypeError):
        mn = 0
    try:
        mx = int(mx) if mx not in (None, '') else 0
    except (ValueError, TypeError):
        mx = 0
    if code == 'charged':
        sk = skill_zh(par) or par
        return '%d 级 %s (%d/%d 次充能)' % (mx, sk, mn, mn)
    if code in ('oskill', 'oskill_set', 'oskill_desc', 'oskill_replaceT', 'oskill_hidden', 'skill'):
        return '%s +%d' % (skill_zh(par) or par, mx)
    if code in ('state', 'aura', 'gethit-skill', 'hit-skill', 'att-skill', 'kill-skill', 'death-skill', 'levelup-skill'):
        if code == 'state' and par in STATE_ZH:
            return ('%s +%d' % (STATE_ZH[par], mx)) if mx else STATE_ZH[par]
        if code == 'aura' and par:
            return '装备时获得 %d 级 %s 灵气' % (mx, skill_zh(par) or par)
        if code == 'gethit-skill':
            return '%d%% 几率被击中时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if code == 'hit-skill':
            return '%d%% 几率击中时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if code == 'att-skill':
            return '%d%% 几率攻击时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if code == 'kill-skill':
            return '%d%% 几率击杀敌人时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if code == 'death-skill':
            return '%d%% 几率死亡时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if code == 'levelup-skill':
            return '%d%% 几率升级时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if par:
            return '%s +%d' % (par, mx)
        return format_desc(prop2tip.get(code, code), mn, mx)
    if code in SPECIAL_ZH:
        return format_desc(SPECIAL_ZH[code], mn, mx)
    st = prop2stat.get(code)
    if not st:
        return format_desc(prop2tip.get(code, '') or code, mn, mx)
    dp, dn = stat2desc.get(st, (None, None))
    key = dp or dn
    if not key:
        return format_desc(prop2tip.get(code, '') or code, mn, mx)
    zh = modkey2zh.get(key)
    if not zh:
        return format_desc(prop2tip.get(code, '') or code, mn, mx)
    return format_desc(zh, mn, mx)

CLASS_SKILL = {'ama': '亚马逊', 'sor': '法师', 'nec': '死灵法师', 'pal': '圣骑士',
               'ass': '刺客', 'bar': '野蛮人', 'dru': '德鲁伊', 'war': '术士'}
CLASS_SKILL_EN = {'ama': 'Ama', 'sor': 'Sor', 'nec': 'Nec', 'pal': 'Pal',
                  'ass': 'Ass', 'bar': 'Bar', 'dru': 'Dru', 'war': 'War'}

# ---------- 解析 runes.txt ----------
def collect_t1(row):
    out = []
    for i in range(1, 8):            # T1Code1..T1Code7
        code = row.get('T1Code' + str(i))
        if not code:
            continue
        par = row.get('T1Param' + str(i))
        mn = row.get('T1Min' + str(i))
        mx = row.get('T1Max' + str(i))
        text = stat_zh(code, par, mn, mx)
        if text:
            out.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
    return out

def collect_runes(row):
    seq = []
    for i in range(1, 7):            # Rune1..Rune6（按序，遇到空停止）
        c = (row.get('Rune' + str(i)) or '').strip()
        if not c:
            break
        r = code2rune.get(c.lower())
        if r:
            seq.append({'code': c, 'zh': r['zh'], 'zh_tw': r['zh_tw'], 'en': r['en']})
        else:
            seq.append({'code': c, 'zh': c, 'zh_tw': c, 'en': c})
    return seq

def collect_itypes(row):
    out = []
    for i in range(1, 7):            # itype1..itype6
        c = (row.get('itype' + str(i)) or '').strip()
        if not c:
            continue
        en = code2type.get(c, c)
        zh = CODE2TYPE_ZH.get(c, en)
        out.append({'code': c, 'name': zh, 'name_en': en})
    return out

runewords = []
with open(p('resource/excel/runes.txt'), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        key = (row.get('Name') or '').strip()       # 如 Runeword1
        if not key:
            continue
        complete = (row.get('complete') or '').strip()
        if complete != '1':                          # 仅实装符文之语（同套装过滤 Expansion / 占位 Armageddon）
            continue
        rw_en = (row.get('*Rune Name') or '').strip()
        runes = collect_runes(row)
        itypes = collect_itypes(row)
        props = collect_t1(row)
        sockets = len(runes)
        req_lvl = max((RUNE_LEVELS.get(x['code'].lower(), 0) for x in runes), default=0)
        patch = (row.get('*Patch Release') or '').strip()
        runewords.append({
            'rw_key': key,
            'rw_en': rw_en,
            'rw_zh': clean_name_zh(name2zh.get(key)),
            'rw_zh_tw': clean_name_zh(name2zh_tw.get(key)),
            'runes': runes,
            'itypes': itypes,
            'props': props,
            'sockets': sockets,
            'req_lvl': req_lvl,
            'patch': patch,
        })

# ---------- 写 CSV ----------
with open(p('resource/mod/runewords_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['rw_en', 'rw_zh', 'rw_zh_tw', 'sockets', 'req_lvl', 'patch', 'runes_zh', 'runes_en', 'itypes', 'props'])
    for r in runewords:
        w.writerow([
            r['rw_en'], r['rw_zh'], r['rw_zh_tw'], r['sockets'], r['req_lvl'], r['patch'],
            ' + '.join(x['zh'] for x in r['runes']),
            ' + '.join(x['en'] for x in r['runes']),
            ', '.join(x['name'] for x in r['itypes']),
            ' | '.join(x['text'] for x in r['props']),
        ])

# ---------- 写 JS ----------
js = '// 符文之语数据（由 _build_rune_data.py 生成，请勿手动编辑）\n'
js += 'window.RUNEWORDS = ' + json.dumps(runewords, ensure_ascii=False, indent=1) + ';\n'
with open(p('js/runewords-items.js'), 'w', encoding='utf-8') as f:
    f.write(js)

# ---------- 报告 ----------
print('实装符文之语数:', len(runewords))
miss_name = [r['rw_en'] for r in runewords if not r['rw_zh']]
miss_rune = [r['rw_en'] for r in runewords if any(not x['zh'] or x['zh'] == x['code'] for x in r['runes'])]
print('缺中文名:', len(miss_name), miss_name[:8])
print('缺符文中文:', len(miss_rune), miss_rune[:8])
print('--- 抽查 ---')
for r in runewords[:2]:
    print(r['rw_en'], '|', r['rw_zh'], '| runes:', ' + '.join('%s(%s)' % (x['zh'], x['en']) for x in r['runes']))
    print('   types:', ', '.join(x['name'] for x in r['itypes']))
    for x in r['props']:
        print('   ', x['text'])
