"""Deterministic native-resolution bright/dark multiscale spot extraction."""

from __future__ import annotations
import math
from typing import Optional
import cv2
import numpy as np
from .types import Candidate, DetectorConfig


def normalize_pixels(image: np.ndarray) -> np.ndarray:
    if not isinstance(image, np.ndarray):
        raise TypeError("Pass a 2-D NumPy pixel array, not a filename or file object")
    if image.ndim != 2 or min(image.shape) < 24:
        raise ValueError("Expected a grayscale 2-D array at least 24 by 24 pixels")
    if image.dtype.kind not in "uif":
        raise TypeError("Pixels must have a real integer or floating-point dtype")
    a = image.astype(np.float64 if image.dtype.itemsize > 4 else np.float32, copy=True)
    if not np.isfinite(a).all():
        raise ValueError("Pixels must be finite")
    lo, hi = np.percentile(a, [1, 99.7])
    if hi <= lo:
        lo, hi = float(a.min()), float(a.max())
    if hi <= lo:
        return np.zeros(image.shape, dtype=np.float32)
    # Scale exceptionally large finite floats before subtraction to avoid overflow.
    if max(abs(float(lo)), abs(float(hi))) > 1e20:
        factor = max(abs(float(lo)), abs(float(hi)))
        a = a.astype(np.float64) / factor
        lo, hi = float(lo) / factor, float(hi) / factor
    return np.clip((a - lo) * (255.0 / (hi - lo)), 0, 255).astype(np.float32)


def find_candidates(
    image: np.ndarray, *, config: Optional[DetectorConfig] = None
) -> tuple[Candidate, ...]:
    cfg = config or DetectorConfig()
    g = normalize_pixels(image)
    h, w = g.shape
    if float(g.max()) == 0:
        return ()
    sf = min(h, w) / 1100.0
    raw = []
    edge = max(2, round(0.003 * min(h, w)))
    # Balance candidate opportunities across the film instead of selecting only the brightest text.
    for scale in cfg.scales:
        sigma = max(0.5, scale * sf)
        smooth = cv2.GaussianBlur(g, (0, 0), sigma)
        background = cv2.GaussianBlur(g, (0, 0), max(3.0, sigma * 5))
        dog = smooth - background
        radius = max(4, min(round(5 * sigma), max(4, round(28 * sf))))
        core = max(1, round(sigma))
        yy, xx = np.mgrid[-radius : radius + 1, -radius : radius + 1]
        rad = xx * xx + yy * yy
        inner = rad <= core * core
        ring = (rad >= (2 * core) ** 2) & (rad <= radius * radius)
        if not ring.any():
            continue
        for sign, polarity in ((1, "bright"), (-1, "dark")):
            response = sign * dog
            window = max(3, 2 * round(sigma) + 1)
            maxima = cv2.dilate(response, np.ones((window, window), np.uint8))
            for gy in range(3):
                for gx in range(3):
                    x0 = gx * w // 3
                    x1 = (gx + 1) * w // 3
                    y0 = gy * h // 3
                    y1 = (gy + 1) * h // 3
                    r = response[y0:y1, x0:x1]
                    ys, xs = np.where((r >= maxima[y0:y1, x0:x1] - 1e-6) & (r >= 2.0))
                    values = r[ys, xs]
                    order = np.lexsort((xs, ys, -values))[:40]
                    for j in order:
                        x = int(xs[j] + x0)
                        y = int(ys[j] + y0)
                        if min(x, y, w - 1 - x, h - 1 - y) < max(edge, radius):
                            continue
                        patch = g[
                            y - radius : y + radius + 1, x - radius : x + radius + 1
                        ]
                        base = float(np.median(patch[ring]))
                        contrast = sign * (float(np.mean(patch[inner])) - base)
                        if contrast < 2:
                            continue
                        noise = float(np.std(patch[ring]))
                        snr = contrast / (noise + 3.0)
                        sectors = [
                            float(np.median(patch[m & ring]))
                            for m in (xx > 0, xx < 0, yy > 0, yy < 0)
                        ]
                        asym = float(np.std(sectors)) / (contrast + 3.0)
                        weight = np.maximum(
                            sign * (patch - base) - contrast * 0.3, 0
                        ) * (rad <= (3 * core) ** 2)
                        mass = float(weight.sum())
                        if mass <= 0:
                            continue
                        cov = (
                            np.array(
                                [
                                    [
                                        (weight * xx * xx).sum(),
                                        (weight * xx * yy).sum(),
                                    ],
                                    [
                                        (weight * xx * yy).sum(),
                                        (weight * yy * yy).sum(),
                                    ],
                                ]
                            )
                            / mass
                        )
                        eig = np.linalg.eigvalsh(cov)
                        elong = float(eig[-1] / max(eig[0], 0.1))
                        score = (
                            (1 - math.exp(-contrast / 18.0))
                            * (1 - math.exp(-snr))
                            * math.exp(-0.3 * min(asym, 5.0))
                            / (1 + 0.3 * max(0.0, math.log(max(1.0, elong)) - 0.5))
                        )
                        raw.append(
                            Candidate(
                                float(x), float(y), float(score), float(sigma), polarity
                            )
                        )
    raw.sort(key=lambda c: (-c.score, c.y, c.x, c.radius, c.polarity))
    kept = []
    grid = {}
    spacing = max(2.0, 2 * sf)
    for c in raw:
        cell = (int(c.x // spacing), int(c.y // spacing))
        near = [
            p
            for dy in (-1, 0, 1)
            for dx in (-1, 0, 1)
            for p in grid.get((cell[0] + dx, cell[1] + dy), ())
        ]
        if any(math.hypot(c.x - p.x, c.y - p.y) < spacing for p in near):
            continue
        kept.append(c)
        grid.setdefault(cell, []).append(c)
    # Spatially balanced cap; sorting and ties are specified, with no RNG.
    counts = {}
    selected = []
    remaining = []
    quota = max(1, cfg.max_candidates // 16)
    for c in kept:
        cell = (min(3, int(c.x * 4 / w)), min(3, int(c.y * 4 / h)))
        if counts.get(cell, 0) < quota:
            counts[cell] = counts.get(cell, 0) + 1
            selected.append(c)
        else:
            remaining.append(c)
    selected = (selected + remaining)[: cfg.max_candidates]
    selected.sort(key=lambda c: (-c.score, c.y, c.x, c.radius, c.polarity))
    return tuple(selected)
