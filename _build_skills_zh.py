# -*- coding: utf-8 -*-
"""按用户的查找方法，把 skills.txt 中 skilldesc 列不为空的技能，
映射到其简体中文译名，输出 resource/skills_zh.csv。

查找链：
  skills.txt(skill, skilldesc) -> skilldesc.txt(skilldesc, str alt)
  -> skills.json(Key=str alt, zhCN)

CSV 列：技能(英文) | skilldesc | str_alt | 简体中文
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def p(rel):
    return os.path.join(ROOT, rel)


def read_tsv(path):
    with open(p(path), encoding='utf-8') as f:
        return [ln.split('\t') for ln in f.read().split('\n')]


# 1) skills.txt：取 (skill, skilldesc)，过滤 skilldesc 非空
sk_rows = read_tsv('resource/excel/skills.txt')
sk_head = sk_rows[0]
i_skill = sk_head.index('skill')
i_desc = sk_head.index('skilldesc')

skills = []  # (skill_name, skilldesc)
for cols in sk_rows[1:]:
    if not cols or not cols[0].strip():
        continue
    if len(cols) <= i_desc:
        continue
    name = cols[i_skill].strip()
    desc = cols[i_desc].strip()
    if desc:                       # 只保留 skilldesc 不为空
        skills.append((name, desc))

# 2) skilldesc.txt：skilldesc -> str alt
sd_rows = read_tsv('resource/excel/skilldesc.txt')
sd_head = sd_rows[0]
i_sd = sd_head.index('skilldesc')
i_alt = sd_head.index('str alt')
sd_map = {}
for cols in sd_rows[1:]:
    if not cols or not cols[0].strip():
        continue
    if len(cols) <= i_alt:
        continue
    key = cols[i_sd].strip()
    alt = cols[i_alt].strip()
    if key:
        sd_map[key] = alt

# 3) skills.json：Key -> zhCN
data = json.load(open(p('resource/string/skills.json'), encoding='utf-8'))
key2zh = {}
for x in data:
    k = x.get('Key', '')
    zh = (x.get('zhCN') or '').strip()
    if k:
        key2zh[k] = zh

# 4) 组装
out = []
unmatched = []
no_alt = []
for name, desc in skills:
    alt = sd_map.get(desc, '')
    zh = key2zh.get(alt, '').strip() if alt else ''
    if not alt:
        no_alt.append((name, desc))
    if not zh:
        unmatched.append((name, desc, alt))
    out.append((name, desc, alt, zh))

# 写出 CSV（utf-8-sig 让 Excel 中文不乱码）
with open(p('resource/skills_zh.csv'), 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['技能(英文)', 'skilldesc', 'str_alt', '简体中文'])
    for row in out:
        w.writerow(row)

total = len(out)
matched = sum(1 for r in out if r[3])
print('skills.txt 中 skilldesc 非空技能总数: %d' % total)
print('成功匹配简体中文: %d' % matched)
print('未匹配(缺 zhCN): %d' % len(unmatched))
print('str alt 缺失: %d' % len(no_alt))
print('输出: resource/skills_zh.csv')

# 打印示例（Fire Ball）与未匹配清单供核对
print('\n--- 示例(应含 Fire Ball -> 火球术) ---')
for r in out:
    if r[0] == 'Fire Ball':
        print(r)

if unmatched:
    print('\n--- 未匹配清单 (skill | skilldesc | str_alt) ---')
    for u in unmatched:
        print(u)
if no_alt:
    print('\n--- str alt 缺失清单 (skill | skilldesc) ---')
    for n in no_alt:
        print(n)
