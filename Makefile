# Learning OS v3 — one-word commands for humans.
# `make` with no target prints this help.

# System interpreter used only to *build* the venv; override if needed
# (e.g. `make setup PYTHON=python3.14`).
PYTHON ?= python3
VENV   := .venv

# Every other target runs on the project venv's interpreter when it exists,
# falling back to the system one otherwise. Run `make setup` once to create it —
# this keeps the tooling off the system Python and sidesteps PEP 668 /
# Homebrew "externally-managed-environment" errors on macOS.
PY := $(shell [ -x $(VENV)/bin/python ] && echo $(VENV)/bin/python || echo $(PYTHON))

# Worker cap for `make test-parallel`. Four concurrent xdist workers is
# the thermal/memory budget for a laptop, not a maximum-throughput
# setting; lower it (e.g. `make test-parallel WORKERS=2`) on a hot or
# small machine.
WORKERS ?= 4

.PHONY: help check warnings views materials inventory verify-materials contract test test-fast test-group test-affected test-paired test-parallel bench lint code-check typecheck all setup setup-lean scrut hooks garden status plan-check system-check stress clean-derived commit-check

help:
	@echo "make check  - validate the repository (schemas + semantic rules)"
	@echo "make warnings - the warning delta against the recorded baseline;"
	@echo "                fails on a NEW signature, never on a deferred one"
	@echo "make views  - rebuild everything under generated/ (the dashboards)"
	@echo "make status - one-screen repository state (tools/los.py; --json for machines)"
	@echo "make materials - rebuild the materials catalogue (materials/README.md + FILES.txt;"
	@echo "                browsing sources is the Obsidian Source Explorer's job since 2026-08-03)"
	@echo "make inventory - rebuild records/materials-manifest.yaml (checksums of the"
	@echo "                external materials tree; run after adding or moving sources)"
	@echo "make verify-materials - sha256-verify the materials tree against the manifest"
	@echo "make contract - report BOTH contract versions: the stored-record format"
	@echo "                (schema_contract.py) and the published manifest shape"
	@echo "                (manifest_contract.py) - different contracts, different consumers"
	@echo "make garden - rebuild views, then point at the Nebula (Garden index)"
	@echo "make test-fast - run tests that do not load the checked-in repository state"
	@echo "make test-group G=<area> - run one area group (see tests/GROUPS.md)"
	@echo "make test-affected [BASE=main] - run the groups touched by this branch"
	@echo "make test-paired - run the Core/UI boundary tests (the pre-push gate's UI-only path)"
	@echo "make test-parallel - run the suite in parallel for fast feedback (WORKERS=4 workers max, zz population files stay serial; never the gate)"
	@echo "make bench    - run the read-only benchmark scripts (never a gate, no thresholds)"
	@echo "make test   - run the complete test suite, including full-repository checks"
	@echo "make lint   - run the defect-oriented static checks used by CI"
	@echo "make code-check - verify Core reachability, dependency cycles, and entrypoint direction"
	@echo "make clean-derived - sweep unreferenced derived-state blobs (disposable cache)"
	@echo "make plan-check - verify a curriculum revision (focused tests, no UI build)"
	@echo "make system-check - verify Core and the sibling Obsidian UI as one release pair"
	@echo "make stress - system-check + production/fuzz/concurrency stress + online URL audit"
	@echo "make all    - check + views + materials + test"
	@echo "make hooks  - install the canonical Core hooks and the paired pre-push gate"
	@echo "make setup  - create .venv, install deps, install Git hooks (run once per clone/move)"
	@echo "make setup-lean - runtime-only .venv for fresh clones (no pytest/ruff; see README)"
	@echo "make commit-check - commit-stage gate: lint, contracts, warnings, arch tests, affected tests (OD13)"

check:
	$(PY) tools/validate.py

warnings:
	$(PY) tools/warning_baseline.py --check

status:
	$(PY) tools/los.py status

views:
	$(PY) tools/generate.py

materials:
	$(PY) tools/build_materials_index.py

inventory:
	$(PY) tools/materials_manifest.py --build

verify-materials:
	$(PY) tools/materials_manifest.py --deep

contract:
	$(PY) tools/schema_contract.py
	$(PY) tools/manifest_contract.py

# Risk-based verification for a curriculum-only plan revision: full offline
# validation, the warning gate, the focused curriculum suites, projection
# regeneration, and a clean diff. Shared Core, schema, gateway, or UI changes
# still require the full paired `make system-check` release gate.
plan-check:
	$(PY) tools/validate.py --compact
	$(PY) tools/warning_baseline.py --check
	$(PY) -m pytest -q tests/test_curriculum_v2.py tests/test_unit_plan_revision.py tests/test_module_plan_warning_gate.py tests/test_vnext_boundaries.py
	$(PY) tools/generate.py
	git diff --check

garden: views
	@echo "Garden index rebuilt -> generated/nebula.md"

test:
	$(PY) -m pytest -q

test-fast:
	$(PY) -m pytest -q -m "not full_repo"

# One area group only, e.g. `make test-group G=gateway`. Groups are defined in
# tests/group_map.py and applied as markers by tests/conftest.py.
test-group:
	@test -n "$(G)" || { echo "usage: make test-group G=<area>" >&2; exit 2; }
	$(PY) -m pytest -q -m "$(G)"

# The groups touched by this branch (commits against BASE plus uncommitted
# changes). A change to shared machinery reruns everything — see tests/GROUPS.md.
# The pre-push gate passes the last stamped Core SHA as BASE when one exists,
# so a review branch reruns only what changed since its last verification.
BASE ?= main
test-affected:
	files=`$(PY) tools/affected_tests.py --base "$(BASE)"` || exit $$?; \
	if [ -z "$$files" ]; then echo "affected: no changes detected"; \
	else $(PY) -m pytest -q $$files; fi

# The Core/UI boundary tests only: every Core test that reads the live sibling
# checkout (marker `paired`, boundary pinned by tests/test_pre_push_hook.py).
# The pre-push gate runs this instead of test-affected when Core is unchanged
# against the last stamped pair. A command-line -m wins over PYTEST_ADDOPTS,
# so the hook's live_install deselection never widens this selection — and no
# paired test carries the live_install mark.
test-paired:
	$(PY) -m pytest -q -m "paired"

# Parallel fast feedback (pytest-xdist). The two zz population files are
# excluded: they aggregate session-wide witness/audit files from the same
# process, so they only mean anything serially and stay in `make test` /
# `make system-check`. This target is feedback, never the acceptance gate.
test-parallel:
	$(PY) -m pytest -q -n $(WORKERS) --dist loadscope -m "not live_install" --ignore=tests/test_scenarios_zz_refusal_sites.py --ignore=tests/test_scenarios_zz_operational_owners.py

# Discoverability only: the read-only benchmark scripts are noisy by nature,
# so they are runnable but never a gate and never part of check/CI.
bench:
	$(PY) tests/benchmark_runtime.py
	$(PY) tests/benchmark_agent_reads.py

lint:
	$(PY) -m ruff check tools tests
	$(MAKE) code-check

code-check:
	$(PY) tools/code_reachability.py

# Commit-stage gate (OD13, 6.0.3): static checks, small tests and the
# affected groups. Stops at the first failure; never replaces system-check.
commit-check:
	$(PY) -m ruff check tools tests
	.venv/bin/lint-imports --no-cache
	$(PY) tools/warning_baseline.py --check
	$(PY) -m pytest -q tests/test_arch_layers.py tests/test_arch_ratchets.py tests/test_arch_surface.py tests/test_move_map.py
	$(MAKE) test-affected BASE="$(BASE)"

clean-derived:
	$(PY) tools/diagnostics_prune.py --derived-state

# One command answers the question agents repeatedly had to reconstruct by
# hand: "is the pair I am about to rely on coherent?" It intentionally changes
# no canonical data. The UI build is deterministic and its own check refuses a
# stale contract mirror or hand-edited bundle.
typecheck:
	$(PY) -m mypy

system-check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(PY) tools/validate.py --no-report
	$(PY) tools/warning_baseline.py --check
	@test -f ../obsidian-ui/package.json || { echo "system-check: sibling ../obsidian-ui is missing" >&2; exit 1; }
# The cross-process recovery test skips itself when the UI is absent, because
# Core is usable alone. The paired gate is the one place where that skip would
# be a lie, so the harness is required here by name — a green release must mean
# the interrupted-write path was actually exercised against this Core.
	@test -f tests/test_ui_gateway_recovery.py || { echo "system-check: tests/test_ui_gateway_recovery.py is missing — the paired Gateway recovery driver cannot run" >&2; exit 1; }
	@test -f ../obsidian-ui/tests/gateway-recovery-harness.js || { echo "system-check: ../obsidian-ui/tests/gateway-recovery-harness.js is missing — the paired Gateway recovery test cannot run" >&2; exit 1; }
	@command -v node >/dev/null || { echo "system-check: node is required to run the paired Gateway recovery test" >&2; exit 1; }
	$(PY) -m pytest -q
	npm --prefix ../obsidian-ui run check
	$(PY) tools/verified_pairs.py stamp

# Deliberate deep audit. Routine work stays on `make check`; release work uses
# `make system-check`; this one command standardizes the rarer, costlier stress
# sweep without making normal edits depend on network availability.
stress: system-check
	$(PY) tools/stress_check.py
	$(PY) tools/validate.py --online --no-report

all: check views materials test

# Viability gate for `setup`: the requested interpreter must run and meet the
# floor before anything under $(VENV) is touched. Without this, a bogus or
# too-old PYTHON deleted a healthy .venv before failing (F-s13-verify-01).
# Keep the floor in sync with requires-python in pyproject.toml.
check-python:
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 12) else 1)' || { echo "setup: refusing to touch $(VENV): '$(PYTHON)' is not a usable Python >= 3.12"; exit 1; }

# What `setup` installs into the venv (appended to pip's -e flag, so the
# value must stay space-free for the recursive `setup-lean` call below).
# `setup-lean` overrides this with the runtime-only spec; a lean venv runs
# every product command but not the test suite, and the pre-commit hook
# skips its static checks loudly until ruff is installed (S09b-F3: full
# .[dev] setup measured ~8x slower warm). Never name it PIP_*: make exports
# a command-line override into every recipe's environment, and pip reads
# any PIP_<OPTION> variable as that option's default — so every pip call,
# including pip's own isolated build-dependency install, also installed
# `-e .` and `make setup-lean` failed in every fresh clone.
SETUP_SPEC ?= .[dev]
setup: check-python
	@if [ -x "$(VENV)/bin/python" ] && [ "$$($(VENV)/bin/python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" = "$$($(PYTHON) -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')" ]; then \
		echo "setup: reusing $(VENV) ($$($(VENV)/bin/python --version))"; \
	else \
		if [ -e "$(VENV)" ]; then echo "setup: removing stale $(VENV) (rebuilding with $$($(PYTHON) --version))"; rm -rf $(VENV); fi; \
		$(PYTHON) -m venv $(VENV); \
	fi
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install "-e$(SETUP_SPEC)"
	$(MAKE) hooks
	@if [ "$(SETUP_SPEC)" != "." ]; then $(MAKE) scrut; fi
	@echo "setup complete: .venv created, deps installed, hooks active."

# Fresh-clone fast path: product commands work in seconds; run plain `make
# setup` afterwards for pytest/ruff. On an existing full venv this target
# does not uninstall anything — it only matters for fresh clones.
setup-lean:
	$(MAKE) setup SETUP_SPEC=.
	@echo "setup-lean complete: runtime-only .venv (no pytest/ruff)."

# The procedure transcripts (tests/test_procedures.py, PLAN D11) run under
# Scrut v0.5.0 at $(VENV)/bin/scrut, the path that test defaults to. Each
# platform's release archive is pinned by GitHub's published SHA-256 and
# checked before anything is installed; CI pins the same Linux archive.
# `setup-lean` skips it, like pytest and ruff.
SCRUT_VERSION := v0.5.0
SCRUT_URL := https://github.com/facebookincubator/scrut/releases/download/$(SCRUT_VERSION)
scrut:
	@if [ -x "$(VENV)/bin/scrut" ] && [ "$$($(VENV)/bin/scrut --version 2>/dev/null)" = "scrut 0.5.0" ]; then \
		echo "setup: reusing $(VENV)/bin/scrut"; \
	else \
		case "$$(uname -s)-$$(uname -m)" in \
		  Darwin-arm64) asset=scrut-$(SCRUT_VERSION)-macos-aarch64.tar.gz; sha=033c6a5ebf189f85169a8f4095ef26a5a9d023ceabb20454c1a48f00b2f2a509;; \
		  Darwin-x86_64) asset=scrut-$(SCRUT_VERSION)-macos-x86_64.tar.gz; sha=c966c34f2cd9738d97e2de57ec89bb414ec1c3aba0a99794846c6a540fd83198;; \
		  Linux-x86_64) asset=scrut-$(SCRUT_VERSION)-linux-x86_64.tar.gz; sha=5c373d077a73dc4a5d4b43f3474e0f443dc72fb42f89b312ef55f934e6e6ba15;; \
		  Linux-aarch64) asset=scrut-$(SCRUT_VERSION)-linux-aarch64.tar.gz; sha=704cd54b42778dc85124739fdfaef75ac7cb1cf65c328a16f6e224c1b66021ba;; \
		  *) echo "setup: no pinned scrut archive for $$(uname -s)-$$(uname -m)" >&2; exit 1;; \
		esac; \
		tmp=$$(mktemp -d) && trap 'rm -rf "$$tmp"' EXIT && \
		curl --proto '=https' --tlsv1.2 -fsSL -o "$$tmp/$$asset" "$(SCRUT_URL)/$$asset" && \
		$(VENV)/bin/python -c 'import hashlib, sys; d = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest(); sys.exit(0 if d == sys.argv[2] else f"setup: scrut archive digest {d} is not the pinned {sys.argv[2]}")' "$$tmp/$$asset" "$$sha" && \
		tar -xzf "$$tmp/$$asset" -C "$$tmp" && \
		bin=$$(find "$$tmp" -type f -name scrut | head -n 1) && test -n "$$bin" && \
		install -m 0755 "$$bin" $(VENV)/bin/scrut && \
		test "$$($(VENV)/bin/scrut --version)" = "scrut 0.5.0" && \
		echo "setup: installed $(VENV)/bin/scrut ($(SCRUT_VERSION))"; \
	fi

hooks:
	HOOKS_DIR=`git rev-parse --git-path hooks`; mkdir -p "$$HOOKS_DIR"; \
	install -m 0755 tools/hooks/pre-commit "$$HOOKS_DIR/pre-commit"; \
	install -m 0755 tools/hooks/post-commit "$$HOOKS_DIR/post-commit"; \
	install -m 0755 tools/hooks/pre-push "$$HOOKS_DIR/pre-push"
	@if [ -d ../obsidian-ui/.git/hooks ]; then \
		install -m 0755 tools/hooks/pre-push ../obsidian-ui/.git/hooks/pre-push; \
	fi
