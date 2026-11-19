# Validation status of the initial library implementation

This document is an evidence ledger, not an accuracy claim. The user has **not yet performed
acceptance testing of this new library**. All new behaviors remain experimental.

## Executed locally

- **132 automated tests passed** in the local Python environment. Coverage includes all ten
  PDF coordinate tables; 0/90/180/270-degree and arbitrary-angle rotations and reflection of candidate geometry;
  synthetic pixel detection for each table; uint8/uint16/float and both polarities;
  deterministic output; caller-array immutability; incomplete/blank/invalid input; identical
  templates; name ambiguity; multiple translated punch groups and conflicting mixed groups;
  optical-cross smoke behavior; explicit limits; guided weak-point recovery and the absence
  of fabricated center coordinates when pixel evidence is absent.
- Test assertions retain the true naming explanation among close alternatives where the
  geometry is ambiguous; they do **not** claim every template has uniquely identifiable names.
- The optical-cross pixel check is a smoke test. It does not validate exact ring/cross-center
  localization, all optical appearances or real optical radiographs.
- Three previously reviewed private radiographs were exercised locally as **development
  smoke tests**, with source content checks unchanged. After adding guided local search,
  two contained a returned group near previously saved locations; one remained substantially
  different from the saved locations. All returned multiple, bounded, uncertain candidates.
  There is no new independent A/B/C/D identity truth, and this tiny inspected cohort cannot
  support a general accuracy estimate. Images, labels, filenames, paths and per-image records
  are not part of the repository or distribution.

The first broad-search prototype passed synthetic tests but missed weak real-image points
because strong anatomy/text responses exhausted the spot budget. Three-observed-point-guided
local rescanning was added in response. This is development on observed examples, not a
held-out improvement claim. An out-of-pattern/mismatched-label case remains unresolved.

## Build and environment checks

- Wheel/sdist construction, Twine checks, installed-wheel template loading and a synthetic
  array-detection smoke test passed locally.
- The locked Nix development shell was entered and all 132 tests passed on its Python 3.14
  interpreter. This is an executed check, not only a supplied lock/configuration file.
- Remote CI outcomes are tracked in the [workflow history](https://github.com/bolton-brush/corner-fiducials/actions/workflows/tests.yml). The initial run failed while provisioning Python 3.9 on Ubuntu 26.04, before algorithm tests executed. CI now pins Ubuntu 24.04 and runs matrix jobs independently; configuration alone is not evidence that a remote run passed.
- TestPyPI/PyPI targets are supplied; no distribution upload is performed merely by committing.

## Not independently validated

- Real-image detection and A/B/C/D identity for each of the ten documented coordinate tables.
- Newer inconsistent Forsyth appearances or any collection absent from the PDF tables.
- Exact optical circle/cross centers on real images.
- Exhaustive enumeration and correct grouping of real multiple punchings/ghosting.
- Michigan outermost-corner decisions in complex extra-mark films.
- Calibrated false-positive, missing-set, label-error or multiple-set confidence probabilities.
- Generalization to new subjects, scan distortions, margins, anatomical/text distractors,
  or all dependency/platform versions.

## How to validate next

Use consented independent subjects and label actual observed A/B/C/D identity, punch-template
family, number of real groups, and ambiguous/unlabelable cases. Separate template identity
ambiguity from a wrong point. Report point distances with stated image units and tolerance,
whole-set correctness, missed sets, wrong extra sets, wrong labels, conflict/truncation rates,
and the number of images needing review. Have a reviewer resolve the current disagreement.
Keep inspected/tuned images in development rather than relabeling them as a new test set.
Do not equate candidate count with true punch-group count or convert this alpha's heuristic
score to a success probability. Historical accuracy from another implementation is not this
library's accuracy.
