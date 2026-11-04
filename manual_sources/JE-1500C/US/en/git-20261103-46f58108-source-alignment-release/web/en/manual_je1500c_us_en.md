<style>
/* Source geometry only. The shared Web theme owns every colour, border, fill,
   heading, callout, table, card and figure style (prepared-document shared-style
   gate). Figures are selected by their shared data attributes. */

/* Source panels keep the print's own width; no visible caption. */
#furo-main-content .hb-reference-figure { max-width: 680px; margin-left: auto; margin-right: auto; }

/* Small print drawings and marks keep a print-like size. */
#furo-main-content .hb-reference-figure[data-reference-id="overview-ac-total"] { max-width: 400px; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map"] { max-width: 560px; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving"] { max-width: 560px; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add"] { max-width: 380px; }
#furo-main-content .hb-reference-figure[data-reference-id="app-results"] { max-width: 560px; }
#furo-main-content .hb-reference-figure:is([data-reference-id^="cleaning-"]) { max-width: 330px; }
#furo-main-content .hb-reference-figure[data-reference-id="contact-qr"] { max-width: 6.5rem; margin-left: 0; }

/* Print case for chapter and subheadings; shared markers stay. */
#furo-main-content :is(h1, h3, h4), #furo-main-content h2:not(.hb-spec-section) { text-transform: none; }

/* Native two-row source button table; original crops, no redrawn icon. */
#furo-main-content [data-source-layout="button-operations"] table { min-width: 0; width: 100%; }
#furo-main-content [data-source-layout="button-operations"] td:first-child { width: 38%; text-align: center; }
#furo-main-content [data-source-button] { display: inline-flex; vertical-align: middle; align-items: center; flex-direction: column; width: 5rem; }
#furo-main-content [data-source-button] img { width: 2.5rem; height: 2.5rem; object-fit: contain; }
#furo-main-content [data-source-button] p { margin: .25rem 0 0; font-size: .75rem; }
#furo-main-content img[src$="button-clock.png"] { width: 1rem; height: 1rem; display: inline; vertical-align: middle; }
#furo-main-content [data-source-layout="cleaning-steps"] { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
@media (max-width: 760px) {
 #furo-main-content [data-source-layout="button-operations"] table { min-width: 40rem; }
 #furo-main-content [data-source-layout="cleaning-steps"] { grid-template-columns: minmax(0, 1fr); }
}
#furo-main-content [data-source-role~="native-contact-card"] { margin: 2.2rem 0 1rem; }
#furo-main-content p[data-source-role~="native-contact-company"] { margin: 0; font-size: 1.25rem; }
#furo-main-content p[data-source-role~="native-contact-address"] { margin: 0.15rem 0 0.75rem; }
#furo-main-content [data-source-role~="native-contact-row"] { display: flex; flex-wrap: wrap; align-items: stretch; gap: 0.6rem; }
#furo-main-content [data-source-role~="native-contact-panel"] {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem 1.4rem;
  padding: 0.75rem 1.2rem;


}
#furo-main-content [data-source-role~="native-contact-qr"] {
  display: grid;
  place-items: center;
  padding: 0.35rem;


}
#furo-main-content [data-source-role~="native-contact-qr"] img { width: 3.6rem !important; height: auto !important; margin: 0 !important; }
#furo-main-content p[data-source-role~="native-contact-phone"] { margin: 0; font-size: 1.55rem; line-height: 1.1; }
#furo-main-content [data-source-role~="native-contact-region"] { font-size: 0.55em; font-weight: 400; }
#furo-main-content [data-source-role~="native-contact-links"] { padding-left: 1.2rem;  }
#furo-main-content [data-source-role~="native-contact-links"] p { margin: 0; line-height: 1.5; }
#furo-main-content img[data-source-role~="native-contact-glyph"] { display: inline-block; width: auto !important; height: 1.05em !important; margin: 0 0.45em 0 0 !important; vertical-align: -0.12em; }
#furo-main-content p[data-source-role~="native-contact-phone"] img[data-source-role~="native-contact-glyph"] { height: 1.15em !important; vertical-align: -0.2em; margin-right: 0.3em !important; }
#furo-main-content .manual-two-col-table {width:100%;table-layout:fixed;}
#furo-main-content .manual-two-col-table > tbody > tr > td {width:50%;vertical-align:top;padding:0 .6rem 0 0;}
#furo-main-content .manual-two-col-table > tbody > tr > td + td {padding:0 0 0 .6rem;}
#furo-main-content :is(h2,h3):has(> [data-source-role~="native-band"]) {display:block;padding:.35rem .7rem;}
#furo-main-content :is(h2,h3):has(> [data-source-role~="native-band"])::before {display:none;}
#furo-main-content [data-source-role~="native-contained-panel"] {max-width:680px;margin:1rem auto;padding:.6rem;}
#furo-main-content [data-source-role~="native-contained-panel"] .hb-reference-figure {margin:.2rem auto;}
#furo-main-content [data-source-role~="native-panel-note"] {padding:.7rem;margin:.5rem 0;}
#furo-main-content [data-source-role~="native-panel-note"] > :last-child {margin-bottom:0;}
#furo-main-content [data-source-role~="native-gray-panel"] {}
#furo-main-content .native-prose-pill {display:inline-block;padding:.1rem .55rem;margin-bottom:.4rem;}
#furo-main-content .native-prose-pill p {margin:0;font-size:.85rem;}
#furo-main-content [data-source-role~="native-contact-panel"] {}
@media(max-width:640px){#furo-main-content .manual-two-col-table > tbody > tr > td {width:100%;padding:0;}}

#furo-main-content td.hb-lcd-number { text-align: center; vertical-align: middle !important; }
#furo-main-content .native-lcd-number {
  display: inline-grid;
  place-items: center;
  min-width: 1.5em;
  height: 1.5em;
  padding: 0 0.12em;
  box-sizing: border-box;


  font-size: 0.86em;
  line-height: 1;
}

/* Source p5 uses the original white warning glyph, not a font character. */

/* Source p10: native text occupies the original right-hand bubble. */
#furo-main-content [data-source-role~="native-figure-scroll"] {overflow-x:auto;}
#furo-main-content [data-source-role~="native-power-figure"] {position:relative;min-width:660px;}
#furo-main-content [data-source-role~="native-power-figure"] .hb-reference-figure {padding:0;}
#furo-main-content [data-source-role~="native-power-note"] {position:absolute;top:57%;left:44%;right:1%;font-size:.8rem;line-height:1.2;}
#furo-main-content [data-source-role~="native-power-note"] p {margin:0;}
#furo-main-content [data-source-role~="native-contained-panel"] > .hb-reference-figure {}
#furo-main-content .hb-troubleshooting-table td.hb-troubleshooting-code:has(> .source-fault-code) {padding:0!important;}
#furo-main-content .source-fault-code {display:block;padding:.2em .5em;}
#furo-main-content .source-fault-code:last-child {}
#furo-main-content .hb-fcc-opening {align-items:center;}
#furo-main-content .hb-spec-table td {vertical-align:top;}

#furo-main-content [data-source-role~="native-power-figure"] {min-width:620px;}
#furo-main-content [data-source-role~="native-power-note"] {position:relative;top:auto;left:auto;right:auto;margin-left:44%;margin-top:-125px;}
#furo-main-content [data-source-role~="native-power-note"] .hb-text-panel, #furo-main-content [data-source-role~="native-power-note"] .hb-text-panel p {font-size:.78rem;line-height:1.25;}
#furo-main-content [data-source-role~="native-power-note"] .hb-text-panel {padding:.6rem;}
#furo-main-content #save-these-instructions>h3::before {display:none;}
#furo-main-content .manual-two-col-table ul ul {list-style-type:"- ";}
#furo-main-content [data-source-role~="native-contained-panel"]>.hb-text-panel {display:table;padding:.35rem .75rem;margin:.2rem 0;}

/* Current source p7 right-hand AC total detail andp15 native caption. */
#furo-main-content .hb-reference-figure[data-reference-id="overview-ac-total"] {margin-left:auto;margin-right:0;}
#furo-main-content [data-source-role~="native-car-note"] {position:relative;margin:-2.7rem 0 .5rem 45%;padding:.3rem .5rem;font-size:.8rem;line-height:1.25;}
#furo-main-content [data-source-role~="native-car-note"] p {margin:0;}
#furo-main-content [data-source-layout="cleaning-steps"]>.container {padding:1rem;}
#furo-main-content [data-source-layout="cleaning-steps"] .hb-reference-figure {margin:0;}
#furo-main-content .native-step-number {display:inline-grid;place-items:center;min-width:1.35em;height:1.35em;line-height:1;}
#furo-main-content #app-setup>section>h2::before {display:inline-block;}
@media(max-width:760px){#furo-main-content [data-source-role~="native-car-note"] {margin:0;}}

#furo-main-content #app-setup>section>h2 {gap:.5em;}

#furo-main-content [data-source-geometry="inline-1"]{width:30px;height:auto}
#furo-main-content [data-source-geometry="inline-2"]{width:48px;height:auto}
#furo-main-content [data-source-layout="safety-columns"] {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1.2rem;}
#furo-main-content [data-source-layout="risk-strip"] {display:grid;grid-template-columns:7% minmax(0,1fr);align-items:center;font-size:.8rem;line-height:1.22;}
#furo-main-content [data-source-layout="warning-lead"] {display:grid;grid-template-columns:20% minmax(0,1fr);align-items:center;font-size:.78rem;line-height:1.18;}
#furo-main-content [data-source-layout="risk-strip"] > *, #furo-main-content [data-source-layout="warning-lead"] > * {padding:.35rem .5rem;}
#furo-main-content [data-source-layout="warning-lead"] [data-source-part="0"] {padding:0;align-self:stretch;display:flex;}
#furo-main-content [data-source-layout="warning-lead"] p {margin:0;}
#furo-main-content [data-source-layout="warning-lead"] [data-source-part="1"] p:first-child {margin-bottom:.15rem;font-size:1.02rem;line-height:1.15;}
#furo-main-content [data-source-heading="safety-pill"] {display:block;width:100%;font-size:1rem;padding:.35rem .7rem;}
#furo-main-content .hb-symbol-signal-table img.hb-signal-icon {width:1.15rem!important;height:1.15rem!important;margin:0!important;object-fit:contain;}
@media(max-width:640px){#furo-main-content [data-source-layout="safety-columns"] {grid-template-columns:minmax(0,1fr);gap:0;}}

#furo-main-content #jackery-inc > h2 {display:block;font-size:1.25rem;line-height:1.2;}
#furo-main-content #jackery-inc > h2::before {display:none;}
#furo-main-content [data-source-layout="cleaning-steps"] .hb-step-copy {grid-template-columns:1.35rem minmax(0,1fr);gap:.35rem;}
#furo-main-content [data-source-layout="cleaning-steps"] .hb-step-copy > .rubric {width:1.35rem;height:1.35rem;font-size:1rem;line-height:1;}
#furo-main-content [data-source-layout="cleaning-steps"] .hb-step-copy > .rubric + p {padding:0;}
@media(max-width:640px){#furo-main-content [data-source-role~="native-contact-panel"] {flex:1;min-width:0;padding:.5rem .6rem;gap:.3rem;}#furo-main-content [data-source-role~="native-contact-phone"] {font-size:1.2rem;}#furo-main-content [data-source-role~="native-contact-links"] {padding-left:1.2rem;}#furo-main-content [data-source-role~="native-contact-row"] {flex-wrap:nowrap;align-items:center;}}

#furo-main-content #app-setup #jackery-inc > h2::before {display:none;}
@media(max-width:640px){#furo-main-content p[data-source-role~="native-contact-phone"] {font-size:1.2rem;}}

#furo-main-content [data-source-role~="native-car-panel"] {padding:0;}
#furo-main-content [data-source-role~="native-car-panel"] .hb-reference-figure {margin:0;}

</style>

<span id="native-introduction"></span>

## IMPORTANT

<p>Congratulations on your new Jackery Explorer 1500 Ultra. Please read this manual carefully before using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible place for frequent reference.</p>

<p>In compliance with laws and regulations, the right of final interpretation of this document and all related documents of this product resides with the Company.</p>

<p>Please kindly notice that no further notifications will be given in case of any update, revision or termination.</p>

<span id="native-safety"></span>

## IMPORTANT SAFETY INFORMATION

<div class="hb-symbol-signal-composition hb-safety-instruction" data-source-layout="risk-strip"><div data-source-part="0"><img alt="" data-source-geometry="inline-1" src="assets/warning_triangle_dark.svg" width="30"/></div><div data-source-part="1"><p><strong>INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS</strong></p></div></div>

<div class="manual-two-col-table" data-source-layout="safety-columns"><div data-source-column="0"><div class="hb-symbol-signal-composition hb-safety-lead" data-source-layout="warning-lead"><div data-source-part="0"><span class="hb-signal-badge"><img alt="" data-source-geometry="inline-2" src="assets/warning_triangle_white.svg" width="48"/></span></div><div data-source-part="1"><p><strong>WARNING</strong></p><p><strong>Always follow these basic precautions when using this product.</strong></p></div></div><ul><li>Read all the instructions before using the product.</li><li>Please ensure that this device maintains a distance of at least 20cm from the human body during use.</li><li>Do not allow children to play on the product. Close supervision of children is necessary when the product is used near children.</li><li>Avoid placing hands or fingers inside the product.</li><li>Stop using the product immediately if it has been physically damaged or modified. Improper use of the product may cause unpredictable behavior, leading to fire, explosion, or injury.</li><li>If any of the following are observed, including but not limited to overheats, emits unusual odors or smoking, leaks, or burns, stop using the product immediately and contact the dealer or our Customer Support.</li><li>Never attempt to open, repair, or modify the product.</li></ul></div><div data-source-column="1"><p>Any tampering, reassembly, or modification of the product can result in electric shock, fire, or battery damage.</p><ul><li>Be aware that liquid ejected from the product may cause irritation or burns. Inappropriate or abusive use may lead to battery leakage. Avoid direct contact with leaking liquid. If the liquid contacts your eyes, seek medical help immediately. If it contacts other body parts, flush with running water and consult a medical professional without delay.</li><li>Do not expose the product to fire or excessive temperatures. Doing so may result in an explosion if the temperature exceeds 130°C (265°F).</li><li>Any use of unrecommended or non-supplied materials or parts with the product may result in a risk of fire, electric shock, or personal injury.</li><li>Do not leave the battery charging unattended for long periods. Always monitor the charging process to ensure safe operation.</li><li>To reduce the risk of electric shock, unplug the product from any power source before attempting any technical service or troubleshooting.</li></ul></div></div>

<p class="hb-prose-pill" data-source-heading="safety-pill"><span class="" data-source-role="native-band">OPERATING INSTRUCTIONS</span></p>

#### SAVE THESE INSTRUCTIONS

<div class="manual-two-col-table" data-source-layout="safety-columns"><div data-source-column="0"><ul><li>Stop using the product immediately if it shows signs of damage. Discontinue use and contact customer support for assistance.</li><li>Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's specified operating temperature ranges :<ul><li>Charging temperature: 32°F to 113°F (0°C to 45°C )</li><li>Discharging temperature: 5°F to 113°F (-15°C to 45°C )</li></ul></li><li>To ensure proper air circulation, keep the product vents uncovered. The area where the product is used must have adequate airflow in a cool, dry environment to prevent overheating.<ul><li>Charging in damp or poorly ventilated spaces may cause safety hazards.</li><li>Water can cause short circuits or damage to the charger, leading to safety risks.</li></ul></li><li>Unplug the power cord from a power outlet during a storm.</li><li>Immediately turn off the product by pressing the power button if it has fallen, been dropped, or exposed to vibrations.</li></ul></div><div data-source-column="1"><ul><li>Ensure the device(s) are powered off before connecting it to the product.</li><li>Do not charge the product using a damaged or broken charging cord or plug.</li><li>Do not use the product to charge any device with a damaged or broken cable or plug.</li><li>Always unplug the charging cord by pulling the plug, not the cord, to reduce the risk of damage.</li><li>Ensure the product is properly secured when transporting it in a moving vehicle.</li><li>DO NOT place the unit upside down or on its side during use or storage.</li><li>DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor during operation in a workshop or repair facility.</li><li>DO NOT use the product's accessories with other devices or equipment.</li><li>Solar charge time depends on weather conditions, place your solar panel where it will get as much direct sunlight as possible.</li></ul></div></div>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/warning_triangle_dark.svg"/>DANGER</span></td><td class="manual-callout-body"><p><strong>This device is intended for indoor use only (Please place this device in a similar indoor environment when using it outdoors, e.g. Home RVs, tents, cabins, etc.).<br/>※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.</strong></p></td></tr></tbody></table>

<p class="hb-prose-pill" data-source-heading="safety-pill"><span class="" data-source-role="native-band">USER MAINTENANCE INSTRUCTIONS</span></p>

<p>During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is expected. As the number of charge and discharge cycles increases and storage time extends, this degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of battery cells.</p>

<span id="native-symbols"></span>

## MEANING OF SYMBOLS

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th scope="col">Symbol</th><th scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="WARNING" class="hb-signal-badge"><img alt="" class="hb-signal-icon" height="18" src="assets/warning_triangle_white.svg" width="18"/><span class="hb-signal-label">WARNING</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in severe injury, death, and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CAUTION" class="hb-signal-badge"><img alt="" class="hb-signal-icon" height="18" src="assets/warning_triangle_white.svg" width="18"/><span class="hb-signal-label">CAUTION</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in personal injury and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTE" class="hb-signal-badge"><img alt="" class="hb-signal-icon" height="18" src="assets/warning_triangle_white.svg" width="18"/><span class="hb-signal-label">NOTE</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in equipment damage, data loss, performance deterioration, or unanticipated results.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="TIP" class="hb-signal-badge"><img alt="" class="hb-signal-icon" height="18" src="assets/warning_triangle_white.svg" width="18"/><span class="hb-signal-label">TIP</span></span></td><td class="hb-symbol-signal-meaning-cell">Supplements the important information or operation tips in the text.</td></tr></tbody></table></figure>

<figure aria-label="MEANING OF SYMBOLS" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks.</td></tr><tr><td class="hb-symbol-icon"><img alt="Read the user manual before operation." class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Read the user manual before operation.</td></tr><tr><td class="hb-symbol-icon"><img alt="Risk of electric shock" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Risk of electric shock</td></tr><tr><td class="hb-symbol-icon"><img alt="Battery charging" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Battery charging</td></tr><tr><td class="hb-symbol-icon"><img alt="Explosive material" class="hb-symbol-art" src="assets/symbol_explosive_material_native_v2_3e3a39.svg"/></td><td class="hb-symbol-meaning">Explosive material</td></tr><tr><td class="hb-symbol-icon"><img alt="Heavy object" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Heavy object</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Do not dismantle the product." class="hb-symbol-art" src="assets/symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">Do not dismantle the product.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep the product away from fire." class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Keep the product away from fire.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep away from children." class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Keep away from children.</td></tr><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly." class="hb-symbol-art" src="assets/symbol_li_ion_htp017.svg"/></td><td class="hb-symbol-meaning">This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly.</td></tr><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer.</td></tr></tbody></table></div></div></figure>

<div class="" data-source-role="native-fcc-fixed"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc_mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">This device complies with part 15 of the FCC Rules. Operation is subject to the following two conditions: (1) This device may not cause harmful interference, and (2) this device must accept any interference received, including interference that may cause undesired operation.</div></div></div></div><p><strong>NOTE:</strong> This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to communications. However, there is no guarantee that radio interference will not occur in a particular installation.</p></div><div class="hb-fcc-column hb-fcc-column-right"><p>If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:</p><ul class="simple"><li><p>Reorient or relocate the receiving antenna.</p></li><li><p>Increase the separation between the equipment and receiver.</p></li><li><p>Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.</p></li><li><p>Consult the dealer or an experienced radio/TV technician for help.</p></li></ul><p><strong>MODIFICATION:</strong> Any changes or modifications not expressly approved by the grantee of this device could void the user’s authority to operate the device.</p></div></div></figure></div>

<span id="native-in_the_box"></span>

## WHAT'S IN THE BOX

<figure aria-label="WHAT'S IN THE BOX" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="three-card-responsive"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Explorer 1500 Ultra" class="hb-inbox-art" src="assets/inbox-unit.png"/><div class="hb-inbox-label"><p>Jackery Explorer 1500 Ultra</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC Charging Cable" class="hb-inbox-art" src="assets/inbox-ac-cable.png"/><div class="hb-inbox-label"><p>AC Charging Cable</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="User Manual" class="hb-inbox-art" src="assets/inbox-user-manual.png"/><div class="hb-inbox-label"><p>User Manual</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">TIP</div><div class="hb-inbox-tip-body">The car charging cable is not included but is available for purchase separately on our website. For assistance, please contact Jackery Customer Support.</div></div></figure>

<span id="native-product_overview"></span>

## PRODUCT OVERVIEW

### FRONT VIEW

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="9f15d9a83a7b2a1fd9dcebbc041066fa354787bce4bf5c62a5a5a1b16489533b" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-front.semantic"><img alt="Front view of the Jackery Explorer 1500 Ultra: LCD; Main Power Button; DC 12V Port, 12V⎓10A Max; Protective Cover; DC Input, 2×DC8020 Ports: Car: 12-16V⎓8A Max, Double to 8A Max, PV: 16-60V⎓12A, Double to 24A / 800W Max; AC Input, 100-120V~60Hz, 15A Max; AC Power Button; USB-C1 Output, 30W Max, 5V⎓3A, 9V⎓3A, 12V⎓2.5A, 15V⎓2A, 20V⎓1.5A; USB-C2 Output, 100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A; USB-A Output, 18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A; AC Output, 120V~60Hz, 1800W" class="hb-reference-art hb-composite-art" src="assets/overview-front.png"/></div></figure>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-ac-total" data-source-fragment-sha256="b1b37a0686fa28c2b1c7acc3ce3ff67f70ba609e5513de8b18fcb1d3932774f1" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-ac-total.semantic"><img alt="AC Total Output, 1800W Rated (2000W for 15min. Max) 3600W Surge Peak" class="hb-reference-art hb-composite-art" src="assets/overview-ac-total.png"/></div></figure>

<span id="native-lcd_display"></span>

## LCD DISPLAY

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="a8359a759a513f6435fcaaf1e512662f774c0a2ea9ee42b778b50d1442118729" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="lcd-map.semantic"><img alt="LCD display with callouts 1 to 22" class="hb-reference-art hb-composite-art" src="assets/lcd-map.png"/></div></figure>

<figure aria-label="LCD DISPLAY" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><span class="native-lcd-number">1</span></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-01-wifi.svg"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description"><strong>On:</strong> Wi-Fi connected.<br/><strong>Blink:</strong> Ready to connect to Wi-Fi.<br/><strong>Off:</strong> Wi-Fi disconnected.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">2</span></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-02-bluetooth.svg"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description"><strong>On:</strong> Bluetooth connected.<br/><strong>Blink:</strong> Ready to connect to Bluetooth.<br/><strong>Off:</strong> Bluetooth disconnected.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">3</span></td><td class="hb-lcd-icon"><img alt="Quiet Charging Mode" class="hb-lcd-icon-art" src="assets/lcd-03-quiet-charging.svg"/></td><td class="hb-lcd-name">Quiet Charging Mode</td><td class="hb-lcd-description"><strong>On:</strong> The noise during charging is significantly minimized, while the charging power is reduced and the charging speed slows down.<br/><strong>Off:</strong> Quiet Charging Mode is disabled.<br/>Enable/disable this feature in the Jackery App.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">4</span></td><td class="hb-lcd-icon"><img alt="Battery Saving Mode" class="hb-lcd-icon-art" src="assets/lcd-04-battery-saving.svg"/></td><td class="hb-lcd-name">Battery Saving Mode</td><td class="hb-lcd-description"><strong>On:</strong> Limits the maximum usable battery capacity to extend battery life.<br/><strong>Off:</strong> Battery Saving Mode is disabled.<br/>Enable/disable this feature in the Jackery App.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">5</span></td><td class="hb-lcd-icon"><img alt="Charging Plan" class="hb-lcd-icon-art" src="assets/lcd-05-charging-plan.svg"/></td><td class="hb-lcd-name">Charging Plan</td><td class="hb-lcd-description">Customize the charging time of the Jackery Explorer 1500 Ultra. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs (Please set in the Jackery App).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">6</span></td><td class="hb-lcd-icon"><img alt="Self-powered Mode" class="hb-lcd-icon-art" src="assets/lcd-06-self-powered.svg"/></td><td class="hb-lcd-name">Self-powered Mode</td><td class="hb-lcd-description">Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs (please enable/disable this feature in the app). The power station must be connected to both solar panels and the grid simultaneously, with load power limited by bypass power.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">7</span></td><td class="hb-lcd-icon"><img alt="UPS" class="hb-lcd-icon-art" src="assets/lcd-07-ups.svg"/></td><td class="hb-lcd-name">UPS</td><td class="hb-lcd-description"><strong>On:</strong> The product is in bypass mode, and the switchover time from grid power to the internal battery is 20 ms.<br/><strong>Off:</strong> The product is not in bypass mode.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">8</span></td><td class="hb-lcd-icon"><img alt="AC Power Indicator" class="hb-lcd-icon-art" src="assets/lcd-08-ac-power.svg"/></td><td class="hb-lcd-name">AC Power Indicator</td><td class="hb-lcd-description">The AC output (pure sine wave) is on.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">9</span></td><td class="hb-lcd-icon"><img alt="Output Voltage and Frequency" class="hb-lcd-icon-art" src="assets/lcd-09-output-voltage-frequency.svg"/></td><td class="hb-lcd-name">Output Voltage and Frequency</td><td class="hb-lcd-description">Displays the output voltage and frequency.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">10</span></td><td class="hb-lcd-icon"><img alt="Input Power" class="hb-lcd-icon-art" src="assets/lcd-10-input-power.svg"/></td><td class="hb-lcd-name">Input Power</td><td class="hb-lcd-description">Displays the input power in watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">11</span></td><td class="hb-lcd-icon"><img alt="Remaining Charge Time" class="hb-lcd-icon-art" src="assets/lcd-11-remaining-charge-time.svg"/></td><td class="hb-lcd-name">Remaining Charge Time</td><td class="hb-lcd-description">Displays the remaining charging time.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">12</span></td><td class="hb-lcd-icon"><img alt="AC Wall Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-12-ac-wall-charging.svg"/></td><td class="hb-lcd-name">AC Wall Charging Indicator</td><td class="hb-lcd-description">The product is charged via the AC Input using grid power.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">13</span></td><td class="hb-lcd-icon"><img alt="Car Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-13-car-charging.svg"/></td><td class="hb-lcd-name">Car Charging Indicator</td><td class="hb-lcd-description">The product is charged via the DC Input (DC8020) using DC 12V (car charging).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">14</span></td><td class="hb-lcd-icon"><img alt="Solar Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-14-solar-charging.svg"/></td><td class="hb-lcd-name">Solar Charging Indicator</td><td class="hb-lcd-description">The product is charged via the DC Input (DC8020) using solar panel(s).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">15</span></td><td class="hb-lcd-icon"><img alt="Battery Power Indicator" class="hb-lcd-icon-art" src="assets/lcd-15-battery-power.svg"/></td><td class="hb-lcd-name">Battery Power Indicator</td><td class="hb-lcd-description">When the product is being charged, the orange circle around the battery percentage will light up in sequence.<br/>When charging other devices, the orange circle will stay on.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">16</span></td><td class="hb-lcd-icon"><img alt="Low Battery Indicator" class="hb-lcd-icon-art" src="assets/lcd-16-low-battery.svg"/></td><td class="hb-lcd-name">Low Battery Indicator</td><td class="hb-lcd-description"><strong>On:</strong> The battery level is below 20%.<br/><strong>Blink:</strong> The battery level is below 5%.<br/><strong>Off:</strong> The battery level is above 20% or the product is charging.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">17</span></td><td class="hb-lcd-icon"><img alt="Remaining Battery Percentage" class="hb-lcd-icon-art" src="assets/lcd-17-remaining-battery.svg"/></td><td class="hb-lcd-name">Remaining Battery Percentage</td><td class="hb-lcd-description">Displays the remaining battery percentage.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">18</span></td><td class="hb-lcd-icon"><img alt="Fault Code" class="hb-lcd-icon-art" src="assets/lcd-18-fault-code.svg"/></td><td class="hb-lcd-name">Fault Code</td><td class="hb-lcd-description">A product error has occurred. Please refer to the Troubleshooting section for details.</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">19</span></td><td class="hb-lcd-icon"><img alt="High Temperature Indicator" class="hb-lcd-icon-art" src="assets/lcd-19a-high-temperature.svg"/></td><td class="hb-lcd-name">High Temperature Indicator</td><td class="hb-lcd-description">High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</td></tr><tr><td class="hb-lcd-icon"><img alt="Low Temperature Indicator" class="hb-lcd-icon-art" src="assets/lcd-19b-low-temperature.svg"/></td><td class="hb-lcd-name">Low Temperature Indicator</td><td class="hb-lcd-description">Low temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">20</span></td><td class="hb-lcd-icon"><img alt="Energy Saving Mode" class="hb-lcd-icon-art" src="assets/lcd-20-energy-saving.svg"/></td><td class="hb-lcd-name">Energy Saving Mode</td><td class="hb-lcd-description"><strong>On:</strong> Energy Saving Mode is enabled.<br/><strong>Off:</strong> Energy Saving Mode is disabled.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">21</span></td><td class="hb-lcd-icon"><img alt="Output Power" class="hb-lcd-icon-art" src="assets/lcd-21-output-power.svg"/></td><td class="hb-lcd-name">Output Power</td><td class="hb-lcd-description">Displays the output power in watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">22</span></td><td class="hb-lcd-icon"><img alt="Remaining Discharge Time" class="hb-lcd-icon-art" src="assets/lcd-22-remaining-discharge-time.svg"/></td><td class="hb-lcd-name">Remaining Discharge Time</td><td class="hb-lcd-description">Displays the remaining discharging time.</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## OPERATIONS

### POWER ON/OFF

<div class="hb-reference-composition" data-source-role="native-contained-panel"><div class="" data-source-role="native-figure-scroll"><div class="" data-source-role="native-power-figure"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-on-off" data-source-fragment-sha256="75eeab2391a17f77dea589410d584475a50fb7470ef0f06f02cf72115e71d7b3" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="power-on-off.semantic"><img alt="POWER ON/OFF: on, Press once; off, Press and hold for 3s" class="hb-reference-art hb-composite-art" src="assets/power-on-off.png"/></div></figure><div class="" data-source-role="native-power-note"><div class="hb-text-panel"><p><strong>Default standby time:</strong> 2 hours</p><p>The product will automatically shut down after 2 hours if there is no charging, no AC output, and the combined output of the DC 12V port and USB ports is less than 3W.<br/>*The standby time can be set in the Jackery App.</p></div></div></div></div><table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>When Energy Saving Mode is enabled, the product will automatically shut down after 12 hours if both the Main Power Button and the AC Power Button are turned on, but the product is neither charging nor discharging. The shutdown time can be set in the Jackery App.</p></td></tr></tbody></table></div>

### AC OUTPUT ON/OFF

<div class="hb-reference-composition" data-source-role="native-contained-panel"><div class="hb-text-panel"><p><strong>Prerequisite:</strong> The product is turned on.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output" data-source-fragment-sha256="975a54bcf1c00d3997f22b390ae7d676d7689e654717be22abca02b05e2d540c" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="ac-output.semantic"><img alt="AC OUTPUT ON/OFF: on, Press once; off, Press once. Open the AC output cover and plug in the device" class="hb-reference-art hb-composite-art" src="assets/ac-output.png"/></div></figure></div>

### DC 12V/USB OUTPUT

<div class="hb-reference-composition" data-source-role="native-contained-panel"><div class="hb-text-panel"><p><strong>Prerequisite:</strong>  The product is turned on.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc-usb-output" data-source-fragment-sha256="9173ab9e313b5b46842255e8f9843bfeb5bb38a435443a778570363ad9660e7d"><div class="hb-reference-semantic" data-reference-id="dc-usb-output.semantic"><img alt="DC 12V/USB OUTPUT: open the port covers and connect devices to the USB ports and the DC 12V port" class="hb-reference-art hb-composite-art" src="assets/dc-usb-output.png"/></div></figure><p>The product can charge your car battery using the Jackery 12V automobile battery charging cable, which is sold separately and available on our website.</p><div class="hb-text-panel" data-source-role="native-panel-note"><p><strong>CAUTION:</strong></p><ul><li>The DC 12V port is only compatible with 12V car batteries and not suitable for 24V systems.</li><li>Do not start the car while the product is charging the car battery through the 12V DC output port, as this may damage the product.</li><li>This feature is intended for emergency use only and cannot charge a dead or damaged car battery.</li></ul></div></div>

### ENERGY SAVING MODE

<p>To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default.<br/>When AC Power Button is turned on, the Energy Saving Mode icon will be displayed on the LCD screen.<br/> If no device is connected or the connected device's power consumption is below a certain threshold (AC Output ≤ 25W), the device will automatically turn off all outputs after 12 hours.</p>

<p><strong>On/Off:</strong> Press and hold both the AC Power Button and Main Power Button for more than 3 seconds.</p>

<p>Please set the Energy Saving Mode duration in the Jackery App.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="energy-saving" data-source-fragment-sha256="938052382a19d1e5ab028087ddafb0170e46cc7aaee3787a40961550ce7dfcc8" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="energy-saving.semantic"><img alt="Main Power Button + AC Power Button" class="hb-reference-art hb-composite-art" src="assets/energy-saving.png"/></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><ul><li>When Energy Saving Mode is disabled, the product will not automatically turn off the AC or DC output.</li><li>Energy Saving Mode resumes previous state after power-on. Manual switching is required for mode changes.</li></ul></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">WARNING</td><td class="manual-callout-body"><p>When Energy Saving Mode is enabled, the product automatically turns off the AC output if the connected device’s power consumption remains low for the configured period. When powering devices that require continuous power, such as refrigerators, routers, security cameras, or aquarium air pumps, we recommend turning off Energy Saving Mode to prevent unexpected power loss from interrupting their operation.</p></td></tr></tbody></table>

### LCD SCREEN ON/OFF

<figure aria-label="LCD SCREEN ON/OFF" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCD SCREEN ON/OFF" class="hb-lcd-mode-art" src="assets/lcd-screen.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">Screen stays on for 2 minutes</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Press the Main Power Button or when the product is charging.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">The LCD turns off automatically and enters sleep mode after 2 minutes.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Always-on Display Mode<br/> (under charging or discharging state)</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Double-press the Main Power Button when the LCD screen is ON.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">In Always-on Display Mode, the LCD screen will automatically turn off after 2 hours if there is no charging, no AC output, and the combined output of the DC 12V port and USB ports is less than 3W.</td></tr></tbody></table></div></figure>

### BUTTON OPERATIONS

<div class="table-wrapper docutils container" data-source-layout="button-operations"><table class="manual-table"><thead><tr><th>Buttons</th><th>Operation</th><th>Function</th></tr></thead><tbody><tr><td><div class="docutils container" data-source-button="main"><img alt="" src="assets/button-main.png"/><p>Main Power Button</p></div> + <div class="docutils container" data-source-button="ac"><img alt="" src="assets/button-ac.png"/><p>AC Power Button</p></div></td><td><img alt="" src="assets/button-clock.png"/>3s<p>Press and hold both for 3s</p></td><td><p>Turn on/off the Energy Saving Mode</p></td></tr><tr><td><div class="docutils container" data-source-button="main"><img alt="" src="assets/button-main.png"/><p>Main Power Button</p></div></td><td><p>Press and hold for 3s to turn off the product, then keep holding for 10s.</p></td><td><p>Reset the product</p></td></tr></tbody></table></div>

<span id="native-ups"></span>

## UNINTERRUPTIBLE POWER SUPPLY (UPS)

<p>Connect the product to a wall outlet with the AC charging cable, then press the AC output button and power your appliances at the same time.<br/>An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup electric power to a load when the mains grid power fails.<br/>In the event of a sudden loss of grid power, the Explorer 1500 Ultra will automatically switch to stored power within 20 ms to keep your appliances running.<br/>In UPS mode, the unit's peak output reaches 1440W before power outages. As simultaneous charging/discharging is enabled in Bypass Mode, the actual output power is lower than the rated output power in this mode but returns to rated output power during outages.</p>

<div class="hb-text-panel" data-source-role="native-contained-panel native-gray-panel"><div class="hb-text-panel"><p><strong>Prerequisite:</strong> The product is turned on.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="9d3ade1a1b542474ff817aed9fb30a4946bc23884906ef04af2828b048e276a6"><div class="hb-reference-semantic" data-reference-id="ups.semantic"><img alt="The product connected to a wall outlet with the AC charging cable and powering an appliance through the AC output" class="hb-reference-art hb-composite-art" src="assets/ups.png"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">WARNING</td><td class="manual-callout-body"><p>Do not use this product for applications such as data servers or medical devices, where a malfunction could endanger life or cause significant property damage.<br/>For the following equipment, a loss of power supply during use could cause serious harm to personal safety or property:</p><ul><li>Medical devices and other equipment closely related to life safety.</li><li>Critical equipment such as social infrastructure and public services.</li><li>Business-critical enterprise equipment, etc.</li></ul><p>Individuals who wear a cardiac pacemaker (pacemaker implant recipients)<br/>must not use this product.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>This product does not support 0 ms switching. Do not connect it to equipment that requires an uninterrupted power supply, such as data servers or workstations.</li><li>Before use, please test compatibility with your device multiple times.</li><li>It is recommended to connect one device at a time. Do not use multiple devices simultaneously, as this may trigger overload protection.</li><li>The UPS function works only when a single unit is connected directly to a wall outlet.Do not connect multiple portable power stations in series (cascade connection). In a cascaded setup, the UPS function will not operate: the unit may fail to switch over during a power outage, causing connected devices to shut down.</li></ul></td></tr></tbody></table>

<span id="native-charging"></span>

## CHARGING

<p><strong>Green energy first:</strong> We advocate to use the green energy first. This product supports two modes of charging at the same time: solar charging and AC wall charging. When AC wall charging and solar charging are turned on at the same time, the product will give priority to solar charging and both methods will be used to charge the battery at the maximum permissible power.</p>

<p class="hb-prose-pill" data-source-role="native-prose-pill"><strong>Fully charge the product before its first use.</strong></p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><ul><li>The recommended charging temperature for the product ranges from 32°F to 113°F (0°C to 45°C ), and the discharging temperature ranges from 5°F to 113°F (-15°C to 45°C ). Operating the product beyond this temperature range may restrict its charging and discharging capabilities, or even prevent it from charging or discharging.</li><li>The charging power and battery capacity of the product may vary due to temperature fluctuations. When the ambient temperature ranges from 5°F to 14°F (-15°C to -10°C), the maximum output power decreases to 1000W.</li></ul></td></tr></tbody></table>

### CHARGING VIA AC WALL OUTLET

<p>Connect the AC charging cable to the AC input port of the product and a wall outlet.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-ac" data-source-fragment-sha256="2f7b88656f221351846157bd1acc6c249d7dfca4ba01fb2040392780dd2fddef"><div class="hb-reference-semantic" data-reference-id="charging-ac.semantic"><img alt="Connect the AC charging cable to the AC input port of the product and a wall outlet" class="hb-reference-art hb-composite-art" src="assets/charging-ac.png"/></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Make sure the AC charging cable is fully and securely plugged into the AC input port. An incomplete connection may cause unstable current, overheating, poor contact, or device malfunction.</p></td></tr></tbody></table>

### CHARGING VIA SOLAR PANELS

<p>Jackery Explorer 1500 Ultra has two DC8020 input ports and is compatible with the Jackery solar panels. If one DC8020 input port needs to connect two solar panels simultaneously, please refer to the figure below for charging through the solar panel connector (sold separately, not included as standard).</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar" data-source-fragment-sha256="0d827356ff87cafbbc5486997b5d64e9c16faa11ba874ee5cda6aa1d0f35e3f0"><div class="hb-reference-semantic" data-reference-id="charging-solar.semantic"><img alt="One solar panel connected to a DC8020 input port" class="hb-reference-art hb-composite-art" src="assets/charging-solar.png"/></div></figure>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar-connector" data-source-fragment-sha256="f8ca50187f43e11295c3b9f4c156e1cb6c324b49a93f386c61ef9402b213d9e7"><div class="hb-reference-semantic" data-reference-id="charging-solar-connector.semantic"><img alt="Two solar panels connected to each DC8020 input port through the solar panel connector" class="hb-reference-art hb-composite-art" src="assets/charging-solar-connector.png"/></div></figure>

<p>It is recommended to use the Jackery Solar Panel to charge the Explorer 1500 Ultra. Ensure that the open-circuit voltage (Voc) of the solar panel falls within the Jackery Explorer 1500 Ultra's DC input voltage range (16V–60V). Jackery is not responsible for any losses caused by using solar panels from other brands.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>One DC8020 input port can be connected to at most two solar panels.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Ensure that the input voltage for both DC input ports is the same. Failure to do so may damage the product. For example:</p><ul><li>It is recommended to use the same model of Jackery solar panels and the same number of panels when connecting solar panels to both DC8020 Input ports.</li><li>Do not charge the product using both a car charger and a solar panel simultaneously. Doing so may blow the car fuse or result in charging failure.</li></ul></td></tr></tbody></table>

### CHARGING WITH A CAR CHARGER

<p>This product can be charged using a 12V car charger. Ensure that the car charger and the 12V car power outlet provide a good connection.</p>

<div class="" data-source-role="native-contained-panel native-gray-panel native-car-panel"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-car" data-source-fragment-sha256="74d27dc7dd00809095b5789105eb266da0500e9d05ef75fa37488159e53b7e9b" data-web-base-art-ref="charging-car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#f1f2f2"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-car.png"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:48.8%;--hb-y:79.7%;--hb-width:46%;--hb-height:9.3%;--hb-fill:#ffffff">*The car charging cable is sold separately.</span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>Please start the vehicle before charging your power station.</li><li>If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it causes non-standard operation. The Company will not be responsible for any loss caused by non-standard operation.</li><li>Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product in 24V vehicle to avoid personal injury and property loss.</li></ul></td></tr></tbody></table>

<span id="native-bottom_cleaning"></span>

## BOTTOM CLEANING

<div class="docutils container" data-source-layout="cleaning-steps"><div class="hb-text-panel"><div class="hb-step-copy"><p class="rubric">1</p><p> Ensure all protective covers on the product are securely closed to prevent water ingress during rinsing.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cleaning-1" data-source-fragment-sha256="aa4ba69b930eee98e1eaddf896b64cfe8ed16d5a2cad6847472eb21cc34ecdae"><div class="hb-reference-semantic" data-reference-id="cleaning-1.semantic"><img alt="Step 1: protective covers closed" class="hb-reference-art hb-composite-art" src="assets/cleaning-1.png"/></div></figure></div><div class="hb-text-panel"><div class="hb-step-copy"><p class="rubric">2</p><p> Lay a dry towel on the floor and place the product upside down on the towel as shown in the illustration to protect the surface.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cleaning-2" data-source-fragment-sha256="cc2dc69385011eef74c252d8979166a1a89c05426bdd8dc5df0fef68368e5a47"><div class="hb-reference-semantic" data-reference-id="cleaning-2.semantic"><img alt="Step 2: the product upside down on a dry towel" class="hb-reference-art hb-composite-art" src="assets/cleaning-2.png"/></div></figure></div><div class="hb-text-panel"><div class="hb-step-copy"><p class="rubric">3</p><p> Follow the illustrated order to remove the screws at the bottom and take off the bottom panel to expose the internal cooling fins.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cleaning-3" data-source-fragment-sha256="122aea5d7c719c15249555b44bfa037a768e3a72ae26aae67272a9cc4361aa85" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="cleaning-3.semantic"><img alt="Step 3: remove the screws (A), then take off the bottom panel (B)" class="hb-reference-art hb-composite-art" src="assets/cleaning-3.png"/></div></figure></div><div class="hb-text-panel"><div class="hb-step-copy"><p class="rubric">4</p><p> Rinse the cooling fins with clean water. You may use a long-bristle brush or a damp cloth to help clean surface dirt. After cleaning, dry thoroughly with a towel and air dry in a shaded area. Ensure no moisture remains before reinstalling the bottom panel.</p></div><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cleaning-4" data-source-fragment-sha256="ba7ed1f550fede2e63fae0496fb2afbcf71d62c62cdf662907fbfff55adb859a"><div class="hb-reference-semantic" data-reference-id="cleaning-4.semantic"><img alt="Step 4: rinse the cooling fins with clean water" class="hb-reference-art hb-composite-art" src="assets/cleaning-4.png"/></div></figure></div></div>

<span id="native-storage"></span>

## STORAGE

<p>Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:</p>

<ul><li>1 month: -20°C to 45°C (0-60%RH)</li><li>3 months: 0°C to 45°C (0-60%RH)</li><li>12 months: 0°C to 25°C (0-60%RH)</li></ul>

<p>If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 months.</p>

<span id="native-troubleshooting"></span>

## TROUBLESHOOTING

<p>If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. If fault persists, please contact Jackery Customer Support.</p>

<figure aria-label="Error Code / Corrective Measures" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table" data-source-layout="fault-rowspan"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Error Code</th><th class="hb-troubleshooting-measures" scope="col">Corrective Measures</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0</td><td class="hb-troubleshooting-measures" rowspan="4">Restart the product.</td></tr><tr><td class="hb-troubleshooting-code">F1</td></tr><tr><td class="hb-troubleshooting-code">F2</td></tr><tr><td class="hb-troubleshooting-code">F3</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Connect the product to loads to discharge its battery until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Charge the product via solar panels or AC wall outlet until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures">1. Wait for the grid to normalize before charging the product via AC wall outlet.<br/>2. Check whether the air intake and exhaust vents are blocked; ensure 30 cm clearance on both side of the product.<br/>3. Place the product in a shaded, well-ventilated area where the ambient temperature is below 45°C.<br/>4. Disconnect all loads from the product, keep it idle and wait until the fault disappears.<br/>5. Restart the product.</td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures">1. Remove all DC inputs from the product.<br/>2. If you charge the product via a solar panel, check the open-circuit voltage (Voc) of the connected solar panel. The product allows a maximum DC input voltage of 60V.<br/>3. Restart the product and keep it idle. Wait until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">Contact Jackery Customer Support.</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">Remove the load connected to the DC12V/USB ports of the product. Wait until the fault disappears.</td></tr></tbody></table></figure>

<span id="native-specifications"></span>

## SPECIFICATIONS

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Explorer 1500 Ultra</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JE-1500C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">30Ah/51.2V DC (1536Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">Around 38.6 lbs / 17.5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">13.2×10.4×11.6 in / 33.6×26.4×29.5 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">4000 cycles to 70%+ capacity</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">IP Rating</th><td class="manual-spec-value hb-spec-value">IP65 (All lids closed)</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">INPUT PORTS</h2>

<figure aria-label="INPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Mode AC Input</th><td class="manual-spec-value hb-spec-value">100-120V ~ 60Hz, 15A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Bypass Mode AC Input</th><td class="manual-spec-value hb-spec-value">100-120V ~ 60Hz, 12A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × DC8020 Ports</th><td class="manual-spec-value hb-spec-value">Car: 12-16V⎓8A Max, Double to 8A Max<br/>PV: 16-60V⎓12A, Double to 24A / 800W Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">OUTPUT PORTS</h2>

<figure aria-label="OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">3 × AC Output</th><td class="manual-spec-value hb-spec-value">120V ~ 60Hz, 1800W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Output in Bypass Mode¹</th><td class="manual-spec-value hb-spec-value">100-120V ~ 60Hz, 12A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Total Output</th><td class="manual-spec-value hb-spec-value">1800W Rated (2000W for 15min. Max) 3600W Surge Peak</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-A Output</th><td class="manual-spec-value hb-spec-value">18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-C1 Output</th><td class="manual-spec-value hb-spec-value">30W Max, 5V⎓3A, 9V⎓3A, 12V⎓2.5A, 15V⎓2A, 20V⎓1.5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-C2 Output</th><td class="manual-spec-value hb-spec-value">100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC 12V Port</th><td class="manual-spec-value hb-spec-value">12V⎓10A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Temperature</th><td class="manual-spec-value hb-spec-value">32°F to 113°F / 0°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Discharge Temperature</th><td class="manual-spec-value hb-spec-value">5°F to 113°F / -15°C to 45°C</td></tr><tr><td class="manual-spec-value hb-spec-value">5°F to 14°F / -15°C to -10°C  Output Power: 1000W</td></tr></tbody></table></figure>

<p>1 The product can charge the battery from the AC wall outlet while delivering power through the AC output ports.</p>

<p>※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>

<span id="native-warranty"></span>

## WARRANTY

<figure aria-label="WARRANTY" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>We only provide our warranty to customers who purchase from the official Jackery website, Jackery-branded third-party platforms, or local authorized dealers.</strong></div><div class="hb-warranty-local-note">*Warranty period and details may vary according to local laws, regulations, and authorized dealers.</div></figure>

### Limited Warranty

<figure aria-label="Limited Warranty" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects in workmanship and material under normal consumer use during the applicable warranty period identified in the 'Warranty Period' section below, subject to the exclusions set forth below.</p><p>This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, nor authorize any person to assume for us, any other liability in connection with the sale of our products.</p></figure>

### Warranty Period

<figure aria-label="Warranty Period" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 YEARS Standard Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Standard Warranty</strong></div></div><div class="hb-warranty-period-copy"><p>The standard warranty period for Jackery Explorer 1500 Ultra is 36 months. In each case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. The sales receipt from the first consumer purchase, or other reasonable documentary proof, is required in order to establish the start date of the warranty period.</p></div></div><div aria-label="2 YEARS Extended Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Extended Warranty</strong></div></div><div class="hb-warranty-period-copy"><p>To activate the Warranty Extension, you must register your product online  or contact our customer service team at hello@jackery.com to extend the standard warranty runtime.</p></div></div></div></figure>

### Repair or Replacement

<figure aria-label="Repair or Replacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the applicable warranty period due to a defect in workmanship or material. The repaired/replaced product assumes the remaining warranty of the original date of purchase.</p></figure>

### Limited to Original Consumer Buyer

<figure aria-label="Limited to Original Consumer Buyer" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable to any subsequent owner.</p></figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery's warranty does not apply to:</p><ul><li>Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as authorized in Jackery's current product literature.</li><li>Attempted repair by anyone other than an authorized facility.</li><li>Any product purchased through an online auction house.</li><li>Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within seven days after you purchase the product and at least once every 6 months thereafter.</li></ul></figure>

### Interpretation Rights

<figure aria-label="Interpretation Rights" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery reserves the right to final interpretation of the above customer after-sales policy.</p></figure>

<span id="native-app_setup"></span>

## APP SETUP

### 1. To download the App and log in

<figure aria-label="Jackery App" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app-store.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Search for "Jackery" in Google Play or App Store to install the App. After that, you can register and log in.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app-qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternatively, scan the QR code below to download and install the App.</p></div></div></div><div class="hb-app-download-semantic"><img alt="Jackery App" class="hb-app-download-semantic-art" src="assets/app-qr.png"/></div></figure>

### 2. To add device

<p>2.1 Click the button <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> to add your device.</p>

<p>2.2 Long press the “POWER” button on the device to turn on, the Wi-Fi and Bluetooth icons on the device flash to indicate that the device has entered the network configuring mode, tap the “Icon Flashed” button and allow the App to connect to nearby devices and open Bluetooth permissions.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add" data-source-fragment-sha256="598c6f200645be24ed4a66e8be7c98ffb7a4e2678c75f0e292a504e1206f6ac0" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-add.semantic"><img alt="App screenshots 2.1 and 2.2" class="hb-reference-art hb-composite-art" src="assets/app-add.png"/></div></figure>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="a48d2e344afc62787c332a3658af2ce759e76f1fc354daa2147b90fc8481c6f8" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-control.semantic"><img alt="Main Power Button and AC Power Button" class="hb-reference-art hb-composite-art" src="assets/app-control.png"/></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>If the device is not connected to the App within 2 hours after being turned on, it will automatically turn off Wi-Fi and Bluetooth.</p></td></tr></tbody></table>

<p>2.3 After tapping the searched device icon, the App automatically connects the device via Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>If "the device has been bound" is prompted during the binding process, the following two ways can be used for connection:</p><ul><li>The device owner will share this device with other users through the App.</li><li>Turn off the product, then press and hold the POWER button for 10 seconds to reset the device and rebind it to the App.</li></ul></td></tr></tbody></table>

<p>2.4 After the device is successfully connected, enter your Wi-Fi password and tap the OK button.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>Please select a Wi-Fi network in 2.4GHz band. The device does not support a Wi-Fi network in 5GHz band.</p></td></tr></tbody></table>

<p>2.5 After the device is successfully added on the App, the Wi-Fi icon on the device will be always on.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-results" data-source-fragment-sha256="c30bcba7039f9dc10e36bc491874bea4257db7614748b0d56bf78916991b0fa6" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-results.semantic"><img alt="App screenshots 2.3, 2.4 and 2.5" class="hb-reference-art hb-composite-art" src="assets/app-results.png"/></div></figure>

<p>The above screenshots are for reference only.</p>

### 3. To unbind the device

<p>Click the Settings icon in the upper right corner of the main interface of the device to enter the settings page, and click the Unbind button at the bottom of the page to unbind the device.</p>

### 4. Notes

#### 4.1 To turn on Wi-Fi and Bluetooth:

<ul><li>Wi-Fi and Bluetooth are automatically turned on after the device is on, and the Wi-Fi and Bluetooth icons on the screen light up.</li></ul>

#### 4.2 To turn off Wi-Fi and Bluetooth:

<ul><li>Wi-Fi and Bluetooth will be automatically turned off if no device is connected within 2 hours.</li></ul>

#### 4.3 To reset Wi-Fi and Bluetooth:

<ul><li>Turn off the product, then press and hold the POWER button for 10 seconds to reset Wi-Fi and Bluetooth to factory settings and reboot the system.</li></ul>

<span id="jackery-inc"></span>

### JACKERY INC.

<div class="" data-source-role="native-contact-card" id="native-contact"><p class="" data-source-role="native-contact-address">5310 Bunche Dr., Fremont, CA 94538-8301</p><div class="" data-source-role="native-contact-row"><div class="hb-reference-composition" data-source-role="native-contact-panel"><p class="" data-source-role="native-contact-phone"><img alt="" class="" data-source-role="native-contact-glyph" src="assets/contact-phone.png"/><strong>1-888-502-2236</strong> <span class="" data-source-role="native-contact-region">(US)</span></p><div class="" data-source-role="native-contact-links"><p class="" data-source-role="native-contact-email"><img alt="" class="" data-source-role="native-contact-glyph" src="assets/contact-mail.png"/>hello@jackery.com</p><p class="" data-source-role="native-contact-web"><img alt="" class="" data-source-role="native-contact-glyph" src="assets/contact-web.png"/>www.jackery.com</p></div></div><div class="hb-reference-composition" data-source-role="native-contact-qr"><img alt="" src="assets/contact-qr.png"/></div></div></div>
