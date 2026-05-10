import sys
import argparse
import cv2
import numpy as np
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("image")
parser.add_argument("--minarea",    type=float, default=100)
parser.add_argument("--epsilon",    type=float, default=0.002)
parser.add_argument("--mode",       choices=["otsu", "canny"], default="otsu")
parser.add_argument("--canny-low",  type=int, default=50)
parser.add_argument("--canny-high", type=int, default=150)
args = parser.parse_args()

input_path = Path(args.image)
OUTPUT = f"vect/{input_path.stem}.txt"

raw = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
if raw is None:
    print(f"Image not found: {input_path}")
    sys.exit(1)

if len(raw.shape) == 3 and raw.shape[2] == 4:
    gray = raw[:, :, 3]
else:
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY) if len(raw.shape) == 3 else raw

if args.mode == "canny":
    binary = cv2.Canny(gray, args.canny_low, args.canny_high)
else:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

COORD_MAX = 16384
h, w = raw.shape[:2]
scale_x = COORD_MAX / (w - 1) if w > 1 else 1
scale_y = COORD_MAX / (h - 1) if h > 1 else 1

def scale_pt(x, y):
    return int(round(x * scale_x)), int(round(y * scale_y))

Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)

all_pts = []
with open(OUTPUT, "w") as f:
    f.write(f"# {w} {h}\n")
    for cnt in contours:
        if cv2.contourArea(cnt) < args.minarea:
            continue
        epsilon = args.epsilon * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        pts = [scale_pt(x, y) for x, y in approx.reshape(-1, 2)]
        pts.append(pts[0])
        all_pts.extend(pts)
        coords = " ,".join(f"{x},{y}" for x, y in pts)
        f.write(f"[{coords} ]\n")

n_paths = sum(1 for line in open(OUTPUT) if not line.startswith('#'))
n_vect  = len(all_pts)
if all_pts:
    xs, ys  = zip(*all_pts)
    print(f"paths   : {n_paths}")
    print(f"vectors : {n_vect}")
    print(f"x       : {min(xs)} .. {max(xs)}")
    print(f"y       : {min(ys)} .. {max(ys)}")
else:
    print("no contours found")
