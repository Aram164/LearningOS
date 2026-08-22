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

.PHONY: help check views materials inventory verify-materials contract test test-fast all setup garden status

help:
	@echo "make check  - validate the repository (schemas + semantic rules), then check"
	@echo "                the Job plans against the world they point at (anchors, vault"
	@echo "                paths, concept ids, anchor drift). Silent when Job is absent."
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
	@echo "make all    - check + views + materials + test"
	@echo "make setup  - create .venv, install deps, install both Git hooks (run once per clone/move)"

check:
	$(PY) tools/validate.py
	$(PY) tools/check_job_plans.py --quiet

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

all: check views materials test

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -e ".[dev]"
	cp tools/hooks/pre-commit tools/hooks/post-commit .git/hooks/
	chmod +x .git/hooks/pre-commit .git/hooks/post-commit
	@echo "setup complete: .venv created, deps installed, hooks active."
