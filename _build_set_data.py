# -*- coding: utf-8 -*-
"""
套装装备数据生成（沿用基底装备 _build_base_data.py 框架）
输入:
  resource/excel/setitems.txt   套装部件属性
  resource/excel/sets.txt       套装整体加成
  resource/excel/properties.txt 属性 code -> itemstatcost stat
  resource/excel/itemstatcost.txt stat -> descstrpos/descstrneg (ModStr Key)
  resource/String/item-modifiers.json  ModStr Key -> 中文显示模板(zhCN)
  resource/String/item-names.json      套装名/部件名 -> 中文(zhCN)
  resource/mod/objects.json           item code -> 中文物品类别(zhCN)
输出:
  resource/mod/setitems_zh.csv  (utf-8-sig, Excel 不乱码)
  resource/mod/sets_zh.csv
  js/set-items.js             (window.SET_ITEMS = {parts, sets})
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
# 查找链：skills.txt(skill, skilldesc, *Id) -> skilldesc.txt(skilldesc, str alt) -> skills.json(Key=str alt, zhCN)
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

def skill_zh(par):
    """把技能引用(par 可为技能名或 *Id 数字)转成简体中文；找不到返回 None。"""
    if not par:
        return None
    par = str(par).strip()
    if par.isdigit() and par in SK_ID2NAME:
        par = SK_ID2NAME[par]          # 数字 id -> 技能名
    sd = SK_NAME2SD.get(par)
    if sd:
        alt = SK_SD2ALT.get(sd)
        if alt and SK_KEY2ZH.get(alt):
            return SK_KEY2ZH[alt]
    if SK_KEY2ZH.get(par):             # 兜底：par 直接就是 str alt 键
        return SK_KEY2ZH[par]
    return None

# D2 特例：ModStr 取不到正确中文的属性（多抗性合并 / stat1 为空 / 模板缺失等）
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
}
# 参数型属性(技能/状态/光环) 的特殊中文
STATE_ZH = {'fullsetgeneric': '完整套装', 'monsterset': '怪物套装'}

# ---------- 文本清洗 ----------
def has_cjk(s):
    return bool(re.search(r'[\u4e00-\u9fff]', s))

def clean_name_zh(zh):
    if not zh:
        return ''
    zh = re.sub(r'ÿc.', '', zh)               # 去颜色码
    cand = [s.strip() for s in zh.split('\n') if s.strip()]
    # 真实名称 = 第一个含中文且不以 '[' 开头的行。
    # item-names.json 中多行格式为：英文名(可选)\n中文名\nÿcU[MAX:...]\nÿc5描述ÿc4，
    # 描述/MAX 行在名称之后，故取首个中文行即可正确得到名称，丢弃后续补充说明。
    for line in cand:
        if has_cjk(line) and not line.startswith('['):
            return line
    # 兜底：无中文行时（纯英文物品名）取第二行/第一行
    if len(cand) >= 2:
        return cand[1]
    return cand[0] if cand else ''

def item_type_zh(code):
    z = code2zh_obj.get(str(code).lower(), '')
    if not z:
        return code
    z = re.sub(r'ÿc.', '', z)
    z = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]', '', z)        # tier 上标
    z = re.sub(r'[\u3131-\u319F]', '', z)       # Hangul Compatibility/Extended Jamo (ㅱㅶ㆜ㆋㆁ 等)
    z = re.sub(r'[☆◆●◇★]', '', z)                # 装饰符
    z = re.sub(r'-{2,}', '', z)                  # 品质线 -----
    z = z.strip()
    if '\n' in z:
        z = [s.strip() for s in z.split('\n') if s.strip()][-1]
    return z or code

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
    if '#' in zh:                                # 英文 *Tooltip 兜底（# 占位）
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
    if code.startswith('Set-'):               # 套装标识属性，非玩家可见
        return None
    # 职业技能等级：code 即职业，直接按 code 翻正确中文（绕过被写死的 ModStr3a 亚马逊模板）
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
    # 参数型（技能 / 状态 / 光环 / 触发）
    # 技能名引用：oskill/skill 等 par 为技能名或 *Id，统一转中文（找不到则保留原 par）
    if code in ('oskill', 'oskill_set', 'oskill_desc', 'oskill_replaceT', 'oskill_hidden', 'skill'):
        return '%s +%d' % (skill_zh(par) or par, mx)
    if code in ('state', 'aura', 'gethit-skill', 'hit-skill'):
        if code == 'state' and par in STATE_ZH:
            return ('%s +%d' % (STATE_ZH[par], mx)) if mx else STATE_ZH[par]
        if code == 'aura' and par:
            return '装备时获得 %d 级 %s 灵气' % (mx, skill_zh(par) or par)
        if code == 'gethit-skill':
            return '%d%% 几率被击中时触发 %d 级技能' % (mn, mx)
        if code == 'hit-skill':
            return '%d%% 几率击中时触发 %d 级技能' % (mn, mx)
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

UICLASS_ZH = {'ama': '亚马逊', 'sor': '法师', 'nec': '死灵法师', 'pal': '圣骑士',
              'bar': '野蛮人', 'dru': '德鲁伊', 'ass': '刺客', 'war': '术士', '0': '通用'}

# 职业技能等级：code 即职业（ama/sor/nec/pal/ass/bar/dru/war）。
# 这些 code 在 properties.txt 全部指向同一个 stat `item_addclassskills` -> ModStr3a，
# 而 item-modifiers.json 把 ModStr3a 硬编码成「亚马逊技能等级」，必须用 code 区分正确职业。
CLASS_SKILL = {'ama': '亚马逊', 'sor': '法师', 'nec': '死灵法师', 'pal': '圣骑士',
               'ass': '刺客', 'bar': '野蛮人', 'dru': '德鲁伊', 'war': '术士'}
CLASS_SKILL_EN = {'ama': 'Ama', 'sor': 'Sor', 'nec': 'Nec', 'pal': 'Pal',
                  'ass': 'Ass', 'bar': 'Bar', 'dru': 'Dru', 'war': 'War'}

def collect_props(row, base):
    """从 row 收集属性。
    base='prop'  -> 取 prop1..prop9 的自身属性，返回 [{code,par,min,max,text}]
    base='aprop' -> 取 aprop1a/b..aprop5a/b 的套装件数附加属性，
                    返回 {件数: [属性]}，其中 aprop1=2件、aprop2=3件...aprop5=6件
    """
    if base == 'prop':
        out = []
        for i in range(1, 10):
            code = row.get('prop' + str(i))
            if not code:
                continue
            par = row.get('par' + str(i))
            mn = row.get('min' + str(i))
            mx = row.get('max' + str(i))
            text = stat_zh(code, par, mn, mx)
            if text:
                out.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
        return out
    if base == 'aprop':
        groups = {}
        for i in range(1, 6):          # aprop1..5 对应 2..6 件套装物品
            grp = []
            for sub in ('a', 'b'):
                code = row.get('aprop%d%s' % (i, sub))
                if not code:
                    continue
                par = row.get('apar%d%s' % (i, sub))
                mn = row.get('amin%d%s' % (i, sub))
                mx = row.get('amax%d%s' % (i, sub))
                text = stat_zh(code, par, mn, mx)
                if text:
                    grp.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
            if grp:
                groups[str(i + 1)] = grp
        return groups
    return []

# ---------- 解析 setitems.txt (部件) ----------
parts = []
with open(p('resource/excel/setitems.txt'), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        if not row.get('index'):
            continue
        set_en = row['set']
        part_en = row['index']
        self_props = collect_props(row, 'prop')
        aprop_props = collect_props(row, 'aprop')
        parts.append({
            'set_en': set_en,
            'set_zh': clean_name_zh(name2zh.get(set_en)),
            'part_en': part_en,
            'part_zh': clean_name_zh(name2zh.get(part_en)),
            'part_zh_tw': clean_name_zh(name2zh_tw.get(part_en)),
            'item_code': row['item'],
            'item_type_zh': item_type_zh(row['item']),
            'item_name_en': row.get('*ItemName', ''),
            'lvl': row.get('lvl', ''),
            'lvl_req': row.get('lvl req', ''),
            'rarity': row.get('rarity', ''),
            'self_props': self_props,
            'aprop_props': aprop_props,
        })

# ---------- 解析 sets.txt (套装整体) ----------
sets = []
with open(p('resource/excel/sets.txt'), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        if not row.get('name'):
            continue
        set_en = row['name']
        ui = (row.get('UIClass') or '0').strip()
        partial = {}
        for k in (2, 3, 4, 5):
            grp = []
            for sub in ('a', 'b'):
                code = row.get('PCode%d%s' % (k, sub))
                if not code:
                    continue
                par = row.get('PParam%d%s' % (k, sub))
                mn = row.get('PMin%d%s' % (k, sub))
                mx = row.get('PMax%d%s' % (k, sub))
                text = stat_zh(code, par, mn, mx)
                if text:
                    grp.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
            if grp:
                partial[str(k)] = grp
        full = []
        for i in range(1, 9):
            code = row.get('FCode%d' % i)
            if not code:
                continue
            par = row.get('FParam%d' % i)
            mn = row.get('FMin%d' % i)
            mx = row.get('FMax%d' % i)
            text = stat_zh(code, par, mn, mx)
            if text:
                full.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
        ver = row.get('version', '0')
        sets.append({
            'set_en': set_en,
            'set_zh': clean_name_zh(name2zh.get(set_en)),
            'version': '资料片' if ver == '100' else '经典版',
            'ui_class': UICLASS_ZH.get(ui, ui),
            'partial': partial,
            'full': full,
        })

# ---------- 写 CSV ----------
def props_to_str(lst):
    return ' | '.join(x['text'] for x in lst)

with open(p('resource/mod/setitems_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['set_en', 'set_zh', 'part_en', 'part_zh', 'item_code', 'item_type_zh', 'item_name_en',
                'lvl', 'lvl_req', 'self_props', 'aprop_2', 'aprop_3', 'aprop_4', 'aprop_5', 'aprop_6'])
    for pt in parts:
        w.writerow([pt['set_en'], pt['set_zh'], pt['part_en'], pt['part_zh'], pt['item_code'],
                    pt['item_type_zh'], pt['item_name_en'], pt['lvl'], pt['lvl_req'],
                    props_to_str(pt['self_props']),
                    props_to_str(pt['aprop_props'].get('2', [])),
                    props_to_str(pt['aprop_props'].get('3', [])),
                    props_to_str(pt['aprop_props'].get('4', [])),
                    props_to_str(pt['aprop_props'].get('5', [])),
                    props_to_str(pt['aprop_props'].get('6', []))])

with open(p('resource/mod/sets_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['set_en', 'set_zh', 'version', 'ui_class', 'partial_2', 'partial_3', 'partial_4', 'partial_5', 'full_set'])
    for s in sets:
        w.writerow([s['set_en'], s['set_zh'], s['version'], s['ui_class'],
                    props_to_str(s['partial'].get('2', [])), props_to_str(s['partial'].get('3', [])),
                    props_to_str(s['partial'].get('4', [])), props_to_str(s['partial'].get('5', [])),
                    props_to_str(s['full'])])

# ---------- 写 JS ----------
js = '// 套装装备数据（由 _build_set_data.py 生成，请勿手动编辑）\n'
js += 'window.SET_ITEMS = ' + json.dumps({'parts': parts, 'sets': sets}, ensure_ascii=False, indent=1) + ';\n'
with open(p('js/set-items.js'), 'w', encoding='utf-8') as f:
    f.write(js)

# ---------- 报告 ----------
print('套装部件数:', len(parts))
print('套装数:', len(sets))
print('--- 抽查 部件(Civerb) ---')
for pt in parts[:3]:
    print(pt['part_en'], '|', pt['part_zh'], '|', pt['item_type_zh'], '| Lv', pt['lvl'], '/req', pt['lvl_req'])
    for x in pt['self_props']:
        print('   ', x['text'])
print('--- 抽查 套装(Civerb/Fuly/Trang) ---')
for s in sets[:1] + [x for x in sets if x['set_en'] == "Trang-Oul's Avatar"]:
    print(s['set_en'], '|', s['set_zh'], '|', s['version'], '|', s['ui_class'])
    for k in ('2', '3', '4', '5'):
        if k in s['partial']:
            print('   %s件:' % k, ' | '.join(x['text'] for x in s['partial'][k]))
    print('   全套:', ' | '.join(x['text'] for x in s['full']))
