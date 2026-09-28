#target illustrator

/*
  Illustrator Text Importer
  ------------------------------------------------------------
  Companion to Illustrator_Text_Extractor.jsx — writes translated /
  revised copy back into the active document.

  Why run-level and not frame-level:
    Assigning textFrame.contents (or paragraph.contents) makes the whole
    range inherit the formatting of its first character. On real artwork
    that silently destroys bold labels, superscript footnote markers and
    mixed-size runs. This script groups every character into formatting
    runs (font + size + baseline + fill) and replaces ONE RUN AT A TIME,
    back to front, so each run keeps its own attributes.

  Two matching modes:
    Glossary   — match by source text. Any CSV with a source column and a
                 target column; you pick the columns from its own header,
                 so the extractor's CSV, a bilingual sheet or a plain
                 2-column list all work. Simple, but it cannot tell two
                 identical strings apart (e.g. two superscript "1" markers
                 where one must go and one must stay).
    Positional — match by Frame + Paragraph + RangeStart, verifying the
                 recorded source text still matches what is in the document.
                 This is what makes THIS SCRIPT'S OWN DRY-RUN REPORT
                 re-importable: run a dry run, fill in the TargetText
                 column, run again. Every run is uniquely addressable and
                 a stale report is refused rather than misapplied.
    The mode is auto-selected: a CSV carrying Frame/Paragraph/RangeStart/
    SourceText columns defaults to Positional, anything else to Glossary.

  Target cell tokens:
    (empty)      leave this text unchanged
    [[DELETE]]   remove this text entirely, whitespace included
    [[SKIP]]     same as empty, but recorded as a deliberate decision

  Two ways to run it:
    1. Dry run (default ON) — changes nothing, writes a report listing
       every formatting run in the document with its font, size, offsets
       and whether the CSV matched it. This report IS the run-level
       export; use it to complete the CSV before applying.
    2. Apply — performs the replacements, then re-reads every touched
       frame and re-checks overflow, and writes a before/after report.

  Usage:
    1. Open the document. SAVE A COPY FIRST — Illustrator's undo for
       scripted text edits is unreliable across many frames.
    2. File > Scripts > Other Script...
    3. Select this .jsx file.
*/

(function () {
    var SCRIPT_NAME = "Illustrator Text Importer";
    var SCRIPT_VERSION = "1.0.0";

    var TOKEN_DELETE = "[[DELETE]]";
    var TOKEN_SKIP = "[[SKIP]]";

    if (app.documents.length === 0) {
        alert("Please open an Illustrator document first.", SCRIPT_NAME);
        return;
    }

    var doc = app.activeDocument;

    var csvFile = File.openDialog("Select the translation CSV", csvFilter());
    if (!csvFile) {
        return;
    }

    var table;
    try {
        table = parseCsv(readTextFile(csvFile));
    } catch (parseError) {
        alert("Unable to read the CSV.\n\n" + errorMessage(parseError), SCRIPT_NAME);
        return;
    }
    if (table.length < 2) {
        alert("The CSV needs a header row and at least one data row.", SCRIPT_NAME);
        return;
    }

    var settings = showSettingsDialog(doc, table[0]);
    if (!settings) {
        return;
    }

    var dict = buildDictionary(table, settings.sourceIndex, settings.targetIndex,
        settings.mode === "positional" ? positionalColumns(table[0]) : null);
    if (dict.count === 0) {
        alert("No usable source/target pairs were found in the chosen columns.", SCRIPT_NAME);
        return;
    }

    var frames = collectTextFrames(doc, settings);
    if (frames.length === 0) {
        alert("No matching editable text objects were found.", SCRIPT_NAME);
        return;
    }

    var outcome;
    try {
        outcome = process(frames, dict, settings, doc);
    } catch (runError) {
        alert("Aborted.\n\n" + errorMessage(runError), SCRIPT_NAME);
        return;
    }

    var suffix = settings.dryRun ? "_import_dryrun.csv" : "_import_report.csv";
    var defaultReport = new File(csvFile.path + "/" + baseName(doc.name) + suffix);
    var reportFile = defaultReport.saveDlg("Save the report", csvFilter());
    if (reportFile) {
        try {
            writeReport(reportFile, outcome.rows);
        } catch (reportError) {
            alert("The run finished but the report could not be saved.\n\n" +
                errorMessage(reportError), SCRIPT_NAME);
        }
    }

    alert(
        (settings.dryRun ? "Dry run complete — nothing was changed.\n\n" : "Import complete.\n\n") +
        "Text frames scanned: " + frames.length + "\n" +
        "Formatting runs found: " + outcome.runsSeen + "\n" +
        (settings.dryRun ? "Runs that WOULD change: " : "Runs changed: ") + outcome.applied + "\n" +
        "Runs deleted: " + outcome.deleted + "\n" +
        "Runs with no CSV match: " + outcome.unmatched + "\n" +
        "Left unchanged on purpose: " + outcome.skipped + "\n" +
        (outcome.flattened > 0 ? "Paragraphs rewritten with formatting flattened: " + outcome.flattened + "\n" : "") +
        "Frames overflowing after import: " + outcome.overset + "\n" +
        (outcome.failed > 0 ? "\nFAILED replacements: " + outcome.failed + " — see the report.\n" : "") +
        (reportFile ? "\nReport:\n" + reportFile.fsName : ""),
        SCRIPT_NAME
    );

    /* ---------------------------------------------------------------- UI */

    function showSettingsDialog(documentRef, header) {
        var dialog = new Window("dialog", SCRIPT_NAME + " " + SCRIPT_VERSION);
        dialog.orientation = "column";
        dialog.alignChildren = ["fill", "top"];

        var positional = positionalColumns(header);

        var modePanel = dialog.add("panel", undefined, "Matching mode");
        modePanel.orientation = "column";
        modePanel.alignChildren = "left";
        modePanel.margins = 14;
        var rbGlossary = modePanel.add("radiobutton", undefined, "Glossary — match by source text");
        var rbPositional = modePanel.add("radiobutton", undefined,
            "Positional — match by Frame + Paragraph + RangeStart (a dry-run report)");
        rbPositional.enabled = positional !== null;
        if (positional !== null) {
            rbPositional.value = true;
        } else {
            rbGlossary.value = true;
        }

        var columnPanel = dialog.add("panel", undefined, "CSV columns");
        columnPanel.orientation = "column";
        columnPanel.alignChildren = ["fill", "top"];
        columnPanel.margins = 14;

        var labels = [];
        for (var h = 0; h < header.length; h++) {
            labels.push(String(h + 1) + ". " + truncate(header[h], 46));
        }

        var sourceGroup = columnPanel.add("group");
        sourceGroup.add("statictext", undefined, "Source:");
        var sourceList = sourceGroup.add("dropdownlist", undefined, labels);
        sourceList.selection = guessColumn(header, ["source (en)", "source", "英文原文", "原文", "en"]);

        var targetGroup = columnPanel.add("group");
        targetGroup.add("statictext", undefined, "Target:");
        var targetList = targetGroup.add("dropdownlist", undefined, labels);
        targetList.selection = guessColumn(header, ["target (pt-br)", "target", "译文", "葡语译文", "translation"]);

        var scopePanel = dialog.add("panel", undefined, "Scope");
        scopePanel.orientation = "column";
        scopePanel.alignChildren = "left";
        scopePanel.margins = 14;
        var rbDocument = scopePanel.add("radiobutton", undefined, "Entire document");
        var rbSelection = scopePanel.add("radiobutton", undefined, "Current selection");
        var rbArtboard = scopePanel.add("radiobutton", undefined, "Active artboard");
        rbDocument.value = true;
        rbSelection.enabled = documentRef.selection && documentRef.selection.length > 0;

        var optionsPanel = dialog.add("panel", undefined, "Options");
        optionsPanel.orientation = "column";
        optionsPanel.alignChildren = "left";
        optionsPanel.margins = 14;

        var cbDryRun = optionsPanel.add("checkbox", undefined, "Dry run — report only, change nothing");
        var cbHidden = optionsPanel.add("checkbox", undefined, "Include hidden text and hidden layers");
        var cbLocked = optionsPanel.add("checkbox", undefined, "Include locked text and locked layers");
        var cbTrimMatch = optionsPanel.add("checkbox", undefined, "Match ignoring surrounding spaces (keeps the original spacing)");
        var cbCaseMatch = optionsPanel.add("checkbox", undefined, "Match ignoring letter case");
        var cbAllowFlatten = optionsPanel.add("checkbox", undefined, "Allow whole-paragraph rows to overwrite mixed-format paragraphs (FLATTENS formatting)");
        cbDryRun.value = true;
        cbHidden.value = false;
        cbLocked.value = true;
        cbTrimMatch.value = true;
        cbCaseMatch.value = false;
        cbAllowFlatten.value = false;

        var warning = dialog.add("statictext", undefined,
            "Save a copy of the document before applying. Scripted text edits are hard to undo in bulk.",
            { multiline: true });
        warning.characters = 62;

        var buttons = dialog.add("group");
        buttons.alignment = "right";
        buttons.add("button", undefined, "Cancel", { name: "cancel" });
        buttons.add("button", undefined, "Run", { name: "ok" });

        if (dialog.show() !== 1) {
            return null;
        }
        if (!sourceList.selection || !targetList.selection) {
            alert("Pick both a source and a target column.", SCRIPT_NAME);
            return null;
        }
        if (sourceList.selection.index === targetList.selection.index) {
            alert("The source and target columns must be different.", SCRIPT_NAME);
            return null;
        }

        return {
            mode: rbPositional.value ? "positional" : "glossary",
            sourceIndex: sourceList.selection.index,
            targetIndex: targetList.selection.index,
            scope: rbSelection.value ? "selection" : (rbArtboard.value ? "artboard" : "document"),
            dryRun: cbDryRun.value,
            includeHidden: cbHidden.value,
            includeLocked: cbLocked.value,
            trimMatch: cbTrimMatch.value,
            caseInsensitive: cbCaseMatch.value,
            allowFlatten: cbAllowFlatten.value
        };
    }

    function positionalColumns(header) {
        var frame = guessColumn(header, ["frame"]);
        var paragraph = guessColumn(header, ["paragraph"]);
        var start = guessColumn(header, ["rangestart", "range start"]);
        var source = guessColumn(header, ["sourcetext", "source text"]);
        if (frame === null || paragraph === null || start === null || source === null) {
            return null;
        }
        return { frame: frame, paragraph: paragraph, start: start, source: source };
    }

    function quoteForDetail(value) {
        return '\u201C' + truncate(safeString(value), 60) + '\u201D';
    }

    function guessColumn(header, candidates) {
        var i, j, cell;
        for (j = 0; j < candidates.length; j++) {
            for (i = 0; i < header.length; i++) {
                cell = String(header[i]).toLowerCase();
                if (cell.indexOf(candidates[j]) >= 0) {
                    return i;
                }
            }
        }
        return null;
    }

    /* -------------------------------------------------------------- CSV */

    function readTextFile(file) {
        file.encoding = "UTF-8";
        if (!file.open("r")) {
            throw new Error("The CSV could not be opened. Error " + file.error + ".");
        }
        var text;
        try {
            text = file.read();
        } finally {
            file.close();
        }
        if (text.length > 0 && text.charCodeAt(0) === 0xFEFF) {
            text = text.substring(1);
        }
        return text;
    }

    // RFC 4180: honours quoted fields containing commas, quotes and newlines.
    function parseCsv(text) {
        var rows = [];
        var row = [];
        var field = "";
        var inQuotes = false;
        var i = 0;
        var ch, next;
        var sawAny = false;

        while (i < text.length) {
            ch = text.charAt(i);

            if (inQuotes) {
                if (ch === '"') {
                    next = text.charAt(i + 1);
                    if (next === '"') {
                        field += '"';
                        i += 2;
                        continue;
                    }
                    inQuotes = false;
                    i++;
                    continue;
                }
                field += ch;
                i++;
                continue;
            }

            if (ch === '"') {
                inQuotes = true;
                sawAny = true;
                i++;
                continue;
            }
            if (ch === ",") {
                row.push(field);
                field = "";
                sawAny = true;
                i++;
                continue;
            }
            if (ch === "\r" || ch === "\n") {
                if (ch === "\r" && text.charAt(i + 1) === "\n") {
                    i++;
                }
                row.push(field);
                if (sawAny || row.length > 1 || trim(row[0]) !== "") {
                    rows.push(row);
                }
                row = [];
                field = "";
                sawAny = false;
                i++;
                continue;
            }
            field += ch;
            sawAny = true;
            i++;
        }

        row.push(field);
        if (sawAny || row.length > 1 || trim(row[0]) !== "") {
            rows.push(row);
        }
        return rows;
    }

    function buildDictionary(table, sourceIndex, targetIndex, positional) {
        var map = {};
        var byPosition = {};
        var count = 0;
        var collisions = [];

        for (var r = 1; r < table.length; r++) {
            var cells = table[r];
            if (sourceIndex >= cells.length) {
                continue;
            }
            var source = String(cells[sourceIndex]);
            var target = targetIndex < cells.length ? String(cells[targetIndex]) : "";
            if (trim(source) === "") {
                continue;
            }
            var entry = { source: source, target: target, row: r + 1, used: 0 };

            if (positional) {
                var posKey = positionKey(
                    cells[positional.frame], cells[positional.paragraph], cells[positional.start]);
                if (posKey !== null && !byPosition.hasOwnProperty(posKey)) {
                    byPosition[posKey] = entry;
                    count++;
                    continue;
                }
            }

            var key = normalizeKey(source);
            if (map.hasOwnProperty(key)) {
                if (map[key].target !== target) {
                    collisions.push(source);
                }
                continue;
            }
            map[key] = entry;
            count++;
        }

        return { map: map, byPosition: byPosition, count: count, collisions: collisions };
    }

    function positionKey(frame, paragraph, start) {
        var f = trim(frame);
        var p = trim(paragraph);
        var s = trim(start);
        if (f === "" || p === "" || s === "") {
            return null;
        }
        return "p:" + f + "|" + p + "|" + s;
    }

    // Keys are looked up in four progressively looser forms; see lookup().
    function normalizeKey(value) {
        return "k:" + String(value);
    }

    function lookup(dict, text, settings) {
        var direct = dict.map[normalizeKey(text)];
        if (direct) {
            return { entry: direct, trimmed: false, lead: "", tail: "", core: text };
        }
        if (settings.trimMatch) {
            var lead = leadingSpace(text);
            var tail = trailingSpace(text);
            var core = text.substring(lead.length, text.length - tail.length);
            var trimmed = dict.map[normalizeKey(core)];
            if (trimmed) {
                return { entry: trimmed, trimmed: true, lead: lead, tail: tail, core: core };
            }
        }
        if (settings.caseInsensitive) {
            var wanted = String(text).toLowerCase();
            var wantedTrim = trim(wanted);
            for (var key in dict.map) {
                if (!dict.map.hasOwnProperty(key)) {
                    continue;
                }
                var candidate = String(dict.map[key].source).toLowerCase();
                if (candidate === wanted) {
                    return { entry: dict.map[key], trimmed: false, lead: "", tail: "", core: text };
                }
                if (settings.trimMatch && trim(candidate) === wantedTrim) {
                    var l = leadingSpace(text);
                    var t = trailingSpace(text);
                    return {
                        entry: dict.map[key],
                        trimmed: true,
                        lead: l,
                        tail: t,
                        core: text.substring(l.length, text.length - t.length)
                    };
                }
            }
        }
        return null;
    }

    function lookupPositional(dict, context, paragraph, start, sourceText) {
        var entry = dict.byPosition[positionKey(context.frameLabel, paragraph.index, start)];
        if (!entry) {
            return null;
        }
        if (String(entry.source) !== String(sourceText)) {
            return { entry: entry, stale: true, trimmed: false, lead: "", tail: "", core: sourceText };
        }
        return { entry: entry, trimmed: false, lead: "", tail: "", core: sourceText };
    }

    /* ------------------------------------------------------------ frames */

    function collectTextFrames(documentRef, options) {
        var frames = [];
        var seen = {};
        var i;

        if (options.scope === "selection") {
            for (i = 0; i < documentRef.selection.length; i++) {
                collectFromItem(documentRef.selection[i], frames, seen);
            }
        } else {
            for (i = 0; i < documentRef.textFrames.length; i++) {
                addUnique(documentRef.textFrames[i], frames, seen);
            }
        }

        var activeIndex = documentRef.artboards.getActiveArtboardIndex();
        var activeRect = documentRef.artboards[activeIndex].artboardRect;
        var kept = [];

        for (i = 0; i < frames.length; i++) {
            var frame = frames[i];
            if (!options.includeHidden && isEffectivelyHidden(frame)) {
                continue;
            }
            if (!options.includeLocked && isEffectivelyLocked(frame)) {
                continue;
            }
            if (options.scope === "artboard" && !rectanglesIntersect(safeVisibleBounds(frame), activeRect)) {
                continue;
            }
            kept.push(frame);
        }
        return kept;
    }

    function collectFromItem(item, frames, seen) {
        if (!item) {
            return;
        }
        var typeName = safeString(item.typename);
        if (typeName === "TextFrame") {
            addUnique(item, frames, seen);
            return;
        }
        if (typeName === "TextRange" || typeName === "InsertionPoint") {
            try {
                addUnique(item.parent, frames, seen);
            } catch (ignoreParent) {}
            return;
        }
        try {
            if (item.pageItems) {
                for (var i = 0; i < item.pageItems.length; i++) {
                    collectFromItem(item.pageItems[i], frames, seen);
                }
            }
        } catch (ignoreChildren) {}
    }

    function addUnique(frame, frames, seen) {
        if (!frame || safeString(frame.typename) !== "TextFrame") {
            return;
        }
        var key = objectKey(frame);
        if (!seen[key]) {
            seen[key] = true;
            frames.push(frame);
        }
    }

    function objectKey(item) {
        try {
            if (item.uuid) {
                return "uuid:" + item.uuid;
            }
        } catch (ignoreUuid) {}
        try {
            return "z:" + item.zOrderPosition + "|" + safeString(item.contents) + "|" + item.position.join(",");
        } catch (ignoreKey) {
            return "fallback:" + Math.random();
        }
    }

    /* --------------------------------------------------------------- runs */

    /*
      Groups a frame's characters into paragraphs, and each paragraph into
      formatting runs. A run is a maximal stretch sharing font, size,
      baseline treatment and fill. Offsets are frame-global, so a TextRange
      can be built from them directly. Paragraph breaks end a run and are
      never part of one.
    */
    function analyzeFrame(frame) {
        var paragraphs = [];
        var characters;
        try {
            characters = frame.characters;
        } catch (noCharacters) {
            return paragraphs;
        }

        var total = characters.length;
        var paragraph = newParagraph(1, 0);
        var current = null;
        var i;

        for (i = 0; i < total; i++) {
            var glyph = "";
            try {
                glyph = characters[i].contents;
            } catch (noGlyph) {
                glyph = "";
            }

            if (glyph === "\r" || glyph === "\n") {
                if (current) {
                    paragraph.runs.push(current);
                    current = null;
                }
                paragraph.end = i;
                paragraphs.push(paragraph);
                paragraph = newParagraph(paragraphs.length + 1, i + 1);
                continue;
            }

            var signature = characterSignature(characters[i]);
            paragraph.text += glyph;

            if (current && current.signature === signature.key) {
                current.text += glyph;
                current.end = i + 1;
                continue;
            }
            if (current) {
                paragraph.runs.push(current);
            }
            current = {
                start: i,
                end: i + 1,
                text: glyph,
                signature: signature.key,
                font: signature.font,
                size: signature.size,
                baseline: signature.baseline
            };
        }

        if (current) {
            paragraph.runs.push(current);
        }
        paragraph.end = total;
        paragraphs.push(paragraph);

        return paragraphs;
    }

    function newParagraph(index, start) {
        return { index: index, start: start, end: start, text: "", runs: [] };
    }

    function characterSignature(character) {
        var font = "[Missing font]";
        var size = "";
        var baseline = "0";
        var fill = "";
        var attributes;

        try {
            attributes = character.characterAttributes;
        } catch (noAttributes) {
            return { key: "?", font: font, size: size, baseline: baseline };
        }
        try {
            font = attributes.textFont.name;
        } catch (noFont) {}
        try {
            size = String(roundNumber(attributes.size, 3));
        } catch (noSize) {}
        try {
            baseline = String(roundNumber(attributes.baselineShift, 3));
        } catch (noBaseline) {}
        try {
            baseline += "/" + String(attributes.baselinePosition);
        } catch (noBaselinePosition) {}
        try {
            fill = colorSignature(attributes.fillColor);
        } catch (noFill) {}

        return {
            key: font + "|" + size + "|" + baseline + "|" + fill,
            font: font,
            size: size,
            baseline: baseline
        };
    }

    function colorSignature(color) {
        if (!color) {
            return "";
        }
        var typeName = safeString(color.typename);
        try {
            if (typeName === "CMYKColor") {
                return "cmyk(" + [round1(color.cyan), round1(color.magenta), round1(color.yellow), round1(color.black)].join(",") + ")";
            }
            if (typeName === "RGBColor") {
                return "rgb(" + [round1(color.red), round1(color.green), round1(color.blue)].join(",") + ")";
            }
            if (typeName === "GrayColor") {
                return "gray(" + round1(color.gray) + ")";
            }
            if (typeName === "SpotColor") {
                return "spot(" + safeString(color.spot.name) + "," + round1(color.tint) + ")";
            }
        } catch (ignoreColor) {}
        return typeName;
    }

    function round1(value) {
        return roundNumber(Number(value), 1);
    }

    /* ------------------------------------------------------------ process */

    function process(frames, dict, settings, documentRef) {
        var rows = [];
        var stats = {
            runsSeen: 0, applied: 0, deleted: 0, unmatched: 0,
            skipped: 0, failed: 0, flattened: 0, overset: 0
        };

        rows.push([
            "Frame", "FrameName", "Layer", "Artboard", "Paragraph", "Runs", "RangeStart", "RangeEnd",
            "Font", "SizePt", "Baseline", "SourceText", "TargetText", "Action", "Detail",
            "FrameTextBefore", "FrameTextAfter", "OversetAfter", "CsvRow"
        ]);

        for (var f = 0; f < frames.length; f++) {
            var frame = frames[f];
            var frameLabel = "T" + padNumber(f + 1, 3);
            var layer = getOwningLayer(frame);
            var context = {
                frameLabel: frameLabel,
                frameName: safeString(frame.name),
                layerName: layer ? safeString(layer.name) : "",
                artboard: artboardLabel(frame, documentRef)
            };
            var before = safeString(frame.contents);
            var firstRow = rows.length;

            var paragraphs = analyzeFrame(frame);
            var plan = [];

            for (var p = 0; p < paragraphs.length; p++) {
                planParagraph(paragraphs[p], dict, settings, context, rows, plan, stats);
            }

            applyPlan(frame, plan, rows, settings, stats);

            var after = settings.dryRun ? before : safeString(frame.contents);
            var overflowing = isOversetText(frame);
            if (overflowing) {
                stats.overset++;
            }
            for (var w = firstRow; w < rows.length; w++) {
                rows[w][15] = before;
                rows[w][16] = after;
                rows[w][17] = overflowing ? "YES" : "no";
            }
        }

        appendUnusedRows(rows, dict);

        return {
            rows: rows,
            runsSeen: stats.runsSeen,
            applied: stats.applied,
            deleted: stats.deleted,
            unmatched: stats.unmatched,
            skipped: stats.skipped,
            failed: stats.failed,
            flattened: stats.flattened,
            overset: stats.overset
        };
    }

    function planParagraph(paragraph, dict, settings, context, rows, plan, stats) {
        var runs = paragraph.runs;
        stats.runsSeen += runs.length;

        if (runs.length === 0) {
            return;
        }

        var matches = [];
        var r;
        for (r = 0; r < runs.length; r++) {
            matches.push(settings.mode === "positional"
                ? lookupPositional(dict, context, paragraph, runs[r].start, runs[r].text)
                : lookup(dict, runs[r].text, settings));
        }

        // Escape hatch: a whole-paragraph CSV row can overwrite a mixed-format
        // paragraph, but only on request, because it flattens every run into
        // the leading run's attributes.
        if (runs.length > 1 && settings.allowFlatten && !anyMatch(matches)) {
            var whole = settings.mode === "positional"
                ? lookupPositional(dict, context, paragraph, paragraph.start, paragraph.text)
                : lookup(dict, paragraph.text, settings);
            if (whole) {
                emit(rows, context, paragraph, null, runs.length,
                    paragraph.start, paragraph.end, paragraph.text,
                    resolve(whole, paragraph.text, settings, plan, {
                        start: paragraph.start, end: paragraph.end
                    }, stats, true));
                stats.flattened++;
                return;
            }
        }

        for (r = 0; r < runs.length; r++) {
            var run = runs[r];
            var hit = matches[r];
            var verdict;
            if (!hit) {
                verdict = { action: "NO_MATCH", detail: "no CSV row for this text", target: "", csvRow: "" };
                stats.unmatched++;
            } else {
                verdict = resolve(hit, run.text, settings, plan,
                    { start: run.start, end: run.end }, stats, false);
            }
            emit(rows, context, paragraph, run, 1, run.start, run.end, run.text, verdict);
        }
    }

    function anyMatch(matches) {
        for (var i = 0; i < matches.length; i++) {
            if (matches[i]) {
                return true;
            }
        }
        return false;
    }

    function resolve(hit, sourceText, settings, plan, range, stats, flatten) {
        var entry = hit.entry;
        entry.used++;

        if (hit.stale) {
            stats.failed++;
            return {
                action: "REFUSED_STALE",
                detail: "CSV row " + entry.row + " expected " + quoteForDetail(entry.source) +
                    " at this position but the document has " + quoteForDetail(sourceText) +
                    "; re-run a dry run before importing",
                target: "",
                csvRow: entry.row
            };
        }

        var rawTarget = entry.target;
        var trimmedTarget = trim(rawTarget);
        var verdict = { action: "", detail: "", target: "", csvRow: entry.row };

        if (trimmedTarget === "" || trimmedTarget === TOKEN_SKIP) {
            verdict.action = "SKIP";
            verdict.detail = trimmedTarget === TOKEN_SKIP ? "explicit [[SKIP]]" : "empty target cell";
            stats.skipped++;
            return verdict;
        }
        if (trimmedTarget === TOKEN_DELETE) {
            verdict.action = "DELETE";
            verdict.detail = "text removed, whitespace included";
            verdict.target = TOKEN_DELETE;
            plan.push({ start: range.start, end: range.end, text: "", verdict: verdict });
            return verdict;
        }
        if (!flatten && (rawTarget.indexOf("\r") >= 0 || rawTarget.indexOf("\n") >= 0)) {
            verdict.action = "REFUSED";
            verdict.detail = "target contains a line break; split it into one row per paragraph";
            stats.failed++;
            return verdict;
        }

        var replacement = hit.trimmed
            ? (hit.lead + trimmedTarget + hit.tail)
            : rawTarget;
        if (replacement === sourceText) {
            verdict.action = "UNCHANGED";
            verdict.detail = "target equals source";
            verdict.target = replacement;
            stats.skipped++;
            return verdict;
        }

        verdict.action = flatten ? "REPLACE_FLATTENED" : "REPLACE";
        verdict.detail = flatten ? "whole paragraph rewritten; run formatting lost" : "";
        verdict.target = replacement;
        plan.push({ start: range.start, end: range.end, text: replacement, verdict: verdict });
        return verdict;
    }

    function emit(rows, context, paragraph, run, runCount, start, end, sourceText, verdict) {
        verdict.rowRef = rows.length;
        rows.push([
            context.frameLabel, context.frameName, context.layerName, context.artboard,
            paragraph.index, runCount, start, end,
            run ? run.font : "(mixed)", run ? run.size : "(mixed)", run ? run.baseline : "(mixed)",
            sourceText, verdict.target, verdict.action, verdict.detail,
            "", "", "", verdict.csvRow
        ]);
    }

    /*
      Applies planned replacements back to front so that offsets recorded
      earlier in the frame stay valid as the text length changes.
    */
    function applyPlan(frame, plan, rows, settings, stats) {
        var i;
        if (settings.dryRun) {
            for (i = 0; i < plan.length; i++) {
                if (plan[i].text === "") {
                    stats.deleted++;
                } else {
                    stats.applied++;
                }
            }
            return;
        }

        plan.sort(function (a, b) { return b.start - a.start; });
        for (i = 0; i < plan.length; i++) {
            var step = plan[i];
            if (replaceRange(frame, step.start, step.end, step.text)) {
                if (step.text === "") {
                    stats.deleted++;
                } else {
                    stats.applied++;
                }
            } else {
                rows[step.verdict.rowRef][13] = "FAILED";
                rows[step.verdict.rowRef][14] = "Illustrator refused the range replacement";
                stats.failed++;
            }
        }
    }

    /*
      Replaces a character range while leaving neighbouring runs untouched.
      TextRange.start / .end are writable, which is the only way to address
      a substring in Illustrator's DOM. start is set first and is always
      <= the range's current end (the frame length), so the range stays valid.
    */
    function replaceRange(frame, start, end, replacement) {
        try {
            var range = frame.textRange;
            range.start = start;
            range.end = end;
            range.contents = replacement;
            return true;
        } catch (rangeError) {
            return false;
        }
    }

    function appendUnusedRows(rows, dict) {
        appendUnusedFrom(rows, dict.map);
        appendUnusedFrom(rows, dict.byPosition);
        for (var c = 0; c < dict.collisions.length; c++) {
            rows.push([
                "", "", "", "", "", "", "", "", "", "", "",
                dict.collisions[c], "", "CSV_DUPLICATE_SOURCE",
                "same source text with a different target; the first row won", "", "", "", ""
            ]);
        }
    }

    function appendUnusedFrom(rows, index) {
        for (var key in index) {
            if (!index.hasOwnProperty(key)) {
                continue;
            }
            var entry = index[key];
            if (entry.used > 0) {
                continue;
            }
            rows.push([
                "", "", "", "", "", "", "", "", "", "", "",
                entry.source, entry.target, "CSV_ROW_UNUSED",
                "this source text was not found in the document", "", "", "", entry.row
            ]);
        }
    }

    /* ------------------------------------------------------------- output */

    function writeReport(file, rows) {
        file.encoding = "UTF-8";
        file.lineFeed = "Unix";
        if (!file.open("w")) {
            throw new Error("The report could not be opened for writing. Error " + file.error + ".");
        }
        try {
            file.write(String.fromCharCode(0xFEFF));
            var lines = [];
            for (var i = 0; i < rows.length; i++) {
                lines.push(csvRow(rows[i]));
            }
            file.write(lines.join("\n"));
        } finally {
            file.close();
        }
    }

    function csvRow(values) {
        var cells = [];
        for (var i = 0; i < values.length; i++) {
            cells.push('"' + safeString(values[i]).replace(/"/g, '""') + '"');
        }
        return cells.join(",");
    }

    /* ------------------------------------------------------------ helpers */

    function artboardLabel(frame, documentRef) {
        var bounds = safeVisibleBounds(frame);
        var centerX = (bounds[0] + bounds[2]) / 2;
        var centerY = (bounds[1] + bounds[3]) / 2;
        for (var i = 0; i < documentRef.artboards.length; i++) {
            var rect = documentRef.artboards[i].artboardRect;
            if (centerX >= rect[0] && centerX <= rect[2] && centerY <= rect[1] && centerY >= rect[3]) {
                return String(i + 1) + " - " + safeString(documentRef.artboards[i].name);
            }
        }
        return "Outside artboards";
    }

    function getOwningLayer(item) {
        var current = item;
        while (current) {
            try {
                if (current.typename === "Layer") {
                    return current;
                }
                current = current.parent;
            } catch (ignoreParent) {
                break;
            }
        }
        return null;
    }

    function isEffectivelyHidden(item) {
        var current = item;
        while (current) {
            try {
                if (current.hidden === true || current.visible === false) {
                    return true;
                }
                if (current.typename === "Document") {
                    break;
                }
                current = current.parent;
            } catch (ignoreHidden) {
                break;
            }
        }
        return false;
    }

    function isEffectivelyLocked(item) {
        var current = item;
        while (current) {
            try {
                if (current.locked === true) {
                    return true;
                }
                if (current.typename === "Document") {
                    break;
                }
                current = current.parent;
            } catch (ignoreLocked) {
                break;
            }
        }
        return false;
    }

    function isOversetText(frame) {
        try {
            return frame.kind === TextType.AREATEXT && frame.overflows === true;
        } catch (ignoreOverset) {}
        return false;
    }

    function safeVisibleBounds(item) {
        try {
            return [item.visibleBounds[0], item.visibleBounds[1], item.visibleBounds[2], item.visibleBounds[3]];
        } catch (ignoreVisible) {
            try {
                return [item.geometricBounds[0], item.geometricBounds[1], item.geometricBounds[2], item.geometricBounds[3]];
            } catch (ignoreGeometric) {
                return [0, 0, 0, 0];
            }
        }
    }

    function rectanglesIntersect(a, b) {
        return !(a[2] < b[0] || a[0] > b[2] || a[1] < b[3] || a[3] > b[1]);
    }

    function leadingSpace(value) {
        var match = String(value).match(/^\s+/);
        return match ? match[0] : "";
    }

    function trailingSpace(value) {
        var match = String(value).match(/\s+$/);
        return match ? match[0] : "";
    }

    function trim(value) {
        return safeString(value).replace(/^\s+|\s+$/g, "");
    }

    function safeString(value) {
        return value === undefined || value === null ? "" : String(value);
    }

    function truncate(value, limit) {
        var text = safeString(value);
        return text.length > limit ? text.substring(0, limit - 1) + "…" : text;
    }

    function roundNumber(value, digits) {
        var power = Math.pow(10, digits);
        return Math.round(Number(value) * power) / power;
    }

    function padNumber(value, width) {
        var text = String(value);
        while (text.length < width) {
            text = "0" + text;
        }
        return text;
    }

    function baseName(filename) {
        return safeString(filename).replace(/\.[^\.]+$/, "");
    }

    function csvFilter() {
        if ($.os.toLowerCase().indexOf("windows") >= 0) {
            return "CSV files:*.csv,All files:*.*";
        }
        return function (file) {
            return file instanceof Folder || file.name.toLowerCase().slice(-4) === ".csv";
        };
    }

    function errorMessage(error) {
        var message = error && error.message ? error.message : safeString(error);
        try {
            if (error.line) {
                message += "\nLine: " + error.line;
            }
        } catch (ignoreLine) {}
        return message;
    }
})();
