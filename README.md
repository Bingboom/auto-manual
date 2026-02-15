# HB Manual Demo Repo v2

Adds component macros to mimic Fig2/Fig3:
- hbAdmonition (DANGER/WARNING/...)
- hbTwoColBox (two-column grey box)
- hbSymbolsTableStart/Row/End
- hbCardGridStart/hbCard/hbCardGridEnd
- hbTipBar

## Build

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/gen_rst.py

cd docs
rm -rf _build
sphinx-build -b latex . _build/latex

cd _build/latex
xelatex hb_manual_demo.tex
xelatex hb_manual_demo.tex
```
