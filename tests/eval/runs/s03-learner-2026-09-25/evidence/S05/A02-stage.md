
## 2026-09-19 — continued: 1-D lasso solved by hand (stage note draft)

Solved the 1-D lasso by hand. Minimize ½(y − w)² + λ|w|.

- If w > 0: derivative w − y + λ = 0 → w = y − λ, valid only if y > λ.
- If w < 0: w = y + λ, valid only if y < −λ.
- Otherwise the minimum is at the kink: w = 0.

So w = sign(y) · max(|y| − λ, 0) — "soft thresholding". Everything with
|y| ≤ λ is set to exactly zero. Ridge in 1-D: w = y / (1 + λ) — shrinks but
never hits zero.

That's why there is no neat matrix formula for the lasso: the solution is
piecewise, and which pieces are active depends on the data. Coordinate descent
applies this 1-D rule to one weight at a time.
