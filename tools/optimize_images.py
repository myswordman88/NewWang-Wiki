#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片体积优化脚本（WebP / AVIF，尽量不降画质）
用法:
  python optimize_images.py <源目录> [--out <输出目录>] [--mode lossless|webp|avif|keep] [--quality 92]

  --mode lossless : WebP 无损（画质逐像素一致，默认，最贴合"不降画质"）
  --mode webp     : WebP 有损（--quality 控制，默认 92，肉眼基本无损）
  --mode avif     : AVIF（体积最小，老浏览器需回退）
  --mode keep     : 保持原格式，仅重新打包/清元数据（PNG/JPEG 无损优化）

输出: 在 --out 目录下生成同名的优化文件（无损/有损 WebP 为 .webp，AVIF 为 .avif，
keep 模式覆盖回原格式），并打印 压缩前/后 体积对比表。
"""
import argparse
import os
import sys
from PIL import Image

SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}
# 动图(gif)默认跳过，避免丢帧


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} TB"


def convert(img, dst, mode, quality):
    if mode == "lossless":
        img.save(dst, "WEBP", lossless=True, method=6, quality=100)
    elif mode == "webp":
        img.save(dst, "WEBP", lossless=False, method=6, quality=quality)
    elif mode == "avif":
        img.save(dst, "AVIF", quality=quality)
    elif mode == "keep":
        ext = os.path.splitext(dst)[1].lower()
        fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}.get(ext.lstrip("."), "PNG")
        save_kwargs = {}
        if fmt == "JPEG":
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            save_kwargs = {"optimize": True, "quality": quality, "progressive": True}
        elif fmt == "PNG":
            save_kwargs = {"optimize": True}
        img.save(dst, fmt, **save_kwargs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="源图片目录")
    ap.add_argument("--out", default=None, help="输出目录（默认 <源目录>/../assets）")
    ap.add_argument("--mode", default="lossless", choices=["lossless", "webp", "avif", "keep"])
    ap.add_argument("--quality", type=int, default=92, help="有损模式质量 0-100")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out) if args.out else os.path.join(os.path.dirname(src), "assets")
    os.makedirs(out, exist_ok=True)

    rows = []
    total_before = total_after = 0
    for name in sorted(os.listdir(src)):
        ext = os.path.splitext(name)[1].lower()
        if ext not in SUPPORTED:
            continue
        sp = os.path.join(src, name)
        try:
            with Image.open(sp) as im:
                im.load()
                base = os.path.splitext(name)[0]
                if args.mode == "keep":
                    dst = os.path.join(out, name)
                elif args.mode == "avif":
                    dst = os.path.join(out, base + ".avif")
                else:
                    dst = os.path.join(out, base + ".webp")
                convert(im, dst, args.mode, args.quality)
        except Exception as e:
            print(f"[跳过] {name}: {e}", file=sys.stderr)
            continue
        b = os.path.getsize(sp)
        a = os.path.getsize(dst)
        total_before += b
        total_after += a
        pct = (1 - a / b) * 100 if b else 0
        rows.append((name, b, a, pct))

    print(f"\n模式: {args.mode}  | 输出目录: {out}\n")
    print(f"{'文件名':<40}{'压缩前':>10}{'压缩后':>10}{'节省':>8}")
    print("-" * 70)
    for name, b, a, pct in rows:
        print(f"{name:<40}{human(b):>10}{human(a):>10}{pct:>7.1f}%")
    if rows:
        print("-" * 70)
        tot_pct = (1 - total_after / total_before) * 100 if total_before else 0
        print(f"{'合计':<40}{human(total_before):>10}{human(total_after):>10}{tot_pct:>7.1f}%")


if __name__ == "__main__":
    main()
