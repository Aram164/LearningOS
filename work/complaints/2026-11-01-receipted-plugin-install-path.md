# Hosted accepted plugin installation needs a reusable receipted path

Task: install the exact accepted Core c61c645d220aa2bbe84855222201936b5170cedb / UI de1866589ff383fce5a6a9c909b8d92edc239fe7 artifact into the authorized live vault. The tracked UI main.js embedded a stale build fingerprint; accepted hosted bytes therefore produced a deliberate tracked output modification. The ordinary installer invokes local UI checks, while this campaign permits full acceptance only in hosted CI.

A campaign-local deployment adapted the installer transaction routines: independently verified receipt/assets, exact live pair and dirty-state allowlist, preserved protected records and vault-owned data.json, verified every installed asset, install:status and running Obsidian Diagnostics. Installation succeeded; this is recorded maintenance complexity, not an assertion of a failed transaction or data loss.

Investigate an explicit accepted-artifact mode in the existing sibling UI install.py, taking a verified receipt and corroborated hosted run identity. Retain exact pair, clean build provenance, declared asset hashes, transaction recovery and settings preservation. Test stale/tampered receipts, wrong heads, partial install/recovery and unchanged vault-owned data. Deliberately resolve tracked generated bundle policy; do not silently hide source modifications or skip gates. This complaint proposes later scoped work only.

Proof retained externally: LearningOS/workbench/gemini-arena-2026-11-01/evidence/stage1-installed.json, stage1 install/status and UI observations, and scripts/deploy_accepted_plugin.py / deploy_receipted_pair.py. Owner: Aram164/learningos-obsidian-ui. The final campaign issue report retains the filed URL; no public upload of private settings or learner records is intended.

Issue: https://github.com/Aram164/learningos-obsidian-ui/issues/12
