project = "Jackery Explorer 1000"
extensions = ["myst_parser"]
source_suffix = {".md": "markdown"}
root_doc = "index"
html_theme = "furo"
language = "uk"
html_static_path = ["_static"]
html_css_files = ["web_manual.css"]
from pathlib import Path
import shutil
def _copy_assets(app, exception):
    if exception is None:
        shutil.copytree(Path(__file__).parent / "assets", Path(app.outdir) / "assets", dirs_exist_ok=True)
def setup(app):
    app.connect("build-finished", _copy_assets)
