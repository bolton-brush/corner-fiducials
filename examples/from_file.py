"""Optional adapter: file decoding stays outside the pixel-array library API."""

import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
from corner_fiducials import detect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument(
        "--template", action="append", help="Optional PDF template ID, repeatable"
    )
    parser.add_argument(
        "--out", required=True, help="New JSON output file outside the source directory"
    )
    args = parser.parse_args()
    source = Path(args.image).resolve()
    out = Path(args.out).resolve()
    if out.is_relative_to(source.parent):
        raise ValueError(
            "Choose an output directory outside the source image directory"
        )
    with Image.open(source) as image:
        if getattr(image, "n_frames", 1) != 1:
            raise ValueError("Select a single image page explicitly")
        pixels = np.array(image)
    result = detect(pixels, templates=args.template)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, allow_nan=False)
    print(result.status, "sets:", len(result.sets), "review:", result.requires_review)


if __name__ == "__main__":
    main()
