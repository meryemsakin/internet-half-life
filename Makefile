PYTHON ?= python3
EVENT ?= straight-outta-compton

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -e '.[dev]'

setup-timesfm:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install -e '.[dev,timesfm]'

sample:
	.venv/bin/internet-half-life build --event $(EVENT)

forecast:
	.venv/bin/internet-half-life forecast --event $(EVENT)
	.venv/bin/internet-half-life render --event $(EVENT)

study:
	.venv/bin/internet-half-life study

test:
	.venv/bin/python -m pytest

.PHONY: setup setup-timesfm sample forecast study test
