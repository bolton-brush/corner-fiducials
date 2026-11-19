# Initial implementation: 0.1.0a1

This is an experimental algorithm/library implementation for issue #1, not a validated
accuracy release. User acceptance testing of these new capabilities has not yet occurred.

## Implemented

- Importable Python package with a NumPy grayscale pixel-array API and structured outputs.
- Native bright/dark multiscale spot extraction and observed-spot-guided local completion.
- Ten AAOF PDF coordinate tables, with original A/B/C/D identity, arbitrary in-plane rotation
  and reflection, and explicit handling of identical or near-indistinguishable templates.
- Multiple punch-group hypotheses, shared-point conflicts, weak fallback evidence, unmatched
  candidates, unresolved naming and search/output limit flags. Ghosting does not cause an
  automatic image exclusion.
- Optional examples, detailed docs, repository `AGENTS.md`, PEP 517 packaging, Invoke targets,
  a pinned Nix development shell, and test/manual-publication workflows.

## Validation performed

- **132 automated tests passed** in the local CPython 3.9 environment.
- **132 automated tests passed** through the locked `nix develop` shell, using its Python
  3.14 interpreter. Nix command/flake features were enabled for the command only; global
  user settings were not modified.
- Wheel and source distribution built; Twine distribution checks passed.
- A separately installed wheel imported successfully, loaded all ten packaged templates,
  and ran synthetic pixel-array detection.
- Three previously reviewed real-image arrays were exercised as local development smoke
  cases; source content checks were unchanged. Two yielded a returned point group near the
  existing saved locations; one retained a substantial discrepancy. This is not an independent
  benchmark and supplies no A/B/C/D identity accuracy estimate.

## Not yet validated or executed

- Independent real-image accuracy for all documented template families and physical names.
- Real optical circle/cross localization and exhaustive true multi-punch grouping.
- Calibrated confidence, false-positive/missing-set rates and user acceptance.
- Remote CI results are tracked in GitHub Actions. The initial run failed during Python 3.9 provisioning on Ubuntu 26.04 before tests executed; the CI follow-up pins Ubuntu 24.04 and disables matrix fail-fast.
- PyPI/TestPyPI upload: targets/workflow are supplied; no upload has been performed.

Known limits and the unresolved development case are retained in [validation.md](validation.md)
and [uncertainty.md](uncertainty.md). Neither candidate count nor a high heuristic score is
an assertion that the returned sets or names are correct. Historical accuracy from other
implementations must not be attributed to this package.
