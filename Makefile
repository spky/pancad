# Redefine OS dependent commands for Windows or Linux
# WARNING: Linux commands haven't been tested
VENV = ./venv
SRC = ./src
TESTS = ./tests
DOCS = ./docs


VENV_ACTIVATE = $(VENV)/Scripts/activate
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip

INIT_PY = $(call rwildcard, $(SRC), *__init__.py)
SRC_PYTHON = $(call rwildcard, $(SRC), *.py)
PYTHON_CODE = $(filter-out $(INIT_PY), $(SRC_PYTHON))

TEST_LOGS = $(call rwildcard, $(TESTS), *.log)

DOCS_SOURCE = $(DOCS)/source
DOCS_BUILD = $(DOCS)/build
DOCS_INDEX_HTML = $(DOCS_BUILD)/html/index.html

PYCACHES = $(call rwildcard, $(SRC) $(TESTS), *__pycache__)

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

rwildcard=$(foreach d, \
	$(wildcard $(1:=/*)), \
	$(call rwildcard,$d,$2) $(filter $(subst *,%,$2),$d) \
)

all: docs

test: 
	$(PYTHON) -m unittest discover tests

docs: $(DOCS_INDEX_HTML)

$(DOCS_INDEX_HTML): $(DOCS_SOURCE) $(PYTHON_CODE)
	make -f Makefile -C $(DOCS) html

poot:
	@echo $(PYCACHES)

setup: $(VENV_ACTIVATE)
	$(PIP) install -r requirements.txt

$(VENV_ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

clean:
ifneq ($(strip $(PYCACHES)),)
	$(RMDIR) $(call FixPath, $(PYCACHES))
endif

pristine: clean
	$(RMDIR) $(call FixPath, $(VENV))