# Redefine OS dependent commands for Windows or Linux
# WARNING: Linux commands haven't been tested
VENV = $(call FixPath, ./venv/)
VENV_ACTIVATE = $(call FixPath, $(VENV)Scripts/activate)
PYTHON = $(call FixPath, $(VENV)Scripts/python)
PIP = $(call FixPath, $(VENV)Scripts/pip)
SRC = $(call FixPath, ./src/)
PYCACHE = $(call FixPath, $(SRC)__pycache__)
TESTS = $(call FixPath, ./tests/)
TEST_LOGS = $(call FixPath, $(wildcard $(TESTS)logs/*.log))
DOCS = $(call FixPath, ./docs/)
DOCS_SOURCE = $(call FixPath, $(DOCS)/source)
DOCS_BUILD = $(call FixPath, $(DOCS)/build)
DOCS_INDEX_HTML = $(call FixPath, $(DOCS_BUILD)/html/index.html)

PYTHON_SRC_FILES = $(addprefix $(SRC), \
	generators.py \
	parsers.py \
	writers.py \
	object_wrappers.py \
	validators.py \
	file.py \
	sketch_readers.py \
	trigonometry.py \
	freecad_sketcher_to_svg.py \
	readers.py \
	element_utils.py \
	elements.py \
	svg_to_freecad_sketcher.py \
	file_handlers.py \
)

PYTHON_TEST_FILES = $(addprefix $(TESTS), \
	test_svg_parsers.py \
	test_svg_generators.py \
	test_svg_writers.py \
	test_svg_validators.py \
	test_svg_file.py \
	test_freecad_object_wrappers.py \
	test_freecad_sketch_readers.py \
	test_trigonometry.py \
	test_freecad_sketcher_to_svg_translators.py \
	test_freecad_svg_file.py \
	test_svg_readers.py \
	test_svg_element_utils.py \
	test_svg_elements.py \
	test_svg_to_freecad_sketcher_translators.py \
	test_file_handlers.py \
)


ifdef OS
	RMDIR = rd  /s /q
	RM = del /Q
	FixPath = $(subst /,\,$1)
else
	ifeq ($(shell uname), Linux)
		RMDIR = rm -rf
		RM = rm -f
		FixPath = $1
	endif
endif

all: docs

test: 
	$(PYTHON) $(call FixPath, $(TESTS)test_freecad_svg_file.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_readers.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_parsers.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_generators.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_validators.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_writers.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_file.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_freecad_object_wrappers.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_freecad_sketch_readers.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_trigonometry.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_freecad_sketcher_to_svg_translators.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_element_utils.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_elements.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_svg_to_freecad_sketcher_translators.py)
	$(PYTHON) $(call FixPath, $(TESTS)test_file_handlers.py)

$(TEST_LOGS): $(PYTHON_TEST_FILES) $(PYTHON_SRC_FILES) 

$(PYTHON_TEST_FILES): 
	echo $@
	$(PYTHON) $@


docs: $(DOCS_INDEX_HTML)

$(DOCS_INDEX_HTML): $(DOCS_SOURCE) $(PYTHON_SRC_FILES)
	make -f Makefile -C $(DOCS) html

setup: $(VENV_ACTIVATE)
	$(PIP) install -r requirements.txt

$(VENV_ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt


clean:
	make -f Makefile -C $(DOCS) clean
	$(RMDIR) $(PYCACHE)

pristine: clean
	$(RMDIR) $(VENV)