PY ?= python3

.PHONY: build build-noview lint clean

lint:
	$(PY) tools/lint_layout_params.py

build:
	$(PY) tools/build.py --open

build-noview:
	$(PY) tools/build.py

clean:
	rm -rf docs/_build
	rm -f docs/latex_theme/params.tex
