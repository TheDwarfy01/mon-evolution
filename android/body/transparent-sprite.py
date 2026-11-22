#!/usr/bin/env python3
"""Remove the neutral studio backdrop from the TWO original IMC HD models.

The input is the pre-existing 1620x1440 WebP sprite (man left, woman right).
The models are not regenerated: segmentation only modifies alpha, preserving
photographic facial detail, the saved color controls and the exact crop.
"""
from pathlib import Path
import sys
import numpy as np
import cv2
from PIL import Image

source = Path(sys.argv[1] if len(sys.argv) > 1 else
              'android/source-1.6.114/app/src/main/assets/models-hq-v2.webp')
original = Image.open(source).convert('RGB')
if original.size != (1620, 1440):
    raise ValueError(f'Unexpected image format: {original.size}')

def cutout(rgb, model):
    h, w = rgb.shape[:2]
    xs, ys = np.meshgrid(np.arange(w, dtype=np.float32) / w,
                         np.arange(h, dtype=np.float32) / h)
    # Keep 0 = definite background and 3 = probable foreground for GrabCut.
    mask = np.full((h, w), cv2.GC_PR_BGD, dtype=np.uint8)
    border = (xs < .105) | (xs > .895) | (ys < .002) | (ys > .994)
    mask[border] = cv2.GC_BGD

    pixels = rgb.astype(np.float32)
    red, green, blue = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    mean = (red + green + blue) / 3
    chroma = pixels.max(axis=2) - pixels.min(axis=2)
    # Warm skin and very dark clothes/hair/shoes stand out sharply from the
    # low-saturation light-grey background. This is not a global white erase.
    warm = (red > green * 1.05) & (red > blue * 1.13) & ((red - green) > 10)
    foreground_color = (mean < 155) | (warm & ((red - green) > 12)) | (chroma > 25)
    plausible = (xs > .15) & (xs < .85) & (ys > .008) & (ys < .988)
    mask[plausible & foreground_color] = cv2.GC_PR_FGD

    # Conservative foreground seeds from anatomy, gated by pixel color: never
    # force light background into the mask between the two legs.
    cores = [
        (.43, .57, .085, .155),  # face
        (.45, .55, .27, .39),   # torso
        (.45, .55, .435, .49),  # abdomen / shirt
        (.35, .45, .69, .79),   # left leg
        (.55, .65, .69, .79),   # right leg
        (.34, .45, .94, .97),   # left shoe
        (.55, .66, .94, .97),   # right shoe
    ]
    for x1, x2, y1, y2 in cores:
        core = (xs >= x1) & (xs <= x2) & (ys >= y1) & (ys <= y2)
        mask[core & foreground_color] = cv2.GC_FGD

    cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, None,
                np.zeros((1, 65), dtype=np.float64),
                np.zeros((1, 65), dtype=np.float64),
                6, cv2.GC_INIT_WITH_MASK)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
                  1, 0).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n < 2:
        raise ValueError(f'{model}: person was not segmented')
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    alpha = np.where(labels == largest, 255, 0).astype(np.uint8)
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE,
                            np.ones((3, 3), np.uint8))
    alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8))
    alpha = cv2.GaussianBlur(alpha, (3, 3), .7)
    occupancy = float(np.mean(alpha) / 255)
    # Fail the build rather than shipping an invisible figure or old grey bg.
    if not (.13 < occupancy < .55):
        raise ValueError(f'{model}: invalid person occupancy {occupancy:.3f}')
    if int(alpha[0, 0]) > 8 or int(alpha[0, -1]) > 8:
        raise ValueError(f'{model}: background not transparent')
    if int(alpha[int(.30*h), int(.50*w)]) < 245:
        raise ValueError(f'{model}: the torso was lost')
    print(f'{model}: transparent cutout OK, coverage {occupancy:.1%}')
    return np.dstack([rgb, alpha])

full = np.array(original)
male = cutout(full[:, :810, :], 'Homme')
female = cutout(full[:, 810:, :], 'Femme')
sprite = Image.fromarray(np.concatenate((male, female), axis=1), 'RGBA')
sprite.save(source, 'WEBP', lossless=True, method=5)
verify = Image.open(source)
assert verify.size == (1620, 1440) and 'A' in verify.getbands()
assert verify.getpixel((0, 0))[3] < 8
assert verify.getpixel((1619, 0))[3] < 8
print(f'Two source-identical transparent models saved in {source} ({source.stat().st_size} bytes)')
