PYTHON ?= python3
export PYTHONPATH := src

.PHONY: run test

run:
	$(PYTHON) -m emulator

test:
	$(PYTHON) -m unittest discover -s tests -v
