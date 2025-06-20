# Fandango Makefile. For development only.

# Settings
MAKEFLAGS=--warn-undefined-variables

# Programs
PYTHON = python
PYTEST = pytest
ANTLR = antlr
BLACK = black
PIP = pip
SED = sed
PAGELABELS = $(PYTHON) -m pagelabels
REQUIREMENTS = requirements.txt


# Default targets
web: requirements.txt parser html
all: web pdf

.PHONY: web all parser install dev-tools docs html latex pdf


## Requirements

requirements.txt:	pyproject.toml
	pip-compile $<

# Install tools for development
UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
# Mac
SYSTEM_DEV_TOOLS = antlr pdftk-java graphviz
SYSTEM_DEV_INSTALL = brew install
else
# Linux
SYSTEM_DEV_TOOLS = antlr pdftk-java graphviz
SYSTEM_DEV_INSTALL = apt-get install
endif


dev-tools: system-dev-tools
	pip install -U black
	pip install -U jupyter-book pyppeteer ghp-import pagelabels
	pip install -U graphviz

system-dev-tools:
	$(SYSTEM_DEV_INSTALL) $(SYSTEM_DEV_TOOLS)


## Tests
TESTS = tests
TEST_SOURCES = $(wildcard $(TESTS)/*.py $(TESTS)/resources/*)

.PHONY: test tests
test tests:
	$(PYTEST)

## Installation
.PHONY: install install-test install-tests
install:
	$(PIP) install -r $(REQUIREMENTS)
	$(PIP) install -e .

# We separate _installing_ from _running_ tests
# so we can run 'make tests' quickly (see above)
# without having to reinstall things
install-test install-tests:
	$(PIP) install -r $(REQUIREMENTS)
	$(PIP) install pytest
	$(PIP) install -e ".[test]"

# Experiments
install-evaluation install-evaluations:
	$(PIP) install -r $(REQUIREMENTS)
	$(PIP) install -e ".[evaluation]"

# Uninstallation
uninstall:
	$(PIP) uninstall -y fandango-learn

# python -m evaluation.vs_isla.run_evaluation
.PHONY: evaluation evaluate experiment experiments

evaluation evaluate:
	$(PYTHON) -m evaluation.run_evaluation

experiment experiments:
	$(PYTHON) -m evaluation.experiments.run_experiments

clean-pip:
	$(PIP) freeze | xargs $(PIP) uninstall -y

build-docker:
	docker build -t fandango-learn .

run-docker:
	docker run -it fandango-learn /bin/bash

run-docker-eval:
	docker run -it fandango-learn-eval /bin/bash