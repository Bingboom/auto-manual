# Workflow guide: environment setup

Part of the [workflow guide](../hello_auto-doc.md); its index lists the other topics.
Add new notes for this topic here, not to the hub.

## 1. Environment Setup

Before running any build, review, check, or publish command, prepare the local environment in the repository root.

### 1.1 Python Environment

The quickest way to get the environment CI uses is the setup script. It finds the
Python version pinned in `pyproject.toml`, builds `.venv` from it, installs
`requirements.lock`, and runs `python -m tools.env_preflight --strict`, which exits
non-zero while anything still differs from CI:

```bash
scripts/setup_dev_env.sh                 # macOS / Linux; --python BIN, --venv DIR, --recreate
```

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_dev_env.ps1   # -Python, -Venv, -Recreate
```

To set it up by hand instead:

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

The dependency install step is mandatory.
Do not skip `python -m pip install -r requirements.txt` or `python3 -m pip install -r requirements.txt` when preparing a fresh environment.

To reproduce the exact environment a release was built with (or to avoid
rendering drift on a long-lived checkout), install from the pinned snapshot
instead: `pip install -r requirements.lock`. Regenerate the lock only on an
intentional dependency change (`pip freeze --exclude-editable`, keep the file
header). `python build.py doctor` prints the effective toolchain versions
(Python packages, xelatex, pandoc, InDesign when present), and every release
manifest embeds the same record under a `toolchain` key — a published PDF can
always name the environment that produced it. `doctor` also reports drift
against the pinned runtime (`env.python`, from `pyproject.toml`) and
`requirements.lock` (`env.lock`) as advisory `WARN` rows; run
`python -m tools.env_preflight` for the same report without a config (`--strict`
exits 1 on any `WARN`). A local
`python -m unittest` run prints the `WARN` rows once before the first test,
so environment-only failures are named up front; it is silent when the
environment matches CI and `AUTO_MANUAL_ENV_PREFLIGHT=0` turns it off.

For fixed-layout PDF work, edit the shared LaTeX component or its
data/layout_params.csv values instead of drawing borders directly in page
RST. Titles (H1 bars), capsule subbars, safety boxes, FCC panels, inbox
cards, tip strips, rounded table frames, symbol tables with controlled
symbol continuations, app steps, and app notices are reusable objects; page
RST supplies their text and image arguments. Body WARNING, CAUTION, NOTE, and TIP label/body tables are mapped
to the same rounded callout family automatically for LaTeX PDF output.
The visible label itself always comes from the page RST / source table. The
renderer does not change `TIP` to `TIPS` (or create any other fallback word),
and a missing label stops the LaTeX/IDML handoff instead of silently inventing
copy.

### 1.2 External Tools

- PDF export requires `xelatex`.
- Word export requires `pandoc` on macOS / Linux and on non-Word-COM paths.
- If the target uses a Word reference template such as the bundle flow, install `pandoc 3.9.0.2` or newer. The bundle exporter now auto-selects a compatible installed `pandoc` when multiple versions are present, and older versions can emit an invalid `/word/media/` content-type override that makes Microsoft Word repair the generated `.docx`.
- The Python dependencies in [`requirements.txt`](../../requirements.txt) include the Sphinx theme and build libraries used by the current workflow.

If you want Gilroy only on your own machine for PDF preview, set `AUTO_MANUAL_LOCAL_GILROY_DIR` to the extracted font folder before running `pdf` or `publish`.
That folder must contain `gilroy-regular-3.otf`, `gilroy-bold-4.otf`, `Gilroy-LightItalic-12.otf`, and `Gilroy-ExtraBoldItalic-10.otf`.
If the env var is not set, or the folder is incomplete, the build keeps the normal shared fallback fonts and CI does not change.

If you only need the exact command semantics for one export path, use [`../code-as-doc/build_doc_guide.md`](../../code-as-doc/build_doc_guide.md) as the authoritative reference.
