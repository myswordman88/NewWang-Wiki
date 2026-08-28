# -*- coding: utf-8 -*-
"""
暗金装备数据生成（沿用 _build_rune_data.py / _build_set_data.py 管线）
输入:
  resource/excel/uniqueitems.txt   暗金装备定义(*ItemName=英文名, code=底材, lvl/lvl req, prop1-12+par/min/max)
  resource/mod/armor.txt           防具底材(code -> type 大类)
  resource/mod/weapons.txt         武器底材(code -> type 大类)
  resource/mod/objects.json        item code -> 中文底材名(zhCN)
  resource/mod/uniques.json        唯一物品 slug -> 图片路径(normal/uber/ultra，含 // 注释需剥离)
  resource/excel/properties.txt / itemstatcost.txt / item-modifiers.json / skills.* (属性中文管线)
  resource/String/item-names.json  暗金英文名 -> 中文名(zhCN 第2行)
输出:
  resource/mod/uniques_zh.csv     (utf-8-sig)
  js/unique-items.js              (window.UNIQUE_ITEMS = [...])
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

# 底材档位（普通/扩展/精英），取自 objects.json 中文名上标 ¹²³（与 _build_base_data.py 同逻辑）
SUP_MARK = {"\u00b9": "普通", "\u00b2": "扩展", "\u00b3": "精英"}
def tier_from_zh(zh):
    for ch, t in SUP_MARK.items():
        if ch in (zh or ""):
            return t
    return ""
code2tier = {}
for x in OBJ:
    k = x.get('Key')
    if k:
        t = tier_from_zh(x.get('zhCN', '') or '')
        if t and k not in code2tier:
            code2tier[k] = t

MODS = json.load(open(p('resource/String/item-modifiers.json'), encoding='utf-8'))
modkey2zh = {x['Key']: x.get('zhCN', '') for x in MODS}

NAMES = json.load(open(p('resource/String/item-names.json'), encoding='utf-8'))
name2zh = {x['Key']: x.get('zhCN', '') for x in NAMES}
name2zh_tw = {x['Key']: x.get('zhTW', '') for x in NAMES}

# 暗金特殊/任务/随从类：部分 index 与 item-names.json 的 Key 不一致，
# 其正确中文名在 item-runes.json（同结构字串表，按 Key 或 enUS）里。并入该表作为兜底。
RUNES = json.load(open(p('resource/String/item-runes.json'), encoding='utf-8'))
name2zh_runes = {}
name2zh_tw_runes = {}
for _x in RUNES:
    _k = _x.get('Key', '')
    _e = _x.get('enUS', '')
    if _k:
        name2zh_runes[_k] = _x.get('zhCN', '')
        name2zh_tw_runes[_k] = _x.get('zhTW', '')
    if _e:                       # 额外用 enUS 建索引，覆盖 "Khalim's Flail" 这类显示名
        name2zh_runes.setdefault(_e, _x.get('zhCN', ''))
        name2zh_tw_runes.setdefault(_e, _x.get('zhTW', ''))

# 手工覆盖：index 既不在 item-names.json 也不在 item-runes.json 的暗金
# （多为任务/随从内部编码项，index 与字串表 Key 完全无关）。
# 前 6 项已在 item-runes.json 中核对（经 Key / enUS）；后 2 项为 D2 标准译名，待用户确认。
UNIQUE_NAME_OVERRIDE = {
    'KhalimFlail': '克林姆的连枷',
    'SuperKhalimFlail': '克林姆的遗愿',
    'Horadric Staff': '赫拉迪姆之杖',
    'Hell Forge Hammer': '地狱熔炉之锤',
    'Constricting Ring': '束缚之戒',
    'Darkfear': '黑暗恐惧',
    'Amulet of the Viper': '蝮蛇护符',     # D2 标准译名，待用户确认
    'Staff of Kings': '国王之杖',           # D2 标准译名，待用户确认
    'SP_QuarkCharm': '夸克契约',            # 赞助人特殊暗金（cm4 咒符），应需求加入；简体玩家可见中文名
    'Blind Eye': '厄运工匠之眼',            # 应需求：简繁均为「厄运工匠之眼」，去掉书名号与英文名后缀
    'SummonNPCCharm': '六道通灵',           # 应需求：赞助人特殊暗金，简体「六道通灵」
    'Legend Starbreaker': '碎星者',          # 传奇品质（赞助_传奇），应需求：简繁均为「碎星者」
}

# 繁体中文名覆盖：仅当用户要求简繁不一致时使用；默认 name_zh_tw 由 name2zh_tw 解析
UNIQUE_NAME_TW_OVERRIDE = {
    'SP_QuarkCharm': '夸克契約',            # 对应 item-names.json 原繁体名
    'Blind Eye': '厄運工匠之眼',            # 应需求：繁体「厄運工匠之眼」
    'SummonNPCCharm': '六道通靈',           # 应需求：繁体「六道通靈」
    'Legend Starbreaker': '碎星者',          # 应需求：繁与简一致
}

# 英文显示名覆盖：内部 index 与玩家可见英文名不一致的特殊暗金
# （如赞助人特殊物 SP_QuarkCharm，内部编码为 SP_QuarkCharm，游戏中显示 Quark Pact）
UNIQUE_EN_OVERRIDE = {
    'SP_QuarkCharm': 'Quark Pact',
    'SummonNPCCharm': 'Six Paths Charm',    # 应需求：英文显示名
    'Legend Starbreaker': 'Star Breaker',   # 应需求：英文显示名
}

# 用户确认：以下特殊/随从暗金不进入公开资料表（雇佣兵专用 + 赞助人特殊物）
EXCLUDE_UNIQUE = {
    # 随从/雇佣兵专用暗金（mod 内部编码，无中文源）
    'Minion UniCap1', 'Minion UniCap2', 'Minion UniCap3', 'Minion UniCap4', 'Minion UniCap5',
    'Minion UniLea6', 'Minion UniCap7', 'Minion UniCap8', 'Minion UniCap9', 'Minion UniCap10',
    'Minion UniKnif1', 'Minion UniKnif2',
    # 赞助人/特殊物（cm4-cm7，非普通掉落暗金）
    # 注：SP_QuarkCharm 已于 2026-08-17 应需求加入公开资料表（见下方 UNIQUE_NAME_OVERRIDE / UNIQUE_EN_OVERRIDE）
    'WangsCharm', 'VIPCharm', 'InheritedCharm',
}

# 传奇&混沌品质（codex 为 赞助_传奇 / 混沌 等标记，独立进入【传奇&混沌】页面 js/legend-items.js，不进暗金表）
LEGEND_SET = {
    'Legend Starbreaker',   # 赞助_传奇，底材高地剑（Highland Blade）
}

prop_rows = list(csv.DictReader(open(p('resource/excel/properties.txt'), encoding='utf-8'), delimiter='\t'))
prop2stat = {r['code']: r['stat1'] for r in prop_rows}
prop2tip = {r['code']: r.get('*Tooltip', '') for r in prop_rows}

stat2desc = {}
for r in csv.DictReader(open(p('resource/excel/itemstatcost.txt'), encoding='utf-8'), delimiter='\t'):
    stat2desc[r['Stat']] = (r.get('descstrpos'), r.get('descstrneg'))

# ---------- 技能名 -> 中文 ----------
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

# ---------- 底材 code -> type 大类（来自 armor.txt / weapons.txt 的 type 列）----------
def load_arm(fp):
    return list(csv.DictReader(open(fp, encoding='utf-8'), delimiter='\t'))

code2type = {}
for r in load_arm(p('resource/mod/armor.txt')) + load_arm(p('resource/mod/weapons.txt')):
    c = (r.get('code') or '').strip()
    if c:
        code2type[c] = (r.get('type') or '').strip()

# itemtypes.txt 英文显示（兜底）
IT_ROWS = list(csv.DictReader(open(p('resource/excel/itemtypes.txt'), encoding='utf-8'), delimiter='\t'))
code2type_en = {}
for r in IT_ROWS:
    c = (r.get('Code') or '').strip()
    if c:
        code2type_en[c] = (r.get('ItemType') or '').strip()

# ---------- 大类（顶部筛选）与 type 中文覆盖层 ----------
TOP_CAT = {
    'weapon': '武器', 'shield': '盾牌', 'helm': '头盔', 'armor': '衣服',
    'glove': '手套', 'boot': '鞋子', 'belt': '腰带',
    'jewelry': '首饰', 'charm': '护符', 'ammo': '弹药',
}
# 首饰二级类型显示（戒指/护身符/珠宝），用于暗金卡片第二行「饰品 · X」，
# 与护符「饰品·护符」保持一致；vip 的底材中文覆盖是「毒蛇护符」（专属暗金名），此处用通用「护身符」
JEWELRY_TYPE_ZH = {'rin': '戒指', 'amu': '项链', 'vip': '毒蛇项链', 'jew': '珠宝'}
TYPE2CAT = {}
for t in ['axe', 'club', 'h2h', 'h2h2', 'hamm', 'knif', 'mace', 'pole', 'scep', 'spea',
          'staf', 'swor', 'wand', 'bow', 'xbow', 'abow', 'ajav', 'aspe', 'jave',
          'mboq', 'mxbq', 'orb', 'taxe', 'tkni', 'tpot', 'mele', 'miss', 'pala', 'weap']:
    TYPE2CAT[t] = 'weapon'
TYPE2CAT.update({'shie': 'shield', 'ashd': 'shield', 'head': 'shield'})
TYPE2CAT.update({'helm': 'helm', 'phlm': 'helm', 'circ': 'helm', 'grim': 'helm', 'pelt': 'helm'})
TYPE2CAT.update({'tors': 'armor'})
TYPE2CAT.update({'glov': 'glove', 'boot': 'boot', 'belt': 'belt'})
TYPE2CAT.update({'rin': 'jewelry', 'amu': 'jewelry', 'vip': 'jewelry', 'jew': 'jewelry'})
TYPE2CAT.update({t: 'charm' for t in
                  ['cm1', 'cm2', 'cm3', 'cm4', 'cjw', 'cs2',
                   'nc1', 'nc2', 'nc3', 'nc4', 'nc5', 'nc6', 'nc7', 'nc8', 'nc9']})
TYPE2CAT.update({'M10': 'ammo', '15': 'ammo'})

# type 中文（武器子类 / 防具子类）覆盖层。沿用符文之语已确认的 5 项 + 扩展。
TYPE_ZH = {
    'ashd': '圣骑士盾牌', 'head': '死灵盾牌', 'helm': '头盔', 'shld': '盾牌', 'tors': '衣服',
    'axe': '斧', 'club': '棍棒', 'grim': '魔典', 'h2h': '拳套（爪）', 'hamm': '锤',
    'knif': '匕首', 'mace': '钉锤', 'mele': '近战武器', 'miss': '远程武器', 'pala': '圣骑士专用',
    'pole': '长柄武器', 'scep': '权杖', 'spea': '矛', 'staf': '法杖', 'swor': '剑',
    'wand': '魔杖', 'weap': '武器',
    # 防具子类
    'shie': '盾牌', 'circ': '冠', 'phlm': '卓越头盔', 'pelt': '德鲁伊法宝',
    'glov': '手套', 'boot': '鞋子', 'belt': '腰带',
    # 武器子类（armor.txt/weapons.txt 实际 code）
    'h2h2': '拳套（爪）', 'abow': '弓', 'ajav': '标枪', 'aspe': '标枪', 'jave': '标枪',
    'mboq': '弹药袋', 'mxbq': '弹药袋', 'orb': '法球', 'taxe': '投掷斧',
    'tkni': '投掷匕首', 'tpot': '投掷瓶', 'bow': '弓', 'xbow': '十字弓',
    # 首饰 / 护符 / 弹药
    'rin': '戒指', 'amu': '护身符', 'vip': '护身符', 'jew': '珠宝',
    'cm1': '小型咒符', 'cm2': '大型咒符', 'cm3': '特大咒符', 'cm4': '咒符', 'cjw': '咒符', 'cs2': '咒符',
    'nc1': '咒符', 'nc2': '咒符', 'nc3': '咒符', 'nc4': '咒符', 'nc5': '咒符',
    'nc6': '咒符', 'nc7': '咒符', 'nc8': '咒符', 'nc9': '咒符', 'M10': '箭', '15': '箭',
}

# 底材中文名覆盖层（objects.json 没有的 code）
BASE_ZH_OVERRIDE = {
    # 任务暗金：底材即其自身，无通用底材中文名，用物品自身中文名覆盖
    'msf': '国王之杖', 'hst': '赫拉迪姆之杖',
    'hfh': '地狱熔炉之锤', 'qf1': '克林姆的连枷',
    'qf2': '克林姆的遗愿',
    'rin': '戒指', 'amu': '护身符', 'vip': '毒蛇护符', 'jew': '珠宝',
    'cm1': '小型咒符', 'cm2': '大型咒符', 'cm3': '特大咒符', 'cm4': '咒符', 'cjw': '咒符', 'cs2': '咒符',
    'nc1': '咒符', 'nc2': '咒符', 'nc3': '咒符', 'nc4': '咒符', 'nc5': '咒符',
    'nc6': '咒符', 'nc7': '咒符', 'nc8': '咒符', 'nc9': '咒符', 'M10': '箭', '15': '箭',
}

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

def item_type_zh(code):
    z = code2zh_obj.get(str(code).lower(), '')
    if not z:
        return code
    z = re.sub(r'ÿc.', '', z)
    z = re.sub(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]', '', z)
    z = re.sub(r'[\u3131-\u319F]', '', z)
    z = re.sub(r'[☆◆●◇★]', '', z)
    z = re.sub(r'-{2,}', '', z)
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
    if '#' in zh:
        val = str(mn) if mn == mx else '%d - %d' % (mn, mx)
        head, rest = zh.split('#', 1)
        zh = head + val + rest.replace('#', str(mx))
    return zh.strip()

def stat_zh(code, par, mn, mx):
    if code is None or code == '':
        return None
    code = code.strip()
    if code.startswith('Set-'):
        return None
    cl = code.lower()
    if cl in CLASS_SKILL:
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
    if cl == 'charged':
        sk = skill_zh(par) or par
        return '%d 级 %s (%d/%d 次充能)' % (mx, sk, mn, mn)
    if cl in ('oskill', 'oskill_set', 'oskill_desc', 'oskill_replaceT', 'oskill_hidden', 'skill'):
        sk = skill_zh(par)
        return ('%s +%d' % (sk, mx)) if sk else ('隐藏技能 (Hidden Skill) +%d' % mx)
    if cl in ('state', 'aura', 'gethit-skill', 'hit-skill', 'att-skill', 'kill-skill', 'death-skill', 'levelup-skill'):
        if cl == 'state' and par in STATE_ZH:
            return ('%s +%d' % (STATE_ZH[par], mx)) if mx else STATE_ZH[par]
        if cl == 'state' and par in CUSTOM_STATE_ZH:
            return ('%s +%d' % (CUSTOM_STATE_ZH[par], mx)) if mx else CUSTOM_STATE_ZH[par]
        if cl == 'aura' and par:
            return '装备时获得 %d 级 %s 灵气' % (mx, skill_zh(par) or par)
        if cl == 'gethit-skill':
            return '%d%% 几率被击中时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if cl == 'hit-skill':
            return '%d%% 几率击中时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if cl == 'att-skill':
            return '%d%% 几率攻击时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if cl == 'kill-skill':
            return '%d%% 几率击杀敌人时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if cl == 'death-skill':
            return '%d%% 几率死亡时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if cl == 'levelup-skill':
            return '%d%% 几率升级时触发 %d 级 %s' % (mn, mx, skill_zh(par) or par)
        if par:
            return '状态 (State) %s +%d' % (par, mx)
        return format_desc(prop2tip.get(code, code), mn, mx)
    if cl in CUSTOM_PROP_ZH and CUSTOM_PROP_ZH[cl]:
        return CUSTOM_PROP_ZH[cl]
    if cl in SPECIAL_ZH:
        return format_desc(SPECIAL_ZH[cl], mn, mx)
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
# mod 自定义状态（state par）
CUSTOM_STATE_ZH = {'spcool': '冷却缩减 (Cooldown)'}
# mod 自定义属性（源 item-modifiers.json 无中文，给双语可读标签，便于后续校正）
CUSTOM_PROP_ZH = {
    'npoint': '点数 (Npoint)',
    'aura_hidden': '隐藏灵气 (Hidden Aura)',
    'awaken_desc': '觉醒 (Awaken)',
    'kill-skill_hidden': '击杀触发技能 (Kill-Skill)',
    'hit-skill_hidden': '击中触发技能 (Hit-Skill)',
    'gethit-skill_hidden': '被击触发技能 (GetHit-Skill)',
    'oskill_hidden': '隐藏技能 (Hidden Skill)',
    'death-skill_hidden': '死亡触发技能 (Death-Skill)',
    'bloody': '染血 (Bloody)',
    'chaos mark': '混沌印记 (Chaos Mark)',
    'com_missileadd': '附加弹药 (Missile Add)',
    'sealedaffixa': '封印词缀A (Sealed Affix A)',
    'sealedaffixb': '封印词缀B (Sealed Affix B)',
    'sealedaffixc': '封印词缀C (Sealed Affix C)',
    'skilltab-war': '战士技能 (War Skills)',
    'magdam-rand': '随机魔法伤害 (Random Mag Dmg)',
    'kill-display': '击杀计数 (Kill Display)',
    'death-display': '死亡计数 (Death Display)',
    'inheritedtimes': '继承次数 (Inherited Times)',
    'oskill_replacet': '替换技能 (Replace Skill)',
    'smithid': '锻造ID (Smith ID)',
    'aura_oskill_replacet': '灵气替换技能 (Aura Replace Skill)',
    'random-aura': '随机灵气 (Random Aura)',
}
# 打造词缀家族（Gelid/Incendiary/Magnetic/Virulent/Breaching/Mystical + 序号）
for _fam, _zh in [('Gelid', '冰霜'), ('Incendiary', '烈焰'), ('Magnetic', '磁力'),
                  ('Virulent', '剧毒'), ('Breaching', '破障'), ('Mystical', '秘法')]:
    for _i in range(1, 7):
        CUSTOM_PROP_ZH[('%s-affix%d' % (_fam, _i)).lower()] = '%s词缀%d (%s Affix %d)' % (_zh, _i, _fam, _i)

# ---------- 图片：uniques.json（剥离 // 注释后解析）----------
def load_uniques_img():
    raw = open(p('resource/mod/uniques.json'), encoding='utf-8').read()
    raw = re.sub(r'//[^\n]*', '', raw)          # 去 // 注释
    data = json.loads(raw)
    m = {}                                       # slug -> 图片 stem（路径最后一段）
    for entry in data:
        for slug, paths in entry.items():
            path = paths.get('normal') or paths.get('uber') or paths.get('ultra') or ''
            stem = path.strip().split('/')[-1].strip()
            if stem:
                m[slug] = stem
    return m

UNIQUE_IMG = load_uniques_img()

# 底材图兜底：从 js/base-items.js 取 code -> 图片 stem（无独立暗金美术时回退）
code2baseimg = {}
try:
    btxt = open(p('js/base-items.js'), encoding='utf-8').read()
    bm = re.search(r'window\.BASE_ITEMS\s*=\s*(\[.*\]);', btxt, re.S)
    if bm:
        for b in json.loads(bm.group(1)):
            img = b.get('img', '')
            if img:
                code2baseimg[str(b.get('code', '')).lower()] = img.split('/')[-1].replace('.webp', '')
except Exception as e:
    print('warn: 加载 base-items.js 失败，底材图兜底不可用:', e)

def slugify(name):
    # 与 uniques.json 的 slug 规则一致：去所有非字母数字（含空格/撇号/连字符）-> 下划线
    return re.sub(r'[^a-z0-9]+', '_', (name or '').strip().lower()).strip('_')

def img_for(name, code):
    slug = slugify(name)
    stem = UNIQUE_IMG.get(slug)
    if not stem:
        stem = slug                            # 兜底：直接用 slug 当文件名
    fp = p('assets/equipment', stem + '.webp')
    if os.path.exists(fp):
        return stem
    # 兜底：暗金无独立美术时，用同底材的基底装备图（如戒指/护身符/武器）
    fb = code2baseimg.get(str(code).lower())
    if fb and os.path.exists(p('assets/equipment', fb + '.webp')):
        return fb
    return None

# ---------- 解析 uniqueitems.txt ----------
def collect_props(row):
    out = []
    eu_list = []                               # 「装备唯一」类属性，强制前置并标红
    sockets = 0
    # 「装备唯一」标记：源 uniqueitems.txt 中 carry1 列不为空 且 par1 列 == 1040 即为「装备唯一」
    carry1 = (row.get('carry1') or '').strip()
    par1 = (row.get('par1') or '').strip()
    eu_flag = bool(carry1) and par1 == '1040'
    if eu_flag:
        eu_list.append({'code': 'oskill_desc', 'par': '1040', 'min': '', 'max': '', 'text': '装备唯一', 'eu': True})
    for i in range(1, 13):                     # prop1..prop12
        code = row.get('prop' + str(i))
        if not code:
            continue
        par = row.get('par' + str(i))
        mn = row.get('min' + str(i))
        mx = row.get('max' + str(i))
        # 「装备唯一」标记已由 carry1/par1 生成，oskill_desc par1=1040 即其数据来源，跳过避免重复
        if eu_flag and code.strip() == 'oskill_desc' and (par or '').strip() == '1040':
            continue
        text = stat_zh(code, par, mn, mx)
        # 地狱火炬(randclassskill)源 data min=0/max=7 为占位，实际固定 +3 至随机职业 技能等级
        if code.strip() == 'randclassskill':
            text = '+3 至 <随机职业> 技能等级'
            mn = '3'
            mx = '3'
        if text:
            text = re.sub(r'ÿc.', '', text).strip()   # 去除 D2 颜色标记（网站不渲染，避免卡片显示乱码）
            # 「装备唯一」特殊处理：去引号与末尾等级数字，标红，并强制放到第一条属性
            if '装备唯一' in text:
                text = re.sub(r'[「」]', '', text)            # 去掉书名号，仅留 装备唯一
                text = re.sub(r'\s*[+\-]?\s*\d+\s*$', '', text).strip()  # 去掉末尾等级数字（+1）
                eu_list.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text, 'eu': True})
            else:
                out.append({'code': code, 'par': par or '', 'min': mn or '', 'max': mx or '', 'text': text})
        if code.strip() == 'sock':
            try:
                sockets = max(sockets, int(mx) if mx not in (None, '') else 0)
            except (ValueError, TypeError):
                pass
    return eu_list + out, sockets

# ---------- 冠名赞助标记：用于网页「冠名赞助」筛选按钮（key=内部 index，可自定义赞助人/描述） ----------
SPONSORED = {
    "Mara's Kaleidoscope": {"sponsor": "Van·幻臆", "desc": "这是van参加猛♂活动时必带的项链"},
    "SP_QuarkCharm": {"sponsor": "夸克网盘", "desc": "当勇士血洒沙场，时空将撕开裂隙，引其残魂重返人世，拾起未竟的荣耀"},
    "SummonNPCCharm": {"sponsor": "蛮胡·子", "desc": "萤火微光亦可照亮前路"},
    "Legend Starbreaker": {"sponsor": "隔壁大王", "desc": "崩解的世界之石碎片融入了這把劍，從此它渴望吞噬一切"},
}

uniques = []
legend_records = []                       # 传奇&混沌品质：独立进入 js/legend-items.js
with open(p('resource/excel/uniqueitems.txt'), encoding='utf-8') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        if not row.get('index'):
            continue
        internal_id = (row.get('index') or '').strip()      # 暗金内部唯一键（对应 item-names.json Key / uniques.json slug）
        if internal_id in EXCLUDE_UNIQUE:                     # 用户确认不进入公开资料表的特殊/随从暗金
            continue
        if re.search(r'codex', internal_id, re.I):            # 奈非天宝典系列（mod 特殊物品，不放入公开资料表）
            continue
        # 无法生成且不入编年史：spawnable 为空（无法生成）+ disableChronicle=1（编年史中不会有）。
        # 例如 Darkfear，这类隐藏/不可获取暗金不进入公开资料表（2026-08-17）。
        # 注意：碎片系列（Defender's/Protector's/Guardian's）spawnable 为空但 disableChronicle 非 1，予以保留。
        # 例外：Crafted * 系列（暗金板子升级版）虽同为此标记，但需展示，故放行（2026-08-17）。
        if (row.get('spawnable') or '').strip() == '' and (row.get('disableChronicle') or '').strip() == '1' \
                and not internal_id.startswith('Crafted '):
            continue
        name_en = UNIQUE_EN_OVERRIDE.get(internal_id, internal_id)   # 玩家可见英文名（默认=内部键）
        base_en = (row.get('*ItemName') or '').strip()      # 底材英文名（展示用）
        code = (row.get('code') or '').strip()
        if not code:                                        # 空 code = 占位/模板行（非真实装备），跳过
            continue
        t = code2type.get(code, '')
        cat = TYPE2CAT.get(t) or TYPE2CAT.get(code, 'weapon')
        subtype_zh = TYPE_ZH.get(t) or TYPE_ZH.get(code) or code2type_en.get(t) or code2type_en.get(code) or t or code
        base_zh = BASE_ZH_OVERRIDE.get(code) or item_type_zh(code)
        ver = (row.get('version') or '').strip()
        version = '资料片' if ver in ('1', '100') else '经典版'
        # 档位（普通/扩展/精英）：底材 code -> objects.json 上标；
        # 首饰/护符/弹药在 D2 无档位 -> 饰品；其余无档位者（任务武器等）-> 任务
        tier_zh = code2tier.get(code)
        if not tier_zh:
            tier_zh = '普通' if cat in ('jewelry', 'charm', 'ammo') else '任务'
        props, sockets = collect_props(row)
        rec = {
            'uid': (row.get('*ID') or '').strip(),
            'name_en': name_en,
            'base_en': base_en,
            'name_zh': clean_name_zh(UNIQUE_NAME_OVERRIDE.get(internal_id) or name2zh.get(internal_id) or name2zh_runes.get(internal_id)),
            'name_zh_tw': clean_name_zh(UNIQUE_NAME_TW_OVERRIDE.get(internal_id) or UNIQUE_NAME_OVERRIDE.get(internal_id) or name2zh_tw.get(internal_id) or name2zh_tw_runes.get(internal_id)),
            'code': code,
            'base_zh': base_zh,
            'type': t or code,
            'cat': cat,
            # 首饰显示具体二级类型（戒指/护身符/珠宝），与护符「饰品·护符」保持一致；其余用大类中文
            'cat_zh': (JEWELRY_TYPE_ZH.get(code) or TOP_CAT.get(cat, cat)) if cat == 'jewelry' else TOP_CAT.get(cat, cat),
            'subtype_zh': subtype_zh,
            'tier_zh': tier_zh,
            'qlvl': (row.get('lvl') or '').strip(),
            'req_lvl': (row.get('lvl req') or '').strip(),
            'version': version,
            'disabled': (row.get('disabled') or '').strip(),
            'sockets': sockets,
            'props': props,
            'img': img_for(internal_id, code),
            # 冠名赞助标记：含此标记的物品在网页渲染专属「冠名赞助」区块，并提供筛选按钮
            'sponsored': internal_id in SPONSORED,
            'sponsor_info': SPONSORED.get(internal_id),
        }
        if internal_id in LEGEND_SET:
            # 传奇品质装备：剔除 mod 内部机制属性（隐藏技能/替换技能/锻造ID），不展示给玩家
            rec['props'] = [p for p in rec['props']
                            if p['code'] not in ('oskill_hidden', 'oskill_replaceT', 'SmithID')]
            rec['legend'] = True            # 品质标记：网页端追加「传奇」橙色标签 + 标题橙色
            legend_records.append(rec)      # 传奇&混沌品质：进入独立页面数据
        else:
            uniques.append(rec)

# ---------- 类别覆盖：部分物品归到【普通】·【珠宝】 ----------
# 保卫者/守卫者/守护者 系列碎片（原护符类）与所有彩虹刻面，统一显示为「普通·珠宝」，
# 并从护符筛选中剥离（cat 由 charm 改 jewelry），由顶部【珠宝】按钮按 cat_zh 筛选。
OTHER_JEWEL_NAMES = {
    "Protector's Frost", "Protector's Stone",
    "Defender's Bile", "Defender's Fire",
    "Guardian's Light", "Guardian's Thunder",
    "Rainbow Facet",
}
for u in uniques:
    if u['name_en'] in OTHER_JEWEL_NAMES:
        u['tier_zh'] = '普通'
        u['cat_zh'] = '珠宝'
        if u['cat'] == 'charm':
            u['cat'] = 'jewelry'

# ---------- 写 CSV ----------
with open(p('resource/mod/uniques_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['name_en', 'name_zh', 'name_zh_tw', 'code', 'base_zh', 'cat', 'cat_zh',
                'subtype_zh', 'tier_zh', 'qlvl', 'req_lvl', 'version', 'sockets', 'img', 'sponsored', 'props'])
    for u in uniques:
        w.writerow([u['name_en'], u['name_zh'], u['name_zh_tw'], u['code'], u['base_zh'],
                    u['cat'], u['cat_zh'], u['subtype_zh'], u['tier_zh'], u['qlvl'], u['req_lvl'],
                    u['version'], u['sockets'], u['img'] or '', '1' if u['sponsored'] else '',
                    ' | '.join(x['text'] for x in u['props'])])

# ---------- 写传奇&混沌 CSV（同格式） ----------
with open(p('resource/mod/legend_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['name_en', 'name_zh', 'name_zh_tw', 'code', 'base_zh', 'cat', 'cat_zh',
                'subtype_zh', 'tier_zh', 'qlvl', 'req_lvl', 'version', 'sockets', 'img', 'sponsored', 'props'])
    for u in legend_records:
        w.writerow([u['name_en'], u['name_zh'], u['name_zh_tw'], u['code'], u['base_zh'],
                    u['cat'], u['cat_zh'], u['subtype_zh'], u['tier_zh'], u['qlvl'], u['req_lvl'],
                    u['version'], u['sockets'], u['img'] or '', '1' if u['sponsored'] else '',
                    ' | '.join(x['text'] for x in u['props'])])

# ---------- 写 JS ----------
js = '// 暗金装备数据（由 _build_unique_data.py 生成，请勿手动编辑）\n'
js += 'window.UNIQUE_ITEMS = ' + json.dumps(uniques, ensure_ascii=False, indent=1) + ';\n'
with open(p('js/unique-items.js'), 'w', encoding='utf-8') as f:
    f.write(js)
ljs = '// 传奇&混沌装备数据（由 _build_unique_data.py 生成，请勿手动编辑）\n'
ljs += 'window.LEGEND_ITEMS = ' + json.dumps(legend_records, ensure_ascii=False, indent=1) + ';\n'
with open(p('js/legend-items.js'), 'w', encoding='utf-8') as f:
    f.write(ljs)

# ---------- 报告 ----------
from collections import Counter
print('暗金装备总数:', len(uniques))
print('传奇&混沌装备数:', len(legend_records), [u['name_en'] for u in legend_records])
print('排除的特殊/随从暗金:', len(EXCLUDE_UNIQUE))
print('分类分布:', dict(Counter(u['cat_zh'] for u in uniques)))
print('档位分布:', dict(Counter(u['tier_zh'] or '无' for u in uniques)))
miss_name = [u['name_en'] for u in uniques if not u['name_zh']]
miss_img = [u['name_en'] for u in uniques if not u['img']]
miss_cat = [u['name_en'] for u in uniques if u['cat'] == 'weapon' and not u['type']]
ov_hit = [u['name_en'] for u in uniques
          if u['name_zh'] and not name2zh.get(u['name_en']) and not name2zh_runes.get(u['name_en'])]
print('经覆盖/备用字串表补名:', len(ov_hit), ov_hit)
print('缺中文名:', len(miss_name), miss_name)
print('缺图片:', len(miss_img), miss_img[:10])
print('含 sock 属性(有孔):', sum(1 for u in uniques if u['sockets']))
print('--- 抽查(武器/盾牌/头盔/衣服/首饰/护符) ---')
for cat in ('weapon', 'shield', 'helm', 'armor', 'jewelry', 'charm', 'ammo'):
    s = [u for u in uniques if u['cat'] == cat]
    if s:
        u = s[0]
        print('[%s] %s | %s | %s | Lv%s/req%s | %s' % (
            u['cat_zh'], u['name_en'], u['name_zh'], u['base_zh'], u['qlvl'], u['req_lvl'], u['img']))
        for x in u['props'][:4]:
            print('   ', x['text'])
