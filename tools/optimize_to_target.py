#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
有损压缩到接近目标体积（默认 100KB/张），用于截图类图片。
原理: 有损 WebP + 在必要时按比例缩小分辨率。牺牲少量清晰度换体积。
用法:
  python optimize_to_target.py <源目录> [--out <输出目录>] [--target 100] [--maxw 0]
    --target : 目标体积(KB)，默认 100
    --maxw   : 强制最长边不超过此像素(0=不限制，仅靠质量逼近)
"""
import argparse
import io
import os
from PIL import Image

SUPPORTED = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}


def human(n):
    for u in ("B", "KB", "MB"):
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024.0
    return f"{n:.1f} TB"


def encode(im, quality):
    buf = io.BytesIO()
    im.save(buf, "WEBP", lossless=False, method=6, quality=quality)
    return buf.getvalue()


def best_for(im, target):
    """在 95..35 间扫描质量，优先选'不超过目标且质量最高'，否则选最小体积。"""
    cand = [(len(encode(im, q)), q) for q in range(95, 30, -5)]
    under = [(s, q) for s, q in cand if s <= target]
    if under:
        return max(under, key=lambda x: x[1])
    return min(cand, key=lambda x: x[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=None)
    ap.add_argument("--target", type=float, default=100)
    ap.add_argument("--maxw", type=int, default=0)
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    out = os.path.abspath(args.out) if args.out else os.path.join(os.path.dirname(src), "assets")
    os.makedirs(out, exist_ok=True)
    target = args.target * 1024

    print(f"目标: {args.target:.0f}KB/张 | 输出: {out}\n")
    print(f"{'文件名':<36}{'原图':>9}{'结果':>9}{'质量':>6}{'缩放':>7}")
    print("-" * 68)
    for name in sorted(os.listdir(src)):
        ext = os.path.splitext(name)[1].lower()
        if ext not in SUPPORTED:
            continue
        sp = os.path.join(src, name)
        original = os.path.getsize(sp)
        with Image.open(sp) as im:
            im.load()
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")  # 有损 webp 不需要 alpha，转 RGB 更小
            scale = 1.0
            size, quality = best_for(im, target)
            # 若仅靠质量仍超目标太多，按比例缩小再试
            while size > target * 1.15 and (args.maxw == 0 or max(im.size) * scale > args.maxw):
                scale *= 0.9
                w, h = im.size
                r = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
                size, quality = best_for(r, target)
            base = os.path.splitext(name)[0]
            dst = os.path.join(out, base + ".webp")
            with open(dst, "wb") as f:
                f.write(encode(im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS) if scale < 1 else im, quality))
        pct = (1 - size / original) * 100
        print(f"{name:<36}{human(original):>9}{human(size):>9}{quality:>5}d{scale:<7.2f}")


if __name__ == "__main__":
    main()
