# Algorithm

This is a deterministic classical image-analysis pipeline. It does not fit a private
supervised model, use a neural network, call an external service or randomly sample points.

## Candidate extraction

Normalize a copy of the pixels using robust contrast percentiles, with a min/max fallback
for sparse spots on an otherwise uniform background. At native resolution, compute
Gaussian difference responses at several scales and both polarities. Find local maxima,
then score contrast, local signal/noise, angular background consistency and elongation.
Spatially balance candidates so that one block of text does not consume the whole budget.
Suppress only very close repeated responses to the same feature; nearby punch groups can
remain separate. Circular optical/cross marks are represented by this same experimental
multiscale extractor; no validated optical-mark classifier is claimed.

## Weak-spot completion

Three strong observed spots can define a candidate template placement even when globally
normalized contrast hides a fourth hole in a light region. Ordered anchor pairs plus a
third nearby observed spot propose local search windows. Normalize those windows from the
original pixels and search actual bright/dark peaks again at native scales. Reserve room
for this local evidence in the candidate budget. Window centers are model predictions,
not detections; the matcher receives only actual observed peaks. Bounded guidance and
candidate limits remain explicit. A synthetic missing-spot test and a no-pixel-evidence
regression check exercise this distinction.

## PDF template matching and A/B/C/D

Catalogue coordinates are physical PDF A/B/C/D, including their original signs. Convert
Cartesian y-up to input-image y-down for geometric fitting. For every ordered candidate
anchor pair B,C and each distinct template geometry, predict A and D using complex
similarity invariants. Repeat with reflection, and query multiple nearby spot alternatives.
Ordered anchors plus similarity transforms cover arbitrary in-plane rotation, not just a
hard-coded A=screen-corner assignment. Convexity and distinct-point checks reject crossed
or collapsed combinations.

Fit all four points by least-squares translation/rotation/uniform scale. Normalize RMS
residual by observed RMS radius. Score shape agreement with mean spot appearance. A
looser residual bound retains poor-geometry fallback hypotheses with warnings. Strong
anisotropic scaling, shear or perspective are not silently fitted away: that could make
unrelated sets look like known templates. The PDF's affine-calibration method is not used
to certify detection identity here; a similarity-derived scale remains provisional.

## Grouping and uncertainty

Collapse identical catalogue coordinates for computation but preserve every associated
collection ID. Group explanations using the same four observed spots; keep close alternate
names and template types. A tolerance based on fit residual and pixel localization is used
to expose near-symmetry, not to assert statistically calibrated confidence. Return all
configured top groups with shared-spot conflicts. Ghosting is a reason to enumerate and
warn, not to discard the image or pretend the highest-scoring group is necessarily true.

Limits bound candidates, neighboring alternatives, hypotheses and output count. A limit
sets `truncated`; remaining candidates are still returned. When a complete group cannot be
found, return `not_found` with spot evidence rather than guessing missing A/B/C/D positions.
Perfect synthetic matching does not demonstrate reliable detection in radiographs with
anatomy, rulers, text, folds, motion artifacts or nonstandard punching devices.

Determinism refers to fixed pixels, configuration and dependency versions. Numerical rounding, local-maximum ties and rankings can differ between dependency versions. Record versions for comparisons; flake.lock pins the Nix development input.

## Joint review prioritization

After matching and bounded output, construct a conflict graph from shared observed spot
indices. Candidate groups above configurable absolute/relative heuristic cutoffs and ordinary
geometry bounds receive utility equal to score minus cutoff. Choose a maximum-utility
nonconflicting subset, so a bridge assembled from two actual groups can lose to two compatible
explanations. For more than 20 eligible groups, use bounded deterministic greedy preference
and report the optimization limit. Weak, overlapping and lower-ranked hypotheses are retained
and classified as alternatives/fallbacks; no source image is selected or excluded automatically.

These conservative 0.90 defaults were checked on a small inspected development pilot. They
are not calibrated thresholds or an independent performance result. Strong distractors can
still receive preference, and weak true sets can receive only fallback status. This step does
not refine coordinates, identify unknown template families, or resolve ambiguous A/B/C/D.
