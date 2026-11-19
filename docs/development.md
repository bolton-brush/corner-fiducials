# Development and releases

Use Python 3.9+ and `python -m pip install -e '.[dev,examples]'`. Core dependencies are NumPy,
headless OpenCV and SciPy. Pillow is optional and used only in examples. The public API can
be imported by other packages without importing file adapters or starting a server.

`invoke test` runs synthetic/API tests. `invoke build` produces wheel/sdist via PEP 517;
`invoke build --no-isolation` uses an already prepared environment. `invoke check` checks
those artifacts with Twine. The CI workflow configures the same checks; configuration is
not evidence that a remote run has passed.

`nix develop` supplies the interpreter and dependencies through `flake.nix`/`flake.lock`.
It assumes the Nix installation has `nix-command` and `flakes` enabled. Otherwise use the
command-line feature flags documented in README; do not silently change a user's settings.
The shell follows the standard [Python environment pattern](https://nix.dev/guides/recipes/python-environment.html).

Publication is separate from testing/committing. `invoke publish` defaults to TestPyPI;
`invoke publish --repository pypi` is explicit. These require configured account credentials
and ownership/availability of the project name. No passwords or tokens belong in Git.
Alternatively, manually dispatch `publish-distribution` after configuring the relevant
PyPI/TestPyPI Trusted Publisher and matching GitHub environment (`pypi` or `testpypi`).
The workflow uses the [PyPA release guidance](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/).
Nothing uploads to a package index merely because a commit is pushed.

When changing code, update the corresponding docs and tests. Never publish private image
fixtures, old human annotations or source-inventory manifests. Real-image validation belongs
in an ignored local directory and must report its cohort, label independence, thresholds,
per-point errors, full-set error rate, missing detections and ambiguous/mixed-set behavior.
A previously inspected or tuned cohort is development evidence, not an independent test.

CI pins Ubuntu 24.04, whose official setup-python manifest provides all matrix versions, rather than following the moving ubuntu-latest image. Matrix fail-fast is disabled so one environment cannot cancel the others. Checkout/setup-python use Node 24 action releases. The initial remote run failed during Python 3.9 provisioning on Ubuntu 26.04, before any package tests ran; see the [workflow history](https://github.com/bolton-brush/corner-fiducials/actions/workflows/tests.yml) for subsequent executed results.
