#!/bin/sh
# Rebuild the branch as a series of focused commits.
#
# The brief asks for A, B and C to be shipped separately ("the canvas review
# was wrong twice before"), and the first pass bundled them into one WIP
# commit. This script resets to the certified pair and re-lands the work as
# one commit per finding, each with its own test.
#
# The procedure transcripts and the scenario recordings pin two things that
# moved for two different reasons:
#
#   * the world's canonical fingerprint (it covers system/schema and
#     system/contracts) — moved by F-05's record-shape change;
#   * the world's warning count — moved by F-01 Part A's scope rule, which
#     reports four of the demo stage's own resources.
#
# So the churn is split by cause: the digests go with F-05, the counts with
# Part A, and every commit's transcripts and recordings match the world as
# it stands at that commit.
set -e
cd "$(dirname "$0")/../../repository" || exit 1
FINAL="$1"
DIGESTS="$2"

take() {
  # take <source dir> <path>...
  source="$1"
  shift
  for path in "$@"; do
    mkdir -p "$(dirname "$path")"
    cp "$source/$path" "$path"
  done
}

commit() {
  git add "$@"
  git commit -q -F "$MSG"
  echo "--- committed: $(git log --oneline -1)"
}

# ---------------------------------------------------------------- 1. F-02
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-02 — the resume screen names the requirement the write path accepts

`los resume` printed the requirement's concept under the label
"Requirement", and `learner.observation.append` wants the requirement's
id. A reader who copied the value the label pointed at was refused by
`los observe` with "unknown requirement". The screen now labels the id —
the value the write path takes — and gives the concept its own line.

The `resume --json` payload does not change shape.

Evidence: the brief's F-02; los-canvas/reports/FINDINGS.md.
EOF
take "$FINAL" tools/learning_os/app/handlers/resume.py tests/test_resume_dossier.py
commit tools/learning_os/app/handlers/resume.py tests/test_resume_dossier.py

# ---------------------------------------------------------------- 2. F-03
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-03 — a note body may not carry its own frontmatter

`note.create` writes the note's frontmatter from the note's own fields and
then appends the body verbatim. A body that carried its own frontmatter
produced two frontmatter blocks, and the published summary became the
second block's YAML — with zero validation errors, so nothing objected.

`_precheck_note` already checked that the body is non-empty and valid
UTF-8; it now also refuses a body that opens with a frontmatter block,
and names the cause so the writer knows what to strip. The scenario suite
witnesses the new refusal site.

Evidence: the brief's F-03; los-canvas/reports/FINDINGS.md.
EOF
take "$FINAL" tools/learning_os/app/handlers/notes.py tests/test_note_create.py \
  tests/scenarios/cases/note.create.yaml \
  tests/scenarios/files/note.create/body-with-frontmatter/body.bin
# The recording pins the world's fingerprint, which moves with F-05; at this
# commit it is still the old one.
take "$DIGESTS" tests/scenarios/recorded/note.create/body-with-frontmatter.json
commit tools/learning_os/app/handlers/notes.py tests/test_note_create.py \
  tests/scenarios/cases/note.create.yaml \
  tests/scenarios/files/note.create/body-with-frontmatter \
  tests/scenarios/recorded/note.create/body-with-frontmatter.json

# ---------------------------------------------------------------- 3. F-04
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-04 — the two material resolvers agree on a fragment

`material://book/lecture.pdf#page=2` names a file and the page to open
inside it. The write path accepted that spelling, the Obsidian UI opens
the file it names (`resource-target.ts` splits the path on `[?#]`), and the
validator's resolver kept the fragment — so it warned that a file which
was there did not resolve, and the warning broke the acceptance gate
OPERATOR.md makes mandatory.

The fragment is now stripped where the reference URI is parsed, which is
where a URI's fragment stops being part of its path. The write path is
untouched: a page fragment is meaningful, and refusing it would break page
destinations. No canonical record carries a fragment today, so both sides
are behaviour-preserving for the corpus.

Evidence: the brief's F-04; los-canvas/reports/FINDINGS.md.
EOF
take "$FINAL" tools/learning_os/derive/validation/references.py tests/test_note_evidence.py
commit tools/learning_os/derive/validation/references.py tests/test_note_evidence.py

# ------------------------------------------------------------------ 4. B
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-01 B — the CLI cannot mint the app's own provenance

The `ui` channel is the system's only expression of "a human pressed a
button", and admission admits a direct-user-gesture only over it. The
Obsidian app builds its envelopes in process, so nothing it does needs the
command line — but the command line could seal one and claim the app's
provenance, which is how an agent-as-librarian got the app's authority.

`seal_envelope.py` now refuses `--channel ui` and exits 2. The channel
stays in `GATEWAY_CHANNELS` for the app, and the operator path is
untouched.

Evidence: the brief's Part B; the approval model in
tools/learning_os/app/admission.py.
EOF
take "$FINAL" tools/seal_envelope.py tests/test_gateway_v2.py
commit tools/seal_envelope.py tests/test_gateway_v2.py

# ------------------------------------------------------------------ 5. C
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-01 C — workflows 23, 24 and 27 are a stop-and-ask

Those three workflows are declared untranscribable: the slides as taught, a
real term boundary with human judgments, and a program that has actually
begun do not exist in a checkout. The procedure index says so, and an
agent that reads the manual knows to stop — an agent under task pressure
may not.

The operator contract now carries a boundary for them, workflow 23 carries
the stop in its own text, and the "Start here" table gains a row that
points at the boundary. No transcript is minted: pointing INDEX.yaml at
one would replace the index cell "Untranscribable: …" with a link and make
an unimplementable workflow look executable.

Evidence: the brief's Part C.
EOF
take "$FINAL" system/OPERATOR.md system/WORKFLOWS.md
commit system/OPERATOR.md system/WORKFLOWS.md

# ------------------------------------------------------------------ 6. A
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-01 A — a stage resource must resolve to material its module adopted

A stage could name material its module never adopted — a source registered
globally, absent from the module's source map, at a locator no route
declares — and the repository validated it with zero errors. The module's
source map is the reviewed statement of what the module covers; nothing
constrained what a stage could teach from it.

A stage resource now has to resolve to something the owning module's map
declares: a route id of that module (spelled at the top level or, for a
compact row, in the authored `material_ref`), or the same source at the
same locator as one of the module's routes. A `kind: reference` row is a
pointer and is exempt — the exemption rests on the row's meaning, not on
`scope_triage`, which the writer of the row also sets.

A warning, not an error: the route-level rule touches 1,462 rows of the
live corpus, and one validation error blocks every canonical write. The
error flip is Aram's, after the corpus migration. The baseline adopts the
measured debt in the same change, and the synthetic fixtures adopt theirs.

The `material_ref` spelling is resolved against the module's own routes
rather than trusted: the loaded study map is expanded, so a compact row's
route binding survives only in the authored bytes, and the rule reads it
there.

Evidence: the brief's Part A; los-canvas/canvas/probes/probe_scope_gap.py
(the probe's stage now reports the warning).
EOF
take "$FINAL" tools/learning_os/derive/validation/plan_rigor.py \
  operations/validation-warning-baseline.yaml tests/repo_builders.py \
  tests/scenario_fixtures.py tests/test_plan_rigor.py
# The digests move with F-05; the warning counts move with this commit.
(cd "$DIGESTS" && find . -type f | sed 's|^\./||') | while read f; do
  mkdir -p "$(dirname "$f")"
  cp "$DIGESTS/$f" "$f"
done
# The backup drill prints the data contract version, and the contract is not
# bumped until F-05 — so at this commit it is still the old number. The old
# number is the one the certified pair declared.
CONTRACT_AT_BASE=$(git show 40d8afe:system/contracts/data-contract.yaml \
  | sed -n 's/^contract_version: \([0-9]*\)$/\1/p')
CONTRACT_AT_TIP=$(sed -n 's/^contract_version: \([0-9]*\)$/\1/p' \
  "$FINAL/system/contracts/data-contract.yaml")
sed -i '' "s/^$CONTRACT_AT_TIP\$/$CONTRACT_AT_BASE/" \
  system/procedures/back-up-and-restore.md
# The recordings carry the world's own commit id, and the fixture's measured
# baseline changed with this commit — so the recordings are re-made here
# rather than carried over.
LOS_RECORD_SCENARIOS=1 .venv/bin/python -m pytest -q --no-header \
  -p no:randomly tests/test_scenarios_effects.py >/dev/null
commit tools/learning_os/derive/validation/plan_rigor.py \
  operations/validation-warning-baseline.yaml tests/repo_builders.py \
  tests/scenario_fixtures.py tests/test_plan_rigor.py system/procedures \
  tests/scenarios

# ----------------------------------------------------------------- 7. F-05
MSG=$(mktemp)
cat > "$MSG" <<'EOF'
fix(core): F-05 — the promotion's verification must name a content-bound artifact

A Master's promotion package could carry `verification.evidence[]` asserting
"official-academic" over a URL that resolves to nothing, and the promotion
landed: every other gate on that path was real, and the one thing missing
was the external fact.

The write path is offline-first — the thirty-day rule is a date check, and
`los validate --online` is a separate, explicitly online audit — so what a
canonical write can require is that the claim is attributable: each
evidence item now names the review that checked it and a local document
whose bytes are bound by a digest, and the document has to say what was
checked. A promotion whose evidence carries no such artifact is refused,
and the digest means the document cannot be edited afterwards without
invalidating the promotion that cited it.

This does not make the external fact true. It makes the claim name the
artefact it rests on, so a reviewer can read what was checked.

The promotion package's accepted shape changes with it, so the data
contract is bumped, and the world's canonical fingerprint moves with it —
which is what the procedure transcripts and the scenario recordings pin.

Evidence: the brief's F-05; los-canvas/reports/t05.
EOF
take "$FINAL" system/schema/master-planning-promotion.schema.json \
  system/contracts/data-contract.yaml tools/learning_os/app/admin/masters_planning.py \
  tests/test_master_promotion.py
# The recordings carry the world's own commit id. The world's tree changes
# with the schema, so the recordings made at the final state are the ones
# this commit needs — the snapshot holds them.
(cd "$FINAL" && find system/procedures tests/scenarios -type f) | while read f; do
  mkdir -p "$(dirname "$f")"
  cp "$FINAL/$f" "$f"
done
commit system/schema/master-planning-promotion.schema.json \
  system/contracts/data-contract.yaml tools/learning_os/app/admin/masters_planning.py \
  tests/test_master_promotion.py system/procedures tests/scenarios
