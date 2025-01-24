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


## Test
test tests:
	$(PIP) install -e ".[test]"
	$(PYTEST)


# Installation
install:
	$(PIP) install -e .

# Uninstallation
uninstall:
	$(PIP) uninstall -y fandangoLearner

