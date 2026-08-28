# Unit Working Notes

## Title

Rust engineering fluency — ownership to PyO3

## Horizon

next

## Cadence

One 90–150 minute stage per week after the current Python foundation is stable. Begin with a closed-book prediction and a 25-minute no-AI implementation; use compiler diagnostics and official documentation before asking an agent. If AI is used, record the exact question, review every suggested change, reject anything you cannot explain, and add a test for the most plausible generated-code failure. Rebuild the stage's core mechanism without AI within 48 hours. The Stratum checkout is read-only throughout; all builds and experiments live in a disposable Rust lab.

## Outcome

Given an unfamiliar Rust or PyO3 path, independently explain ownership, borrowing, lifetime, trait, error, concurrency, and FFI behavior; design a small crate with explicit invariants; follow compiler diagnostics rather than guessing; test, document, profile, and package it; and review a Python-to-Rust boundary for copies, errors, GIL behavior, and thread safety. Evidence is a no-AI Rust/Python extension capstone and a read-only architectural comparison with Stratum, not completion of readings.
