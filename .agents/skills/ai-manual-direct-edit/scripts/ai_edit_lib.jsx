// Reusable pure-ASCII ExtendScript helper library for direct Adobe Illustrator
// manual editing. Keep this file strictly ASCII (escape Unicode via \uXXXX).

function aiGetFontOrFallback(name, fallbackName) {
    try {
        return app.textFonts.getByName(name);
    } catch (e) {
        if (fallbackName) {
            try {
                return app.textFonts.getByName(fallbackName);
            } catch (e2) {
                return app.textFonts[0];
            }
        }
        return app.textFonts[0];
    }
}

function aiMakeColor(doc, r, g, b) {
    if (doc.documentColorSpace == DocumentColorSpace.CMYK) {
        var c = new CMYKColor();
        var rf = r / 255.0;
        var gf = g / 255.0;
        var bf = b / 255.0;
        var k = 1.0 - Math.max(rf, Math.max(gf, bf));
        if (k >= 0.999) {
            c.cyan = 0;
            c.magenta = 0;
            c.yellow = 0;
            c.black = 100;
        } else {
            c.cyan = ((1.0 - rf - k) / (1.0 - k)) * 100.0;
            c.magenta = ((1.0 - gf - k) / (1.0 - k)) * 100.0;
            c.yellow = ((1.0 - bf - k) / (1.0 - k)) * 100.0;
            c.black = k * 100.0;
        }
        return c;
    }
    var rgb = new RGBColor();
    rgb.red = r;
    rgb.green = g;
    rgb.blue = b;
    return rgb;
}

function aiMakePureRed(doc) {
    if (doc.documentColorSpace == DocumentColorSpace.CMYK) {
        var c = new CMYKColor();
        c.cyan = 0;
        c.magenta = 100;
        c.yellow = 100;
        c.black = 0;
        return c;
    }
    var rgb = new RGBColor();
    rgb.red = 230;
    rgb.green = 0;
    rgb.blue = 18;
    return rgb;
}

function aiPalette(doc) {
    return {
        text: aiMakeColor(doc, 64, 64, 65),
        header: aiMakeColor(doc, 65, 64, 66),
        muted: aiMakeColor(doc, 149, 150, 154),
        border: aiMakeColor(doc, 64, 64, 65),
        rule: aiMakeColor(doc, 180, 181, 184),
        card: aiMakeColor(doc, 210, 211, 213),
        shade: aiMakeColor(doc, 235, 236, 236),
        white: aiMakeColor(doc, 255, 255, 255),
        red: aiMakePureRed(doc)
    };
}

function aiPagePoint(rect, px, py) {
    return [rect[0] + px, rect[1] - py];
}

function aiBoundsIntersects(vb, rect) {
    return !(vb[2] < rect[0] || vb[0] > rect[2] || vb[3] > rect[1] || vb[1] < rect[3]);
}

function aiFramesInBox(doc, rect, pad) {
    var margin = (pad === undefined || pad === null) ? 2.0 : pad;
    var res = [];
    for (var i = 0; i < doc.textFrames.length; i++) {
        var tf = doc.textFrames[i];
        var gb = tf.geometricBounds;
        var cx = (gb[0] + gb[2]) / 2.0;
        var cy = (gb[1] + gb[3]) / 2.0;
        if (cx >= rect[0] - margin && cx <= rect[2] + margin && cy <= rect[1] + margin && cy >= rect[3] - margin) {
            res.push(tf);
        }
    }
    return res;
}

function aiFindFrame(doc, rect, substr, opts) {
    var o = opts || {};
    var arr = aiFramesInBox(doc, rect, o.pad);
    for (var i = 0; i < arr.length; i++) {
        var tf = arr[i];
        if (tf.contents.indexOf(substr) === -1) continue;
        var topY = rect[1] - tf.geometricBounds[1];
        if (o.yMin !== undefined && o.yMin !== null && topY < o.yMin) continue;
        if (o.yMax !== undefined && o.yMax !== null && topY > o.yMax) continue;
        return tf;
    }
    if (o.log) {
        o.log("WARNING: frame not found containing: " + substr);
    }
    return null;
}

function aiReplaceSub(tf, oldStr, newStr, opts) {
    if (!tf) return 0;
    var o = opts || {};
    var all = !!o.all;
    var markRed = (o.markRed === undefined) ? true : !!o.markRed;
    var fillColor = o.color || aiMakePureRed(tf.layer.parent);
    var count = 0;
    var startPos = 0;
    while (true) {
        var idx = tf.contents.indexOf(oldStr, startPos);
        if (idx === -1) break;
        if (newStr.length === 0) {
            for (var k = oldStr.length - 1; k >= 0; k--) {
                tf.characters[idx + k].remove();
            }
            startPos = idx;
        } else {
            for (var j = oldStr.length - 1; j >= 1; j--) {
                tf.characters[idx + j].remove();
            }
            tf.characters[idx].contents = newStr;
            if (markRed && fillColor) {
                for (var r = 0; r < newStr.length; r++) {
                    tf.characters[idx + r].characterAttributes.fillColor = fillColor;
                }
            }
            startPos = idx + newStr.length;
        }
        count++;
        if (!all) break;
    }
    return count;
}

function aiColorSubstrings(tf, substrList, color) {
    if (!tf || !substrList) return;
    var full = tf.contents;
    for (var si = 0; si < substrList.length; si++) {
        var sub = substrList[si];
        var start = 0;
        while (true) {
            var pos = full.indexOf(sub, start);
            if (pos === -1) break;
            for (var ci = 0; ci < sub.length; ci++) {
                tf.characters[pos + ci].characterAttributes.fillColor = color;
            }
            start = pos + sub.length;
        }
    }
}

function aiFixSpecialGlyphs(tf, opts) {
    if (!tf) return;
    var o = opts || {};
    var dcFont = o.dcFont || aiGetFontOrFallback("SegoeUISymbol", "ArialUnicodeMS");
    var circleFont = o.circleFont || aiGetFontOrFallback("NotoSansSymbols-Regular", "ArialUnicodeMS");
    var subFont = o.subFont || aiGetFontOrFallback("Gilroy-Regular", "Helvetica");
    var s = tf.contents;
    for (var i = s.length - 1; i >= 0; i--) {
        var ch = s.charAt(i);
        if (ch === "\u2393") {
            tf.characters[i].characterAttributes.textFont = dcFont;
        } else if (ch === "\u2460") {
            tf.characters[i].characterAttributes.textFont = circleFont;
        } else if (ch === "\u2084") {
            var baseSize = tf.characters[i].characterAttributes.size;
            var baseColor = tf.characters[i].characterAttributes.fillColor;
            tf.characters[i].contents = "4";
            tf.characters[i].characterAttributes.textFont = subFont;
            tf.characters[i].characterAttributes.size = baseSize * 0.72;
            tf.characters[i].characterAttributes.baselineShift = -baseSize * 0.22;
            tf.characters[i].characterAttributes.fillColor = baseColor;
        }
    }
}

function aiAddPointText(layer, rect, px, py, text, font, size, color, opts) {
    var o = opts || {};
    var p = aiPagePoint(rect, px, py);
    var tf = layer.textFrames.pointText([p[0], p[1]]);
    tf.contents = text;
    var ca = tf.textRange.characterAttributes;
    ca.textFont = font;
    ca.size = size;
    ca.fillColor = color;
    aiFixSpecialGlyphs(tf, o.glyphOpts);
    if (o.alignRightX !== undefined && o.alignRightX !== null) {
        var gbR = tf.geometricBounds;
        tf.translate((rect[0] + o.alignRightX) - gbR[2], 0);
    } else if (o.centerWidth !== undefined && o.centerWidth !== null) {
        var gbC = tf.geometricBounds;
        var w = gbC[2] - gbC[0];
        tf.translate((rect[0] + px + (o.centerWidth - w) / 2.0) - gbC[0], 0);
    }
    return tf;
}

function aiAddAreaText(layer, rect, px, py, w, h, text, font, size, color, opts) {
    var o = opts || {};
    var p = aiPagePoint(rect, px, py);
    var box = layer.pathItems.rectangle(p[1], p[0], w, h);
    var tf = layer.textFrames.areaText(box);
    tf.contents = text;
    var ca = tf.textRange.characterAttributes;
    ca.textFont = font;
    ca.size = size;
    ca.fillColor = color;
    if (o.leading) {
        ca.autoLeading = false;
        ca.leading = o.leading;
    }
    if (o.boldSubstrings && o.boldFont) {
        var full = tf.contents;
        for (var bi = 0; bi < o.boldSubstrings.length; bi++) {
            var sub = o.boldSubstrings[bi];
            var pos = full.indexOf(sub);
            if (pos !== -1) {
                for (var ci = 0; ci < sub.length; ci++) {
                    tf.characters[pos + ci].characterAttributes.textFont = o.boldFont;
                }
            }
        }
    }
    if (o.redSubstrings && o.redColor) {
        aiColorSubstrings(tf, o.redSubstrings, o.redColor);
    }
    aiFixSpecialGlyphs(tf, o.glyphOpts);
    return tf;
}

function aiAddRoundRect(layer, rect, px, py, w, h, rad, fillColor, strokeColor, strokeWidth) {
    var p = aiPagePoint(rect, px, py);
    var rr = layer.pathItems.roundedRectangle(p[1], p[0], w, h, rad, rad);
    if (fillColor) {
        rr.filled = true;
        rr.fillColor = fillColor;
    } else {
        rr.filled = false;
    }
    if (strokeColor && strokeWidth > 0) {
        rr.stroked = true;
        rr.strokeColor = strokeColor;
        rr.strokeWidth = strokeWidth;
    } else {
        rr.stroked = false;
    }
    return rr;
}

function aiAddLine(layer, rect, x0, y0, x1, y1, strokeColor, strokeWidth) {
    var p0 = aiPagePoint(rect, x0, y0);
    var p1 = aiPagePoint(rect, x1, y1);
    var ln = layer.pathItems.add();
    ln.setEntirePath([p0, p1]);
    ln.filled = false;
    ln.stroked = true;
    ln.strokeColor = strokeColor;
    ln.strokeWidth = strokeWidth;
    return ln;
}

function aiAddCalloutPill(layer, rect, px, py, w, h, label, bodyText, opts) {
    var o = opts || {};
    var pal = o.palette || aiPalette(layer.parent);
    var lw = o.labelW || 46.0;
    var tp = (o.textTopPad !== undefined && o.textTopPad !== null) ? o.textTopPad : 4.5;
    var fontReg = o.fontReg || aiGetFontOrFallback("Gilroy-Regular", "Helvetica");
    var fontBold = o.fontBold || aiGetFontOrFallback("Gilroy-Bold", "Helvetica-Bold");
    var textColor = o.color || pal.red;
    var labelColor = o.labelColor || textColor;
    var fontSize = o.fontSize || 5.6;
    var leading = o.leading || (fontSize * 1.28);

    aiAddRoundRect(layer, rect, px, py, w, h, 5.5, pal.shade, null, 0);
    aiAddRoundRect(layer, rect, px + 2.5, py + 2.5, lw, h - 5.0, 3.8, pal.white, null, 0);
    aiAddPointText(layer, rect, px + 2.5, py + h / 2.0 + 2.8, label, fontBold, o.labelSize || 7.5, labelColor, { centerWidth: lw });
    return aiAddAreaText(layer, rect, px + lw + 8.0, py + tp, w - lw - 14.0, h - tp - 2.0, bodyText, fontReg, fontSize, textColor, { leading: leading });
}

function aiDrawNativeTable(layer, rect, x0, y0, x1, col1W, rows, opts) {
    var o = opts || {};
    var pal = o.palette || aiPalette(layer.parent);
    var fontReg = o.fontReg || aiGetFontOrFallback("Gilroy-Regular", "Helvetica");
    var fontBold = o.fontBold || aiGetFontOrFallback("Gilroy-Bold", "Helvetica-Bold");
    var fs = o.fontSize || 5.4;
    var lead = o.leading || (fs * 1.25);
    var padX = o.padX || 5.0;
    var padY = o.padY || 2.8;
    var rad = o.radius || 4.5;
    var hdr = !!o.headerRow;
    var leftBold = !!o.leftBold;
    var totalW = x1 - x0;
    var col2W = totalW - col1W;

    function estimateLines(text, maxW, fontSize) {
        var paras = text.split("\r");
        var total = 0;
        var avgCharW = fontSize * 0.49;
        for (var pi = 0; pi < paras.length; pi++) {
            var p = paras[pi];
            if (p.length === 0) {
                total += 0.6;
                continue;
            }
            var words = p.split(" ");
            var lineW = 0;
            var lines = 1;
            for (var wi = 0; wi < words.length; wi++) {
                var ww = (words[wi].length + 1) * avgCharW;
                if (lineW > 0 && lineW + ww > maxW) {
                    lines++;
                    lineW = ww;
                } else {
                    lineW += ww;
                }
            }
            total += lines;
        }
        return total;
    }

    var rowHeights = [];
    var totalH = 0;
    for (var ri = 0; ri < rows.length; ri++) {
        var isH = hdr && ri === 0;
        var rfs = isH ? (fs + 0.5) : fs;
        var rlead = isH ? (rfs * 1.25) : lead;
        var lLines = estimateLines(rows[ri][0], col1W - 2 * padX, rfs);
        var rLines = estimateLines(rows[ri][1], col2W - 2 * padX, rfs);
        var rh = Math.max(lLines, rLines) * rlead + 2 * padY;
        if (o.minRowH && rh < o.minRowH) rh = o.minRowH;
        rowHeights.push(rh);
        totalH += rh;
    }

    aiAddRoundRect(layer, rect, x0, y0, totalW, totalH, rad, pal.white, null, 0);
    aiAddRoundRect(layer, rect, x0, y0, col1W, totalH, rad, pal.shade, null, 0);
    var sqP = aiPagePoint(rect, x0 + col1W - rad, y0);
    var sq = layer.pathItems.rectangle(sqP[1], sqP[0], rad, totalH);
    sq.filled = true;
    sq.fillColor = pal.shade;
    sq.stroked = false;

    aiAddLine(layer, rect, x0 + col1W, y0, x0 + col1W, y0 + totalH, pal.rule, 0.5);
    var cy = y0;
    for (var rowIdx = 0; rowIdx < rows.length; rowIdx++) {
        var rowH = rowHeights[rowIdx];
        var isHdr = hdr && rowIdx === 0;
        var rowFs = isHdr ? (fs + 0.5) : fs;
        var rowLead = isHdr ? (rowFs * 1.25) : lead;
        var ro = (rows[rowIdx].length > 2 && rows[rowIdx][2]) ? rows[rowIdx][2] : {};
        if (rowIdx > 0) aiAddLine(layer, rect, x0, cy, x1, cy, pal.rule, 0.5);

        var lFont = (isHdr || leftBold) ? fontBold : fontReg;
        var lColor = ro.redLeft ? pal.red : pal.text;
        var lCnt = estimateLines(rows[rowIdx][0], col1W - 2 * padX, rowFs);
        var lTop = cy + Math.max(padY, (rowH - lCnt * rowLead) / 2.0);
        var ltf = aiAddAreaText(layer, rect, x0 + padX, lTop, col1W - 2 * padX, rowH - padY + 4, rows[rowIdx][0], lFont, rowFs, lColor, { leading: rowLead });
        if (leftBold || isHdr) {
            for (var pIdx = 0; pIdx < ltf.paragraphs.length; pIdx++) {
                ltf.paragraphs[pIdx].paragraphAttributes.justification = Justification.CENTER;
            }
        }

        var rFont = isHdr ? fontBold : fontReg;
        var rColor = ro.redRight ? pal.red : pal.text;
        var rCnt = estimateLines(rows[rowIdx][1], col2W - 2 * padX, rowFs);
        var rTop = cy + Math.max(padY, (rowH - rCnt * rowLead) / 2.0);
        aiAddAreaText(layer, rect, x0 + col1W + padX, rTop, col2W - 2 * padX, rowH - padY + 6, rows[rowIdx][1], rFont, rowFs, rColor, {
            leading: rowLead,
            boldFont: fontBold,
            boldSubstrings: ro.boldSubs || null,
            redColor: pal.red,
            redSubstrings: ro.redRightSubs || null
        });
        cy += rowH;
    }

    aiAddRoundRect(layer, rect, x0, y0, totalW, totalH, rad, null, pal.border, 0.85);
    return y0 + totalH;
}

function aiRemoveItemsOutsideBoxes(layer, pageBoxes, opts) {
    var o = opts || {};
    var maxBorderDim = o.maxBorderDim || 0;
    var removed = 0;
    for (var i = layer.pageItems.length - 1; i >= 0; i--) {
        var it = layer.pageItems[i];
        var vb = it.visibleBounds;
        var w = vb[2] - vb[0];
        var h = vb[1] - vb[3];
        if (maxBorderDim > 0 && (w > maxBorderDim || h > maxBorderDim)) {
            it.remove();
            removed++;
            continue;
        }
        var touchesKept = false;
        for (var pi = 0; pi < pageBoxes.length; pi++) {
            if (aiBoundsIntersects(vb, pageBoxes[pi])) {
                touchesKept = true;
                break;
            }
        }
        if (!touchesKept) {
            it.remove();
            removed++;
        }
    }
    return removed;
}

function aiRemoveItemsInBand(layer, rect, yMin, yMax, opts) {
    var o = opts || {};
    var keepPageNumY = (o.keepPageNumY === undefined) ? 496.0 : o.keepPageNumY;
    var maxFrameW = o.maxFrameW || ((rect[2] - rect[0]) * 0.93);
    var maxFrameH = o.maxFrameH || ((rect[1] - rect[3]) * 0.93);
    var removed = 0;
    for (var i = layer.pageItems.length - 1; i >= 0; i--) {
        var it = layer.pageItems[i];
        var vb = it.visibleBounds;
        var w = vb[2] - vb[0];
        var h = vb[1] - vb[3];
        if (w > maxFrameW && h > maxFrameH) continue;
        var cx = (vb[0] + vb[2]) / 2.0;
        var cy = (vb[1] + vb[3]) / 2.0;
        if (cx >= rect[0] - 3 && cx <= rect[2] + 3 && cy <= rect[1] + 5 && cy >= rect[3] - 3) {
            var topY = rect[1] - vb[1];
            var midY = rect[1] - cy;
            if (keepPageNumY > 0 && topY > keepPageNumY) continue;
            if (midY >= yMin && midY <= yMax) {
                it.remove();
                removed++;
            }
        }
    }
    return removed;
}

function aiTranslateItemsInBand(layer, rect, yMin, yMax, dx, dy, opts) {
    var o = opts || {};
    var keepPageNumY = (o.keepPageNumY === undefined) ? 496.0 : o.keepPageNumY;
    var maxFrameW = o.maxFrameW || ((rect[2] - rect[0]) * 0.93);
    var maxFrameH = o.maxFrameH || ((rect[1] - rect[3]) * 0.93);
    var moved = 0;
    for (var i = 0; i < layer.pageItems.length; i++) {
        var it = layer.pageItems[i];
        var vb = it.visibleBounds;
        var w = vb[2] - vb[0];
        var h = vb[1] - vb[3];
        if (w > maxFrameW && h > maxFrameH) continue;
        var cx = (vb[0] + vb[2]) / 2.0;
        var cy = (vb[1] + vb[3]) / 2.0;
        if (cx >= rect[0] - 3 && cx <= rect[2] + 3 && cy <= rect[1] + 3 && cy >= rect[3] - 3) {
            var topY = rect[1] - vb[1];
            var midY = rect[1] - cy;
            if (keepPageNumY > 0 && topY > keepPageNumY) continue;
            if (midY >= yMin && midY <= yMax) {
                it.translate(dx, dy);
                moved++;
            }
        }
    }
    return moved;
}

function aiSampleBannerColor(layer, rect, fallbackColor) {
    function scanItems(items) {
        for (var i = 0; i < items.length; i++) {
            var it = items[i];
            if (it.typename === "GroupItem") {
                var sub = scanItems(it.pageItems);
                if (sub) return sub;
            } else if (it.typename === "PathItem" && it.filled) {
                var vb = it.visibleBounds;
                var w = vb[2] - vb[0];
                var h = vb[1] - vb[3];
                var cx = (vb[0] + vb[2]) / 2.0;
                var cy = (vb[1] + vb[3]) / 2.0;
                if (cx >= rect[0] && cx <= rect[2] && cy <= rect[1] && cy >= rect[3]) {
                    var py = rect[1] - cy;
                    if (w > 240 && h > 14 && h < 30 && py > 18 && py < 55) {
                        return it.fillColor;
                    }
                }
            }
        }
        return null;
    }
    return scanItems(layer.pageItems) || fallbackColor;
}

function aiSaveEditablePdf(doc, outPath) {
    var pdfOpts = new PDFSaveOptions();
    pdfOpts.preserveEditability = true;
    pdfOpts.compatibility = PDFCompatibility.ACROBAT7;
    pdfOpts.generateThumbnails = true;
    pdfOpts.viewAfterSaving = false;
    var outFile = new File(outPath);
    doc.saveAs(outFile, pdfOpts);
    return outFile.fsName;
}

function aiSaveNativeAi(doc, outPath) {
    var aiOpts = new IllustratorSaveOptions();
    aiOpts.pdfCompatible = true;
    aiOpts.compressed = true;
    aiOpts.embedICCProfile = true;
    var outFile = new File(outPath);
    doc.saveAs(outFile, aiOpts);
    return outFile.fsName;
}
