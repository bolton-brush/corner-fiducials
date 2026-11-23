# API and return contract

## `detect(image, *, templates=None, config=None)`

Input: a 2-D NumPy grayscale array, at least 24×24 pixels, with finite real integer or float
values. uint8, uint16 and float arrays are exercised in tests. Read-only and non-contiguous
arrays are accepted. RGB/multiframe arrays, filenames, NaN and Inf are rejected explicitly.
The input is not mutated. Contrast is normalized in a separate array; extraction stays at
native resolution. File formats, EXIF/TIFF orientation, filesystem writes and networking
are outside the API.

`templates`: optional template-ID string or iterable of IDs from `get_templates()`.
`config`: immutable `DetectorConfig`. All configuration values are validated.
Unknown IDs are errors even when the input image is blank.

## `find_candidates(image, *, config=None)`

Returns deterministic native-pixel `Candidate(x,y,score,radius,polarity)` records. Scores
summarize local spot appearance. Radius describes a detection scale, not measured hole size.
An empty candidate tuple is a valid low-information result, not four fabricated coordinates.

## `match_candidates(candidates, image_shape, *, templates=None, config=None)`

Allows callers with their own image analysis to use the PDF matcher directly. Candidate
coordinates/scores must be finite and inside `(height,width)`; score is in `[0,1]` and radius
is positive. Inputs above the configured cap are truncated with an explicit warning.
Indices in hypotheses refer to `result.candidates` (after any cap), not an earlier input list.

## `DetectionResult`

- `image_shape`: caller's height/width; coordinates are zero-based x/y in these exact axes.
- `status`: `candidate`, `uncertain`, `multiple_candidates`, or `not_found`.
- `sets`: proposed point groups; each is still a hypothesis requiring review.
- `candidates`: retained spot evidence, including when no complete group matches.
- `warnings`: collection/geometry ambiguity, multiple interpretations, limits and calibration.
- `truncated`: search or output was bounded; absence from the result is not proof of absence.
- `requires_review=True`, `experimental=True`: this alpha is not an automatic selection API.
- `to_dict()`: nested public records suitable for JSON serialization.

## Each `FiducialSet`

`best` and `alternatives` are `Hypothesis` records. Each hypothesis contains:

- physical `fiducials` named A/B/C/D, with x/y coordinates;
- possible `template_types` (one geometry can have multiple collection IDs);
- `candidate_indices` in A/B/C/D order;
- `geometry_error`: RMS similarity-fit residual divided by RMS observed radius;
- `score`: appearance × geometric agreement, **not a correctness probability**;
- provisional `pixels_per_mm`, in-plane rotation and reflection of that explanation.

A group's `template_types` unions close competing explanations. `template_status` is
`ambiguous` when more than one ID remains. Collection identity must then stay unresolved.
`label_status` is `ambiguous` when near-equal fits assign different A/B/C/D names. In that
case `named_points` is `None`; `best.fiducials` is only a tentative mapping and alternatives
must remain visible. Search limits can instead set `label_status=unresolved_due_to_limits`, also leaving `named_points=None`. Otherwise `named_points` exposes the geometrically distinguishable
mapping, which still needs human review and is not proven anatomical orientation.

`conflicts_with` lists other returned group indices sharing spots. Such groups may be
cross-combinations from a double punching. Separate disjoint sets may be real groups or
coincident false matches; neither case is automatically certified.

## Configuration

Defaults: native DoG scales `(0.5,0.8,1.2,2,3.5,6)` referenced to the shorter image dimension
at 1100 pixels; at most 240 candidates, 8 output sets, 2 nearest-neighbor alternatives and
4096 bounded hypotheses; anchor span ≥18% of the shorter image dimension. Similarity-fit
residual ≤0.035 is an ordinary candidate; up to 0.075 can be retained as a weak fallback.
Residuals, scores and ambiguity tolerances are provisional engineering thresholds, not
independently calibrated acceptance limits. All can be inspected in `DetectorConfig`.
Smaller/numerous sets may need explicit limits/span changes; truncation must be honored.

`to_dict()` includes `named_points` (null if unresolved) and `template_type` (null for multiple IDs) alongside the complete tentative hypotheses. A 24-window geometry-guided local search can recover weak spots from original pixels using three observed anchors; `guided_windows=0` disables it. Its bounds and use are reported in warnings. A predicted location without pixel evidence is never inserted as an observed point.

## Joint review preference (0.1.0a2)

`result.preferred_set_indices` contains zero-based indices into the unchanged full `sets`
list. `to_dict()` includes it. Each set adds `review_priority` (`preferred`, `alternative`,
`fallback`) and `preference_reason`. These are workflow suggestions, not calibrated confidence,
true group counts, accepted detections, or physical-name certification. `requires_review`
remains true even for preferred entries. All coordinate/name alternatives remain accessible.

`preferred_min_score=0.90` and `preferred_relative_score=0.90` are configurable engineering
cutoffs on the existing heuristic score. Eligible scores must exceed the larger of the
absolute cutoff and relative cutoff times the best returned score; ordinary geometry and
non-weak spot evidence are also required. A maximum-weight nonconflicting collection is
suggested using excess score above that cutoff. No eligible entries means an empty preference
list, not an empty detection result. The explicit `no_preferred_set...` warning signals this.

At most 20 eligible sets use exact optimization; larger lists use deterministic greedy
preference with `joint_preference_optimization_limited`. This bound does not discard sets.
Sets sharing observed candidate indices are considered incompatible only for this suggestion;
real groups that share a hole can remain among alternatives and must be inspected manually.
Spatially near but different candidate indices are not certified duplicates. All existing
search, output, conflict, template and A/B/C/D ambiguity flags still apply.
