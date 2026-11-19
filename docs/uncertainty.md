# Uncertainty is part of the result

A result is evidence for review, not an automatic image-selection decision.

- **Identical templates:** original Forsyth, Fels and ordinary Oregon cannot be distinguished
  from their coordinate geometry. Return all matching IDs.
- **Near-symmetry:** if several assignments fit within localization uncertainty, A/B/C/D
  remain ambiguous. `named_points=None`; tentative mappings remain in hypotheses.
- **Ghosting/multiple punching:** return multiple groups. Mixed groups can share spots with
  other groups; preserve `conflicts_with`. Do not count every returned group as a true set.
- **Weak shape or spots:** keep fallback explanations marked `poor_geometry_fallback` or
  `weak_spot_evidence`, rather than claiming confident names or simply deleting the image.
- **No complete fit:** return the retained spot candidates and `not_found`. Do not fabricate
  the missing point or invent an undocumented template.
- **Bounded search:** `truncated=True` means not all possibilities were returned. Small
  nested sets, many groups or closely spaced spots may exceed default search assumptions.
- **Michigan side marks:** an interior compatible group must not be assumed to be the outer
  four. The current matcher returns a verification warning rather than certifying this rule
  from geometry alone.
- **Appearance ambiguity:** rulers, text and anatomy can resemble punch spots. Optical
  circle/cross support has only synthetic evidence in the initial implementation.

All alpha results set `requires_review=True`. Scores are deterministic ranking values, not
calibrated probabilities or a guarantee that the highest-ranked hypothesis is correct.
There are no independent human A/B/C/D orientation labels for every supported collection.
A provisional pixels/mm fit does not independently establish anatomical scale.
