VENV = ./venv
SRC = ./src
TESTS = ./tests
DOCS = ./docs
DIST = ./dist

rwildcard=$(strip $(foreach d, \
	$(wildcard $(1:=/*)), \
	$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d) \
))

# Redefine OS dependent commands for Windows or Linux
# WARNING: Linux commands haven't been tested
ifdef OS
	RMDIR = @rd  /s /q
	RM = del /Q
	FixPath = $(subst /,\,$1)
else
	ifeq ($(shell uname), Linux)
		RMDIR = rm -rf
		RM = rm -f
		FixPath = $1
	endif
endif

VENV_ACTIVATE = $(VENV)/Scripts/activate
PYTHON = python
PIP = pip

INIT_PY := $(call rwildcard, $(SRC), *__init__.py)
SRC_PYTHON := $(call rwildcard, $(SRC), *.py)
PYTHON_CODE := $(filter-out $(INIT_PY), $(SRC_PYTHON))

TEST_LOGS := $(call rwildcard, $(TESTS), *.log)

DOCS_SOURCE := $(DOCS)/source
DOCS_BUILD := $(DOCS)/build
DOCS_DOCTREES := $(DOCS_BUILD)/doctrees
DOCS_HTML := $(DOCS_BUILD)/html
DOCS_INDEX_HTML := $(DOCS_BUILD)/html/index.html

DOCS_RST := $(call rwildcard, $(DOCS_SOURCE), *.rst)
DOCS_PY := $(DOCS_SOURCE)/conf.py
DOCS_MAKE := $(DOCS)/Makefile

PYCACHES := $(call rwildcard, $(SRC) $(TESTS), *__pycache__)

all: docs

test:
	$(PYTHON) -m unittest discover

docs: $(DOCS_INDEX_HTML)

$(DOCS_INDEX_HTML): $(PYTHON_CODE) $(DOCS_PY)
	make -f Makefile -C $(DOCS) html

setup: $(VENV_ACTIVATE)
	$(PIP) install -r requirements.txt

$(VENV_ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

build:
	$(PYTHON) -m build

clean:
ifneq ($(strip $(PYCACHES)),)
	$(RMDIR) $(call FixPath, $(PYCACHES))
endif
ifneq ($(strip $(wildcard $(DOCS_DOCTREES))),)
	$(RMDIR) $(call FixPath, $(DOCS_DOCTREES))
endif
ifneq ($(strip $(wildcard $(DOCS_HTML))),)
	$(RMDIR) $(call FixPath, $(DOCS_HTML))
endif
ifneq ($(strip $(wildcard $(DIST))),)
	$(RMDIR) $(call FixPath, $(DIST))
endif

pristine: clean
ifneq ($(strip $(wildcard $(VENV))),)
	$(RMDIR) $(call FixPath, $(VENV))
endif