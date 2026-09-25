# Temperature in softmax and in annealing — AI-derived transcription

*Provenance: AI-derived (manual-bundle provider) from the Garden seed
`knowledge/garden/temperature-everywhere.md`. The seed is unchanged; this is
not the learner's own wording.*

## The seed's question

Softmax temperature `exp(z/T)` and the annealing acceptance probability
`exp(−Δ/T)` are both "exponentials divided by T". Coincidence or the same
physics?

## Discussion summary

Not a coincidence — both are the Boltzmann (Gibbs) distribution from
statistical mechanics, `p(state) ∝ exp(−E(state) / T)` (with Boltzmann's
constant absorbed into T).

- **Softmax:** read each logit as a negative energy, `E_i = −z_i`. Then
  `softmax(z/T)_i = exp(−E_i/T) / Σ_j exp(−E_j/T)` is exactly the Boltzmann
  distribution over the classes. High T → near-uniform; T → 0 → all mass on the
  lowest-energy (largest-logit) class.
- **Simulated annealing:** the Metropolis acceptance rule `min(1, exp(−ΔE/T))`
  is the rule that makes the random walk's long-run distribution the Boltzmann
  distribution over states. Lowering T slowly concentrates that distribution on
  low-energy (low-cost) states — the "cooling metal" picture.

So T plays the same role in both: it sets how strongly probability prefers
low-energy states. Softmax samples the distribution directly (few states);
annealing samples it by a Markov chain (too many states to enumerate).

## Open for the learner

- Does the Boltzmann reading explain why temperature scaling is used for
  calibration?
- Related notes to read side by side: note-softmax-temperature,
  note-simulated-annealing, note-markov-chains-stationary.
