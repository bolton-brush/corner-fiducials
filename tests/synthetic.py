"""Synthetic fixtures only: never redistribute private radiographs or labels."""

import numpy as np


def transformed(template, angle=0, reflected=False, scale=2.0, offset=(80.0, 80.0)):
    p = template.points()
    p[:, 1] *= -1
    if reflected:
        p[:, 0] *= -1
    r = np.deg2rad(angle)
    matrix = np.array([[np.cos(r), -np.sin(r)], [np.sin(r), np.cos(r)]])
    p = p @ matrix.T * scale
    p -= p.min(axis=0)
    return p + np.array(offset)


def render(points, shape=None, dark=False, dtype=np.uint16, optical=False):
    if shape is None:
        shape = (int(np.max(points[:, 1])) + 85, int(np.max(points[:, 0])) + 85)
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    image = (12000 + xx * 2 + yy).astype(np.float32)
    for x, y in points:
        radius = np.hypot(xx - x, yy - y)
        if optical:
            image[(radius >= 4) & (radius <= 6)] = 62000
            image[(radius <= 5) & ((np.abs(xx - x) < 0.8) | (np.abs(yy - y) < 0.8))] = (
                62000
            )
        else:
            image[radius <= 3] = 62000
    if dark:
        image = 65535 - image
    if dtype == np.uint8:
        return np.clip(image / 257, 0, 255).astype(dtype)
    if np.issubdtype(dtype, np.floating):
        return (image / 65535).astype(dtype)
    return image.astype(dtype)
