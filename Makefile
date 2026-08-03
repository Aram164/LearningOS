# Learning OS v3 — one-word commands for humans.
# `make` with no target prints this help.

# System interpreter used only to *build* the venv; override if needed
# (e.g. `make setup PYTHON=python3.12`).
PYTHON ?= python3
VENV   := .venv

# Every other target runs on the project venv's interpreter when it exists,
# falling back to the system one otherwise. Run `make setup` once to create it —
# this keeps the tooling off the system Python and sidesteps PEP 668 /
# Homebrew "externally-managed-environment" errors on macOS.
PY := $(shell [ -x $(VENV)/bin/python ] && echo $(VENV)/bin/python || echo $(PYTHON))

.PHONY: help check views materials test all setup garden status

help:
	@echo "make check  - validate the repository (schemas + semantic rules)"
	@echo "make views  - rebuild everything under generated/ (the dashboards)"
	@echo "make status - one-screen repository state (tools/los.py; --json for machines)"
	@echo "make materials - rebuild the materials catalogue (materials/README.md + FILES.txt;"
	@echo "                browsing sources is the Obsidian Source Explorer's job since 2026-08-03)"
	@echo "make garden - rebuild views, then point at the Nebula (Garden index)"
	@echo "make test   - run the test suite"
	@echo "make all    - check + views + materials + test"
	@echo "make setup  - create .venv, install deps, install both Git hooks (run once per clone/move)"

check:
	$(PY) tools/validate.py

status:
	$(PY) tools/los.py status

views:
	$(PY) tools/generate.py

materials:
	$(PY) tools/build_materials_index.py

garden: views
	@echo "Garden index rebuilt -> generated/nebula.md"

test:
	$(PY) -m pytest -q

all: check views materials test

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements-dev.txt
	cp tools/hooks/pre-commit tools/hooks/post-commit .git/hooks/
	chmod +x .git/hooks/pre-commit .git/hooks/post-commit
	@echo "setup complete: .venv created, deps installed, hooks active."
