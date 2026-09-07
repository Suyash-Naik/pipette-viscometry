"""Generate synthetic aspiration curves matching the structure of the real
`Graph series00N BF.csv` test data (frame,microns; microns quantized to the
camera pixel scale). Trend shape is the same -- baseline, sharp aspiration
jump, viscoelastic relaxation dip, slow creep, release drop, slow retraction
-- but the values are independent of the originals.
"""
import csv
import random
from pathlib import Path

PX_UM = 0.8664456  # micron-per-pixel scale inferred from the real recordings
OUT = Path(__file__).resolve().parents[0]


def interp(anchors, n):
    """Piecewise-linear interpolation through (frame, pixels) anchors."""
    out = []
    for f in range(n):
        for (f0, v0), (f1, v1) in zip(anchors, anchors[1:]):
            if f0 <= f <= f1:
                t = 0.0 if f1 == f0 else (f - f0) / (f1 - f0)
                out.append(v0 + t * (v1 - v0))
                break
        else:
            out.append(anchors[-1][1])
    return out


def quantize(curve, rng, jitter=0.18, max_step=2):
    """Round to whole pixels with tracking jitter, capping the frame-to-frame
    step in the slow phases the way the real segmentation output does."""
    px = []
    for i, v in enumerate(curve):
        p = round(v + rng.gauss(0, jitter))
        if px:
            slope = abs(curve[i] - curve[i - 1])
            cap = max(max_step, round(slope) + 1)
            p = max(px[-1] - cap, min(px[-1] + cap, p))
        px.append(max(1, p))
    return px


def write(name, anchors, n, seed, glitch=None):
    rng = random.Random(seed)
    px = quantize(interp(anchors, n), rng)
    if glitch:  # transient tracking dropout, as seen in series002 @ frame 158
        f, drop = glitch
        px[f] -= drop
        px[f + 1] -= drop - rng.randint(2, 4)
    path = OUT / name
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["frame", "microns"])
        for f, p in enumerate(px):
            w.writerow([f, f"{p * PX_UM:.4f}"])
    print(f"{name}: n={n} px min={min(px)} max={max(px)} peak@{px.index(max(px))}")


# series003: single sustained creep, shorter run than the originals
write(
    "Graph series003 BF.csv",
    [(0, 3), (5, 4), (6, 17), (9, 27), (16, 38), (24, 40), (34, 37),
     (48, 38), (150, 74), (160, 73), (190, 41), (205, 34), (235, 21),
     (267, 12)],
    268,
    seed=20260906,
)

# series004: double relaxation dip and a longer creep, like series002
write(
    "Graph series004 BF.csv",
    [(0, 6), (4, 6), (5, 16), (8, 26), (14, 36), (22, 43), (40, 31),
     (58, 33), (104, 51), (128, 53), (150, 45), (176, 47), (300, 72),
     (310, 71), (340, 44), (360, 38), (390, 22)],
    391,
    seed=771203,
    glitch=(148, 15),
)
