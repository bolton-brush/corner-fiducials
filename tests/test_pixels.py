import numpy as np
import pytest
from corner_fiducials import *
from synthetic import transformed, render


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda t: t.id)
def test_all_documented_templates_end_to_end_on_synthetic_pixels(template):
    p = transformed(template, scale=1.8)
    image = render(p)
    before = image.copy()
    r = detect(image, templates=[template.id])
    assert np.array_equal(image, before)
    assert r.sets
    assert any(
        max(
            np.hypot(h.fiducials[k].x - p[j, 0], h.fiducials[k].y - p[j, 1])
            for j, k in enumerate("ABCD")
        )
        < 4
        for s in r.sets
        for h in (s.best,) + s.alternatives
    )


@pytest.mark.parametrize("dtype", [np.uint8, np.uint16, np.float32, np.float64])
@pytest.mark.parametrize("dark", [False, True])
def test_bit_depth_and_polarity(dtype, dark):
    p = transformed(get_templates(["bolton_brush"])[0])
    im = render(p, dtype=dtype, dark=dark)
    im.setflags(write=False)
    r = detect(im, templates=["bolton_brush"])
    assert r.sets


def test_full_pixel_ghost_image_returns_both_sets():
    p = transformed(get_templates(["bolton_brush"])[0])
    q = p + [20, 22]
    r = detect(
        render(np.vstack((p, q))),
        templates=["bolton_brush"],
        config=DetectorConfig(max_sets=32),
    )
    for truth in (p, q):
        assert any(
            max(
                np.hypot(h.fiducials[k].x - truth[j, 0], h.fiducials[k].y - truth[j, 1])
                for j, k in enumerate("ABCD")
            )
            < 4
            for s in r.sets
            for h in (s.best,) + s.alternatives
        )


def test_optical_cross_pixel_smoke():
    p = transformed(get_templates(["oregon_optical"])[0])
    r = detect(render(p, optical=True), templates=["oregon_optical"])
    assert r.sets
    # Optical extraction is a smoke test, not subpixel-center or real-image validation.
    assert any(
        "optical_circle_cross_appearance_not_clinically_validated" in s.warnings
        for s in r.sets
    )


def test_deterministic_and_no_file_api():
    im = render(transformed(get_templates(["bolton_brush"])[0]))
    a = detect(im, templates=["bolton_brush"])
    b = detect(im, templates=["bolton_brush"])
    assert a.to_dict() == b.to_dict()
    with pytest.raises(TypeError):
        detect("/tmp/not-a-pixel-array.tif")


def test_blank_and_incomplete_return_evidence_without_inventing_names():
    r = detect(np.zeros((100, 100), dtype="uint16"))
    assert not r.sets and r.status == "not_found"
    r = match_candidates(
        [Candidate(10, 10), Candidate(70, 10), Candidate(10, 70)], (100, 100)
    )
    assert not r.sets and len(r.candidates) == 3


@pytest.mark.parametrize(
    "image",
    [
        np.ones((5, 5)),
        np.zeros((100, 100, 3)),
        np.full((100, 100), np.nan),
        np.full((100, 100), np.inf),
        np.ones((100, 100), dtype=complex),
    ],
)
def test_invalid_arrays(image):
    with pytest.raises((ValueError, TypeError)):
        detect(image)


def test_noncontiguous_array():
    im = render(transformed(get_templates(["bolton_brush"])[0]))
    assert detect(im[:, ::-1], templates=["bolton_brush"]).sets


def test_geometry_guidance_recovers_a_missing_observed_spot():
    from corner_fiducials.guidance import augment_candidates

    p = transformed(get_templates(["bolton_brush"])[0])
    im = render(p)
    initial = tuple(Candidate(*v) for v in p[1:])
    cs, used, limited = augment_candidates(
        im, initial, ["bolton_brush"], DetectorConfig()
    )
    assert used and any(np.hypot(c.x - p[0, 0], c.y - p[0, 1]) < 3 for c in cs)
    assert match_candidates(cs, im.shape, templates=["bolton_brush"]).sets


def test_guidance_does_not_fabricate_expected_center_without_pixel_evidence():
    from corner_fiducials.guidance import augment_candidates

    p = transformed(get_templates(["bolton_brush"])[0])
    im = render(p[1:], shape=(600, 650))
    cs, used, limited = augment_candidates(
        im, tuple(Candidate(*v) for v in p[1:]), ["bolton_brush"], DetectorConfig()
    )
    assert used
    assert not any(np.hypot(c.x - p[0, 0], c.y - p[0, 1]) < 3 for c in cs)


def test_large_finite_float_range_normalizes_without_overflow():
    from corner_fiducials.candidates import normalize_pixels

    # Construct safely: linspace across both extremes can itself overflow.
    a = np.linspace(-1.0, 1.0, 10000).reshape(100, 100) * 1e308
    normalized = normalize_pixels(a)
    assert np.isfinite(normalized).all()
    assert normalized.min() >= 0 and normalized.max() <= 255


def test_template_id_generator_is_consumed_once():
    image = render(transformed(get_templates(["bolton_brush"])[0]))
    result = detect(image, templates=(x for x in ["bolton_brush"]))
    assert result.sets
