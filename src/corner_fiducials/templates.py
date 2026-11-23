"""The ten coordinate tables documented in AAOF Scaled Measurements v1.9."""

from __future__ import annotations
import json
from dataclasses import dataclass
from importlib.resources import files
import numpy as np


@dataclass(frozen=True)
class Template:
    id: str
    collection: str
    coordinates_mm: tuple[tuple[float, float], ...]
    pdf_pages: tuple[int, ...]
    nominal_dpi: int
    notes: str

    def points(self) -> np.ndarray:
        """Return a fresh A,B,C,D array with Cartesian y-up coordinates."""
        return np.array(self.coordinates_mm, dtype=float)


_DATA = json.loads(
    files("corner_fiducials.data")
    .joinpath("templates.json")
    .read_text(encoding="utf-8")
)
TEMPLATES = tuple(
    Template(
        r["id"],
        r["collection"],
        tuple(tuple(r["coordinates_mm"][k]) for k in "ABCD"),
        tuple(r["pdf_pages"]),
        r["nominal_dpi"],
        r["notes"],
    )
    for r in _DATA["templates"]
)
SOURCE = _DATA["source"]


def get_templates(names=None) -> tuple[Template, ...]:
    if names is None:
        return TEMPLATES
    if isinstance(names, str):
        names = [names]
    wanted = set(names)
    unknown = wanted - {t.id for t in TEMPLATES}
    if unknown:
        raise ValueError("Unknown template IDs: " + ", ".join(sorted(unknown)))
    result = tuple(t for t in TEMPLATES if t.id in wanted)
    if not result:
        raise ValueError("At least one template is required")
    return result
