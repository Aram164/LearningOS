# Learning OS v3 — one-word commands for humans.
# `make` with no target prints this help.

PY ?= python3

.PHONY: help check views test all setup

help:
	@echo "make check  - validate the repository (schemas + semantic rules)"
	@echo "make views  - rebuild everything under generated/ (the dashboards)"
	@echo "make test   - run the test suite"
	@echo "make all    - check + views + test"
	@echo "make setup  - install Python deps and both Git hooks (run once per clone/move)"

check:
	$(PY) tools/validate.py

views:
	$(PY) tools/generate.py

test:
	$(PY) -m pytest -q

all: check views test

setup:
	$(PY) -m pip install --upgrade pyyaml "jsonschema>=4" pytest \
		|| $(PY) -m pip install --break-system-packages --upgrade pyyaml "jsonschema>=4" pytest
	cp tools/hooks/pre-commit tools/hooks/post-commit .git/hooks/
	chmod +x .git/hooks/pre-commit .git/hooks/post-commit
	@echo "setup complete: deps installed, hooks active."
