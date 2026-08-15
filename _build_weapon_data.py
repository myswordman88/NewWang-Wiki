# -*- coding: utf-8 -*-
"""从 weapons.txt + objects.json 生成干净的武器数据：
- 与 armor_zh.csv 高度对齐：基础属性为伤害（mindam/maxdam）而非防御
- 武器独有列：speed（攻击速度，负值=越快）、rangeadder（攻击距离加成）、reqdex（需求敏捷）
- tier 来自 objects.json 中文名上标（¹=普通，²=扩展，³=精英）
- 孔数三档来自 npcs.json spelldescstr -> zhTW 的 [BD…] 段
- 排除空 code 与 Expansion 分隔行（name 为空或 type 为空）
- 中文名取自 objects.json 官方本地化表 zhCN
输出：assets/mod/weapons_zh.csv（干净版，utf-8-sig） + js/weapon-items.js（window.WEAPON_ITEMS）
"""
import csv, json, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
WEAPON = os.path.join(ROOT, "assets", "mod", "weapons.txt")
OBJ = os.path.join(ROOT, "assets", "mod", "objects.json")
NPC_OUT = os.path.join(ROOT, "assets", "mod", "npcs.json")
CSV_OUT = os.path.join(ROOT, "assets", "mod", "weapons_zh.csv")
JS_OUT = os.path.join(ROOT, "js", "weapon-items.js")

# type -> 大类（分组，贴近暗黑2常规译名；亚马逊变体并入对应大类）
TYPE_GROUP = {
    "swor": "剑", "axe": "斧", "bow": "弓", "pole": "长柄武器", "staf": "法杖",
    "knif": "匕首", "jave": "标枪", "spea": "长矛", "orb": "法球", "wand": "魔杖",
    "xbow": "弩", "mace": "钉头锤", "hamm": "锤", "h2h2": "拳套", "h2h": "拳套",
    "scep": "权杖", "club": "棍棒", "tkni": "飞刀", "taxe": "投掷斧", "tpot": "投掷武器",
    "abow": "弓", "aspe": "长矛", "ajav": "标枪", "mboq": "弓", "mxbq": "十字弓",
}
# objects.json 中文名上标 -> tier（¹=普通，²=扩展，³=精英）
SUP_MARK = {"\u00b9": "普通", "\u00b2": "扩展", "\u00b3": "精英"}
VERSION_MAP = {"0": "普通", "1": "扩展", "2": "精英", "100": "扩展"}
# 任务物品 / 不参与资料站展示的武器 code（如图腾、剧情道具），从源头排除
EXCLUDE_CODES = {
    "hdm", "hfh",          # 赫拉迪姆之锤、地狱熔炉之锤（剧情锤）
    "qf1", "qf2",          # Khalim's Flail、Khalim's Will（任务钉头锤）
    "leg",                 # Wirt's Leg（维特的腿，合成红门任务物）
    "w01", "w02",          # Minions Knife 1/2（mod 召唤物专用匕首）
    "d33", "g33",          # Decoy Gidbinn、The Gidbinn（匕首任务物）
    "hst", "msf",          # Horadric Staff、Staff of Kings（法杖任务物）
}
# 整类排除的 type（不参与资料站展示）
EXCLUDE_TYPES = {"tpot"}   # 投掷武器（投掷药水等，非装备）
# 指定中文名 / 改类的特殊条目（code -> 覆盖字段）
OVERRIDES = {
    "aq0": {"category": "其他", "name_zh": "弓箭", "name_zh_tw": "弓箭"},   # Magic Arrows
    "cq0": {"category": "其他", "name_zh": "弩失", "name_zh_tw": "弩失"},   # Magic Bolts（按用户给定名）
}

def tier_from_zh(zh):
    """从 objects.json 中文名里检测上标 ¹²³，返回 普通/扩展/精英；无则空。"""
    for ch, t in SUP_MARK.items():
        if ch in (zh or ""):
            return t
    return ""

def load_objects():
    with open(OBJ, encoding="utf-8") as f:
        data = json.load(f)
    m = {}
    if isinstance(data, list):
        for item in data:
            key = item.get("Key")
            if key:
                zh = item.get("zhCN", "") or ""
                m[key] = {"zh": zh, "tw": item.get("zhTW", "") or "", "tier": tier_from_zh(zh)}
    elif isinstance(data, dict):
        sample = next(iter(data.values())) if data else None
        if isinstance(sample, dict) and "Key" in sample:
            for v in data.values():
                key = v.get("Key")
                if key:
                    zh = v.get("zhCN", "") or ""
                    m[key] = {"zh": zh, "tw": v.get("zhTW", "") or "", "tier": tier_from_zh(zh)}
        else:
            for k, v in data.items():
                if isinstance(v, dict):
                    zh = v.get("zhCN", "") or ""
                    m[k] = {"zh": zh, "tw": v.get("zhTW", "") or "", "tier": tier_from_zh(zh)}
                else:
                    m[k] = {"zh": str(v), "tw": "", "tier": ""}
    return m

OBJMAP = load_objects()

# npcs.json：spelldescstr 值 -> zhTW（含三档孔数描述的本地化文本）
def load_npcs():
    with open(NPC_OUT, encoding="utf-8") as f:
        data = json.load(f)
    m = {}
    for it in data:
        key = it.get("Key")
        if key:
            m[key] = it.get("zhTW", "") or ""
    return m
NPC_MAP = load_npcs()

# D2 颜色码 ÿcN（ÿ=U+00FF，后跟一个字符）在 npcs 描述文本里，须剔除
FF = "\u00ff"
def parse_sockets(zhtw):
    """从 npcs.json 的 spelldescstr zhTW 解析三档（普通/扩展/精英）最大孔数。
    例 '[BDS:8-11/2]' -> ['2','2','2']；'[BDÿc1Sÿc5:2-3/ÿc11-2-4ÿc5]' -> ['1','2','4']。
    '/' 之后为孔数段：单数字=三档相同，'a-b-c'=普通/扩展/精英。返回 ['a','b','c'] 或 None。"""
    if not zhtw:
        return None
    s = re.sub(FF + r"c.", "", zhtw)        # 去掉颜色码 ÿcN
    m = re.search(r"\[BD[^\]]*\]", s)
    seg = m.group(0) if m else s
    after = seg.split("/")[-1] if "/" in seg else seg
    after = re.sub(r"[^0-9\-]", "", after)  # 仅留数字与短横线
    if not after:
        return None
    parts = [p for p in after.split("-") if p != ""]
    if len(parts) == 1:
        return [parts[0], parts[0], parts[0]]
    if len(parts) == 3:
        return parts
    return [parts[0], parts[0], parts[0]]

# 图片映射：assets/sprite/items.json 是 [{code:{asset:"分类/文件名"}}, ...]
SPRITE_MAP = os.path.join(ROOT, "assets", "sprite", "items.json")
EQUIP_WEBP_DIR = os.path.join(ROOT, "assets", "equipment")
IMG_REL = "assets/equipment/"

def load_item_map():
    """items.json -> {code: 图片文件名(不含扩展名)}。容错解析 // 与尾逗号。"""
    if not os.path.exists(SPRITE_MAP):
        return {}
    txt = open(SPRITE_MAP, encoding="utf-8").read()
    txt = re.sub(r"//[^\n]*", "", txt)
    txt = re.sub(r",(\s*[}\]])", r"\1", txt)
    try:
        data = json.loads(txt)
    except Exception as e:
        print("[warn] items.json 解析失败:", e)
        return {}
    m = {}
    if isinstance(data, list):
        for d in data:
            if not isinstance(d, dict):
                continue
            for code, v in d.items():
                if isinstance(v, dict) and v.get("asset"):
                    m[code] = v["asset"].rsplit("/", 1)[-1]
    return m

ITEMMAP = load_item_map()

def resolve_img(code):
    """返回 webp 相对路径（图片已转换则），否则空串（以后补图时自动生效）。"""
    stem = ITEMMAP.get(code)
    if not stem:
        return ""
    p = os.path.join(EQUIP_WEBP_DIR, stem + ".webp")
    return (IMG_REL + stem + ".webp") if os.path.exists(p) else ""

# 游戏显示用的装饰符号（如 ★），并非武器真实名称的一部分，统一剔除
SYMBOL_STRIP = "★☆◆●◇■□▲▼►◄➤✦✧♦♣♥♠✪✯❖⬤⬛⬜➜✸"

def clean_zh(s):
    """去掉 Mod 本地化前缀标记与游戏显示装饰符号，保留真实中文名。"""
    s = (s or "").strip()
    m = re.match(r'^[^\u3400-\u4dbf\u4e00-\u9fff\s]+\s+(.*)$', s)
    s = m.group(1) if m else s
    s = re.sub("[" + re.escape(SYMBOL_STRIP) + "]", "", s)
    return s.strip()

def parse_int(s, default=0):
    s = (s or "").strip()
    try:
        return int(float(s))
    except ValueError:
        return default

rows = []
with open(WEAPON, encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        code = (row.get("code") or "").strip()
        name_en = (row.get("name") or "").strip()
        if not code:
            continue  # 跳过空 code（含 Expansion 分隔行）
        if code in EXCLUDE_CODES:
            continue  # 跳过任务物品 / 不参与资料站展示的武器
        typ = (row.get("type") or "").strip()
        if not typ:
            continue  # 跳过无 type 的分隔行
        if typ in EXCLUDE_TYPES:
            continue  # 跳过整类排除的武器（如投掷武器）
        ver = (row.get("version") or "").strip()
        category = TYPE_GROUP.get(typ, typ or "?")
        obj = OBJMAP.get(code)
        zh = obj["zh"] if obj else ""
        tw = obj["tw"] if obj else ""
        tier = (obj["tier"] if obj and obj["tier"] else VERSION_MAP.get(ver, ver or "?"))
        name_zh = clean_zh(zh) if zh.strip() else name_en  # 回退英文名
        name_zh_tw = clean_zh(tw)
        # 基础伤害按 主手(mindam) → 双手(2handmindam) → 投掷(minmisdam) 取第一档非空
        dmin = dmax = 0
        for cmin, cmax in (("mindam", "maxdam"), ("2handmindam", "2handmaxdam"), ("minmisdam", "maxmisdam")):
            vmin = (row.get(cmin) or "").strip()
            vmax = (row.get(cmax) or "").strip()
            if vmin or vmax:
                dmin = parse_int(vmin)
                dmax = parse_int(vmax)
                break
        davg = round((dmin + dmax) / 2, 1) if (dmin or dmax) else 0
        dura = parse_int(row.get("durability"))
        reqstr = parse_int(row.get("reqstr"))
        reqdex = parse_int(row.get("reqdex"))
        qlvl = parse_int(row.get("level"))
        sockets = parse_int(row.get("gemsockets"))
        speed = parse_int(row.get("speed"))
        rangeadder = parse_int(row.get("rangeadder"))
        sp = (row.get("spelldescstr") or "").strip()
        sock3 = parse_sockets(NPC_MAP.get(sp)) if sp else None
        item = {
            "code": code,
            "name_en": name_en,
            "name_zh": name_zh,
            "name_zh_tw": name_zh_tw,
            "category": category,
            "type_raw": typ,
            "tier": tier,
            "durability": dura,
            "damage_min": dmin,
            "damage_max": dmax,
            "damage_avg": davg,
            "reqstr": reqstr,
            "reqdex": reqdex,
            "qlvl": qlvl,
            "max_sockets": sockets,
            "sockets3": "/".join(sock3) if sock3 else "",
            "speed": speed,
            "rangeadder": rangeadder,
            "img": resolve_img(code),
        }
        if code in OVERRIDES:
            item.update(OVERRIDES[code])
        rows.append(item)

# 写干净 CSV（utf-8-sig 让 Excel 双击不乱码）
fields = ["code", "name_en", "name_zh", "name_zh_tw", "category", "type_raw", "tier",
          "durability", "damage_min", "damage_max", "damage_avg", "reqstr", "reqdex",
          "qlvl", "max_sockets", "sockets3", "speed", "rangeadder", "img"]
with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# 写 JS 数据（供后续页面接线）
os.makedirs(os.path.dirname(JS_OUT), exist_ok=True)
with open(JS_OUT, "w", encoding="utf-8") as f:
    f.write("// 自动生成：武器基底数据（来自 weapons.txt + objects.json）\n")
    f.write("// 生成脚本 _build_weapon_data.py；基础伤害取 mindam/maxdam（主手/单手伤害）。\n")
    f.write("window.WEAPON_ITEMS = ")
    json.dump(rows, f, ensure_ascii=False, indent=1)
    f.write(";\n")

unmapped = [r["code"] for r in rows if r["name_zh"] == r["name_en"] and not (OBJMAP.get(r["code"]) or {}).get("zh", "").strip()]
print("武器总条目:", len(rows))
print("分类分布:", {c: sum(1 for r in rows if r["category"] == c) for c in dict.fromkeys(r["category"] for r in rows)})
print("级别分布:", {t: sum(1 for r in rows if r["tier"] == t) for t in dict.fromkeys(r["tier"] for r in rows)})
fb = [r["code"] for r in rows if not (OBJMAP.get(r["code"]) or {}).get("tier")]
print("tier 来自 version 回退条数:", len(fb), fb[:20])
print("中文名回退英文（objects.json 缺失）条数:", len(unmapped), unmapped[:10])
print("已配图（webp 存在）条数:", sum(1 for r in rows if r["img"]))
print("输出 CSV:", CSV_OUT)
print("输出 JS :", JS_OUT)
