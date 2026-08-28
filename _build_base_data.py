# -*- coding: utf-8 -*-
"""从 armor.txt + objects.json 生成干净的基底装备数据：
- 按 type 分组为大类 category（头盔/铠甲/盾牌/手套/靴子/腰带）
- 按 objects.json 中文名上标映射 tier（¹=普通，²=扩展，³=精英）
- 排除空 code 与 M01-M09（召唤物专用，不在游戏中）
- 中文名取自 objects.json 官方本地化表 zhCN
输出：resource/mod/armor_zh.csv（干净版） + js/base-items.js（window.BASE_ITEMS）
"""
import csv, json, re, os

ROOT = os.path.dirname(os.path.abspath(__file__))
ARMOR = os.path.join(ROOT, "resource", "mod", "armor.txt")
OBJ = os.path.join(ROOT, "resource", "mod", "objects.json")
CSV_OUT = os.path.join(ROOT, "resource", "mod", "armor_zh.csv")
JS_OUT = os.path.join(ROOT, "js", "base-items.js")

# type -> 大类（分组，贴合暗黑核分类）
TYPE_GROUP = {
    "helm": "头盔", "circ": "头盔", "phlm": "头盔", "head": "盾牌", "grim": "盾牌",
    "tors": "铠甲", "pelt": "头盔",
    "shie": "盾牌", "ashd": "盾牌",
    "glov": "手套", "boot": "靴子", "belt": "腰带",
}
# objects.json 中文名上标 -> tier（¹=普通，²=扩展，³=精英）
SUP_MARK = {"\u00b9": "普通", "\u00b2": "扩展", "\u00b3": "精英"}
VERSION_MAP = {"0": "普通", "1": "扩展", "2": "精英", "100": "扩展"}

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
NPC_OUT = os.path.join(ROOT, "resource", "mod", "npcs.json")
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

# 图片映射：resource/sprite/items.json 是 [{code:{asset:"分类/文件名"}}, ...]
# 图片文件名 = asset 的 basename；多个 tier 的 code 可能共用同一张图（如 cap/xap/uap 都指向 cap_hat）
SPRITE_MAP = os.path.join(ROOT, "resource", "mod", "items.json")
EQUIP_WEBP_DIR = os.path.join(ROOT, "assets", "equipment")
IMG_REL = "assets/equipment/"

def load_item_map():
    """items.json -> {code: 图片文件名(不含扩展名)}。
    该文件混有 // 行注释和尾逗号，做容错解析。"""
    if not os.path.exists(SPRITE_MAP):
        return {}
    txt = open(SPRITE_MAP, encoding="utf-8").read()
    txt = re.sub(r"//[^\n]*", "", txt)          # 去掉行注释
    txt = re.sub(r",(\s*[}\]])", r"\1", txt)     # 去掉尾逗号
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

# 游戏显示用的装饰符号（如 ★），并非装备真实名称的一部分，统一剔除（含常见变形以防后续出现）
SYMBOL_STRIP = "★☆◆●◇■□▲▼►◄➤✦✧♦♣♥♠✪✯❖⬤⬛⬜➜✸"

def clean_zh(s):
    """去掉 Mod 本地化前缀标记（如 ㅱ¹ / ㆋ 等）与游戏显示装饰符号（★ 等），保留真实中文名。"""
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
with open(ARMOR, encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        code = (row.get("code") or "").strip()
        name_en = (row.get("name") or "").strip()
        if not code:
            continue  # 跳过空 code（含 Expansion 分隔行）
        if re.fullmatch(r"M0[1-9]", code):
            continue  # M01-M09 召唤物专用，忽略
        typ = (row.get("type") or "").strip()
        ver = (row.get("version") or "").strip()
        category = TYPE_GROUP.get(typ, typ or "?")
        obj = OBJMAP.get(code)
        zh = obj["zh"] if obj else ""
        tw = obj["tw"] if obj else ""
        tier = (obj["tier"] if obj and obj["tier"] else VERSION_MAP.get(ver, ver or "?"))
        name_zh = clean_zh(zh) if zh.strip() else name_en  # 回退英文名
        name_zh_tw = clean_zh(tw)
        dmin = parse_int(row.get("minac"))
        dmax = parse_int(row.get("maxac"))
        davg = round((dmin + dmax) / 2, 1) if (dmin or dmax) else 0
        dura = parse_int(row.get("durability"))
        reqstr = parse_int(row.get("reqstr"))
        qlvl = parse_int(row.get("level"))
        sockets = parse_int(row.get("gemsockets"))
        speed = parse_int(row.get("speed"))
        sp = (row.get("spelldescstr") or "").strip()
        sock3 = parse_sockets(NPC_MAP.get(sp)) if sp else None
        rows.append({
            "code": code,
            "name_en": name_en,
            "name_zh": name_zh,
            "name_zh_tw": name_zh_tw,
            "category": category,
            "type_raw": typ,
            "tier": tier,
            "durability": dura,
            "defense_min": dmin,
            "defense_max": dmax,
            "defense_avg": davg,
            "reqstr": reqstr,
            "qlvl": qlvl,
            "max_sockets": sockets,
            "sockets3": "/".join(sock3) if sock3 else "",
            "speed": speed,
            "img": resolve_img(code),
        })

# 首饰（护身符/戒指）不在 armor.txt 里，这里显式补上，避免套装卡片找不到图。重跑本脚本也会保留。
# 图片指向「原版随机变体图」：amulet.webp / ring.webp 是 mod 新增的固定图（已删除），
# 改回原版 amulet1.webp / ring1.webp；vip 仍走 items.json 默认映射（viper_amulet.webp）。
JEWELRY = {
    "amu": ("项链", "Amulet", "amulet1", "项链"),
    "rin": ("戒指", "Ring", "ring1", "戒指"),
    "vip": ("毒蛇项链", "Viper Amulet", "viper_amulet", "项链"),
}
have_codes = {r["code"] for r in rows}
for code, (zh, en, stem, cat) in JEWELRY.items():
    if code in have_codes:
        continue
    if stem:
        p = os.path.join(EQUIP_WEBP_DIR, stem + ".webp")
        img = (IMG_REL + stem + ".webp") if os.path.exists(p) else ""
    else:
        img = resolve_img(code)
    if not img:
        continue  # 没有对应 webp 则跳过（以后补图会自动生效）
    rows.append({
        "code": code,
        "name_en": en,
        "name_zh": zh,
        "name_zh_tw": zh,
        "category": cat,
        "type_raw": "",
        "tier": "普通",
        "durability": 0,
        "defense_min": 0,
        "defense_max": 0,
        "defense_avg": 0,
        "reqstr": 0,
        "qlvl": 0,
        "max_sockets": 0,
        "sockets3": "",
        "speed": 0,
        "img": img,
    })

# 写干净 CSV
fields = ["code", "name_en", "name_zh", "name_zh_tw", "category", "type_raw", "tier",
          "durability", "defense_min", "defense_max", "defense_avg", "reqstr", "qlvl", "max_sockets", "sockets3", "speed", "img"]
with open(CSV_OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# 写 JS 数据
os.makedirs(os.path.dirname(JS_OUT), exist_ok=True)
with open(JS_OUT, "w", encoding="utf-8") as f:
    f.write("// 自动生成：基底装备数据（来自 armor.txt + objects.json）\n")
    f.write("// 生成脚本 _build_base_data.py；M01-M09 召唤物装备已排除。\n")
    f.write("window.BASE_ITEMS = ")
    json.dump(rows, f, ensure_ascii=False, indent=1)
    f.write(";\n")

unmapped = [r["code"] for r in rows if r["name_zh"] == r["name_en"] and not (OBJMAP.get(r["code"]) or {}).get("zh", "").strip()]
print("总条目（已排除 M01-M09 与空 code）:", len(rows))
print("分类分布:", {c: sum(1 for r in rows if r["category"] == c) for c in dict.fromkeys(r["category"] for r in rows)})
print("级别分布:", {t: sum(1 for r in rows if r["tier"] == t) for t in dict.fromkeys(r["tier"] for r in rows)})
fb = [r["code"] for r in rows if not (OBJMAP.get(r["code"]) or {}).get("tier")]
print("tier 来自 version 回退（objects.json 无上标）条数:", len(fb), fb[:20])
print("中文名回退英文（objects.json 缺失）条数:", len(unmapped), unmapped[:10])
print("已配图（webp 存在）条数:", sum(1 for r in rows if r["img"]))
print("输出:", CSV_OUT)
print("输出:", JS_OUT)
