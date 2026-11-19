"""Exhaustive ordered-anchor geometric matching; retains multiple explanations."""

from __future__ import annotations
from dataclasses import replace
import itertools, math
import numpy as np
from scipy.spatial import cKDTree
from .types import (
    Candidate,
    DetectorConfig,
    Point,
    Hypothesis,
    FiducialSet,
    DetectionResult,
)
from .templates import get_templates


def match_candidates(candidates, image_shape, *, templates=None, config=None):
    cfg = config or DetectorConfig()
    if len(image_shape) != 2 or any(
        type(x) not in (int, np.int64, np.int32) or x <= 0 for x in image_shape
    ):
        raise ValueError("image_shape must be (height,width)")
    h, w = map(int, image_shape)
    cs = tuple(candidates)
    warnings = []
    truncated = False
    for c in cs:
        if not isinstance(c, Candidate):
            raise TypeError("Pass Candidate objects")
        if not all(math.isfinite(v) for v in (c.x, c.y, c.score, c.radius)) or not (
            0 <= c.x < w and 0 <= c.y < h and 0 <= c.score <= 1 and c.radius > 0
        ):
            raise ValueError("Invalid candidate coordinate, score or radius")
    if len(cs) > cfg.max_candidates:
        cs = tuple(sorted(cs, key=lambda c: (-c.score, c.y, c.x))[: cfg.max_candidates])
        warnings.append("candidate_limit_reached")
        truncated = True
    if len(cs) >= cfg.max_candidates:
        warnings.append("candidate_budget_saturated")
        truncated = True
    selected = get_templates(templates)
    if len(cs) < 4:
        return DetectionResult(
            (h, w),
            "not_found",
            (),
            cs,
            ("fewer_than_four_candidates",),
            truncated=truncated,
        )
    xy = np.array([(c.x, c.y) for c in cs])
    z = xy[:, 0] + 1j * xy[:, 1]
    tree = cKDTree(xy)
    ii, jj = np.where(~np.eye(len(cs), dtype=bool))
    edges = z[jj] - z[ii]
    length = np.abs(edges)
    valid = length >= cfg.min_span_fraction * min(h, w)
    ii, jj, edges, length = ii[valid], jj[valid], edges[valid], length[valid]
    if not len(ii):
        return DetectionResult(
            (h, w),
            "not_found",
            (),
            cs,
            ("no_anchor_with_required_span",),
            truncated=truncated,
        )
    families = {}
    for t in selected:
        families.setdefault(t.coordinates_mm, []).append(t)
    hypotheses = {}
    neighbor_count = min(cfg.neighbors, len(cs))
    for coordinates, types in families.items():
        # The library accepts pixels in their current orientation. Cartesian PDF y-up becomes y-down.
        q = np.array(coordinates)
        qz = q[:, 0] - 1j * q[:, 1]
        for reflected in (False, True):
            qref = np.conj(qz) if reflected else qz
            qa = (qref[0] - qref[1]) / (qref[2] - qref[1])
            qd = (qref[3] - qref[1]) / (qref[2] - qref[1])
            pa = z[ii] + qa * edges
            pd = z[ii] + qd * edges
            da, ia = tree.query(np.column_stack((pa.real, pa.imag)), k=neighbor_count)
            dd, idd = tree.query(np.column_stack((pd.real, pd.imag)), k=neighbor_count)
            if neighbor_count == 1:
                da, ia, dd, idd = [x[:, None] for x in (da, ia, dd, idd)]
            for ka, kd in itertools.product(range(neighbor_count), repeat=2):
                # A loose seed gate allows final all-four fitting to expose weak fallback matches.
                gate = (
                    da[:, ka]
                    <= np.maximum(3.0, cfg.fallback_geometry_error * length * 2)
                ) & (
                    dd[:, kd]
                    <= np.maximum(3.0, cfg.fallback_geometry_error * length * 2)
                )
                if not gate.any():
                    continue
                ids = np.column_stack((ia[gate, ka], ii[gate], jj[gate], idd[gate, kd]))
                different = np.array([len(set(r)) == 4 for r in ids])
                ids = ids[different]
                if not len(ids):
                    continue
                observed = z[ids]
                center = observed.mean(axis=1, keepdims=True)
                pc = observed - center
                qc = qref - qref.mean()
                coef = (pc * np.conj(qc)).sum(axis=1) / (np.abs(qc) ** 2).sum()
                fitted = center + coef[:, None] * qc
                span = np.sqrt(np.mean(np.abs(pc) ** 2, axis=1))
                error = np.sqrt(
                    np.mean(np.abs(observed - fitted) ** 2, axis=1)
                ) / np.maximum(span, 1.0)
                scores = np.array([c.score for c in cs])[ids].mean(axis=1) * np.exp(
                    -0.5 * (error / 0.018) ** 2
                )
                for k in np.where(error <= cfg.fallback_geometry_error)[0]:
                    indices = tuple(int(x) for x in ids[k])
                    polygon = xy[ids[k]]
                    edge_vectors = np.roll(polygon, -1, axis=0) - polygon
                    cross = (
                        edge_vectors[:, 0] * np.roll(edge_vectors, -1, axis=0)[:, 1]
                        - edge_vectors[:, 1] * np.roll(edge_vectors, -1, axis=0)[:, 0]
                    )
                    if not (np.all(cross > 0) or np.all(cross < 0)):
                        continue
                    key = (tuple(t.id for t in types), indices)
                    hypothesis = Hypothesis(
                        tuple(t.id for t in types),
                        {
                            letter: Point(float(xy[j, 0]), float(xy[j, 1]))
                            for letter, j in zip("ABCD", indices)
                        },
                        indices,
                        float(error[k]),
                        float(scores[k]),
                        float(abs(coef[k])),
                        float(np.rad2deg(np.angle(coef[k]))),
                        reflected,
                    )
                    old = hypotheses.get(key)
                    if old is None or hypothesis.geometry_error < old.geometry_error:
                        hypotheses[key] = hypothesis
        # Bound memory while retaining evidence that the search was truncated.
        if len(hypotheses) > cfg.max_hypotheses:
            values = sorted(
                hypotheses.values(),
                key=lambda v: (
                    -v.score,
                    v.geometry_error,
                    v.template_types,
                    v.candidate_indices,
                ),
            )[: cfg.max_hypotheses]
            hypotheses = {(v.template_types, v.candidate_indices): v for v in values}
            truncated = True
    groups = {}
    for hypo in hypotheses.values():
        groups.setdefault(tuple(sorted(hypo.candidate_indices)), []).append(hypo)
    sets = []
    for hs in groups.values():
        hs.sort(
            key=lambda x: (
                x.geometry_error,
                -x.score,
                x.template_types,
                x.candidate_indices,
            )
        )
        best = hs[0]
        tolerance = max(
            cfg.ambiguity_margin,
            cfg.label_noise_pixels / max(1.0, best.pixels_per_mm * 150),
        )
        close = tuple(
            v for v in hs if v.geometry_error <= best.geometry_error + tolerance
        )
        types = tuple(sorted({t for v in close for t in v.template_types}))
        labels = {v.candidate_indices for v in close}
        notes = []
        if len(types) > 1:
            notes.append("template_identity_ambiguous")
        if len(labels) > 1:
            notes.append("fiducial_names_ambiguous")
        if best.geometry_error > cfg.max_geometry_error:
            notes.append("poor_geometry_fallback")
        if min(cs[j].score for j in best.candidate_indices) < 0.25:
            notes.append("weak_spot_evidence")
        if "michigan" in types:
            notes.append("verify_outermost_corners_when_extra_side_marks_exist")
        if "oregon_optical" in types:
            notes.append("optical_circle_cross_appearance_not_clinically_validated")
        sets.append(
            FiducialSet(
                best,
                close[1:],
                types,
                "ambiguous" if len(labels) > 1 else "distinguishable",
                "ambiguous" if len(types) > 1 else "distinguishable",
                warnings=tuple(notes),
            )
        )
    sets.sort(
        key=lambda s: (
            -s.best.score,
            s.best.geometry_error,
            s.best.candidate_indices,
            s.template_types,
        )
    )
    if len(sets) > cfg.max_sets:
        sets = sets[: cfg.max_sets]
        truncated = True
        warnings.append("set_limit_reached")
    final = []
    for i, s in enumerate(sets):
        used = set(s.best.candidate_indices)
        conflicts = tuple(
            j
            for j, t in enumerate(sets)
            if j != i and used.intersection(t.best.candidate_indices)
        )
        notes = list(s.warnings)
        if conflicts:
            notes.append("shares_points_with_alternative_sets")
        if truncated:
            notes.append("naming_not_certified_under_search_limits")
        final.append(
            replace(
                s,
                conflicts_with=conflicts,
                label_status=(
                    "unresolved_due_to_limits" if truncated else s.label_status
                ),
                warnings=tuple(notes),
            )
        )
    if len(final) > 1:
        warnings.append("multiple_punch_sets_or_competing_explanations_not_confirmed")
    if truncated:
        warnings.append("search_or_output_truncated")
    if not final:
        warnings.append("no_complete_pdf_template_match_candidates_preserved")
    warnings.append("experimental_scores_are_not_calibrated_probabilities")
    status = (
        "not_found"
        if not final
        else (
            "multiple_candidates"
            if len(final) > 1
            else ("uncertain" if final[0].warnings else "candidate")
        )
    )
    return DetectionResult(
        (h, w),
        status,
        tuple(final),
        cs,
        tuple(dict.fromkeys(warnings)),
        truncated=truncated,
    )
