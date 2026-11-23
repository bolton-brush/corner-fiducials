"""Run without private data: two translated punch groups on a synthetic film."""

import json
import numpy as np
from corner_fiducials import detect, get_templates, DetectorConfig


def make_image():
    template = get_templates(["bolton_brush"])[0].points()
    template[:, 1] *= -1
    p = template * 2 + [80, 80]
    yy, xx = np.mgrid[:520, :560]
    image = (10000 + xx * 3 + yy * 2).astype("uint16")
    for group in (p, p + [20, 24]):
        for x, y in group:
            image[(xx - x) ** 2 + (yy - y) ** 2 <= 9] = 63000
    return image


if __name__ == "__main__":
    result = detect(
        make_image(), templates=["bolton_brush"], config=DetectorConfig(max_sets=16)
    )
    print(json.dumps(result.to_dict(), indent=2))
