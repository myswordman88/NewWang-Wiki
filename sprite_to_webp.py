#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将暗黑2重制版(D2R)的 .sprite 文件 (SpA1 格式, 未压缩 RGBA8888) 转换为压缩的 webp。

格式说明（实测自 assets/sprite 下样本）:
  - 字节 0-3 : 魔数 "SpA1"
  - 字节 6-7 : 宽 (uint16 LE)
  - 字节 8-9 : 高 (uint16 LE)
  - 字节 40+ : 像素数据, RGBA8888, 行优先, 长度 = w*h*4

用法:
  python sprite_to_webp.py [源目录] [输出目录]
默认: 源=assets/sprite  输出=assets/equipment

特性:
  - 递归扫描源目录（支持 assets/sprite/helmet/ 这类按分类分子目录的布局）
  - 自动跳过 .lowend.sprite（低模占位，非成品图标）
  - 自动跳过非 SpA1 文件
  - 输出 webp (quality=85, 保留透明通道) 到输出目录，文件名=原 sprite 的 stem（不含分类前缀）
  - 同时输出 _preview/*.png 供人工核对 (确认后可删)
  - 打印压缩前后体积对比
"""
import os
import sys
import struct
import glob
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "assets/sprite"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/equipment"
PRE = os.path.join(OUT, "_preview")
WEBP_QUALITY = 85


def convert_one(path):
    b = open(path, "rb").read()
    if b[:4] != b"SpA1":
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
        stem = os.path.splitext(os.path.basename(path))[0]
        wp = os.path.join(OUT, stem + ".webp")
        pp = os.path.join(PRE, stem + ".png")
        img.save(wp, "WEBP", quality=WEBP_QUALITY, method=6)
        img.save(pp, "PNG")
        sz_in = os.path.getsize(path)
        sz_out = os.path.getsize(wp)
        return (stem, w, h, sz_in, sz_out), None
    except Exception as e:
        return None, f"转换失败({type(e).__name__}:{e})"


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PRE, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SRC, "**", "*.sprite"), recursive=True))
    # 跳过 .lowend.sprite（低模占位图，非成品图标）
    files = [f for f in files if not os.path.basename(f).endswith(".lowend.sprite")]
    print(f"源目录: {SRC}  输出: {OUT}")
    print(f"待转换 .sprite 文件(已跳过 .lowend): {len(files)}\n")
    total_in = total_out = 0
    ok = 0
    for f in files:
        res, err = convert_one(f)
        if err:
            print(f"  [!] {os.path.basename(f)}: {err}")
            continue
        stem, w, h, sz_in, sz_out = res
        total_in += sz_in
        total_out += sz_out
        ok += 1
        print(f"  [OK] {stem}: {w}x{h}  sprite {sz_in//1024}KB -> webp {sz_out//1024}KB ({sz_out/sz_in:.1%})")
    print(f"\n转换完成: {ok} 个")
    if total_in:
        print(f"合计体积: {total_in//1024}KB -> {total_out//1024}KB, 压缩率 {total_out/total_in:.1%}")


if __name__ == "__main__":
    main()
