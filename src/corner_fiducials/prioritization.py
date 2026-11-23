"""Conservative joint review preferences; never discard returned hypotheses."""

from dataclasses import replace
from functools import lru_cache


def prioritize_sets(sets, config):
    """Prefer a compatible collection over a conflicting bridge hypothesis.

    Cutoffs operate on uncalibrated heuristic scores, not probabilities. Shared
    candidate spots make sets mutually exclusive for this *suggestion* only;
    overlapping real punches can still be inspected in the complete result.
    """
    if not sets:
        return (), ()
    cutoff = max(
        config.preferred_min_score,
        max(s.best.score for s in sets) * config.preferred_relative_score,
    )
    eligible = [
        i
        for i, s in enumerate(sets)
        if s.best.score > cutoff
        and s.best.geometry_error <= config.max_geometry_error
        and "weak_spot_evidence" not in s.warnings
    ]
    notes = []
    # Bound only preference optimization. The full hypothesis list is preserved.
    if len(eligible) > 20:
        notes.append("joint_preference_optimization_limited")
        chosen = []
        occupied = set()
        for i in sorted(eligible, key=lambda i: (-sets[i].best.score, i)):
            used = set(sets[i].best.candidate_indices)
            if not occupied.intersection(used):
                chosen.append(i)
                occupied.update(used)
    else:
        masks = []
        for i in eligible:
            used = set(sets[i].best.candidate_indices)
            masks.append(
                sum(
                    1 << k
                    for k, j in enumerate(eligible)
                    if used.intersection(sets[j].best.candidate_indices)
                )
            )

        @lru_cache(None)
        def solve(mask):
            if not mask:
                return 0.0, ()
            bit = mask & -mask
            k = bit.bit_length() - 1
            skip = solve(mask & ~bit)
            score, indices = solve(mask & ~masks[k])
            take = (
                score + sets[eligible[k]].best.score - cutoff,
                (eligible[k],) + indices,
            )
            if take[0] > skip[0] + 1e-12:
                return take
            if abs(take[0] - skip[0]) <= 1e-12 and take[1] < skip[1]:
                return take
            return skip

        chosen = solve((1 << len(eligible)) - 1)[1]
    chosen = set(chosen)
    preferred_spots = {p for i in chosen for p in sets[i].best.candidate_indices}
    output = []
    for i, s in enumerate(sets):
        if i in chosen:
            priority, reason = "preferred", "joint_nonconflicting_heuristic_preference"
        elif preferred_spots.intersection(s.best.candidate_indices):
            priority, reason = "alternative", "competes_with_preferred_spots"
        else:
            priority, reason = "fallback", "insufficient_relative_or_absolute_support"
        output.append(replace(s, review_priority=priority, preference_reason=reason))
    if not chosen:
        notes.append("no_preferred_set_all_hypotheses_require_manual_inspection")
    notes.append("review_preferences_are_uncalibrated_not_confirmed_detections")
    return tuple(output), tuple(notes)
