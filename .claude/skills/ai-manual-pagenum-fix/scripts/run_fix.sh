#!/bin/bash
# Apply a change spec to a .ai with Adobe Illustrator (macOS only). Never touches the original.
# Usage: tools/run_fix.sh SRC.ai SPEC.json [--dry-run] [--app "Adobe Illustrator 2026"]
#   --dry-run : open the file, check every change matches its frame, save nothing.
# Output: "<SRC without .ai>_修正.ai" next to SRC, PNGs of changed artboards in ~/Desktop/aifix_png/<model>/
set -euo pipefail
SRC="$1"; SPEC="$2"; shift 2
DRY=""; APP="Adobe Illustrator 2026"
while [ $# -gt 0 ]; do case "$1" in --dry-run) DRY="--dry-run";; --app) APP="$2"; shift;; esac; shift; done
HERE="$(cd "$(dirname "$0")" && pwd)"
MODEL="$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["model"])' "$SPEC")"
WORK="$HOME/Desktop/aifix_work.ai"; TMP="$HOME/Desktop/aifix_tmp.ai"; JSX="$HOME/Desktop/aifix_run.jsx"; PNG="$HOME/Desktop/aifix_png/$MODEL"
DST="${SRC%.ai}_修正.ai"
[ -z "$DRY" ] && [ -e "$DST" ] && { echo "already exists: $DST"; exit 1; }
python3 "$HERE/spec2jsx.py" "$SPEC" "$JSX" $DRY
PAGES="$(python3 -c 'import json,sys;print(",".join(sorted({str(c["page"]) for c in json.load(open(sys.argv[1]))["changes"] if c.get("op")!="delete_artboard"},key=int)))' "$SPEC")"
cp "$SRC" "$WORK"; mkdir -p "$PNG"; rm -f "$TMP"
osascript -l JavaScript - "$APP" "$WORK" "$JSX" "$TMP" "$PNG" "$PAGES" "$DRY" <<'JXA'
function run(argv) {
  var ai = Application(argv[0]), sa = Application.currentApplication(); sa.includeStandardAdditions = true;
  ai.doJavascript('app.userInteractionLevel=UserInteractionLevel.DONTDISPLAYALERTS;app.open(new File("' + argv[1] + '"));"opened"');
  var r = String(ai.doJavascript(sa.read(Path(argv[2]))));
  console.log(r);
  if (argv[6] === "--dry-run" || r.indexOf(" FAIL=0 ") < 0) {
    ai.doJavascript('app.activeDocument.close(SaveOptions.DONOTSAVECHANGES);"closed"');
    console.log(argv[6] === "--dry-run" ? "DRY RUN: nothing saved" : "NOT SAVED: fix the FAIL lines in the spec first");
    return;
  }
  // PNGs use post-deletion artboard indexes; verify.py does the exact page mapping
  ai.doJavascript('var d=app.activeDocument,P="' + argv[5] + '".split(",");for(var i=0;i<P.length;i++){var k=parseInt(P[i],10)-1;if(k>=d.artboards.length)continue;d.artboards.setActiveArtboardIndex(k);var o=new ExportOptionsPNG24();o.antiAliasing=true;o.artBoardClipping=true;o.horizontalScale=150;o.verticalScale=150;d.exportFile(new File("' + argv[4] + '/p"+(k+1)+".png"),ExportType.PNG24,o);}' +
    'var s=new IllustratorSaveOptions();s.compatibility=Compatibility.ILLUSTRATOR24;s.pdfCompatible=true;s.embedICCProfile=true;d.saveAs(new File("' + argv[3] + '"),s);d.close(SaveOptions.DONOTSAVECHANGES);"saved"');
  console.log("saved");
}
JXA
rm -f "$WORK"
[ -n "$DRY" ] && exit 0
[ -f "$TMP" ] || { echo "no output saved"; exit 1; }
mv "$TMP" "$DST"
echo "saved: $DST"; echo "PNGs: $PNG"
python3 "$HERE/verify.py" "$SRC" "$DST" "$SPEC"
