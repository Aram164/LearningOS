
## 2026-09-27 — note typed after a talk on JAX (filed by the operator)

Speaker: "backprop is just reverse-mode autodiff applied to a scalar loss".
Reverse mode: one backward sweep per *output*. Forward mode: one sweep per
*input*. Loss = 1 output, millions of inputs → reverse. jax.jvp vs jax.vjp.
