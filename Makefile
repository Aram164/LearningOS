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

.PHONY: help check warnings views materials inventory verify-materials contract test test-fast lint all setup hooks garden status system-check stress

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
	@echo "make test   - run the complete test suite, including full-repository checks"
	@echo "make lint   - run the defect-oriented static checks used by CI"
	@echo "make system-check - verify Core and the sibling Obsidian UI as one release pair"
	@echo "make stress - system-check + production/fuzz/concurrency stress + online URL audit"
	@echo "make all    - check + views + materials + test"
	@echo "make hooks  - install the canonical Core hooks and the paired pre-push gate"
	@echo "make setup  - create .venv, install deps, install Git hooks (run once per clone/move)"

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

garden: views
	@echo "Garden index rebuilt -> generated/nebula.md"

test:
	$(PY) -m pytest -q

test-fast:
	$(PY) -m pytest -q -m "not full_repo"

lint:
	$(PY) -m ruff check tools tests

# One command answers the question agents repeatedly had to reconstruct by
# hand: "is the pair I am about to rely on coherent?" It intentionally changes
# no canonical data. The UI build is deterministic and its own check refuses a
# stale contract mirror or hand-edited bundle.
system-check:
	$(MAKE) lint
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

# Deliberate deep audit. Routine work stays on `make check`; release work uses
# `make system-check`; this one command standardizes the rarer, costlier stress
# sweep without making normal edits depend on network availability.
stress: system-check
	$(PY) tools/stress_check.py
	$(PY) tools/validate.py --online --no-report

all: check views materials test

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"
	$(MAKE) hooks
	@echo "setup complete: .venv created, deps installed, hooks active."

hooks:
	install -m 0755 tools/hooks/pre-commit .git/hooks/pre-commit
	install -m 0755 tools/hooks/post-commit .git/hooks/post-commit
	install -m 0755 tools/hooks/pre-push .git/hooks/pre-push
	@if [ -d ../obsidian-ui/.git/hooks ]; then \
		install -m 0755 tools/hooks/pre-push ../obsidian-ui/.git/hooks/pre-push; \
	fi
