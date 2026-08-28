#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 resource/sprite/rune/ 下的 33 个符文 .sprite（SpA1 格式）转换为 webp，
按 r01~r33 命名输出到 assets/runes/，供符文之语页面直接 <img> 引用。
同时输出 resource/equipment_preview/rune_<rNN>.png 供人工核对（确认后可删）。

英文名 -> rNN 映射取自 resource/mod/objects.json（与 _build_rune_data.py 的 code2rune 同源），
sprite 文件名形如 {en_lower}_rune.sprite（如 el_rune.sprite）。
"""
import os
import re
import struct
import glob
import json
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SPRITE_DIR = os.path.join(ROOT, "resource/sprite/rune")
OBJ = os.path.join(ROOT, "resource/mod/objects.json")
OUT_WEBP = os.path.join(ROOT, "assets/runes")
OUT_PNG = os.path.join(ROOT, "resource/equipment_preview")
WEBP_QUALITY = 90
WEBP_METHOD = 6


def clean_rune(s):
    if not s:
        return ""
    s = re.sub(r"ÿc.", "", s)
    s = s.replace("ㅪ", "").replace("★", "").replace("-", "")
    s = re.sub(r"\s+", "", s)
    m = re.search(r"符文：([^A-Za-z]+)", s)
    return m.group(1) if m else s


def build_code2rune():
    obj = json.load(open(OBJ, encoding="utf-8-sig"))
    m = {}
    for x in obj:
        k = str(x.get("Key", "")).lower()
        if re.match(r"^r\d+$", k):
            en = re.search(r"([A-Za-z]+)\s*Rune", x.get("enUS", ""))
            m[k] = (en.group(1) if en else "").lower()
    return m


def convert_one(path, out_webp, out_png):
    b = open(path, "rb").read()
    if b[:4] not in (b"SpA1", b"SPa1"):
        return None, "跳过(非SpA1)"
    w = struct.unpack("<H", b[6:8])[0]
    h = struct.unpack("<H", b[12:14])[0]
    off = 40
    need = w * h * 4
    px = b[off:off + need]
    if len(px) < need:
        return None, f"像素区不足(需{need}, 实{len(px)})"
    try:
        img = Image.frombytes("RGBA", (w, h), px)
        img.save(out_webp, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
        img.save(out_png, "PNG")
        return (w, h, os.path.getsize(path), os.path.getsize(out_webp)), None
    except Exception as e:
        return None, f"转换失败({type(e).__name__}:{e})"


def main():
    code2rune = build_code2rune()
    os.makedirs(OUT_WEBP, exist_ok=True)
    os.makedirs(OUT_PNG, exist_ok=True)

    # 仅取 r01..r33 且英文名能对应到 sprite 文件者
    codes = sorted([c for c in code2rune if re.match(r"^r\d+$", c)],
                   key=lambda c: int(re.search(r"\d+", c).group()))
    print(f"映射符文数: {len(codes)}")

    total_in = total_out = 0
    ok = 0
    missing = []
    for c in codes:
        en = code2rune[c]
        sp = os.path.join(SPRITE_DIR, f"{en}_rune.sprite")
        if not os.path.exists(sp):
            missing.append((c, en))
            print(f"  [!] {c} <- {en}_rune.sprite 不存在")
            continue
        wp = os.path.join(OUT_WEBP, f"{c}.webp")
        pp = os.path.join(OUT_PNG, f"rune_{c}.png")
        res, err = convert_one(sp, wp, pp)
        if err:
            print(f"  [!] {c}: {err}")
            continue
        w, h, sz_in, sz_out = res
        total_in += sz_in
        total_out += sz_out
        ok += 1
        if ok <= 3 or c in ("r33",):
            print(f"  [OK] {c} ({en}): {w}x{h}  sprite {sz_in//1024}KB -> webp {sz_out//1024}KB ({sz_out/sz_in:.1%})")
    if missing:
        print(f"\n缺失 {len(missing)} 个: {missing}")
    print(f"\n转换完成: {ok}/{len(codes)}")
    if total_in:
        print(f"合计体积: {total_in//1024}KB -> {total_out//1024}KB, 压缩率 {total_out/total_in:.1%}")


if __name__ == "__main__":
    main()
