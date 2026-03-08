PY ?= python3
MODEL ?= JHP-2000A

.PHONY: validate build build-noview phase1-generate clean

validate:
	$(PY) tools/validate_config.py --config config.yaml
	$(PY) tools/validate_layout_params.py --csv data/layout_params.csv

build:
	$(PY) tools/build_docs.py --model $(MODEL) --clean

build-noview:
	$(PY) tools/build_docs.py --model $(MODEL) --clean --no-open

phase1-generate:
	$(PY) tools/phase1_build.py

clean:
	rm -rf docs/_build
	rm -f docs/renderers/latex/params.tex
