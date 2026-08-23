/* InDesign final-mile runner. HB_JOB_PATH is injected by tools/indesign_finalize.py. */
(function () {
    function jsonParse(text) {
        return eval("(" + text + ")");
    }

    function jsonStringify(value) {
        if (value === null) { return "null"; }
        if (typeof value === "string") {
            var escaped = "";
            for (var ci = 0; ci < value.length; ci += 1) {
                var character = value.charAt(ci);
                var code = value.charCodeAt(ci);
                if (character === "\\") { escaped += "\\\\"; }
                else if (character === '"') { escaped += '\\"'; }
                else if (character === "\r") { escaped += "\\r"; }
                else if (character === "\n") { escaped += "\\n"; }
                else if (character === "\t") { escaped += "\\t"; }
                else if (code < 32) { escaped += "\\u00" + (code < 16 ? "0" : "") + code.toString(16); }
                else { escaped += character; }
            }
            return '"' + escaped + '"';
        }
        if (typeof value === "number" || typeof value === "boolean") { return String(value); }
        if (value instanceof Array) {
            var items = [];
            for (var ai = 0; ai < value.length; ai += 1) { items.push(jsonStringify(value[ai])); }
            return "[" + items.join(",") + "]";
        }
        var fields = [];
        for (var key in value) {
            if (value.hasOwnProperty(key)) {
                fields.push(jsonStringify(key) + ":" + jsonStringify(value[key]));
            }
        }
        return "{" + fields.join(",") + "}";
    }

    function readText(path) {
        var file = File(path);
        file.encoding = "UTF-8";
        if (!file.open("r")) { throw Error("cannot open job: " + path); }
        var text = file.read();
        file.close();
        return text;
    }

    function writeJson(path, value) {
        var file = File(path);
        file.parent.create();
        file.encoding = "UTF-8";
        if (!file.open("w")) { throw Error("cannot write report: " + path); }
        file.write(jsonStringify(value));
        file.write("\n");
        file.close();
    }

    function itemLabel(item) {
        try { return String(item.label || ""); } catch (_) { return ""; }
    }

    function isLcdTableStory(story) {
        try {
            return String(story.storyTitle || "").indexOf(" table segment ") > 0;
        } catch (_) {
            return false;
        }
    }

    function isTroubleshootingTableStory(story) {
        try {
            return String(story.storyTitle || "") === "troubleshooting table";
        } catch (_) {
            return false;
        }
    }

    function resizeLcdTableShell(frame, markerAllowance) {
        var table = frame.parentStory.tables[0];
        var frameBounds = frame.geometricBounds;
        var oldBottom = Number(frameBounds[2]);
        var tableHeight = 0;
        for (var ri = 0; ri < table.rows.length; ri += 1) {
            tableHeight += Number(table.rows[ri].height);
        }
        var newBottom = Number(frameBounds[0]) + tableHeight + Number(markerAllowance || 0);
        var delta = newBottom - oldBottom;
        if (Math.abs(delta) < 0.01) { return false; }

        var oldHeight = oldBottom - Number(frameBounds[0]);
        var oldWidth = Number(frameBounds[3]) - Number(frameBounds[1]);
        var siblings = frame.parent.allPageItems;
        for (var si = 0; si < siblings.length; si += 1) {
            var item = siblings[si];
            if (item.constructor.name !== "Rectangle") { continue; }
            var bounds = item.geometricBounds;
            var itemHeight = Number(bounds[2]) - Number(bounds[0]);
            var itemWidth = Number(bounds[3]) - Number(bounds[1]);
            var isFullShell = itemHeight > oldHeight * 0.9 && itemWidth > oldWidth * 0.9;
            var isBottomMask = !isFullShell &&
                Math.abs(Number(bounds[2]) - oldBottom) < 0.2;
            if (isFullShell) {
                bounds[2] = newBottom;
                item.geometricBounds = bounds;
            } else if (isBottomMask) {
                bounds[0] = Number(bounds[0]) + delta;
                bounds[2] = Number(bounds[2]) + delta;
                item.geometricBounds = bounds;
            }
        }
        frameBounds[2] = newBottom;
        frame.geometricBounds = frameBounds;
        return true;
    }

    function fitLcdTableShells(doc) {
        var fitted = 0;
        var items = doc.allPageItems;
        for (var ii = 0; ii < items.length; ii += 1) {
            var frame = items[ii];
            if (frame.constructor.name !== "TextFrame" ||
                    frame.parent.constructor.name !== "Group") { continue; }
            try {
                if (frame.parentStory.tables.length === 1 &&
                        isLcdTableStory(frame.parentStory) &&
                        resizeLcdTableShell(frame, 1.0)) {
                    fitted += 1;
                }
            } catch (_) {}
        }
        doc.recompose();
        return fitted;
    }

    function fitTroubleshootingTableShells(doc) {
        var fitted = 0;
        var items = doc.allPageItems;
        for (var ii = 0; ii < items.length; ii += 1) {
            var frame = items[ii];
            if (frame.constructor.name !== "TextFrame" ||
                    frame.parent.constructor.name !== "Group") { continue; }
            try {
                if (frame.parentStory.tables.length === 1 &&
                        isTroubleshootingTableStory(frame.parentStory) &&
                        resizeLcdTableShell(frame, 1.0)) {
                    fitted += 1;
                }
            } catch (_) {}
        }
        doc.recompose();
        return fitted;
    }

    function substituteMissingFont(doc, sourceName, targetName) {
        var sourceFont = doc.fonts.itemByName(sourceName);
        if (!sourceFont.isValid || sourceFont.status === FontStatus.INSTALLED) {
            return null;
        }
        var targetFont = app.fonts.itemByName(targetName);
        if (!targetFont.isValid || targetFont.status !== FontStatus.INSTALLED) {
            throw Error("required host fallback font is not installed: " + targetName);
        }

        var changed = [];
        try {
            app.findTextPreferences = NothingEnum.nothing;
            app.changeTextPreferences = NothingEnum.nothing;
            app.findTextPreferences.appliedFont = sourceFont;
            app.changeTextPreferences.appliedFont = targetFont;
            changed = doc.changeText();
        } finally {
            app.findTextPreferences = NothingEnum.nothing;
            app.changeTextPreferences = NothingEnum.nothing;
        }
        var forcedResiduals = 0;
        try {
            app.findTextPreferences = NothingEnum.nothing;
            app.findTextPreferences.appliedFont = sourceFont;
            var residuals = doc.findText();
            for (var ri = 0; ri < residuals.length; ri += 1) {
                try {
                    residuals[ri].appliedFont = targetFont;
                    forcedResiduals += 1;
                } catch (_) {}
            }
        } finally {
            app.findTextPreferences = NothingEnum.nothing;
        }
        return {
            source: sourceName,
            target: targetName,
            replacements: changed.length,
            forced_residuals: forcedResiduals,
            reason: "host_missing_font"
        };
    }

    function applyHostFontSubstitutions(doc) {
        var substitutions = [];
        var mappings = [
            ["Segoe UI Symbol\tRegular", "Apple Symbols\tRegular"],
            ["Yu Gothic\tRegular", "Arial Unicode MS\tRegular"]
        ];
        for (var mi = 0; mi < mappings.length; mi += 1) {
            var result = substituteMissingFont(doc, mappings[mi][0], mappings[mi][1]);
            if (result !== null) { substitutions.push(result); }
        }
        doc.recompose();
        return substitutions;
    }

    function textHasVisibleContent(value) {
        return String(value || "")
            .replace(/[\u0000-\u0020\u0016\uFEFF\uFFFC]+/g, "")
            .length > 0;
    }

    function appliedFontName(textRange) {
        try {
            var applied = textRange.appliedFont;
            if (applied && applied.name) { return String(applied.name); }
            return String(applied || "");
        } catch (_) {
            return "";
        }
    }

    function fontHasTextUsage(doc, font) {
        var matches = [];
        try {
            app.findTextPreferences = NothingEnum.nothing;
            app.changeTextPreferences = NothingEnum.nothing;
            app.findTextPreferences.appliedFont = font;
            matches = doc.findText();
            for (var mi = 0; mi < matches.length; mi += 1) {
                if (!textHasVisibleContent(matches[mi].contents)) { continue; }
                var appliedName = appliedFontName(matches[mi]);
                var missingFamily = String(font.name || "").split("\t")[0];
                var appliedFamily = appliedName.split("\t")[0];
                if (!appliedFamily || appliedFamily === missingFamily) { return true; }
            }
            return false;
        } catch (_) {
            // A failed audit must remain fail-closed: retain the missing-font
            // finding instead of silently declaring an unverified face clean.
            return true;
        } finally {
            app.findTextPreferences = NothingEnum.nothing;
            app.changeTextPreferences = NothingEnum.nothing;
        }
    }

    function fontUsageSamples(doc, font) {
        var samples = [];
        try {
            app.findTextPreferences = NothingEnum.nothing;
            app.findTextPreferences.appliedFont = font;
            var matches = doc.findText();
            for (var mi = 0; mi < matches.length && samples.length < 12; mi += 1) {
                if (!textHasVisibleContent(matches[mi].contents)) { continue; }
                samples.push({
                    contents: String(matches[mi].contents).slice(0, 32),
                    applied_font: appliedFontName(matches[mi])
                });
            }
        } catch (error) {
            samples.push({error: String(error)});
        } finally {
            app.findTextPreferences = NothingEnum.nothing;
        }
        return samples;
    }

    function fitTerminalCarrierFrames(doc) {
        var results = [];
        for (var si = 0; si < doc.stories.length; si += 1) {
            var story = doc.stories[si];
            var title = String(story.storyTitle || "");
            var contents = String(story.contents || "");
            var isMeasuredOverview = title.indexOf("product_overview") >= 0;
            var isMarkerOnlyCarrier = !textHasVisibleContent(contents);
            if (!story.overflows ||
                    (story.tables.length > 0 && !isMeasuredOverview) ||
                    story.textContainers.length === 0) { continue; }
            var maxGrowth = isMeasuredOverview ? 160.0 : isMarkerOnlyCarrier ? 24.0 : 0.0;
            if (maxGrowth <= 0) { continue; }
            var frame = story.textContainers[story.textContainers.length - 1];
            if (frame.constructor.name !== "TextFrame" ||
                    !frame.parentPage || !frame.parentPage.isValid) { continue; }
            var growth = 0.0;
            while (story.overflows && growth < maxGrowth) {
                var bounds = frame.geometricBounds;
                bounds[2] = Number(bounds[2]) + 4.0;
                frame.geometricBounds = bounds;
                growth += 4.0;
                doc.recompose();
            }
            results.push({
                title: title,
                growth: growth,
                cleared: !story.overflows
            });
        }
        return results;
    }

    function isComposedSymbolTableStory(story) {
        try {
            var title = String(story.storyTitle || "");
            return title === "Signal words" || title.indexOf("Symbol icons ") === 0;
        } catch (_) {
            return false;
        }
    }

    function resizeComposedTableShell(frame) {
        var table = frame.parentStory.tables[0];
        var frameBounds = frame.geometricBounds;
        var oldBottom = Number(frameBounds[2]);
        var tableHeight = 0;
        for (var ri = 0; ri < table.rows.length; ri += 1) {
            tableHeight += Number(table.rows[ri].height);
        }
        var newBottom = Number(frameBounds[0]) + tableHeight + 4.0;
        if (Math.abs(newBottom - oldBottom) < 0.01) { return false; }

        var pageItems = frame.parentPage.allPageItems;
        for (var pi = 0; pi < pageItems.length; pi += 1) {
            var item = pageItems[pi];
            if (item.constructor.name !== "Rectangle") { continue; }
            var bounds = item.geometricBounds;
            var sameShell =
                Math.abs(Number(bounds[0]) - Number(frameBounds[0])) < 0.2 &&
                Math.abs(Number(bounds[1]) - Number(frameBounds[1])) < 0.2 &&
                Math.abs(Number(bounds[2]) - oldBottom) < 0.2 &&
                Math.abs(Number(bounds[3]) - Number(frameBounds[3])) < 0.2;
            if (sameShell) {
                bounds[2] = newBottom;
                item.geometricBounds = bounds;
            }
        }
        frameBounds[2] = newBottom;
        frame.geometricBounds = frameBounds;
        return true;
    }

    function fitComposedSymbolTableShells(doc) {
        var fitted = 0;
        var items = doc.allPageItems;
        for (var ii = 0; ii < items.length; ii += 1) {
            var frame = items[ii];
            if (frame.constructor.name !== "TextFrame") { continue; }
            try {
                if (frame.parentPage && frame.parentPage.isValid &&
                        frame.parentStory.tables.length === 1 &&
                        isComposedSymbolTableStory(frame.parentStory) &&
                        resizeComposedTableShell(frame)) {
                    fitted += 1;
                }
            } catch (_) {}
        }
        doc.recompose();
        return fitted;
    }

    var job = jsonParse(readText(HB_JOB_PATH));
    var report = {
        schema_version: "indesign-preflight/v1",
        input_idml: job.input_idml,
        output_indd: job.output_indd,
        output_pdf: job.output_pdf,
        success: false,
        page_count: 0,
        story_count: 0,
        overset_stories: [],
        missing_fonts: [],
        bad_links: [],
        stable_labels: {pages: 0, text_frames: 0},
        fitted_lcd_table_groups: 0,
        fitted_troubleshooting_table_groups: 0,
        fitted_symbol_table_shells: 0,
        carrier_frame_fits: [],
        font_substitutions: [],
        font_usage_audit: [],
        pdf_export: {
            requested_preset: String(job.pdf_preset || ""),
            applied_preset: null,
            page_range: null,
            requested_output_intent: String(job.output_intent || ""),
            applied_document_cmyk_profile: null
        },
        stage: "init",
        error: null
    };
    var doc = null;
    var oldInteraction = app.scriptPreferences.userInteractionLevel;
    var oldBackground = null;
    try {
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        try {
            oldBackground = app.backgroundTaskPreferences.enableBackgroundTask;
            app.backgroundTaskPreferences.enableBackgroundTask = false;
        } catch (_) {}
        report.stage = "open_idml";
        doc = app.open(File(job.input_idml), false);
        report.stage = "apply_output_intent";
        doc.cmykProfile = job.output_intent;
        report.pdf_export.applied_document_cmyk_profile = String(doc.cmykProfile);
        doc.recompose();
        report.fitted_lcd_table_groups = fitLcdTableShells(doc);
        report.fitted_troubleshooting_table_groups = fitTroubleshootingTableShells(doc);
        report.fitted_symbol_table_shells = fitComposedSymbolTableShells(doc);
        report.carrier_frame_fits = fitTerminalCarrierFrames(doc);
        report.font_substitutions = applyHostFontSubstitutions(doc);
        report.carrier_frame_fits = report.carrier_frame_fits.concat(
            fitTerminalCarrierFrames(doc)
        );
        report.font_substitutions = report.font_substitutions.concat(
            applyHostFontSubstitutions(doc)
        );
        report.carrier_frame_fits = report.carrier_frame_fits.concat(
            fitTerminalCarrierFrames(doc)
        );
        report.page_count = doc.pages.length;
        report.story_count = doc.stories.length;

        for (var pi = 0; pi < doc.pages.length; pi += 1) {
            try {
                doc.pages[pi].insertLabel("hb:page_id", "physical-" + (pi + 1));
                report.stable_labels.pages += 1;
            } catch (_) {}
        }
        var frames = doc.textFrames.everyItem().getElements();
        for (var ti = 0; ti < frames.length; ti += 1) {
            var parentPage = frames[ti].parentPage;
            var pagePart = parentPage && parentPage.isValid ? parentPage.documentOffset + 1 : 0;
            frames[ti].label = "hb:page=" + pagePart + ";frame=" + ti;
            report.stable_labels.text_frames += 1;
        }

        for (var si = 0; si < doc.stories.length; si += 1) {
            var story = doc.stories[si];
            if (story.overflows) {
                var containers = [];
                for (var tci = 0; tci < story.textContainers.length; tci += 1) {
                    var container = story.textContainers[tci];
                    var containerPage = container.parentPage;
                    containers.push({
                        page: containerPage && containerPage.isValid ? containerPage.documentOffset + 1 : 0,
                        label: itemLabel(container)
                    });
                }
                report.overset_stories.push({
                    index: si,
                    id: String(story.id),
                    label: itemLabel(story),
                    preview: String(story.contents).replace(/[\r\n]+/g, " ").slice(0, 120),
                    text_containers: containers
                });
            }
        }

        var fonts = doc.fonts.everyItem().getElements();
        for (var fi = 0; fi < fonts.length; fi += 1) {
            var font = fonts[fi];
            // InDesign keeps a substituted source font in doc.fonts even
            // after every text range has moved to the installed fallback.
            // Only a live text use is a preflight failure; an unused resource
            // entry is provenance, not a missing deliverable dependency.
            if (font.status !== FontStatus.INSTALLED) {
                var hasTextUsage = fontHasTextUsage(doc, font);
                report.font_usage_audit.push({
                    name: String(font.name),
                    status: String(font.status),
                    live_text_usage: hasTextUsage,
                    samples: fontUsageSamples(doc, font)
                });
                if (hasTextUsage) {
                    report.missing_fonts.push({name: String(font.name), status: String(font.status)});
                }
            }
        }

        for (var li = 0; li < doc.links.length; li += 1) {
            var link = doc.links[li];
            if (link.status !== LinkStatus.NORMAL) {
                report.bad_links.push({
                    name: String(link.name), status: String(link.status),
                    path: String(link.filePath || "")
                });
            }
        }

        report.stage = "save_indd";
        doc.save(File(job.output_indd));
        report.stage = "validate_pdf_preset";
        var pdfPreset = app.pdfExportPresets.itemByName(job.pdf_preset);
        if (!pdfPreset.isValid) {
            throw Error("PDF export preset is not installed: " + job.pdf_preset);
        }
        report.pdf_export.applied_preset = String(pdfPreset.name);
        app.pdfExportPreferences.pageRange = PageRange.ALL_PAGES;
        report.pdf_export.page_range = "ALL_PAGES";
        report.stage = "export_pdf";
        doc.exportFile(ExportFormat.pdfType, File(job.output_pdf), false, pdfPreset);
        report.stage = "complete";
        report.success = report.overset_stories.length === 0 &&
            report.missing_fonts.length === 0 && report.bad_links.length === 0;
        doc.close(SaveOptions.YES);
        doc = null;
    } catch (error) {
        report.error = String(error) + (error.line ? " at line " + error.line : "");
        if (doc !== null) {
            try { doc.close(SaveOptions.NO); } catch (_) {}
        }
    } finally {
        if (oldBackground !== null) {
            try { app.backgroundTaskPreferences.enableBackgroundTask = oldBackground; } catch (_) {}
        }
        app.scriptPreferences.userInteractionLevel = oldInteraction;
        writeJson(job.report_json, report);
    }
}());
