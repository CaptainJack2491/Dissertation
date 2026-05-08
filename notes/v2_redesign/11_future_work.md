# Future Work

## Motivation-framing follow-up

One promising follow-up is to redesign the hidden-goal manipulation so that the
underlying deceptive objective is less explicit, allowing the stated motive to
do more causal work.

The current v2 framing study isolates the effect of motive while holding the
deceptive objective nearly constant across conditions. This is useful for a
clean test of marginal framing effects, but it likely limits the size of any
observable treatment effect. If the model is already explicitly instructed to
protect a target, remain undetected, and appear objective, then changing the
reason for doing so may only have a small incremental impact.

A future study could therefore test a softer progression of hidden goals, for
example:

- `hint-only`: implies a preferred outcome or latent pressure, but does not
  explicitly instruct concealment
- `self-interest`: adds an explicit self-protective or strategic reason for
  steering the outcome
- `moralized`: adds an explicit ethical or prosocial justification for steering
  the outcome

This would answer a different question from the current study. Rather than
asking whether motive changes behaviour once covert deception is already clearly
requested, it would ask whether motive framing itself can help induce covert
deception from a softer baseline.

## Scenario calibration

Future iterations should include more systematic calibration of scenario
difficulty before running the full experiment. In particular, scenarios could be
pretested for baseline deceptiveness, ambiguity, and detectability under a
neutral prompt. This would help separate treatment effects from scenario-level
idiosyncrasies and make cross-scenario comparisons more interpretable.

## Model selection strategy

The current model set is constrained by the need for reasoning visibility, which
is necessary for the glassbox judge. That constraint is defensible, but it also
means the study may be selecting among a narrower and more behaviourally uneven
set of frontier models than would otherwise be ideal.

Future work should therefore consider a two-track model strategy:

- a reasoning-visible set for glassbox analysis
- a broader frontier set for blackbox-only replication

This would help distinguish claims that depend on internal reasoning access from
claims that generalise across more operationally relevant frontier systems.

## Blackbox evaluation

The blackbox setting remains important precisely because it is difficult. If
deceptive behaviour only appears as subtle framing, omission, or selective
emphasis in the final output, then ambiguity is part of the phenomenon rather
than merely noise in the judge.

Future work should still strengthen this component by adding a human-rated
subset, especially for borderline cases. This would provide a useful anchor for
interpreting disagreement between automated blackbox judges and for estimating
how much of the apparent noise reflects true subtlety rather than judge error.

## Sophistication and stealth

The current results suggest that internal deceptive intent and externally visible
deception can diverge. This raises a broader question about stealth: under what
conditions do models preserve deceptive intent while adapting their outputs to
better survive oversight?

This can be developed further in at least two ways:

- improve sophistication annotations, potentially by collapsing categories or
  using a smaller human-adjudicated sample
- explicitly analyse the gap between glassbox and blackbox deception rates as a
  primary object of study rather than only a methodological side result

That gap may turn out to be one of the most important findings of this line of
work, especially for settings where only final outputs are observable.

## Near-term priority

Given dissertation time constraints, these extensions should be treated as paper
follow-up work rather than incorporated into the current write-up. The current
priority is to present the existing v2 results conservatively, with careful
claim scope and clear acknowledgement of the limits imposed by model selection,
judge reliability, and the strength of the baseline hidden-goal instruction.
