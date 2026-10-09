<style>
/* Shared Manual IR owns typography and components. Native geometry only. */
.hb-reference-figure { max-width: 720px; margin: 1rem auto; }
.native-step-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 1rem; margin: 1rem 0; }
.native-step-card { border: 1px solid var(--hb-border-color,#dedede); border-radius: 12px; padding: 1rem; min-width: 0; }
.native-step-card p { margin: 0 0 .75rem; }
.native-step-card .hb-reference-figure { margin: 0; }
.native-step-card .hb-reference-live-label { font-size: max(10px, 2.8cqw) !important; }
[data-reference-id="wood-prep"] .hb-reference-art-panel::before,
[data-reference-id="concrete-prep"] .hb-reference-art-panel::before { content: ""; position:absolute; border:1px dashed #858585; border-radius:12px; left:31%; top:10%; width:47%; height:82%; }
[data-reference-id="wood-prep"] .hb-reference-live-label,
[data-reference-id="concrete-prep"] .hb-reference-live-label { font-weight:700; }
[data-reference-id="overview"] .hb-reference-live-label { font-size:max(10px,2.2cqw) !important; }
[data-reference-id="power"] .hb-reference-live-label:nth-of-type(odd) { font-weight:700; }
.hb-inbox-card-art { max-height:180px; object-fit:contain; }
@media(max-width:760px) {
 .native-step-grid { grid-template-columns: minmax(0,1fr); }
}

.native-step-card:has(img[src*="-result"]) .hb-reference-figure { max-width:120px; margin-inline:auto; }
[data-reference-id="wood-prep"] .hb-reference-art-panel::before { top:23%; height:69%; }
[data-reference-id="concrete-prep"] .hb-reference-art-panel::before { left:28%; top:23%; width:49%; height:69%; }
.native-step-card [data-reference-id="wood-prep"] .hb-reference-live-label,
.native-step-card [data-reference-id="concrete-prep"] .hb-reference-live-label { font-size:9px !important; }
[data-reference-id="overview"] [data-source-line="1"] { font-size:max(8px,1.65cqw) !important; }
[data-reference-id="overview"] [data-source-line="0"],
[data-reference-id="overview"] [data-source-line="2"],
[data-reference-id="overview"] [data-source-line="3"] { font-weight:700; }

@media(max-width:760px) { .hb-reference-figure:not([data-reference-id="lcd"]) .hb-reference-live-label { font-size:10px; } }

[data-reference-id="overview"] [data-source-line="2"] { font-size:max(8px,1.65cqw) !important; font-weight:400; }
[data-reference-id="overview"] [data-source-line="4"] { font-weight:700; }

.native-inline-pack { display:inline-block; width:11px; height:15px; vertical-align:middle; margin:0 3px; }

/* Native FCC geometry: compact mark above the left copy; shared panel/breakpoints. */
#furo-main-content .hb-fcc-opening { display:block; }
#furo-main-content .hb-fcc-mark { width:2.6rem !important; margin:0 0 .4rem !important; }

/* Native LCD glyphs need a larger cell footprint, including stacked readouts. */
#furo-main-content .hb-lcd-col-icon { width:14%; }
#furo-main-content .hb-lcd-col-name { width:26%; }
#furo-main-content .hb-lcd-col-description { width:54%; }
#furo-main-content table.hb-lcd-icon-table td.hb-lcd-icon { padding-inline:.35rem !important; }
#furo-main-content .hb-lcd-icon-art { width:4.5rem !important; height:auto !important; }

/* CSS owns the native power panel and its inset live Note, never the base art. */
.native-power-panel { position:relative; border:2px solid var(--hb-line-soft); border-radius:var(--hb-panel-radius); padding:.6rem; margin:.6rem 0 1.35rem; }
.native-power-panel .hb-reference-figure { max-width:none; margin:0; }
#furo-main-content .native-power-panel table.manual-callout-table { position:absolute; right:3%; bottom:5%; width:60% !important; margin:0 !important; font-size:.85rem; line-height:1.3; }
#furo-main-content .native-power-panel .manual-callout-label { width:18% !important; padding:.7rem .5rem !important; background:var(--hb-surface) !important; }
#furo-main-content .native-power-panel .manual-callout-body { padding:.7rem !important; background:var(--hb-paper) !important; }
#furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="0"],
#furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="2"] { font-size:max(10px,3.2cqw) !important; }
@media(max-width:760px) {
 #furo-main-content .native-power-panel table.manual-callout-table { position:static; width:100% !important; margin:.4rem 0 0 !important; }
}

@media(max-width:760px) {
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label { font-size:.88rem !important; }
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="0"],
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="2"] { font-size:1rem !important; margin-top:.7rem; }
}

/* Native portrait and the shared state table fill the same desktop row. */
.hb-lcd-mode-composition.hb-lcd-mode-portrait { grid-template-columns:minmax(0,1.4fr) minmax(0,3fr); align-items:stretch; }
.hb-lcd-mode-portrait .hb-lcd-mode-art-panel { position:relative; aspect-ratio:246/477; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-art { position:absolute; left:0; top:0; width:auto !important; height:100% !important; max-width:none; max-height:none; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-state { font-weight:400; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-action { font-weight:600; }
@media(max-width:760px) {
 .hb-lcd-mode-composition.hb-lcd-mode-portrait { grid-template-columns:minmax(0,1fr); }
 .hb-lcd-mode-portrait .hb-lcd-mode-art-panel { aspect-ratio:auto; }
 #furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-art { position:static; width:9rem !important; height:auto !important; max-width:100%; }
}

/* Native vertical-stand opening: plain heading, live inset caption, unframed result. */
#furo-main-content :is(#vertical-stand,#support-vertical,#soporte-vertical,#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 { background:transparent; color:var(--hb-brand-dark); border:0; border-radius:0; padding:0; font-size:1.15rem; line-height:1.3; margin-bottom:.35rem; }
.native-vertical-opening { display:grid; grid-template-columns:minmax(0,2.7fr) minmax(0,1fr); gap:2.6rem; align-items:end; margin-bottom:1rem; }
.native-vertical-preparation { min-width:0; }
#furo-main-content .native-vertical-preparation > p { margin:0 0 .35rem; }
.native-vertical-opening .hb-reference-figure { margin:0; max-width:none; }
.native-vertical-result .hb-reference-figure { position:static; }
.native-vertical-result { position:relative; align-self:stretch; margin-top:-2.2rem; }
#furo-main-content .native-vertical-result img { position:absolute; right:0; top:0; height:100% !important; width:auto !important; max-width:none !important; }
#furo-main-content [data-reference-id="vertical-prep"] .hb-reference-live-label { font-size:.95rem !important; line-height:1.25; }
@media(max-width:760px) {
 .native-vertical-opening { grid-template-columns:minmax(0,1fr); gap:1rem; }
 .native-vertical-result { width:7.5rem; margin:0 auto; }
 #furo-main-content .native-vertical-result img { position:static; width:100% !important; height:auto !important; max-width:100%; }
 #furo-main-content [data-reference-id="vertical-prep"] .hb-reference-live-label { font-size:.85rem !important; }
}

/* Native vertical-stand installation: each step occupies a full-width row. */
#furo-main-content :is(#vertical-stand,#support-vertical,#soporte-vertical) .native-step-grid { grid-template-columns:minmax(0,1fr); }

/* Native wall-mount title and compact introduction/subsection spacing. */
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 .headerlink { color:inherit; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > p { margin:0; line-height:1.5; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section { margin-top:.65rem; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section > h2 { margin:0 0 .65rem; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section > h2::before { display:none; }

/* Native wooden-wall opening reuses the admitted base art with live inset copy. */
.native-wood-opening .hb-reference-figure { margin:0; max-width:none; }
#furo-main-content .native-wood-preparation .hb-reference-art-panel { background:#f7f7f7; border-radius:var(--hb-panel-radius); overflow:hidden; }
#furo-main-content .native-wood-preparation .hb-reference-art { mix-blend-mode:multiply; }
#furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="0"] { font-size:.9rem !important; font-weight:400; line-height:1.2; }
#furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="1"] { font-size:max(10px,3cqw) !important; }
#furo-main-content .native-wood-result .hb-reference-figure { max-width:none; }
#furo-main-content .native-wood-result img { width:100% !important; height:auto !important; max-width:100% !important; }
@media(min-width:761px) {
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) { display:grid; grid-template-columns:minmax(0,2.05fr) minmax(0,1fr); column-gap:2rem; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 { grid-column:1; grid-row:1; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > p { grid-column:1; grid-row:2; }
 #furo-main-content :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera), .native-wood-opening { display:contents; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera) > h2 { grid-column:1; grid-row:3; margin:.65rem 0; }
 .native-wood-preparation { grid-column:1; grid-row:4; min-width:0; }
 .native-wood-result { grid-column:2; grid-row:1 / span 4; align-self:start; min-width:0; }
 #furo-main-content :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera) > .native-wall-wood-steps { grid-column:1 / -1; grid-row:5; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section:not(:is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera)) { grid-column:1 / -1; }
}
@media(max-width:760px) {
 .native-wood-opening { display:grid; grid-template-columns:minmax(0,1fr); gap:1rem; }
 .native-wood-result { width:8.5rem; margin-inline:auto; }
 #furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="0"] { font-size:.85rem !important; }
}

/* Wall installation preserves native panels and cross-panel drawing groups. */
.native-wall-wood-steps { display:grid; grid-template-columns:minmax(0,1.8fr) minmax(0,1fr); gap:1rem; margin:1rem 0; }
.native-wall-wood-steps > :is(.native-wood-1-2,.native-wood-5,.native-wood-6,.native-wood-7) { grid-column:1 / -1; }
.native-wall-concrete-steps { display:grid; grid-template-columns:minmax(0,1fr); gap:1rem; margin:1rem 0; }
.native-wall-panel { position:relative; min-width:0; }
.native-wall-panel .hb-reference-figure { max-width:none; margin:0; }
.native-wall-panel:not(.native-wall-pair) { border:2px solid var(--hb-line-soft); border-radius:var(--hb-panel-radius); overflow:hidden; }
.native-wall-panel .hb-reference-art-panel::before,.native-wall-panel .hb-reference-art-panel::after { pointer-events:none; }
.native-wall-pair .hb-reference-art-panel::before,.native-wall-pair .hb-reference-art-panel::after { content:""; position:absolute; top:.5%; height:98%; border:2px solid var(--hb-line-soft); border-radius:var(--hb-panel-radius); z-index:0; box-sizing:border-box; }
.native-concrete-4-5 .hb-reference-art-panel::before { left:.5%; width:54.6%; }
.native-concrete-4-5 .hb-reference-art-panel::after { left:57%; width:41.6%; }
.native-concrete-6-7 .hb-reference-art-panel::before { left:.5%; width:39.6%; }
.native-concrete-6-7 .hb-reference-art-panel::after { left:42.4%; width:56.4%; }
.native-concrete-8-9 .hb-reference-art-panel::before { left:1.1%; width:33.6%; }
.native-concrete-8-9 .hb-reference-art-panel::after { left:36.6%; width:62%; }
#furo-main-content .native-wall-panel .hb-reference-live-label { font-size:max(10px,1.92cqw) !important; line-height:1.2; font-weight:400; }
#furo-main-content :is(.native-wood-3,.native-wood-4) .hb-reference-live-label { font-size:max(10px,3cqw) !important; }
.native-concrete-opening { display:grid; grid-template-columns:minmax(0,2.35fr) minmax(0,1fr); gap:1.2rem; align-items:end; }
.native-concrete-opening .hb-reference-figure { max-width:none; margin:0; }
#furo-main-content .native-concrete-preparation .hb-reference-art-panel { background:#f7f7f7; border-radius:var(--hb-panel-radius); }
#furo-main-content .native-concrete-preparation .hb-reference-art { mix-blend-mode:multiply; }
#furo-main-content [data-reference-id="concrete-prep"] [data-source-line="0"] { font-size:.9rem !important; font-weight:400; }
#furo-main-content [data-reference-id="concrete-prep"] [data-source-line="1"] { font-size:max(10px,3cqw) !important; }
@media(max-width:760px) {
 .native-wall-wood-steps,.native-concrete-opening { grid-template-columns:minmax(0,1fr); }
 .native-concrete-result { width:8.5rem; margin-inline:auto; }
 #furo-main-content .native-wall-panel .hb-reference-live-label { font-size:.85rem !important; line-height:1.4; }
 .native-wall-panel:not(.native-wall-pair) { padding:.4rem; }
}

/* Native translation density must not collide with the measurement labels. */
@media(min-width:761px) {
 #furo-main-content .native-concrete-4-5 .hb-reference-live-label { font-size:max(10px,1.8cqw) !important; }
 #furo-main-content .native-wood-5 .hb-reference-live-label { font-size:max(10px,1.6cqw) !important; }
}
@media(max-width:760px) {
 .native-concrete-4-5 .hb-reference-art-panel::before,.native-concrete-4-5 .hb-reference-art-panel::after { height:calc(100cqw * 228 / 316 * .98); }
 .native-concrete-6-7 .hb-reference-art-panel::before,.native-concrete-6-7 .hb-reference-art-panel::after { height:calc(100cqw * 232 / 316 * .98); }
 .native-concrete-8-9 .hb-reference-art-panel::before,.native-concrete-8-9 .hb-reference-art-panel::after { height:calc(100cqw * 189 / 316 * .98); }
}

</style>

<h1 class="hb-preface-heading" id="preface"><span class="hb-preface-region">US</span> <span>IMPORTANT</span></h1>

<div class="hb-preface-prose"><p>Congratulations on your new Jackery Battery Pack. Please read this manual carefully before using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible place for future reference.</p><p>In compliance with laws and regulations, the right of final interpretation of this document and all related documents of this product resides with the Company. Although every effort has been made to ensure the accuracy of this manual, Jackery Inc. assumes no responsibility for any errors that may appear.</p><p>Please note that no further notifications will be given in case of any update, revision, or termination. For the latest version of the product manuals, visit support.jackery.com.</p><p>* The images are for reference purposes only. Please refer to the actual product.</p></div>

<span id="safety"></span>

# IMPORTANT SAFETY INFORMATION

<p>The basic safety precautions should be followed when using this product, including:</p>

<ul><li>Please read all instructions before using this product.</li><li>Close supervision is required when using this product near children to reduce the risk.</li><li>Risk of electric shock may occur if using accessories recommended or sold by non-professional product manufacturers.</li><li>When the product is not in use, please unplug the power plug from the product's socket.</li><li>Do not dismantle the product, which may lead to unpredictable risks such as ﬁre, explosion or electric shock.</li><li>Do not use the product through damaged cords or plugs, or damaged output cables, which may cause electric shock.</li><li>Charge the product in a well ventilated area and do not restrict ventilation in any way.</li><li>Please put the product in a ventilated and dry place to avoid rain and water to cause electric shock.</li><li>Do not expose the product to ﬁre or high temperature (under direct sunlight or in vehicle under high heat), which may cause accidents such as ﬁre and explosion.</li><li>When using it for the ﬁrst time, please fully charge the device before use. If this product is stored for a long period of time (3 months - 6 months) with the power depleted, its performance will deteriorate and may even become unchargeable.</li></ul>

<span id="symbols"></span>

# MEANING OF SYMBOLS

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbol</th><th class="hb-symbol-signal-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="WARNING" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">WARNING</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in severe injury, death, and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CAUTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CAUTION</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in personal injury and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTE" class="hb-signal-badge"><span class="hb-signal-label">NOTE</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in equipment damage, data loss, performance deterioration, or unanticipated results.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="TIP" class="hb-signal-badge"><span class="hb-signal-label">TIP</span></span></td><td class="hb-symbol-signal-meaning-cell">Supplements the important information or operation tips in the text.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks." class="hb-symbol-art" src="assets/symbol-1.svg"/></td><td class="hb-symbol-meaning">Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks.</td></tr><tr><td class="hb-symbol-icon"><img alt="Read the user manual before operation." class="hb-symbol-art" src="assets/symbol-2.svg"/></td><td class="hb-symbol-meaning">Read the user manual before operation.</td></tr><tr><td class="hb-symbol-icon"><img alt="Do not dismantle the product." class="hb-symbol-art" src="assets/symbol-3.svg"/></td><td class="hb-symbol-meaning">Do not dismantle the product.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep the product away from fire." class="hb-symbol-art" src="assets/symbol-4.svg"/></td><td class="hb-symbol-meaning">Keep the product away from fire.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep away from children." class="hb-symbol-art" src="assets/symbol-5.svg"/></td><td class="hb-symbol-meaning">Keep away from children.</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly." class="hb-symbol-art" src="assets/symbol-6.svg"/></td><td class="hb-symbol-meaning">This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly.</td></tr><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer." class="hb-symbol-art" src="assets/symbol-7.png"/></td><td class="hb-symbol-meaning">This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">This device complies with part 15 of the FCC Rules. Operation is subject to the following two conditions:</div><div class="line">(1) This device may not cause harmful interference, and</div><div class="line">(2) This device must accept any interference received, including interference that may cause undesired operation.</div></div></div></div><p><strong>NOTE:</strong> This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to radio communications.</p></div><div class="hb-fcc-column hb-fcc-column-right"><p>However, there is no guarantee that interference will not occur in a particular installation. If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:</p><ul class="simple"><li><p>Reorient or relocate the receiving antenna.</p></li><li><p>Increase the separation between the equipment and receiver.</p></li><li><p>Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.</p></li><li><p>Consult the dealer or an experienced radio/TV technician for help.</p></li></ul><p><strong>MODIFICATION:</strong> Any changes or modifications not expressly approved by the grantee of this device could void the user’s authority to operate the device.</p></div></div></figure>

<span id="inbox"></span>

# WHAT'S IN THE BOX

<figure aria-label="What's in the box" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Battery Pack" class="hb-inbox-art" src="assets/inbox-1.png"/><div class="hb-inbox-label"><p>Jackery Battery Pack</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Expansion Cable" class="hb-inbox-art" src="assets/inbox-2.png"/><div class="hb-inbox-label"><p>Expansion Cable</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Documents" class="hb-inbox-art" src="assets/inbox-3.png"/><div class="hb-inbox-label"><p>Documents</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Vertical Stand" class="hb-inbox-art" src="assets/inbox-4.png"/><div class="hb-inbox-label"><p>Vertical Stand</p></div></li></ol></figure>

<span id="overview"></span>

# PRODUCT OVERVIEW

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview" data-source-fragment-sha256="6c8191de26bb59669690df39ef0a0f178989c98b948a374bb3eac923351df39d" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:63%;--hb-y:2%;--hb-width:34%;--hb-height:5%">DC Expansion Port</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62%;--hb-y:7%;--hb-width:36%;--hb-height:3%">Input:40V-57.6V⎓24A Max</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62%;--hb-y:10%;--hb-width:36%;--hb-height:3%">Output:40V-57.6V⎓50A Max</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62%;--hb-y:34%;--hb-width:36%;--hb-height:5%">Main Power Button</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:65%;--hb-y:49%;--hb-width:33%;--hb-height:5%">LCD Screen</span></div></div></figure>

<span id="lcd"></span>

# LCD SCREEN

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd" data-source-fragment-sha256="03e21106852d242795966b24aa9810919ea195cada895b83a1562d154766433f" data-web-base-art-ref="lcd" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:8.7534%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:22.8417%;--hb-y:4.22%;--hb-width:2.1667%;--hb-height:5.3299%">2</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:39.3679%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:39.4125%;--hb-y:94.2347%;--hb-width:2.0889%;--hb-height:5.3299%">7</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:10.8057%;--hb-y:95.0695%;--hb-width:2.2%;--hb-height:5.3299%">5</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:3.1402%;--hb-y:95.0695%;--hb-width:2.2889%;--hb-height:5.3299%">4</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:24.0513%;--hb-y:95.0695%;--hb-width:2.1778%;--hb-height:5.3299%">6</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:58.7708%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:89.3849%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span></div></div></figure>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Input Power / Remaining Charge Time" class="hb-lcd-icon-art" src="assets/lcd-icon-1.svg"/></td><td class="hb-lcd-name">Input Power / Remaining Charge Time</td><td class="hb-lcd-description">Displays the input power and remaining charging time alternately.</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Remaining Battery Percentage" class="hb-lcd-icon-art" src="assets/lcd-icon-2.svg"/></td><td class="hb-lcd-name">Remaining Battery Percentage</td><td class="hb-lcd-description">Displays the remaining battery percentage.</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="Output Power / Remaining Discharge Time" class="hb-lcd-icon-art" src="assets/lcd-icon-3.svg"/></td><td class="hb-lcd-name">Output Power / Remaining Discharge Time</td><td class="hb-lcd-description">Displays the output power and remaining discharging time alternately.</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-icon-4.svg"/></td><td class="hb-lcd-name">Charging Indicator</td><td class="hb-lcd-description"><strong>On:</strong> The Jackery Battery Pack is in the charging state. <strong>Off:</strong> The Jackery Battery Pack is not in the charging state.</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="Battery Power Indicator" class="hb-lcd-icon-art" src="assets/lcd-icon-5.svg"/></td><td class="hb-lcd-name">Battery Power Indicator</td><td class="hb-lcd-description">The orange circle indicates the remaining battery level.</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="DC Input" class="hb-lcd-icon-art" src="assets/lcd-icon-6.svg"/></td><td class="hb-lcd-name">DC Input</td><td class="hb-lcd-description"><strong>On:</strong> The Jackery DC Input Module is connected. <strong>Off:</strong> The Jackery DC Input Module is disconnected.</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="Fault Code" class="hb-lcd-icon-art" src="assets/lcd-icon-7.svg"/></td><td class="hb-lcd-name">Fault Code</td><td class="hb-lcd-description">A product error has occurred. Please refer to the Troubleshooting section for details.</td></tr></tbody></table></figure>

<span id="operations"></span>

# OPERATIONS

## POWER ON/OFF

<div class="native-power-panel"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="7eee304b7982a18b667ba836dc8f5c694902a7e2a11fbf1d8c434c91fa18f9ab" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71%;--hb-y:10%;--hb-width:27%;--hb-height:9%">On</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:71%;--hb-y:18%;--hb-width:27%;--hb-height:7%">Press once</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:71%;--hb-y:29%;--hb-width:27%;--hb-height:9%">Oﬀ</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:71%;--hb-y:36%;--hb-width:27%;--hb-height:7%">Press and hold for 3s</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:77%;--hb-y:46%;--hb-width:12%;--hb-height:8%">3s</span></div></div></figure><table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><p>The product will automatically shut down if it is not charged or no loads are connected for 2 hours.</p></td></tr></tbody></table></div>

## LCD SCREEN ON/OFF

<figure aria-label="LCD SCREEN ON/OFF" class="hb-lcd-mode-composition hb-lcd-mode-portrait" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCD SCREEN ON/OFF" class="hb-lcd-mode-art" src="assets/lcd-button.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">Shortly On</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Press the Main Power Button or when the product is charging.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Steady On (in charging or discharging state)</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Double-press the Main Power Button when the product is powered on.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">The LCD turns off automatically after 2 hours of inactivity.</td></tr></tbody></table></div></figure>

<span id="troubleshooting"></span>

# TROUBLESHOOTING

<p>If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. If the fault persists, please contact Jackery Customer Support.</p>

<figure aria-label="Error Code / Corrective Measures" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Error Code</th><th class="hb-troubleshooting-measures" scope="col">Corrective Measures</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0 / F2 / F3</td><td class="hb-troubleshooting-measures">Restart the product.</td></tr><tr><td class="hb-troubleshooting-code">F1 / F6 / F7 / F8</td><td class="hb-troubleshooting-measures">Contact Jackery Customer Support.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Connect the product to loads to discharge its battery until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Charge the product via solar panels or an AC wall outlet until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures"><p><strong>In high temperature condition:</strong></p><ol><li>Disconnect all charging and discharging cables to the product (including wall charger, solar panels, car charger, and load devices).</li><li>Place the product in a shaded, well-ventilated area where the ambient temperature is below 113°F (45°C).</li><li>Keep the product idle and wait until the fault disappears.</li><li>If the fault persists after repeated attempts, please contact the distributor or Jackery Customer Support.</li></ol><p><strong>In low temperature condition:</strong></p><ol><li>Move the product to a warmer environment above 32°F (0°C).</li><li>Do not use or charge the product outdoors in extremely cold conditions. If necessary, preheat it indoors.</li><li>If the device is moved indoors from a cold environment, let it sit for a while before use.</li><li>When the Low Temperature indicator appears, keep the product idle and wait for the system to recover automatically.</li><li>If the fault persists after repeated attempts, please contact the distributor or Jackery Customer Support.</li></ol></td></tr></tbody></table></figure>

<span id="positioning"></span>

# POSITIONED WITH JACKERY FRIDGEGUARD

## PARALLEL ARRANGEMENT

<p>Position the Jackery Battery Pack and Jackery FridgeGuard in a parallel arrangement.</p>

<div class="hb-reference-figure"><img alt="parallel" class="hb-reference-art" src="assets/parallel.png"/></div>

## STACKED

<p>Place the Jackery Battery Pack and Jackery FridgeGuard in a stack.</p>

<div class="hb-reference-figure"><img alt="stacked" class="hb-reference-art" src="assets/stacked.png"/></div>

## WITH BRACKETS

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>Do not install the product on the non bearing structure, including gypsum board, thermal insulating wall, hollow brick, or the product may fall.</li><li>Avoid the electrical wires, water pipes, gas pipes and other facilities inside the walls.</li></ul></td></tr></tbody></table>

<span id="vertical"></span>

# VERTICAL STAND

<div class="native-vertical-opening"><div class="native-vertical-preparation"><p>Jackery Battery Pack installed with the vertical stand can be positioned on the ground. Please follow the installation steps below:</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="vertical-prep" data-source-fragment-sha256="725c3ed4bede95f2ffafb1f18be72ae08848fa38ad9715ffa72c1b5cff99f0fe" data-web-base-art-ref="vertical-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="vertical-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#f7f7f7"><img alt="" class="hb-reference-art hb-reference-art hb-composite-art" src="assets/vertical-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4%;--hb-y:3%;--hb-width:92%;--hb-height:14%">Preparation before installation:</span></div></div></figure></div><div class="native-vertical-result"><div class="hb-reference-figure"><img alt="Vertical stand installation result" class="hb-reference-art" src="assets/vertical-result.png"/></div></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Remove two screws from the bottom of the Battery Pack.</p><div class="hb-reference-figure"><img alt="vertical-1" class="hb-reference-art" src="assets/vertical-1.png"/></div></div><div class="native-step-card"><p>2. Align the mounting holes on the bottom of the Battery Pack with the holes on the vertical stand.</p><div class="hb-reference-figure"><img alt="vertical-2" class="hb-reference-art" src="assets/vertical-2.png"/></div></div><div class="native-step-card"><p>3. Tighten the screws.</p><div class="hb-reference-figure"><img alt="vertical-3" class="hb-reference-art" src="assets/vertical-3.png"/></div></div></div>

<span id="wall-mount"></span>

# JACKERY WALL-MOUNTED BRACKET (SOLD SEPARATELY)

<p>Jackery Battery Pack installed with the mounting bracket can be positioned on the wall. Please follow the installation steps below:</p>

## ON WOODEN WALLS

<div class="native-wood-opening"><div class="native-wood-preparation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-prep" data-source-fragment-sha256="9ded90a2e3a3f2ec103b041147b0fa54f2d72a3973f8d9f888cea00dc70f6626" data-web-base-art-ref="wood-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:5%;--hb-y:3%;--hb-width:68%;--hb-height:13%">Preparation before installation:</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:57%;--hb-y:24%;--hb-width:21%;--hb-height:18%">SOLD SEPARATELY</span></div></div></figure></div><div class="native-wood-result"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-result" data-source-fragment-sha256="2e978cda681b76846b63f1c5748f6a108df9f818ff24f6534cd7c3a8989216f3" data-web-base-art-ref="wood-result" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-result.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-result.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:10%;--hb-y:0%;--hb-width:80%;--hb-height:10%">wood stud</span></div></div></figure></div></div>

<div class="native-wall-wood-steps"><div class="native-wall-panel native-wood-1-2"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-1-2" data-source-fragment-sha256="55b6cbab18b38b1bd5ed9236d45d9057c4fabc99ee27c5323c4f4654f028b00c" data-web-base-art-ref="wood-1-2" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-1-2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-1-2.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3%;--hb-y:5%;--hb-width:70%;--hb-height:8%">1. Install the Jackery FridgeGuard according to the user manual.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3%;--hb-y:13%;--hb-width:70%;--hb-height:8%">2. Remove two screws from the bottom of the Battery Pack.</span></div></div></figure></div><div class="native-wall-panel native-wood-3"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-3" data-source-fragment-sha256="0f0ee4e4872b0c3e3052ae7f3ccb92033aa4c7b7adf5dcab8d1e35bbf6e2c893" data-web-base-art-ref="wood-3" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-3.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:39%;--hb-y:4%;--hb-width:57%;--hb-height:22%">3. Securely attach the upper and lower mounting brackets to the back of the Battery Pack.</span></div></div></figure></div><div class="native-wall-panel native-wood-4"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-4" data-source-fragment-sha256="8532f600d1888686aec8ecab6595cf6a0b1b8598ebcf479335ea5538bef30f77" data-web-base-art-ref="wood-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7%;--hb-y:4%;--hb-width:89%;--hb-height:17%">4. Use a stud finder to identify wood studs behind the wall.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:65%;--hb-y:32%;--hb-width:32%;--hb-height:11%">wood stud</span></div></div></figure></div><div class="native-wall-panel native-wood-5"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-5" data-source-fragment-sha256="2b2e0ec33e8ef722decbff96f3596fcdb2251284fd1aace8fe24cc9dd33a8ac8" data-web-base-art-ref="wood-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3%;--hb-y:4%;--hb-width:94%;--hb-height:13%">5. Measure a horizontal distance of 406mm (16 in) from the bolt position on the Jackery FridgeGuard, and mark the mounting point on the wood stud of the wall.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3%;--hb-y:16%;--hb-width:94%;--hb-height:10%">* 406mm (16 in) is the recommended distance, and actual distance depends on wall conditions.</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:33.5914%;--hb-y:21.1809%;--hb-width:16.2108%;--hb-height:7.557%">wood stud</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:58.5429%;--hb-y:20.5752%;--hb-width:16.2108%;--hb-height:7.557%">wood stud</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:44.8879%;--hb-y:40.1803%;--hb-width:19.0607%;--hb-height:7.557%">406mm (16 in)</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:4.6084%;--hb-y:67.2917%;--hb-width:25.3171%;--hb-height:7.557%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-wall-panel native-wood-6"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-6" data-source-fragment-sha256="f9258da45c467d5c0c9fa90b819c18ac6861abefd8c772747065f257b8305f87" data-web-base-art-ref="wood-6" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-6.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-6.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3%;--hb-y:4%;--hb-width:94%;--hb-height:15%">6. Drive the wood screw into the wall at the mounting point, leaving a 2-4mm gap between the screw and the wall.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:66.3707%;--hb-y:31.4483%;--hb-width:13.4462%;--hb-height:9.2069%">2~4mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:44.5016%;--hb-y:21.3514%;--hb-width:16.2108%;--hb-height:9.2069%">wood stud</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:1.9525%;--hb-y:39.2574%;--hb-width:22.2641%;--hb-height:8.1724%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-wall-panel native-wood-7"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-7" data-source-fragment-sha256="8896d094dfd5aacc080be67064609c76730817f14eb96cd4f7de7fb383d7fb2a" data-web-base-art-ref="wood-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="wood-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3%;--hb-y:3%;--hb-width:94%;--hb-height:18%">7. Hang the Battery Pack onto the screw vertically. Drive a self-tapping screw through the mounting hole in the bottom bracket into the wall and tighten it. Then, fully tighten the wood screw.</span></div></div></figure></div></div>

## ON CONCRETE WALLS

<div class="native-concrete-opening"><div class="native-concrete-preparation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-prep" data-source-fragment-sha256="4fd692538b2e960b76be9a03af84cfe0413257ed6a33cee87070b5009646a39b" data-web-base-art-ref="concrete-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4%;--hb-y:3%;--hb-width:75%;--hb-height:13%">Preparation before installation:</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:54%;--hb-y:27%;--hb-width:25%;--hb-height:18%">SOLD SEPARATELY</span></div></div></figure></div><div class="native-concrete-result"><div class="hb-reference-figure"><img alt="concrete-result" class="hb-reference-art" src="assets/concrete-result.png"/></div></div></div>

<div class="native-wall-concrete-steps"><div class="native-wall-panel native-concrete-1-2"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-1-2" data-source-fragment-sha256="bc32ed46c5b5af61025f5d7c1097f7389fc2deaacca1a5a336c67dd12f97eedd" data-web-base-art-ref="concrete-1-2" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-1-2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-1-2.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3%;--hb-y:5%;--hb-width:70%;--hb-height:8%">1. Install the Jackery FridgeGuard according to the user manual.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3%;--hb-y:13%;--hb-width:70%;--hb-height:8%">2. Remove two screws from the bottom of the Battery Pack.</span></div></div></figure></div><div class="native-wall-panel native-concrete-3"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-3" data-source-fragment-sha256="ac58535bcc15f3ee633f7543a0a643c59699ce8eef6b1829815772d37f5567d6" data-web-base-art-ref="concrete-3" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-3.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:40%;--hb-y:3%;--hb-width:56%;--hb-height:16%">3. Securely attach the upper and lower mounting brackets to the back of the Battery Pack.</span></div></div></figure></div><div class="native-wall-panel native-wall-pair native-concrete-4-5"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-4-5" data-source-fragment-sha256="d87abb9f98d491263daa0f4dfb617bcfddc257459cdd95e401874504c299a298" data-web-base-art-ref="concrete-4-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-4-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-4-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.6%;--hb-y:4.8%;--hb-width:48%;--hb-height:11%">4. Measure a horizontal distance of 406mm (16 in) from the bolt position on the Jackery FridgeGuard, and mark the mounting point on the wall.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3.6%;--hb-y:18.5%;--hb-width:48%;--hb-height:11%">* 406mm (16 in) is the recommended distance, and actual distance depends on wall conditions.</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:13.443%;--hb-y:30%;--hb-width:17.3639%;--hb-height:7%">406mm (16 in)</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:22.9652%;--hb-y:78%;--hb-width:30.807%;--hb-height:7%">Jackery FridgeGuard</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:59%;--hb-y:4.8%;--hb-width:38%;--hb-height:19%">5. Drill a hole at the mounting point using an 8mm masonry impact drill to a depth of approximately 70mm. Insert an expansion bolt and loosen its nut by 2-4mm.</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:79.1899%;--hb-y:41%;--hb-width:9.1044%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:76.1551%;--hb-y:73%;--hb-width:10.4051%;--hb-height:7%">2~4mm</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:87.8608%;--hb-y:52%;--hb-width:9.9715%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-wall-panel native-wall-pair native-concrete-6-7"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-6-7" data-source-fragment-sha256="205f597a27d503eba199f8dbf5cb6d2347e71aea68e3ad2b88f6d6500541e61f" data-web-base-art-ref="concrete-6-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-6-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-6-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.6%;--hb-y:4.3%;--hb-width:34%;--hb-height:13%">6. Hang the Battery Pack onto the expansion bolt vertically and mark the mounting point on the wall.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:45.5%;--hb-y:4.3%;--hb-width:50.5%;--hb-height:13%">7. Remove the product. Drill a hole at the mounting point and insert an expansion bolt without the nut and washer into the hole.</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:78.1551%;--hb-y:39%;--hb-width:13.443%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:85.9968%;--hb-y:50%;--hb-width:11.2025%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-wall-panel native-wall-pair native-concrete-8-9"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-8-9" data-source-fragment-sha256="d8303152eae226cae56598e21d504a281e0e47da5ba446184fc2dfc1b240a3d9" data-web-base-art-ref="concrete-8-9" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="concrete-8-9.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-8-9.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4%;--hb-y:5%;--hb-width:28%;--hb-height:12%">8. Hang the product onto the upper expansion bolt.</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:39%;--hb-y:5%;--hb-width:57%;--hb-height:12%">9. Lift the product to align the pre-installed bolt and lower it into place. Tighten the nut.</span></div></div></figure></div></div>

<span id="connections"></span>

# CONNECTIONS

<p>Jackery Battery Pack can be used along with Jackery FridgeGuard to meet the increased capacity needs.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Ensure all products are powered off before connecting the Jackery FridgeGuard to the Jackery Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="connections" class="hb-reference-art" src="assets/connections.png"/></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTES</td><td class="manual-callout-body"><p>The display of the icon <img alt="" class="native-inline-pack" src="assets/connection-icon.svg"/> on the LCD screen (Jackery FridgeGuard) signifies a successful connection between the battery pack and the Jackery FridgeGuard.</p></td></tr></tbody></table>

<span id="charging"></span>

# CHARGING

## CHARGING VIA AC WALL OUTLET

<p>When charging from the wall, this product must be used with Jackery FridgeGuard.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">WARNING</td><td class="manual-callout-body"><p>Ensure all products are powered off before connecting the Jackery FridgeGuard to the Jackery Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="ac" class="hb-reference-art" src="assets/ac.png"/></div>

## CHARGING VIA SOLAR PANELS (SOLD SEPARATELY)

<p>Charge your product with solar panels and Jackery DC Input Module as shown in the figure below. Please refer to the Jackery DC Input Module user manual for more information.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar" data-source-fragment-sha256="f22437451b71c691729af99ef4443af2145b0d02b6d23ae7128a0012024e57d7" data-web-base-art-ref="solar" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:23.2139%;--hb-y:51.0353%;--hb-width:14.2673%;--hb-height:5.1953%">SolarSaga 500 X</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:57.8558%;--hb-y:76.2323%;--hb-width:8.3319%;--hb-height:5.1953%">DC8020</span></div></div></figure>

<p>*The Jackery DC Input Module is sold separately.</p>

## CHARGING WITH A CAR CHARGER (SOLD SEPARATELY)

<p>Charge your product with car charger and Jackery DC Input Module as shown in the figure below. Please refer to the Jackery DC Input Module user manual for more information.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="d88e9dd241317e0965c1260eb8ffa88b4abd74d64ac5992505b1a1fc83417892" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65%;--hb-y:14%;--hb-width:25%;--hb-height:9%">Vehicle</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:30%;--hb-y:63%;--hb-width:20%;--hb-height:9%">DC8020</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="2" style="--hb-x:53%;--hb-y:65%;--hb-width:43%;--hb-height:18%;--hb-fill:#f2f2f2">※ The car charging cable and Jackery DC Input Module are sold separately.</span></div></div></figure>

<span id="storage"></span>

# STORAGE

<p>Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:</p>

<ul><li>1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)</li><li>3 months: 32°F to 113°F / 0°C to 45°C (0-60%RH)</li><li>12 months: 32°F to 77°F / 0°C to 25°C (0-60%RH)</li></ul>

<p>If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 months.</p>

<span id="specifications"></span>

# SPECIFICATIONS

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JBP-1000B-SIL</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">20Ah / 51.2Vdc (1024 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 19.8 lbs/9 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">23.6 × 12.8 × 2.4 in/60 × 32.5 × 6 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">6000 cycles to 70%+ capacity</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">INPUT/OUTPUT PORTS</h2>

<figure aria-label="INPUT/OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">40V-57.6V⎓24A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">40V-57.6V⎓50A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1250A/1.55ms</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Discharge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr></tbody></table></figure>

<span id="warranty"></span>

# WARRANTY

<figure aria-label="Warranty" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel">We only provide our warranty to customers who purchase from the official Jackery website, Jackery-branded third-party platforms, or local authorized dealers.</div><div class="hb-warranty-local-note">*Warranty period and details may vary according to local laws, regulations, and authorized dealers.</div></figure>

## Limited Warranty

<figure aria-label="Limited Warranty" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects in workmanship and material under normal consumer use during the applicable warranty period identified in the 'Warranty Period' section below, subject to the exclusions set forth below.</p><p>This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, nor authorize any person to assume for us, any other liability in connection with the sale of our products.</p></figure>

## Warranty Period

<figure aria-label="Warranty Period" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 YEARS Standard Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Standard Warranty</strong></div></div><div class="hb-warranty-period-copy">The standard warranty period for Jackery Battery Pack is 36 months. In each case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. The sales receipt from the first consumer purchaser, or other reasonable documentary proof, is required in order to establish the start date of the warranty period.</div></div><div aria-label="2 YEARS Extended Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Extended Warranty</strong></div></div><div class="hb-warranty-period-copy">To activate the Warranty Extension, you must register your product online or contact our customer service team at hello@jackery.com to extend the standard warranty runtime.</div></div></div></figure>

## Repair or replacement

<figure aria-label="Repair or replacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the applicable warranty period due to a defect in workmanship or material. The repaired/replaced product assumes the remaining warranty of the original date of purchase.</p></figure>

## Limited to Original Consumer Buyer

<figure aria-label="Limited to Original Consumer Buyer" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable to any subsequent owner.</p></figure>

## Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery's warranty does not apply to:</p><ul><li>Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as authorized in Jackery's current product literature.</li><li>Attempted repair by anyone other than an authorized facility.</li><li>Any product purchased through an online auction house.</li><li>Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within seven days after you purchase the product and at least once every 6 months thereafter.</li></ul></figure>

## Interpretation Rights

<figure aria-label="Interpretation Rights" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery reserves the right to final interpretation of the above customers' after-sales policy.</p></figure>

<span id="contact"></span>

# JACKERY INC.

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>hello@jackery.com www.jackery.com 1-888-502-2236 (US)</p>
