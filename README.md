# corner-fiducials

A Python library that returns corner-fiducial **hypotheses** from a grayscale pixel array.
It uses deterministic, classical image analysis: multiscale bright/dark spot detection followed
by geometric matching against the coordinate tables in AAOF *Scaled Measurements* v1.9.
There is no neural model, random sampling, private training data, image-file API or network call
in the library. Results preserve uncertain names, indistinguishable templates and competing
punch groups instead of treating every match as a confirmed detection.

**Status: experimental alpha (`0.1.0a1`).** Implementation and synthetic tests are available.
All new template/appearance/multiple-group behavior is not yet independently validated on
real images. Do not transfer an earlier version's retrospective accuracy to this library.
See [validation status](docs/validation.md) and [known limitations](docs/uncertainty.md).

## Install and call

```sh
python -m pip install -e '.[dev,examples]'
```

```python
import numpy as np
from corner_fiducials import detect

# pixels is an already decoded 2-D grayscale NumPy array (uint8/uint16/float).
# The library never changes the array or reads/writes any image files.
pixels = np.asarray(your_grayscale_pixels)
result = detect(pixels)  # all documented coordinate tables

# Optional: restrict matching if the punch template is already known.
result = detect(pixels, templates=["bolton_brush"])
for group in result.sets:
    print(group.template_types, group.label_status, group.warnings)
    if group.named_points is not None:
        print(group.named_points["A"].x, group.named_points["A"].y)
    else:
        # Never mistake a tentative mapping for uniquely identified physical names.
        print(group.best.fiducials, group.alternatives)
```

Output coordinates are **zero-based native input-array pixels**, x right, y down. A/B/C/D are
physical PDF names and can appear at any image corner. The array's orientation is used exactly
as supplied; file decoding/orientation belongs to the caller. `result.to_dict()` is JSON-friendly.
All results currently set `requires_review=True`. Numeric scores are heuristics, not calibrated
probabilities. A fitted pixels/mm value is provisional, not independently validated calibration.

## Templates and multiple punch groups

The catalogue includes all **ten documented coordinate tables**: Iowa, Mathews, original
Forsyth Twin, Fels, Denver, Michigan, early optical Oregon, ordinary Oregon, Burlington and
Bolton-Brush. There are fewer than ten distinct geometries: original Forsyth/Fels/ordinary
Oregon are identical. Newer Forsyth subjects have no consistent fixed pattern in the PDF;
Richardson has no coordinate table in this document. No coordinates are invented for either.
The optical circle/cross extractor is experimental. See [template provenance](docs/templates.md).

Matching considers arbitrary in-plane rotation and reflection, not a fixed screen-corner
assignment. Multiple sets can be returned, including overlapping alternative groupings.
`conflicts_with` and warnings identify shared-point/mixed-group interpretations. These are
**possible sets**, not a claim that a ghost image contains that many true punchings. Search and
output bounds are configurable and explicitly reported as `truncated`; unmatched spot
candidates remain available when no complete template fits. See [the result contract](docs/api.md).

## Repository layout

```text
src/corner_fiducials/   Public API, spot extraction, geometry and result objects
  data/templates.json  PDF coordinates and source/version/page provenance
tests/                 Synthetic images and API/geometry regression tests
examples/              Optional file adapter and synthetic debugging example
docs/                  Algorithm, API, template notes, uncertainty and validation
pyproject.toml         Package metadata and dependencies
tasks.py               Invoke test/build/check/publish targets
flake.nix / flake.lock  Nix development shell and pinned input
AGENTS.md              Repository structure and development/documentation rules
```

No private radiographs, human annotation exports or study-source manifests are included.

## Develop, build and release

```sh
invoke test
invoke build
invoke check
# Explicit publishing targets, NOT run by tests or a normal commit:
invoke publish --repository testpypi
invoke publish --repository pypi
```

Build produces a source distribution and wheel in `dist/`. PyPI publication requires ownership
of the chosen project name and configured release credentials, or the manual GitHub workflow
and a configured [Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/).
Publication has not been executed as part of development. The build workflow follows the
[Python Packaging User Guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).

For Nix users with `nix-command` and `flakes` enabled:

```sh
nix develop
invoke test
invoke build --no-isolation
```

If those Nix features are not enabled in your installation, use
`nix --extra-experimental-features 'nix-command flakes' develop` without changing global
settings. The shell supplies Python, NumPy, OpenCV, SciPy and build/test tools; no image data
are downloaded. See [development details](docs/development.md).

## Reference

AAOF Legacy Collection, *Scaled Measurements from the AAOF Legacy Collection Images*, v1.9,
2022-02-28. Coordinates, the continued Denver row and collection-specific exceptions were
checked against the supplied PDF. Exact PDF SHA256 and 1-based PDF page numbers are in the
catalogue. The PDF itself is not redistributed. Detection identifies a compatible punch shape;
it cannot establish the study collection when multiple collections share that shape.
