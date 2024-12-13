VENV = venv
VENV_ACTIVATE = $(VENV)/Scripts/activate
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip
PYCACHE = ./src/__pycache__
TESTS = ./tests

# Redefine OS dependent commands for Windows or Linux
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

svg_test: $(TESTS)/svg_d_attribute_parsing_test.py $(VENV_ACTIVATE)
	$(PYTHON) $(call FixPath, $(TESTS)/svg_d_attribute_parsing_test.py)
	$(PYTHON) $(call FixPath, $(TESTS)/test_svg_generators.py)
	$(PYTHON) $(call FixPath, $(TESTS)/test_svg_writers.py)

setup: $(VENV_ACTIVATE)
	$(PIP) install -r requirements.txt

$(VENV_ACTIVATE): requirements.txt
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

clean:
	$(RMDIR) $(call FixPath,$(PYCACHE))
	$(RMDIR) $(call FixPath,$(VENV))