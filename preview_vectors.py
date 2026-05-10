import sys
import re
import math
import argparse
import cv2
import numpy as np
from pathlib import Path

NAMED_COLORS = {
    "green":    (0, 255, 0),
    "red":      (0, 0, 255),
    "white":    (255, 255, 255),
    "fuchsia":  (255, 0, 255),
    "orange":   (0, 165, 255),
    "rainbow":  None,
}
DEFAULT_COLOR = (0, 0, 255)
TIP_PX = 10
TIP_ANGLE = math.radians(25)
COORD_MAX = 16384

parser = argparse.ArgumentParser()
parser.add_argument("vectors")
parser.add_argument("--size",  type=int, default=1200)
parser.add_argument("--color", default="red")
args = parser.parse_args()

def parse_file(path):
    paths = []
    orig_w = orig_h = None
    with open(path) as f:
        for line in f:
            if line.startswith('#'):
                m = re.match(r'#\s*(\d+)\s+(\d+)', line)
                if m:
                    orig_w, orig_h = int(m.group(1)), int(m.group(2))
                continue
            nums = list(map(int, re.findall(r'\d+', line)))
            pts = [(nums[i], nums[i+1]) for i in range(0, len(nums)-1, 2)]
            if len(pts) >= 2:
                paths.append(pts)
    return paths, orig_w, orig_h

def hsv_to_bgr(h, s, v):
    arr = np.uint8([[[int(h * 179), int(s * 255), int(v * 255)]]])
    bgr = cv2.cvtColor(arr, cv2.COLOR_HSV2BGR)[0][0]
    return (int(bgr[0]), int(bgr[1]), int(bgr[2]))

def rainbow_colors(n):
    PHI = 0.618033988749895
    colors = []
    h = 0.0
    for _ in range(n):
        colors.append(hsv_to_bgr(h, 1.0, 1.0))
        h = (h + PHI) % 1.0
    return colors

def draw_arrow(img, a, b, color, tip_px):
    cv2.line(img, a, b, color, 1, cv2.LINE_AA)
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    if length < 1:
        return
    dx, dy = (bx - ax) / length, (by - ay) / length
    w1x = bx - tip_px * (dx * math.cos(TIP_ANGLE) - dy * math.sin(TIP_ANGLE))
    w1y = by - tip_px * (dy * math.cos(TIP_ANGLE) + dx * math.sin(TIP_ANGLE))
    w2x = bx - tip_px * (dx * math.cos(TIP_ANGLE) + dy * math.sin(TIP_ANGLE))
    w2y = by - tip_px * (dy * math.cos(TIP_ANGLE) - dx * math.sin(TIP_ANGLE))
    cv2.line(img, b, (int(w1x), int(w1y)), color, 1, cv2.LINE_AA)
    cv2.line(img, b, (int(w2x), int(w2y)), color, 1, cv2.LINE_AA)

def draw(paths, out_path, orig_w, orig_h, min_short_side, color_arg):
    scale = max(min_short_side / min(orig_w, orig_h), 1.0)
    pad = int(30 * scale)
    w = int(orig_w * scale) + pad * 2
    h = int(orig_h * scale) + pad * 2
    img = np.zeros((h, w, 3), dtype=np.uint8)

    use_rainbow = color_arg is None
    colors = rainbow_colors(len(paths)) if use_rainbow else None

    for i, pts in enumerate(paths):
        color = colors[i] if use_rainbow else color_arg
        shifted = [
            (int(x / COORD_MAX * (orig_w - 1) * scale) + pad,
             int(y / COORD_MAX * (orig_h - 1) * scale) + pad)
            for x, y in pts
        ]
        for a, b in zip(shifted, shifted[1:]):
            draw_arrow(img, a, b, color, TIP_PX)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(out_path, img)
    print(f"Saved: {out_path}  ({w}x{h})")

color_name = args.color.lower()
if color_name not in NAMED_COLORS:
    print(f"Unknown color: {color_name}. Using red.")
    color_arg = DEFAULT_COLOR
else:
    color_arg = NAMED_COLORS[color_name]

stem = Path(args.vectors).stem
output_file = f"preview/{stem}.png"

paths, orig_w, orig_h = parse_file(args.vectors)
if orig_w is None or orig_h is None:
    print("Dimensions not found in vectors file. Regenerate with updated extract_contours.py.")
    sys.exit(1)

draw(paths, output_file, orig_w, orig_h, args.size, color_arg)
