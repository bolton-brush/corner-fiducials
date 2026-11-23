# Working on corner-fiducials

## Structure and scope
- `src/corner_fiducials/`: public array-only API, types, spot extraction, geometric matching.
- `src/corner_fiducials/data/templates.json`: manually transcribed AAOF PDF coordinate tables.
- `tests/`: reproducible synthetic/API tests. No private radiographs or labels.
- `examples/`: optional decoding/debug adapters; these are not library dependencies.
- `docs/`: API, algorithm, template provenance, uncertainty and validation notes.
- `tasks.py`, `pyproject.toml`, `flake.nix`: development, build and explicit release targets.

## Development
Use `python -m pip install -e '.[dev,examples]'`, or `nix develop` with flakes enabled.
Run `invoke test`; build with `invoke build`; validate artifacts with `invoke check`.
TestPyPI/PyPI publication is an explicit release action, not part of testing or a normal commit.

## Invariants
- The public API takes an existing 2-D pixel array. Do not add filename decoding or file writes
  to `detect`, `find_candidates`, or `match_candidates`.
- Never mutate caller pixels. Coordinates are zero-based x/y in the caller's current array.
- A/B/C/D are physical PDF labels, not fixed screen-corner names. Keep uncertain name mappings
  and indistinguishable template identities explicit. Scores are not probabilities.
- Multiple hypotheses can be overlapping/mixed groups. Preserve conflict and truncation flags;
  do not turn ghosting into automatic exclusion or assert distinct sets are ground truth.
- Preserve source PDF coordinate signs, the Denver page continuation, duplicate tables, and
  collection-specific notes. Update catalogue tests for any transcription changes.
- Do not copy private images, human annotations, source manifests, credentials, local paths,
  or historically fitted private models into this repository, artifacts or examples.
- Use independent, consented, subject-separated labels for accuracy claims. Synthetic tests
  demonstrate implementation behavior, not real-image performance for a collection.

## Documentation is part of the change
Always update affected README/docs/examples and validation status when behavior, result
schemas, template support, thresholds, packaging or tests change. Distinguish executed checks
from checks merely configured, and implemented behavior from human-validated accuracy.
Keep experiment outcomes and known failures visible. Do not claim an unexecuted test passed.
