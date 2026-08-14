# -*- coding: utf-8 -*-
# 临时脚本：armor.txt + objects.json -> 中文对照 CSV
# 中文名取自 objects.json (Key==armor.code): zhCN=简中, zhTW=繁体
import csv, json, re

SRC = "assets/mod/armor.txt"
OBJ = "assets/mod/objects.json"
OUT = "assets/mod/armor_zh.csv"

def clean(s):
    if not s:
        return ""
    s = re.sub(r"ÿc[0-9]", "", s)            # 去掉 D2 颜色码 ÿc0..ÿc9
    s = re.sub(r"[^\u3400-\u9fffA-Za-z0-9 ]", "", s)  # 只留 中/英/数/空格
    return s.strip()

# 读本地化表
with open(OBJ, encoding="utf-8") as f:
    objs = json.load(f)
zh_map, tw_map = {}, {}
for o in objs:
    k = o.get("Key")
    if not k:
        continue
    zh_map[k] = clean(o.get("zhCN", ""))
    tw_map[k] = clean(o.get("zhTW", ""))

# 读 armor.txt（编码容错）
raw = open(SRC, "rb").read()
try:
    txt = raw.decode("utf-8")
except UnicodeDecodeError:
    txt = raw.decode("gb18030")
rows = list(csv.DictReader(txt.splitlines(), delimiter="\t"))

TYPE_ZH = {"helm": "头盔", "tors": "铠甲", "shld": "盾牌"}
TIER = {"0": "普通", "1": "扩展", "2": "精英"}

out, missing = [], []
for r in rows:
    name = (r.get("name") or "").strip()
    if not name:
        continue
    code = (r.get("code") or "").strip()
    dmin = (r.get("minac") or "").strip()
    dmax = (r.get("maxac") or "").strip()
    avg = ""
    if dmin and dmax:
        try:
            avg = str((int(dmin) + int(dmax)) // 2)
        except ValueError:
            pass
    zhv = zh_map.get(code, "")
    if not zhv:
        zhv = name + "[?]"
        missing.append(code)
    out.append({
        "code": code,
        "name_en": name,
        "name_zh": zhv,
        "name_zh_tw": tw_map.get(code, ""),
        "category": TYPE_ZH.get((r.get("type") or "").strip(), (r.get("type") or "").strip() + "[?]"),
        "tier": TIER.get((r.get("version") or "").strip(), (r.get("version") or "").strip()),
        "defense_min": dmin, "defense_max": dmax, "defense_avg": avg,
        "durability": (r.get("durability") or "").strip(),
        "reqstr": (r.get("reqstr") or "").strip(),
        "qlvl": (r.get("level") or "").strip(),
        "max_sockets": (r.get("gemsockets") or "").strip(),
    })

fields = ["code", "name_en", "name_zh", "name_zh_tw", "category", "tier",
          "defense_min", "defense_max", "defense_avg", "durability",
          "reqstr", "qlvl", "max_sockets"]
with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out)

print("解析行数:", len(out))
print("未匹配到中文名的 code 数:", len(missing), missing[:10])
# 校验 Helm(hlm) 是否正确映射
for o in out:
    if o["code"] == "hlm":
        print("校验 hlm ->", o["name_zh"], "/", o["name_zh_tw"], "|", o["name_en"])
    if o["code"] == "cap":
        print("校验 cap ->", o["name_zh"], "/", o["name_zh_tw"], "|", o["name_en"])
