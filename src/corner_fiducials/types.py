"""Public, structured result objects. Scores are heuristics, never probabilities."""

from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Candidate:
    x: float
    y: float
    score: float = 1.0
    radius: float = 1.0
    polarity: str = "unknown"

    def __post_init__(self):
        # Caller-created candidates often contain NumPy scalars. Keep JSON output portable.
        for name in ("x", "y", "score", "radius"):
            object.__setattr__(self, name, float(getattr(self, name)))
        if not isinstance(self.polarity, str):
            raise TypeError("polarity must be a string")


@dataclass(frozen=True)
class Hypothesis:
    template_types: tuple[str, ...]
    fiducials: dict[str, Point]
    candidate_indices: tuple[int, ...]  # A,B,C,D order, not screen corners
    geometry_error: float
    score: float
    pixels_per_mm: float
    rotation_degrees: float
    reflected: bool
    scale_is_provisional: bool = True


@dataclass(frozen=True)
class FiducialSet:
    best: Hypothesis
    alternatives: tuple[Hypothesis, ...]
    template_types: tuple[str, ...]
    label_status: str
    template_status: str
    conflicts_with: tuple[int, ...] = ()
    warnings: tuple[str, ...] = ()
    requires_review: bool = True

    review_priority: str = "fallback"
    preference_reason: str = "not_prioritized"

    @property
    def template_type(self) -> Optional[str]:
        return self.template_types[0] if len(self.template_types) == 1 else None

    @property
    def named_points(self) -> Optional[dict[str, Point]]:
        """Only expose a single mapping when its geometry is distinguishable."""
        return self.best.fiducials if self.label_status == "distinguishable" else None


@dataclass(frozen=True)
class DetectionResult:
    image_shape: tuple[int, int]
    status: str
    sets: tuple[FiducialSet, ...]
    candidates: tuple[Candidate, ...]
    warnings: tuple[str, ...] = ()
    requires_review: bool = True
    experimental: bool = True
    truncated: bool = False

    @property
    def preferred_set_indices(self) -> tuple[int, ...]:
        return tuple(
            i for i, s in enumerate(self.sets) if s.review_priority == "preferred"
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["preferred_set_indices"] = list(self.preferred_set_indices)
        for record, group in zip(result["sets"], self.sets):
            record["named_points"] = (
                {k: asdict(v) for k, v in group.named_points.items()}
                if group.named_points is not None
                else None
            )
            record["template_type"] = group.template_type
        return result


@dataclass(frozen=True)
class DetectorConfig:
    scales: tuple[float, ...] = (0.5, 0.8, 1.2, 2.0, 3.5, 6.0)
    max_candidates: int = 240
    max_sets: int = 8
    neighbors: int = 2
    min_span_fraction: float = 0.18
    max_geometry_error: float = 0.035
    fallback_geometry_error: float = 0.075
    ambiguity_margin: float = 0.004
    label_noise_pixels: float = 1.5
    max_hypotheses: int = 4096
    guided_windows: int = 24
    preferred_min_score: float = 0.90
    preferred_relative_score: float = 0.90

    def __post_init__(self):
        for name in ("preferred_min_score", "preferred_relative_score"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                raise ValueError(name + " must be a finite number in [0,1]")
        for name in ("max_candidates", "max_sets", "neighbors", "max_hypotheses"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(name + " must be a positive integer")
        if type(self.guided_windows) is not int or not 0 <= self.guided_windows <= 256:
            raise ValueError("guided_windows must be 0..256")
        if self.max_candidates < 4 or self.max_candidates > 2000:
            raise ValueError("max_candidates must be 4..2000")
        if self.neighbors > 4:
            raise ValueError("neighbors must be at most 4")
        import math

        if not self.scales or any(not math.isfinite(s) or s <= 0 for s in self.scales):
            raise ValueError("scales must be finite and positive")
        if not 0 < self.min_span_fraction < 1:
            raise ValueError("min_span_fraction must be between 0 and 1")
        if not 0 < self.max_geometry_error <= self.fallback_geometry_error < 0.5:
            raise ValueError("Invalid geometry tolerances")
        if not math.isfinite(self.ambiguity_margin) or self.ambiguity_margin < 0:
            raise ValueError("Invalid ambiguity margin")
        if not math.isfinite(self.label_noise_pixels) or self.label_noise_pixels < 0:
            raise ValueError("Invalid label noise")
