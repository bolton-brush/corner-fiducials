"""Recover weak local spots using three observed candidates, never fabricated points."""

from __future__ import annotations
import math
import cv2
import numpy as np
from scipy.spatial import cKDTree
from .templates import get_templates
from .types import Candidate
from .candidates import normalize_pixels


def augment_candidates(image, candidates, template_names, config):
    if len(candidates) < 3 or not config.guided_windows:
        return candidates, False, False
    h, w = image.shape
    cs = tuple(candidates)
    xy = np.array([(c.x, c.y) for c in cs])
    z = xy[:, 0] + 1j * xy[:, 1]
    tree = cKDTree(xy)
    anchors = np.array(
        sorted(range(len(cs)), key=lambda i: (-cs[i].score, cs[i].y, cs[i].x))[:24]
    )
    bi, cj = np.meshgrid(anchors, anchors, indexing="ij")
    bi = bi.ravel()
    cj = cj.ravel()
    edge = z[cj] - z[bi]
    length = np.abs(edge)
    valid = (bi != cj) & (length >= config.min_span_fraction * min(h, w))
    bi, cj, edge, length = bi[valid], cj[valid], edge[valid], length[valid]
    targets = []
    families = {t.coordinates_mm: t for t in get_templates(template_names)}
    for coordinates in families:
        q = np.array(coordinates)
        qz = q[:, 0] - 1j * q[:, 1]
        for reflect in (False, True):
            qr = np.conj(qz) if reflect else qz
            pa = z[bi] + (qr[0] - qr[1]) / (qr[2] - qr[1]) * edge
            pd = z[bi] + (qr[3] - qr[1]) / (qr[2] - qr[1]) * edge
            da, ia = tree.query(np.column_stack((pa.real, pa.imag)))
            dd, idd = tree.query(np.column_stack((pd.real, pd.imag)))
            for known, missing, dist, third, missing_dist in [
                (pa, pd, da, ia, dd),
                (pd, pa, dd, idd, da),
            ]:
                # A third actual spot must support the seed; the fourth must not already be nearby.
                mask = (
                    (dist <= np.maximum(3.0, 0.018 * length))
                    & (missing_dist > np.maximum(3.0, 0.012 * length))
                    & (third != bi)
                    & (third != cj)
                )
                for k in np.flatnonzero(mask):
                    center = missing[k]
                    x, y = float(center.real), float(center.imag)
                    radius = max(24, round(0.035 * length[k]))
                    if not (8 < x < w - 8 and 8 < y < h - 8):
                        continue
                    a = xy[bi[k]]
                    b = xy[cj[k]]
                    c = xy[third[k]]
                    area = (
                        abs(
                            (b[0] - a[0]) * (c[1] - a[1])
                            - (b[1] - a[1]) * (c[0] - a[0])
                        )
                        / 2
                    )
                    coverage = math.sqrt(area / max(1, h * w))
                    quality = (
                        (cs[bi[k]].score + cs[cj[k]].score + cs[third[k]].score)
                        / 3
                        * math.exp(-0.5 * (dist[k] / max(3.0, 0.018 * length[k])) ** 2)
                        * coverage
                    )
                    targets.append((quality, x, y, radius))
    targets.sort(key=lambda t: (-t[0], t[2], t[1]))
    windows = []
    for item in targets:
        if any(
            math.hypot(item[1] - p[1], item[2] - p[2]) < min(item[3], p[3]) * 0.6
            for p in windows
        ):
            continue
        windows.append(item)
        if len(windows) >= config.guided_windows:
            break
    extra = []
    sf = min(h, w) / 1100.0
    for _, cx, cy, radius in windows:
        x0 = max(0, round(cx) - radius)
        x1 = min(w, round(cx) + radius + 1)
        y0 = max(0, round(cy) - radius)
        y1 = min(h, round(cy) + radius + 1)
        # Local contrast uses ORIGINAL input pixels, not the globally clipped preview.
        crop = normalize_pixels(image[y0:y1, x0:x1])
        found = []
        for scale in (0.5, 0.8, 1.2, 2.0, 3.5):
            sigma = max(0.5, scale * sf)
            dog = cv2.GaussianBlur(crop, (0, 0), sigma) - cv2.GaussianBlur(
                crop, (0, 0), max(3.0, sigma * 5)
            )
            for sign, polarity in [(1, "bright-guided"), (-1, "dark-guided")]:
                response = sign * dog
                maximum = cv2.dilate(
                    response, np.ones((max(3, 2 * round(sigma) + 1),) * 2, np.uint8)
                )
                ys, xs = np.where((response >= maximum - 1e-6) & (response >= 2))
                values = response[ys, xs]
                order = np.lexsort((xs, ys, -values))[:20]
                for j in order:
                    x = int(xs[j])
                    y = int(ys[j])
                    r = max(4, round(4 * sigma))
                    if min(x, y, crop.shape[1] - 1 - x, crop.shape[0] - 1 - y) < r:
                        continue
                    patch = crop[y - r : y + r + 1, x - r : x + r + 1]
                    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
                    rad = xx * xx + yy * yy
                    inner = rad <= max(1, sigma) ** 2
                    ring = (rad >= (2 * max(1, sigma)) ** 2) & (rad <= r * r)
                    if not ring.any():
                        continue
                    contrast = sign * (
                        float(np.mean(patch[inner])) - float(np.median(patch[ring]))
                    )
                    if contrast < 2:
                        continue
                    noise = float(np.std(patch[ring]))
                    asym = np.std(
                        [
                            np.median(patch[ring & m])
                            for m in (xx > 0, xx < 0, yy > 0, yy < 0)
                        ]
                    ) / (contrast + 3)
                    score = (
                        (1 - math.exp(-contrast / 18))
                        * (1 - math.exp(-contrast / (noise + 3)))
                        * math.exp(-0.3 * min(float(asym), 5))
                    )
                    # Weak peaks far from the model expectation rank lower, not as invented centers.
                    distance = math.hypot(x + x0 - cx, y + y0 - cy)
                    score *= math.exp(-0.1 * (distance / max(1, radius)) ** 2)
                    found.append(
                        Candidate(
                            float(x + x0),
                            float(y + y0),
                            float(score),
                            float(sigma),
                            polarity,
                        )
                    )
        found.sort(key=lambda c: (-c.score, c.y, c.x))
        local = []
        for c in found:
            if any(math.hypot(c.x - p.x, c.y - p.y) < max(2.0, 2 * sf) for p in local):
                continue
            local.append(c)
            if len(local) >= 3:
                break
        extra.extend(local)
    # Reserve room for guided evidence rather than losing it again to globally strong anatomy.
    merged = []
    spacing = max(2.0, 2 * sf)
    for c in sorted(extra, key=lambda p: (-p.score, p.y, p.x)) + list(cs):
        if any(math.hypot(c.x - p.x, c.y - p.y) < spacing for p in merged):
            continue
        merged.append(c)
        if len(merged) >= config.max_candidates:
            break
    merged.sort(key=lambda c: (-c.score, c.y, c.x, c.radius, c.polarity))
    return tuple(merged), bool(windows), len(windows) >= config.guided_windows
