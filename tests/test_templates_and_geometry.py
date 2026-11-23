import itertools, json
import numpy as np
import pytest
from corner_fiducials import *
from synthetic import transformed


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.id)
@pytest.mark.parametrize(
    "angle,reflection", tuple(itertools.product((0, 90, 180, 270), (False, True)))
)
def test_all_pdf_tables_name_actual_points_under_rotation_and_reflection(
    template, angle, reflection
):
    p = transformed(template, angle, reflection)
    r = match_candidates(
        [Candidate(*v) for v in p], (1000, 1000), templates=[template.id]
    )
    assert r.sets
    s = r.sets[0]
    # Ambiguity is allowed; never assume A is at the screen's top-left.
    possible = (s.best,) + s.alternatives
    assert any(h.candidate_indices == (0, 1, 2, 3) for h in possible)
    assert min(h.geometry_error for h in possible) < 1e-10
    assert r.requires_review and r.experimental


def test_catalogue_values_and_continued_denver_table():
    assert len(TEMPLATES) == 10
    assert get_templates(["denver"])[0].points()[3].tolist() == [228.4, 7.3]
    assert get_templates(["oregon_optical"])[0].points()[0].tolist() == [-2.8, -132.8]
    assert get_templates(["bolton_brush"])[0].points()[3].tolist() == [176.9, -159.6]


def test_identical_templates_are_not_uniquely_identified():
    t = get_templates(["fels"])[0]
    p = transformed(t)
    r = match_candidates([Candidate(*v) for v in p], (800, 800))
    assert any(
        {"fels", "forsyth_twin_original", "oregon"} <= set(s.template_types)
        for s in r.sets
    )
    assert r.sets[0].template_status == "ambiguous"


def test_two_punch_sets_returned_instead_of_ghost_rejection():
    p = transformed(get_templates(["bolton_brush"])[0])
    q = p + [22, 28]
    pts = np.vstack((p, q))
    r = match_candidates(
        [Candidate(*v) for v in pts],
        (800, 800),
        templates=["bolton_brush"],
        config=DetectorConfig(max_sets=32),
    )
    found = {frozenset(s.best.candidate_indices) for s in r.sets}
    assert frozenset(range(4)) in found and frozenset(range(4, 8)) in found
    assert r.status == "multiple_candidates"
    assert r.requires_review


def test_competing_mixed_groups_are_flagged():
    p = transformed(get_templates(["bolton_brush"])[0])
    q = p + [5, 7]
    r = match_candidates(
        [Candidate(*v) for v in np.vstack((p, q))],
        (800, 800),
        templates=["bolton_brush"],
        config=DetectorConfig(max_sets=32),
    )
    assert any(s.conflicts_with for s in r.sets)
    assert any("shares_points_with_alternative_sets" in s.warnings for s in r.sets)


def test_near_symmetry_exposes_label_ambiguity_and_no_single_named_points():
    p = transformed(get_templates(["iowa"])[0])
    r = match_candidates([Candidate(*v) for v in p], (900, 900), templates=["iowa"])
    assert r.sets[0].label_status == "ambiguous"
    assert r.sets[0].named_points is None


def test_bad_geometry_returns_weak_fallback_or_unmatched_candidates():
    p = transformed(get_templates(["bolton_brush"])[0])
    p[3] += [55, 25]
    r = match_candidates(
        [Candidate(*v) for v in p], (900, 900), templates=["bolton_brush"]
    )
    assert r.candidates
    assert not r.sets or all("poor_geometry_fallback" in s.warnings for s in r.sets)


def test_limit_is_explicit_and_serializable():
    p = transformed(get_templates(["bolton_brush"])[0])
    q = p + [5, 7]
    r = match_candidates(
        [Candidate(*v) for v in np.vstack((p, q))],
        (900, 900),
        config=DetectorConfig(max_sets=1),
    )
    assert r.truncated and "search_or_output_truncated" in r.warnings
    json.dumps(r.to_dict(), allow_nan=False)


def test_michigan_extra_side_marks_retains_outer_set():
    t = get_templates(["michigan"])[0]
    p = transformed(t)
    extra = []
    for start, end in [(p[0], p[1]), (p[3], p[2])]:
        extra.extend(start + (end - start) * f for f in (0.25, 0.5, 0.75))
    r = match_candidates(
        [Candidate(*v) for v in np.vstack((p, extra))],
        (900, 900),
        templates=["michigan"],
        config=DetectorConfig(max_sets=32),
    )
    assert any(
        frozenset(s.best.candidate_indices) == frozenset(range(4)) for s in r.sets
    )
    assert all(
        "verify_outermost_corners_when_extra_side_marks_exist" in s.warnings
        for s in r.sets
    )


@pytest.mark.parametrize("bad", [[], ["richardson"], ["nonexistent"]])
def test_no_invented_template_table(bad):
    with pytest.raises(ValueError):
        get_templates(bad)


@pytest.mark.parametrize("angle", [17, 37, 123, -48])
@pytest.mark.parametrize("reflection", [False, True])
def test_arbitrary_in_plane_angles_are_not_fixed_corner_assignments(angle, reflection):
    t = get_templates(["bolton_brush"])[0]
    p = transformed(t, angle, reflection)
    r = match_candidates(
        [Candidate(*v) for v in p], (1000, 1000), templates=["bolton_brush"]
    )
    assert any(
        h.candidate_indices == (0, 1, 2, 3) and h.geometry_error < 1e-10
        for s in r.sets
        for h in (s.best,) + s.alternatives
    )


def test_numpy_scalar_candidates_have_json_safe_results():
    p = transformed(get_templates(["bolton_brush"])[0]).astype(np.float32)
    r = match_candidates(
        [Candidate(v[0], v[1], np.float32(0.9)) for v in p],
        (800, 800),
        templates=["bolton_brush"],
    )
    assert r.sets
    json.dumps(r.to_dict(), allow_nan=False)
