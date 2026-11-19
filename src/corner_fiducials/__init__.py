"""Deterministic, pixel-array-only AAOF fiducial hypotheses. No image-file I/O or GUI."""

from dataclasses import replace
from .types import (
    Candidate,
    DetectorConfig,
    DetectionResult,
    FiducialSet,
    Hypothesis,
    Point,
)
from .templates import Template, TEMPLATES, get_templates
from .candidates import find_candidates
from .matching import match_candidates
from .guidance import augment_candidates

__version__ = "0.1.0a1"


def detect(image, *, templates=None, config=None):
    """Return named/template hypotheses; input is a 2-D NumPy pixel array.

    Coordinates use the input array's exact axes, zero-based x right/y down.
    Every result requires review; ambiguities and multiple explanations are retained.
    """
    cfg = config or DetectorConfig()
    # Validate requested template IDs even on blank images.
    template_ids = tuple(t.id for t in get_templates(templates))
    candidates = find_candidates(image, config=cfg)
    candidates, guided, limited = augment_candidates(
        image, candidates, template_ids, cfg
    )
    result = match_candidates(
        candidates, image.shape, templates=template_ids, config=cfg
    )
    if guided:
        warnings = result.warnings + ("bounded_geometry_guided_local_search_used",)
        if limited:
            warnings += ("guided_search_limit_reached",)
            groups = tuple(
                replace(
                    s,
                    label_status="unresolved_due_to_limits",
                    warnings=s.warnings + ("naming_not_certified_under_search_limits",),
                )
                for s in result.sets
            )
            result = replace(result, sets=groups, truncated=True)
        result = replace(result, warnings=warnings)
    return result


__all__ = [
    "detect",
    "find_candidates",
    "match_candidates",
    "get_templates",
    "TEMPLATES",
    "Template",
    "Candidate",
    "DetectorConfig",
    "DetectionResult",
    "FiducialSet",
    "Hypothesis",
    "Point",
]
