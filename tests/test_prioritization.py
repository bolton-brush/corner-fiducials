"""Joint preference is conservative presentation, not deletion or certification."""

from dataclasses import replace
import pytest
from corner_fiducials import (
    DetectorConfig,
    FiducialSet,
    Hypothesis,
    Point,
    DetectionResult,
)
from corner_fiducials.prioritization import prioritize_sets


def group(indices, score, error=0.001):
    h = Hypothesis(
        ("bolton_brush",),
        {k: Point(float(i), float(i)) for k, i in zip("ABCD", indices)},
        tuple(indices),
        error,
        score,
        10.0,
        0.0,
        False,
    )
    return FiducialSet(h, (), ("bolton_brush",), "ambiguous", "distinguishable")


def test_two_compatible_groups_outweigh_a_conflicting_bridge():
    # The bridge alone has a higher score than either real group, but not both.
    source = (
        group((0, 1, 4, 5), 0.99),
        group((0, 1, 2, 3), 0.96),
        group((4, 5, 6, 7), 0.96),
    )
    result, _ = prioritize_sets(source, DetectorConfig())
    assert [s.review_priority for s in result] == [
        "alternative",
        "preferred",
        "preferred",
    ]
    assert [s.best for s in result] == [s.best for s in source]
    assert all(s.requires_review for s in result)


def test_low_support_preserved_as_fallback_without_preference():
    source = (group((0, 1, 2, 3), 0.7),)
    result, notes = prioritize_sets(source, DetectorConfig())
    assert len(result) == 1 and result[0].review_priority == "fallback"
    assert "no_preferred_set_all_hypotheses_require_manual_inspection" in notes
    assert source[0].preference_reason == "not_prioritized"  # immutable input


def test_nearby_alternative_never_claimed_as_another_preferred_group():
    source = (group((0, 1, 2, 3), 0.99), group((0, 1, 2, 4), 0.98))
    result, _ = prioritize_sets(source, DetectorConfig())
    assert [s.review_priority for s in result] == ["preferred", "alternative"]


def test_weak_or_poor_geometry_cannot_be_preferred_even_with_high_score():
    weak = replace(group((0, 1, 2, 3), 0.99), warnings=("weak_spot_evidence",))
    poor = group((4, 5, 6, 7), 0.99, 0.06)
    result, _ = prioritize_sets((weak, poor), DetectorConfig())
    assert all(s.review_priority == "fallback" for s in result)


def test_more_than_twenty_eligible_sets_have_an_explicit_optimization_limit():
    source = tuple(group(tuple(range(i * 4, i * 4 + 4)), 0.99) for i in range(21))
    result, notes = prioritize_sets(source, DetectorConfig())
    assert len(result) == 21
    assert "joint_preference_optimization_limited" in notes
    assert all(s.review_priority == "preferred" for s in result)


def test_preference_serializes_without_certifying_names():
    sets, _ = prioritize_sets((group((0, 1, 2, 3), 0.99),), DetectorConfig())
    r = DetectionResult((100, 100), "uncertain", sets, ())
    d = r.to_dict()
    assert d["preferred_set_indices"] == [0]
    assert d["sets"][0]["named_points"] is None
    assert d["requires_review"] is True


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf"), True, "0.9"])
@pytest.mark.parametrize("name", ["preferred_min_score", "preferred_relative_score"])
def test_invalid_preference_cutoffs_rejected(name, value):
    with pytest.raises(ValueError):
        DetectorConfig(**{name: value})
