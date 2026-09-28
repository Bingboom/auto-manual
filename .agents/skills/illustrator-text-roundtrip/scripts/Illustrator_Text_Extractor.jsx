#target illustrator

/*
  Illustrator Text Extractor
  ------------------------------------------------------------
  Extracts editable text from the active Adobe Illustrator document.

  Output formats:
    - TXT: readable text grouped by text object
    - CSV: suitable for Excel, localization, and review workflows
    - JSON: structured data for downstream processing

  Supported scopes:
    - Entire document
    - Current selection (including text inside selected groups)
    - Active artboard

  Usage:
    1. Open an Illustrator document.
    2. Choose File > Scripts > Other Script...
    3. Select this .jsx file.
*/

(function () {
    var SCRIPT_NAME = "Illustrator Text Extractor";
    var SCRIPT_VERSION = "1.0.0";

    if (app.documents.length === 0) {
        alert("Please open an Illustrator document first.", SCRIPT_NAME);
        return;
    }

    var doc = app.activeDocument;
    var settings = showSettingsDialog(doc);
    if (!settings) {
        return;
    }

    var records;
    try {
        records = collectRecords(doc, settings);
    } catch (collectError) {
        alert("Unable to extract text.\n\n" + errorMessage(collectError), SCRIPT_NAME);
        return;
    }

    if (records.length === 0) {
        alert("No matching editable text objects were found.", SCRIPT_NAME);
        return;
    }

    sortRecords(records, settings.sortOrder);

    var defaultName = baseName(doc.name) + "_text." + settings.format.toLowerCase();
    var outputFile = new File(defaultName).saveDlg("Save extracted text", fileFilter(settings.format));
    if (!outputFile) {
        return;
    }
    outputFile = ensureExtension(outputFile, settings.format.toLowerCase());

    try {
        writeOutput(outputFile, records, settings, doc);
        alert(
            "Extraction complete.\n\n" +
            records.length + " text object(s) exported to:\n" + outputFile.fsName,
            SCRIPT_NAME
        );
    } catch (writeError) {
        alert("Unable to save the extracted text.\n\n" + errorMessage(writeError), SCRIPT_NAME);
    }

    function showSettingsDialog(documentRef) {
        var dialog = new Window("dialog", SCRIPT_NAME + " " + SCRIPT_VERSION);
        dialog.orientation = "column";
        dialog.alignChildren = ["fill", "top"];

        var scopePanel = dialog.add("panel", undefined, "Extraction scope");
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

        var cbHidden = optionsPanel.add("checkbox", undefined, "Include hidden text and hidden layers");
        var cbLocked = optionsPanel.add("checkbox", undefined, "Include locked text and locked layers");
        var cbEmpty = optionsPanel.add("checkbox", undefined, "Include empty text objects");
        var cbWhitespace = optionsPanel.add("checkbox", undefined, "Normalize line breaks and tabs to spaces");
        cbHidden.value = false;
        cbLocked.value = true;
        cbEmpty.value = false;
        cbWhitespace.value = false;

        var outputPanel = dialog.add("panel", undefined, "Output");
        outputPanel.orientation = "column";
        outputPanel.alignChildren = ["fill", "top"];
        outputPanel.margins = 14;

        var formatGroup = outputPanel.add("group");
        formatGroup.add("statictext", undefined, "Format:");
        var formatList = formatGroup.add("dropdownlist", undefined, ["CSV", "TXT", "JSON"]);
        formatList.selection = 0;

        var sortGroup = outputPanel.add("group");
        sortGroup.add("statictext", undefined, "Order:");
        var sortList = sortGroup.add("dropdownlist", undefined, [
            "Visual order (artboard, top to bottom)",
            "Illustrator object order"
        ]);
        sortList.selection = 0;

        var cbMetadata = outputPanel.add("checkbox", undefined, "Include metadata and positioning information");
        cbMetadata.value = true;

        var buttons = dialog.add("group");
        buttons.alignment = "right";
        buttons.add("button", undefined, "Cancel", { name: "cancel" });
        buttons.add("button", undefined, "Extract", { name: "ok" });

        if (dialog.show() !== 1) {
            return null;
        }

        return {
            scope: rbSelection.value ? "selection" : (rbArtboard.value ? "artboard" : "document"),
            includeHidden: cbHidden.value,
            includeLocked: cbLocked.value,
            includeEmpty: cbEmpty.value,
            normalizeWhitespace: cbWhitespace.value,
            format: formatList.selection.text,
            sortOrder: sortList.selection.index === 0 ? "visual" : "object",
            includeMetadata: cbMetadata.value
        };
    }

    function collectRecords(documentRef, options) {
        var frames = [];
        var seen = {};
        var i;

        if (options.scope === "selection") {
            for (i = 0; i < documentRef.selection.length; i++) {
                collectTextFramesFromItem(documentRef.selection[i], frames, seen);
            }
        } else {
            for (i = 0; i < documentRef.textFrames.length; i++) {
                addUniqueFrame(documentRef.textFrames[i], frames, seen);
            }
        }

        var activeArtboardIndex = documentRef.artboards.getActiveArtboardIndex();
        var activeArtboardRect = documentRef.artboards[activeArtboardIndex].artboardRect;
        var results = [];

        for (i = 0; i < frames.length; i++) {
            var frame = frames[i];

            if (!options.includeHidden && isEffectivelyHidden(frame)) {
                continue;
            }
            if (!options.includeLocked && isEffectivelyLocked(frame)) {
                continue;
            }
            if (options.scope === "artboard" && !rectanglesIntersect(safeVisibleBounds(frame), activeArtboardRect)) {
                continue;
            }

            var text = safeString(frame.contents);
            if (options.normalizeWhitespace) {
                text = normalizeWhitespace(text);
            }
            if (!options.includeEmpty && trim(text) === "") {
                continue;
            }

            results.push(makeRecord(frame, text, documentRef, i + 1));
        }

        return results;
    }

    function collectTextFramesFromItem(item, frames, seen) {
        if (!item) {
            return;
        }

        var typeName = safeString(item.typename);
        if (typeName === "TextFrame") {
            addUniqueFrame(item, frames, seen);
            return;
        }
        if (typeName === "TextRange" || typeName === "InsertionPoint") {
            try {
                addUniqueFrame(item.parent, frames, seen);
            } catch (ignoreTextRangeParent) {}
            return;
        }

        try {
            if (item.pageItems) {
                for (var i = 0; i < item.pageItems.length; i++) {
                    collectTextFramesFromItem(item.pageItems[i], frames, seen);
                }
            }
        } catch (ignoreChildren) {}
    }

    function addUniqueFrame(frame, frames, seen) {
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
        } catch (ignoreObjectKey) {
            return "fallback:" + Math.random();
        }
    }

    function makeRecord(frame, text, documentRef, objectOrder) {
        var bounds = safeVisibleBounds(frame);
        var artboardIndex = findArtboardIndex(bounds, documentRef);
        var fontsAndSizes = getFontsAndSizes(frame);
        var layer = getOwningLayer(frame);

        return {
            objectOrder: objectOrder,
            text: text,
            name: safeString(frame.name),
            note: safeString(frame.note),
            textType: textFrameKind(frame),
            layer: layer ? safeString(layer.name) : "",
            artboardNumber: artboardIndex >= 0 ? artboardIndex + 1 : 0,
            artboardName: artboardIndex >= 0 ? safeString(documentRef.artboards[artboardIndex].name) : "Outside artboards",
            fonts: fontsAndSizes.fonts.join("; "),
            fontSizesPt: fontsAndSizes.sizes.join("; "),
            leftPt: roundNumber(bounds[0], 3),
            topPt: roundNumber(bounds[1], 3),
            rightPt: roundNumber(bounds[2], 3),
            bottomPt: roundNumber(bounds[3], 3),
            widthPt: roundNumber(bounds[2] - bounds[0], 3),
            heightPt: roundNumber(bounds[1] - bounds[3], 3),
            hidden: isEffectivelyHidden(frame),
            locked: isEffectivelyLocked(frame),
            overset: isOversetText(frame)
        };
    }

    function getFontsAndSizes(frame) {
        var fonts = [];
        var sizes = [];
        var fontSeen = {};
        var sizeSeen = {};

        try {
            var characters = frame.characters;
            for (var i = 0; i < characters.length; i++) {
                var attributes = characters[i].characterAttributes;
                var fontName = "";
                var size = "";
                try {
                    fontName = attributes.textFont.name;
                } catch (missingFont) {
                    fontName = "[Missing font]";
                }
                try {
                    size = String(roundNumber(attributes.size, 3));
                } catch (missingSize) {}

                if (fontName && !fontSeen[fontName]) {
                    fontSeen[fontName] = true;
                    fonts.push(fontName);
                }
                if (size && !sizeSeen[size]) {
                    sizeSeen[size] = true;
                    sizes.push(size);
                }
            }
        } catch (ignoreFormatting) {}

        return { fonts: fonts, sizes: sizes };
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

    function textFrameKind(frame) {
        try {
            if (frame.kind === TextType.POINTTEXT) { return "Point Text"; }
            if (frame.kind === TextType.AREATEXT) { return "Area Text"; }
            if (frame.kind === TextType.PATHTEXT) { return "Path Text"; }
        } catch (ignoreKind) {}
        return "Text";
    }

    function safeVisibleBounds(item) {
        try {
            return [item.visibleBounds[0], item.visibleBounds[1], item.visibleBounds[2], item.visibleBounds[3]];
        } catch (ignoreVisibleBounds) {
            try {
                return [item.geometricBounds[0], item.geometricBounds[1], item.geometricBounds[2], item.geometricBounds[3]];
            } catch (ignoreGeometricBounds) {
                return [0, 0, 0, 0];
            }
        }
    }

    function rectanglesIntersect(a, b) {
        return !(a[2] < b[0] || a[0] > b[2] || a[1] < b[3] || a[3] > b[1]);
    }

    function findArtboardIndex(bounds, documentRef) {
        var centerX = (bounds[0] + bounds[2]) / 2;
        var centerY = (bounds[1] + bounds[3]) / 2;
        var bestIndex = -1;
        var bestArea = 0;

        for (var i = 0; i < documentRef.artboards.length; i++) {
            var rect = documentRef.artboards[i].artboardRect;
            if (centerX >= rect[0] && centerX <= rect[2] && centerY <= rect[1] && centerY >= rect[3]) {
                return i;
            }
            var overlapWidth = Math.max(0, Math.min(bounds[2], rect[2]) - Math.max(bounds[0], rect[0]));
            var overlapHeight = Math.max(0, Math.min(bounds[1], rect[1]) - Math.max(bounds[3], rect[3]));
            var overlapArea = overlapWidth * overlapHeight;
            if (overlapArea > bestArea) {
                bestArea = overlapArea;
                bestIndex = i;
            }
        }
        return bestIndex;
    }

    function sortRecords(recordsToSort, sortOrder) {
        if (sortOrder === "object") {
            recordsToSort.sort(function (a, b) { return a.objectOrder - b.objectOrder; });
            return;
        }
        recordsToSort.sort(function (a, b) {
            if (a.artboardNumber !== b.artboardNumber) {
                return a.artboardNumber - b.artboardNumber;
            }
            if (Math.abs(a.topPt - b.topPt) > 0.5) {
                return b.topPt - a.topPt;
            }
            return a.leftPt - b.leftPt;
        });
    }

    function writeOutput(file, recordsToWrite, options, documentRef) {
        file.encoding = "UTF-8";
        file.lineFeed = "Unix";
        if (!file.open("w")) {
            throw new Error("The output file could not be opened. Error " + file.error + ".");
        }

        try {
            file.write("\uFEFF");
            if (options.format === "CSV") {
                file.write(buildCsv(recordsToWrite, options.includeMetadata));
            } else if (options.format === "JSON") {
                file.write(buildJson(recordsToWrite, options, documentRef));
            } else {
                file.write(buildTxt(recordsToWrite, options.includeMetadata, documentRef));
            }
        } finally {
            file.close();
        }
    }

    function buildCsv(recordsToWrite, includeMetadata) {
        var rows = [];
        var headers = includeMetadata ? [
            "Index", "Text", "Name", "Note", "Text Type", "Layer", "Artboard Number", "Artboard Name",
            "Fonts", "Font Sizes (pt)", "Left (pt)", "Top (pt)", "Right (pt)", "Bottom (pt)",
            "Width (pt)", "Height (pt)", "Hidden", "Locked", "Overset"
        ] : ["Index", "Text"];
        rows.push(csvRow(headers));

        for (var i = 0; i < recordsToWrite.length; i++) {
            var r = recordsToWrite[i];
            var values = includeMetadata ? [
                i + 1, r.text, r.name, r.note, r.textType, r.layer, r.artboardNumber, r.artboardName,
                r.fonts, r.fontSizesPt, r.leftPt, r.topPt, r.rightPt, r.bottomPt,
                r.widthPt, r.heightPt, r.hidden, r.locked, r.overset
            ] : [i + 1, r.text];
            rows.push(csvRow(values));
        }
        return rows.join("\n");
    }

    function csvRow(values) {
        var cells = [];
        for (var i = 0; i < values.length; i++) {
            var value = safeString(values[i]).replace(/"/g, '""');
            cells.push('"' + value + '"');
        }
        return cells.join(",");
    }

    function buildTxt(recordsToWrite, includeMetadata, documentRef) {
        var lines = [];
        lines.push("Document: " + documentRef.name);
        lines.push("Extracted: " + formatDate(new Date()));
        lines.push("Text objects: " + recordsToWrite.length);
        lines.push("");

        for (var i = 0; i < recordsToWrite.length; i++) {
            var r = recordsToWrite[i];
            lines.push("===== Text " + (i + 1) + " =====");
            if (includeMetadata) {
                lines.push("Artboard: " + r.artboardNumber + " - " + r.artboardName);
                lines.push("Layer: " + r.layer);
                lines.push("Type: " + r.textType);
                lines.push("Name: " + r.name);
                lines.push("Fonts: " + r.fonts);
                lines.push("Font sizes (pt): " + r.fontSizesPt);
                lines.push("Bounds (pt): " + [r.leftPt, r.topPt, r.rightPt, r.bottomPt].join(", "));
                lines.push("Hidden: " + r.hidden + " | Locked: " + r.locked + " | Overset: " + r.overset);
            }
            lines.push("");
            lines.push(r.text);
            lines.push("");
        }
        return lines.join("\n");
    }

    function buildJson(recordsToWrite, options, documentRef) {
        var lines = [];
        lines.push("{");
        lines.push('  "document": ' + jsonString(documentRef.name) + ",");
        lines.push('  "extractedAt": ' + jsonString(formatDate(new Date())) + ",");
        lines.push('  "scope": ' + jsonString(options.scope) + ",");
        lines.push('  "count": ' + recordsToWrite.length + ",");
        lines.push('  "items": [');

        for (var i = 0; i < recordsToWrite.length; i++) {
            var r = recordsToWrite[i];
            lines.push("    {");
            lines.push('      "index": ' + (i + 1) + ",");
            lines.push('      "text": ' + jsonString(r.text) + (options.includeMetadata ? "," : ""));
            if (options.includeMetadata) {
                lines.push('      "name": ' + jsonString(r.name) + ",");
                lines.push('      "note": ' + jsonString(r.note) + ",");
                lines.push('      "textType": ' + jsonString(r.textType) + ",");
                lines.push('      "layer": ' + jsonString(r.layer) + ",");
                lines.push('      "artboardNumber": ' + r.artboardNumber + ",");
                lines.push('      "artboardName": ' + jsonString(r.artboardName) + ",");
                lines.push('      "fonts": ' + jsonString(r.fonts) + ",");
                lines.push('      "fontSizesPt": ' + jsonString(r.fontSizesPt) + ",");
                lines.push('      "boundsPt": {"left": ' + r.leftPt + ', "top": ' + r.topPt + ', "right": ' + r.rightPt + ', "bottom": ' + r.bottomPt + '},');
                lines.push('      "widthPt": ' + r.widthPt + ",");
                lines.push('      "heightPt": ' + r.heightPt + ",");
                lines.push('      "hidden": ' + r.hidden + ",");
                lines.push('      "locked": ' + r.locked + ",");
                lines.push('      "overset": ' + r.overset);
            }
            lines.push("    }" + (i < recordsToWrite.length - 1 ? "," : ""));
        }
        lines.push("  ]");
        lines.push("}");
        return lines.join("\n");
    }

    function jsonString(value) {
        return '"' + safeString(value)
            .replace(/\\/g, "\\\\")
            .replace(/"/g, '\\"')
            .replace(/\r/g, "\\r")
            .replace(/\n/g, "\\n")
            .replace(/\t/g, "\\t")
            .replace(/[\u0000-\u001F]/g, function (character) {
                var hex = character.charCodeAt(0).toString(16);
                while (hex.length < 4) { hex = "0" + hex; }
                return "\\u" + hex;
            }) + '"';
    }

    function normalizeWhitespace(value) {
        return value.replace(/[\r\n\t]+/g, " ").replace(/ {2,}/g, " ");
    }

    function trim(value) {
        return safeString(value).replace(/^\s+|\s+$/g, "");
    }

    function safeString(value) {
        return value === undefined || value === null ? "" : String(value);
    }

    function roundNumber(value, digits) {
        var power = Math.pow(10, digits);
        return Math.round(Number(value) * power) / power;
    }

    function baseName(filename) {
        return safeString(filename).replace(/\.[^\.]+$/, "");
    }

    function ensureExtension(file, extension) {
        if (file.name.toLowerCase().slice(-(extension.length + 1)) !== "." + extension) {
            return new File(file.fsName + "." + extension);
        }
        return file;
    }

    function fileFilter(format) {
        var extension = format.toLowerCase();
        if ($.os.toLowerCase().indexOf("windows") >= 0) {
            return format + " files:*." + extension + ",All files:*.*";
        }
        return function (file) {
            return file instanceof Folder || file.name.toLowerCase().slice(-(extension.length + 1)) === "." + extension;
        };
    }

    function formatDate(date) {
        function pad(number) { return number < 10 ? "0" + number : String(number); }
        return date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate()) +
            "T" + pad(date.getHours()) + ":" + pad(date.getMinutes()) + ":" + pad(date.getSeconds());
    }

    function errorMessage(error) {
        var message = error && error.message ? error.message : safeString(error);
        try {
            if (error.line) {
                message += "\nLine: " + error.line;
            }
        } catch (ignoreErrorLine) {}
        return message;
    }
})();
