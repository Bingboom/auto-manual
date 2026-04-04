PY ?= python
CONFIG ?= config.us.yaml
OPEN_FLAG :=
NO_CLEAN_FLAG :=

ifeq ($(OPEN),1)
OPEN_FLAG := --open
endif

ifeq ($(NO_CLEAN),1)
NO_CLEAN_FLAG := --no-clean
endif

.PHONY: validate rst word html pdf all clean

validate:
	$(PY) build.py validate --config $(CONFIG)

rst:
	$(PY) build.py rst --config $(CONFIG) $(OPEN_FLAG) $(NO_CLEAN_FLAG)

word:
	$(PY) build.py word --config $(CONFIG) $(OPEN_FLAG) $(NO_CLEAN_FLAG)

html:
	$(PY) build.py html --config $(CONFIG) $(OPEN_FLAG) $(NO_CLEAN_FLAG)

pdf:
	$(PY) build.py pdf --config $(CONFIG) $(OPEN_FLAG) $(NO_CLEAN_FLAG)

all:
	$(PY) build.py all --config $(CONFIG) $(OPEN_FLAG) $(NO_CLEAN_FLAG)

clean:
	$(PY) build.py clean --config $(CONFIG)

