<style>
/* JA-TS02A source geometry only. Shared Web theme owns headings, callouts, tables and figures. */

/* Figures: the print's own art width; no visible caption (the art carries its labels). */
.native-figure { max-width: 680px; margin: 1rem auto; min-width: 0; }
.native-figure .hb-reference-figure { margin: 0; max-width: none; }
#furo-main-content .native-figure img { width: 100% !important; height: auto !important; max-height: none; }
.native-art { max-width: 400px; }
.native-narrow { max-width: 420px; }
.native-phone { max-width: 260px; }

/* Print text beside its figure (steps, App screens): one reading unit, stacked on phones. */
.native-media { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1.2rem; align-items: start; margin: 1rem 0; }
.native-media-art-first { grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); }
.native-media > * { min-width: 0; }
.native-media .native-figure { margin: 0 auto; }
.native-media-copy > :first-child { margin-top: 0; }
@media (max-width: 760px) {
  .native-media, .native-media-art-first { grid-template-columns: minmax(0, 1fr); }
}

/* p17 indicator states: two printed lines in one grey panel. */
#furo-main-content p.native-status-panel {
  display: inline-block; margin: 0.6rem 0; padding: 0.45rem 0.9rem;
  border-radius: var(--hb-panel-radius); background: var(--hb-surface);
}

/* Inline App controls at text size. */
#furo-main-content img.native-inline-control {
  display: inline-block; width: 1.25em !important; height: 1.25em !important;
  margin: 0 0.1em !important; vertical-align: -0.22em; object-fit: contain;
}

/* p5 ingestion hazard: the print's icon column beside its bullet list. */
.native-ingestion { display: grid; grid-template-columns: 2.2rem minmax(0, 1fr); gap: 0.6rem; align-items: start; margin: 0.8rem 0; }
#furo-main-content .native-ingestion > img { width: 2.2rem !important; height: auto; margin: 0.2rem 0 0 !important; }
.native-ingestion > ul { margin: 0; }

/* Warning lockups: the print draws the triangle and signal word without a frame. */
#furo-main-content table.native-lockup-open { border-color: var(--hb-line-soft) !important; }

/* Tables the print rules as a full grid: white header cells, semibold as printed. */
#furo-main-content table.native-print-grid th { background: var(--hb-paper) !important; font-weight: 600; }
#furo-main-content table.native-print-grid td { vertical-align: middle; }
#furo-main-content table.native-print-grid :is(td, th)[rowspan] { vertical-align: middle; }
#furo-main-content table.native-symbols td.native-symbol-cell { width: 5.5rem; text-align: center; }
#furo-main-content table.native-symbols td.native-symbol-cell img { width: 2.1rem !important; height: auto; margin: 0 !important; }

/* p6 specifications: open rules, regular labels, no fill, as printed. */
#furo-main-content table.native-spec-rules { border-top: 1.5px solid var(--hb-text) !important; border-bottom: 1.5px solid var(--hb-text) !important; }
#furo-main-content table.native-spec-rules td { border-left: 0 !important; padding-top: 0.42rem !important; padding-bottom: 0.42rem !important; }
#furo-main-content table.native-spec-rules td:first-child { width: 48%; }

/* p7 cables: wire colour swatches beside the colour names. */
#furo-main-content td.native-wire::after {
  content: ""; display: inline-block; width: 1.4em; height: 0.36em; margin-left: 0.45em;
  border-radius: 0.18em; vertical-align: 0.15em; border: 1px solid var(--hb-text);
}
#furo-main-content td.native-wire-black::after { background: #1f1f1f; }
#furo-main-content td.native-wire-red::after { background: #c8352b; border-color: #c8352b; }
#furo-main-content td.native-wire-white::after { background: #ffffff; }
#furo-main-content td.native-wire-green::after { background: #4f9d5d; border-color: #4f9d5d; }
#furo-main-content table.native-cables td:not(.native-cable-group) { text-align: center; }

/* p14 torque: centred cells and unbroken values, as printed. */
#furo-main-content table.native-torque :is(td, th) { text-align: center; white-space: nowrap; }

/* Two- and three-column tables fit a phone; only the wide torque table scrolls. */
@media (max-width: 760px) {
  #furo-main-content table.native-fit { min-width: 0 !important; }
  #furo-main-content table.native-led, #furo-main-content table.native-cables { min-width: 0 !important; }
}

/* Print case for subheadings (the print sets them in bold title case); shared markers stay. */
#furo-main-content h2:not(.hb-spec-section), #furo-main-content :is(h3, h4) { text-transform: none; }

/* Room for two-digit step numbers (the print's 1-24 safety list). */
#furo-main-content ol.native-steps { padding-left: 2.4em; }

/* Print-grid tables are compact, as printed. */
#furo-main-content table.native-print-grid :is(td, th) { padding: 0.42rem 0.6rem !important; }
#furo-main-content table.native-cables td:not(.native-cable-group),
#furo-main-content table.native-led td:nth-last-child(2) { white-space: nowrap; }
/* Six unbroken columns fit the desktop text column (655 px at 1280) without scrolling. */
#furo-main-content table.native-torque { font-size: 0.85rem; }
#furo-main-content table.native-torque :is(td, th) { padding: 0.42rem 0.3rem !important; }
@media (max-width: 760px) {
  #furo-main-content table.native-cables td:not(.native-cable-group),
  #furo-main-content table.native-led td:nth-last-child(2) { white-space: normal; }
}
@media (max-width: 420px) {
  #furo-main-content table.native-print-grid:not(.native-torque) :is(td, th) { padding: 0.42rem 0.4rem !important; }
}

</style>

<span id="native-safety"></span>

## SAFETY INSTRUCTIONS

### Disclaimer

<p>Congratulations on your new Jackery Smart Transfer Switch. Please read this manual carefully before using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible place for further reference.<br/>In compliance with laws and regulations, the right of final interpretation of this document and all related documents of this product resides with the Company.<br/>Please kindly notice that no further notifications will be given in case of any update, revision, or termination.</p>

### Warning

<ol class="native-steps"><li>The installation or servicing of this product should only be performed by qualified electrical personnel.</li><li>Prior to installation, operation, or servicing of this product, carefully read the instruction manual.</li><li>Installation of this product must conform to local standards, national electrical safety standards, and the manufacturer's instructions.</li><li>Specifications of self-provided cables should meet the requirements of the Installation Guide and comply with local regulations.</li><li>The AC cables are high-voltage cables. Risk of death or serious injury due to electric shock.</li><li>There is a high possibility of electric shock or serious burns due to the high voltage in the product.</li><li>Use appropriate personal protective equipment (PPE) and follow safe electrical work practices.</li><li>Do not touch exposed wires with your hands.</li><li>Be cautious to prevent injury when moving heavy objects. Wear personal protective equipment such as protective gloves and shoes when manually moving the product.</li><li>Do not install or operate the equipment in extreme weather events such as lightning, snow, heavy rain, strong wind, etc.</li><li>Do not install or operate the product in an area where flammable or explosive materials are stored.</li><li>Inspect the product and cables for damage before installing. Do not install the product or cables if damaged in any way.</li><li>Turn off all power supplying this product before installation. Disconnect each circuit individually before servicing.</li><li>Always use a properly rated voltage-sensing device to confirm the power is off.</li><li>During the drilling process, cover the interior product to prevent debris from falling into the product, and clear the debris after drilling to prevent interference with the equipment.</li><li>Do not damage, smear, or cover any warning labels on the device. All labels must be visible after installation.</li><li>Before operating the product, check the electrical connections to ensure that the product is reliably and permanently grounded.</li><li>Do not place any kind of objects on top of the product during operation.</li><li>To completely de-energize the product, ensure all main breakers and branch breakers are turned off and physically unplug all loads. Failure to do so may pose a risk of electric shock.</li><li>Do not place or install flammable or potentially explosive objects near the product or in explosive atmospheres.</li><li>Do not insert foreign objects into any part of the equipment.</li><li>Do not connect life-support systems, medical equipment, or any other equipment used where product failure could lead to injury to persons or loss of life to circuits that can be remotely switched.</li><li>Install the product in a location that prevents damage from flooding. Ensure that no water sources are above or near the product, including downspouts, sprinklers, or faucets.</li><li>If needed, replace all devices, doors, and covers before turning on the power.</li></ol>

### Caution

<ol class="native-steps"><li>In the case of cable damage, it must be replaced by the manufacturer, customer service, or qualified personnel to prevent a safety hazard.</li><li>Do not use solvents to clean the product.</li><li>The product must be disposed of according to local codes and regulations.</li><li>This product is not intended to be used as a service disconnect.</li><li>Do not use parts or accessories other than those specified for use with the product.</li><li>When installing the product, the screws need to be tightened according to the specification torque using a special tool.</li><li>Keep out of reach of children or animals.</li><li>This product is designed for residential use only.</li></ol>

### FCC Statement

<p>This device complies with part 15 of the FCC Rules. Operation is subject to the following two conditions: (1) This device may not cause harmful interference, and (2) this device must accept any interference received, including interference that may cause undesired operation.<br/>MODIFICATION: Any changes or modifications not expressly approved by the grantee of this device could void the user’s authority to operate the device.<br/>NOTE: This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to radio communications. However, there is no guarantee that interference will not occur in a particular installation. If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:<br/>--Reorient or relocate the receiving antenna.<br/>--Increase the separation between the equipment and receiver.<br/>--Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.<br/>--Consult the dealer or an experienced radio/TV technician for help.</p>

### IC Warning

<p>This device complies with Industry Canada licence-exempt RSS standard(s).<br/>Operation is subject to the following two conditions:<br/>(1) this device may not cause interference, and (2) this device must accept any interference, including interference that may cause undesired operation of the device.<br/>This Class B digital apparatus complies with Canadian lCES-003.</p>

<p>IC RF Statement:<br/>When using the product, maintain a distance of 20 cm from the body to ensure compliance with RF exposure requirements.</p>

<div class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><ul class="native-bullets"><li>INGESTION HAZARD: This product contains a button cell or coin battery.</li><li>DEATH or serious injury can occur if ingested.</li><li>A swallowed button cell or coin battery can cause Internal Chemical Burns in as little as 2 hours.</li><li>KEEP new and used batteries OUT OF REACH of CHILDREN.</li><li>Seek immediate medical attention if a battery is suspected to be swallowed or inserted inside any part of the body.</li></ul></div>

### Meaning of symbols

<p>The following tables explain the meaning of the symbols used in the instruction manual and its packaging.</p>

<div class="table-wrapper docutils container native-table-wrap"><table class="manual-table native-print-grid native-symbols native-fit"><thead><tr><th scope="col">Symbol</th><th scope="col">Meaning</th></tr></thead><tbody><tr><td class="native-symbol-cell"><img alt="The position for connecting the protection ground cable." src="assets/symbol_grounding.png"/></td><td>The position for connecting the protection ground cable.</td></tr><tr><td class="native-symbol-cell"><img alt="Caution, risk of danger." src="assets/symbol_warning_triangle.svg"/></td><td>Caution, risk of danger.</td></tr><tr><td class="native-symbol-cell"><img alt="Caution, risk of electric shock." src="assets/symbol_electric_shock.svg"/></td><td>Caution, risk of electric shock.</td></tr><tr><td class="native-symbol-cell"><img alt="Refer to the operation instructions." src="assets/symbol_read_manual.svg"/></td><td>Refer to the operation instructions.</td></tr></tbody></table></div>

<span id="native-specifications"></span>

## SPECIFICATIONS

<div class="table-wrapper docutils container native-table-wrap"><table class="manual-table native-spec-rules native-fit"><tbody><tr><td>Product Name</td><td>Jackery Smart Transfer Switch</td></tr><tr><td>Model No.</td><td>JA-TS02A</td></tr><tr><td>AC Voltage (Nominal)</td><td>120V/240V~ 60Hz</td></tr><tr><td>Feed-In Type</td><td>Split Phase</td></tr><tr><td>Maximum Input Current</td><td>100A Grid / 60A Power Station</td></tr><tr><td>Maximum Output Current</td><td>60A Home Load / 33.4A Power Station</td></tr><tr><td>Maximum Input Short-Circuit Current</td><td>10KA</td></tr><tr><td>Overvoltage Category</td><td>IV</td></tr><tr><td>UPS</td><td>≤20ms</td></tr><tr><td>Enclosure Type (Distribution Panel)</td><td>NEMA Type 1</td></tr><tr><td>Number of Load Branches</td><td>12</td></tr><tr><td>Main Circuit</td><td>2 AWG</td></tr><tr><td>Branch Circuit</td><td>14 AWG 12 AWG 10 AWG</td></tr><tr><td>Communication</td><td>Wi-Fi and Bluetooth</td></tr><tr><td>Operating Temperature</td><td>-20°C~40°C (-4°F~104°F)</td></tr><tr><td>Dimensions</td><td>22 x 14.7 x 7.87 in/56 x 37.4 x 20 cm</td></tr><tr><td>Weight</td><td>About 25.57 lbs/11.6 kg</td></tr></tbody></table></div>

<p>* When using the product, ensure it is connected to a 240V split phase mains voltage.</p>

<span id="native-package-list"></span>

## PACKAGE LIST

<div class="native-figure native-package-list native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-list" data-source-fragment-sha256="e3a756e64227f70d159fa49ba746aa3ebdd3e3e8dce95ce4d5d70c01b8fdb08c" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="package-list.semantic"><img alt="Package list" class="hb-reference-art hb-composite-art" src="assets/package-list.png"/></div></figure></div>

<span id="native-what-you-need"></span>

## WHAT YOU NEED

<div class="native-figure native-optional-tools native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="optional-tools" data-source-fragment-sha256="e4abc777d194fa450fdd4bc40548ee6bbbba35e1ac4cd5940d03d1f1531a3be3" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="optional-tools.semantic"><img alt="Optional installation components" class="hb-reference-art hb-composite-art" src="assets/optional-tools.png"/></div></figure></div>

### Optionals

<div class="table-wrapper docutils container native-table-wrap"><table class="manual-table native-print-grid native-cables"><thead><tr><th colspan="2" scope="col">Cables</th><th scope="col">Color</th><th scope="col">Current</th><th scope="col">Gauge</th></tr></thead><tbody><tr><td class="native-cable-group" rowspan="4">For Grid to Electrical Panel</td><td>L1</td><td class="native-wire native-wire-black">Black</td><td rowspan="4">100A Max</td><td>2 AWG</td></tr><tr><td>L2</td><td class="native-wire native-wire-red">Red</td><td>2 AWG</td></tr><tr><td>N</td><td class="native-wire native-wire-white">White</td><td>2 AWG</td></tr><tr><td>GND</td><td class="native-wire native-wire-green">Green</td><td>6 AWG</td></tr><tr><td class="native-cable-group" rowspan="4">For Home Loads to 12 Branch Circuits</td><td>L1</td><td class="native-wire native-wire-black">Black</td><td rowspan="4">30A Max</td><td>14 AWG -10 AWG</td></tr><tr><td>L2</td><td class="native-wire native-wire-red">Red</td><td>14 AWG -10 AWG</td></tr><tr><td>N</td><td class="native-wire native-wire-white">White</td><td>14 AWG -10 AWG</td></tr><tr><td>GND</td><td class="native-wire native-wire-green">Green</td><td>14 AWG -10 AWG</td></tr><tr><td class="native-cable-group">Emergency Stop Circuit (Connect to Emergency Stop Button)</td><td>/</td><td>/</td><td>2A Max</td><td>24 AWG</td></tr></tbody></table></div>

<p>* An 100-amp, 2-pole branch breaker is needed for the home districution panel.<br/>* Max. 30-amp branch breakers for home loads.</p>

<span id="native-product-overview"></span>

## PRODUCT OVERVIEW

### Dimensions

<div class="native-figure native-dimensions native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dimensions" data-source-fragment-sha256="e61f24ec2c339b1a7ae3acca2cb4cfcdfbfe58da791ecf748a988a18d7f62172" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="dimensions.semantic"><img alt="Dimensions" class="hb-reference-art hb-composite-art" src="assets/dimensions.png"/></div></figure></div>

<p>* The figures are for reference purposes only, please refer to the actual product.</p>

### With Deadfront Cover Installed

<div class="native-figure native-covered-overview native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="covered-overview" data-source-fragment-sha256="d9345d2ae845c89882a0b6eb32df5dfeb1eda899a807e3712ec2461541a24812" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="covered-overview.semantic"><img alt="With deadfront cover installed" class="hb-reference-art hb-composite-art" src="assets/covered-overview.png"/></div></figure></div>

#### IoT Button with Indicator

<ul class="native-bullets"><li>Short-press the button to turn on/off the Bluetooth and Wi-Fi.</li><li>Long press and hold the button for 5 sec to reset the Bluetooth and Wi-Fi (the Smart Transfer Switch will retain the previous settings).</li></ul>

<p>*If Wi-Fi and Bluetooth are not paired within two hours, they will automatically turn off.</p>

#### Emergency Stop Button

<p>In case of emergency, this button can be manually activated to shut off output of the entire system immediately.</p>

### LED Indicators

<div class="table-wrapper docutils container native-table-wrap"><table class="manual-table native-print-grid native-led"><thead><tr><th scope="col">Indicator</th><th scope="col">Status</th><th scope="col">Description</th></tr></thead><tbody><tr><td class="native-led-name" rowspan="3">Grid Indicator</td><td>Flashing Blue</td><td>Grid power present, not supplying home loads</td></tr><tr><td>Solid Blue</td><td>Grid power supplying home loads</td></tr><tr><td>Off</td><td>No grid power</td></tr><tr><td class="native-led-name" rowspan="3">Power Station Indicator (AC1/AC2)</td><td>Flashing Green</td><td>Power station connected &amp; on standby, not supplying power to home loads</td></tr><tr><td>Solid Green</td><td>power station connected and supplying power to home loads. In STS, power supply to home loads depends on commissioning settings.</td></tr><tr><td>Off</td><td>Power Station not connected</td></tr><tr><td class="native-led-name" rowspan="3">IoT Indicator</td><td>Flashing Green</td><td>Wi-Fi &amp; Bluetooth on, not paired</td></tr><tr><td>Solid Green</td><td>Wi-Fi &amp; Bluetooth on, paired</td></tr><tr><td>Off</td><td>Wi-Fi &amp; Bluetooth off</td></tr><tr><td class="native-led-name" rowspan="2">Error Indicator</td><td>Solid Red</td><td>Product malfunction</td></tr><tr><td>Off</td><td>Normal operation</td></tr></tbody></table></div>

### With Deadfront Cover Removed

<div class="native-figure native-uncovered-overview native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="uncovered-overview" data-source-fragment-sha256="82d034ad0a780b61e12ba881f466e40fe59252cae4c6a8a3f734a7c38e7c4f32" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="uncovered-overview.semantic"><img alt="With deadfront cover removed" class="hb-reference-art hb-composite-art" src="assets/uncovered-overview.png"/></div></figure></div>

#### Normal Backup Mode

<p>The UPS function is disabled by default. In the event of a power outage, the portable power station will automatically power your home loads with the stored power within 5 seconds. Once grid power is restored, the system automatically switches back to grid supply.</p>

<table class="manual-callout-table manual-callout-table hb-callout-label-shaded"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>The power station must remain turned on; otherwise, the STS cannot switch to battery power after an outage.</p></td></tr></tbody></table>

#### UPS Mode

<p>In this mode, the UPS function is enabled. During a power outage, the system automatically switches to battery power within 20 milliseconds.</p>

<ul class="native-bullets"><li>The portable power station remains active at all times and continuously consumes a small amount of power, even when not in use.</li><li>If the power station is being charged by the STS, the switch time may exceed 20 milliseconds.</li><li>Once grid power is restored, the system automatically switches back to grid supply.</li></ul>

<table class="manual-callout-table manual-callout-table hb-callout-label-shaded"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>The UPS function can only work if the STS is successfully connected to the Jackery Explorer 5000 Plus or Jackery HomePower 5000 Plus.Before using the UPS mode, please ensure:</p><ol class="native-steps"><li>The UPS function is enabled in the Jackery App.</li><li>The portable power station is turned on and not charging.</li></ol></td></tr></tbody></table>

<span id="native-pre-installation"></span>

## PRE-INSTALLATION

### System Overview

<div class="native-figure native-system-overview native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="system-overview" data-source-fragment-sha256="485fb9304b1dc5b697c77d7e16b542b559051f380d48f87d5136b48cb2bd9b17" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="system-overview.semantic"><img alt="System overview" class="hb-reference-art hb-composite-art" src="assets/system-overview.png"/></div></figure></div>

<p>* If there is no Wi-Fi available, please connect your device with Bluetooth.<br/><strong>* If the device's Wi-Fi and Bluetooth are turned on and haven't connected to the Jackery App within two hours, both will automatically turn off.</strong></p>

### Installation Location

<p>Install the Jackery Smart Transfer Switch indoors.</p>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-open"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/symbol_warning_triangle_yellow.svg"/>Warning</span></td><td class="manual-callout-body"><ul class="native-bullets"><li>Make sure the product is placed in a dry and well-ventilated location.</li><li>Ensure that the door opens to an angle of at least 90 degrees.</li><li>Installation personnel need to wear insulating gloves, safety glasses, and rubber-soled shoes.</li><li>Prior to installation, ensure the main circuit breaker and all branch circuits are turned off.</li></ul></td></tr></tbody></table>

<span id="native-installation-guide"></span>

## INSTALLATION GUIDE

<p><strong>Note: </strong>The details below are general guidelines for installing space and are not guaranteed to be applicable. Please consult your local AHJ or Utility before use.</p>

### Surface Mounting

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-open"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/symbol_warning_triangle_yellow.svg"/>Warning</span></td><td class="manual-callout-body"><p>The product is not waterproof and is designed specifically for indoor use.</p></td></tr></tbody></table>

<div class="native-media"><div class="native-media-copy"><ol class="native-steps"><li>Install the upper and lower wall brackets on the back of the Smart Transfer Switch using 4 M4 screws. Tighten all screws with a torque of 0.8 N·m.</li></ol></div><div class="native-media-art"><div class="native-figure native-mounting-brackets native-art"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-brackets" data-source-fragment-sha256="44308da080eeb91070c8f7fcce2dadbfaae7f6e894a25f157b548bd313cd8f75"><div class="hb-reference-semantic" data-reference-id="mounting-brackets.semantic"><img alt="Attach the wall brackets" class="hb-reference-art hb-composite-art" src="assets/mounting-brackets.png"/></div></figure></div></div></div>

<ol class="native-steps" start="2"><li>Secure the marking-off template on the mounting surface and carefully mark each hole location with a pencil.</li></ol>

<div class="native-figure native-mounting-template native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-template" data-source-fragment-sha256="fd3932763c2e63590d5ebf73d0c82f9b89c44de954ff83bc076d754d3483d2f3" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="mounting-template.semantic"><img alt="Marking-off template positions" class="hb-reference-art hb-composite-art" src="assets/mounting-template.png"/></div></figure></div>

<ol class="native-steps" start="3"><li>Fasten the Smart Transfer Switch with 4 M6 expansion bolts or M6 screws.</li></ol>

<div class="native-figure native-mounting-fasteners native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-fasteners" data-source-fragment-sha256="49a3f853290ead0e444c6527cb3b8f08d08ec7becba75dbe6ecc4aa5aec6d9ad" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="mounting-fasteners.semantic"><img alt="Fasten the Smart Transfer Switch" class="hb-reference-art hb-composite-art" src="assets/mounting-fasteners.png"/></div></figure></div>

### Locating STS Cable Entry

<ul class="native-bullets"><li>During the drilling process, cover the interior equipment to prevent debris from falling into the equipment.</li><li>Remove the debris after drilling to prevent interference with the equipment.</li></ul>

<div class="native-figure native-cable-entry native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cable-entry" data-source-fragment-sha256="fd90b26fd89ed86fd37d7baa6c1019c51e5130b00866a214c3543d2982328bd9" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="cable-entry.semantic"><img alt="Permissible cable entry locations. Please shut off the power before working on the wiring. Do not drill outside designated area." class="hb-reference-art hb-composite-art" src="assets/cable-entry.png"/></div></figure></div>

### Electrical Connections

<p>Warning</p>

<ul class="native-bullets"><li>Risk of electric shock! Before wiring, make sure the power is off. Ensure that both the main and branch circuit breakers are turned off.</li><li>Ensure that conduits are installed before wiring between the electrical panel and the Jackery Smart Transfer Switch to enhance safety and protect wires from damage.</li><li>As shown in the picture, you can move the breakers from electrical panel to the Smart Transfer Switch.</li><li>The Installation of the 100A circuit breaker in the electrical panel is as shown in the picture.</li><li>The breakers in the transfer switch must NOT exceed 30A.</li></ul>

<div class="native-figure native-grid-preparation native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="grid-preparation" data-source-fragment-sha256="8e1afb963ee02b145b809629b70296b998a4e73f7132075e81b7e63bda981ad0" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="grid-preparation.semantic"><img alt="Electrical panel and Smart Transfer Switch. Only single-pole and two-pole breakers, no tandem breakers." class="hb-reference-art hb-composite-art" src="assets/grid-preparation.png"/></div></figure></div>

#### Connecting the Grid Conductors

<ol class="native-steps"><li>Make sure all branch breakers and the main breaker are turned off.</li><li>Remove the covers from both the electrical panel and the Smart Transfer Switch.</li><li>Remove the knockout from the electrical panel and drill permissible cable entry hole(s) on the Smart Transfer Switch.</li><li>Install a conduit (not included) between the electrical panel and the Smart Transfer Switch.</li><li>Pull the pre-wired wires from the electrical panel bundled through the conduit.</li><li>Install a compatible 100A, 2-pole branch breaker (not included) in the electrical panel.</li><li>Locate the GROUND wire of the electrical panel and connect it to the grid ground lugs of the Smart Transfer Switch.</li><li>Locate the NEUTRAL wire in the electrical panel and connect it to the grid neutral lugs of the Smart Transfer Switch.</li><li>Locate the HOT wires of the 100-amp, 2-pole branch breaker added to the electrical panel and connect to the Smart Transfer Switch. Then, Install the power supply cover on the Smart Transfer Switch.</li></ol>

<div class="native-figure native-grid-wiring native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="grid-wiring" data-source-fragment-sha256="9868eb207ab372756f23175451292e4edd4e6d39df6dddf65bd1f95370d850fe" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="grid-wiring.semantic"><img alt="Grid conductor connections" class="hb-reference-art hb-composite-art" src="assets/grid-wiring.png"/></div></figure></div>

#### Connecting the Home Load Conductors

<p>* The home load supports simultaneous connection to both 120V and 240V circuits, with a maximum of 12 circuits for 120V and 6 circuits for 240V.</p>

<ol class="native-steps"><li>From the electrical panel, select a branch circuit to be powered by the STS during a power outage. When there is no power outage, selected circuits will be powered by the utility.</li><li>Turn off the selected circuit breaker in the electrical panel.</li><li>Remove HOT wire from the selected circuit breaker.</li><li>Remove NEUTRAL wire of the selected circuit from the NEUTRAL bus bar.</li><li>Remove the GROUND wire of the selected circuit from the ground bus bar.</li><li>Connect the the HOT wire removed from the electrical panel to the breaker on the Smart Transfer Switch.</li><li>Connect the the NEUTRAL wire removed from the electrical panel to the neutral bus bar on the Smart Transfer Switch.</li><li>The GROUND wire of the electrical panel does not need to be connected to the STS.</li><li>Label the circuit breaker on the Smart Transfer Switch cover.</li><li>Repeat for each circuit.</li></ol>

<div class="native-figure native-load-wiring native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="load-wiring" data-source-fragment-sha256="8c85c43f7187b00811400c9a3df4e796b887e9baba3ea84db5b00dc6ecfaafb0" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="load-wiring.semantic"><img alt="Home load conductor connections" class="hb-reference-art hb-composite-art" src="assets/load-wiring.png"/></div></figure></div>

<p>Conductor Tightening Torque</p>

<div class="table-wrapper docutils container native-table-wrap"><table class="manual-table native-print-grid native-torque"><thead><tr><th scope="col">Grid</th><th scope="col">Torque</th><th scope="col">Strip Length</th><th scope="col">Home Load</th><th scope="col">Torque</th><th scope="col">Strip Length</th></tr></thead><tbody><tr><td>L1</td><td>30.98 In-lbs/3.5 N·m</td><td>0.47" (12 mm)</td><td>L1</td><td>20.36 In-lbs/2.3 N·m</td><td>0.39" (10 mm)</td></tr><tr><td>L2</td><td>30.98 In-lbs/3.5 N·m</td><td>0.47" (12 mm)</td><td>L2</td><td>20.36 In-lbs/2.3 N·m</td><td>0.39" (10 mm)</td></tr><tr><td>N</td><td>46.02 In-lbs/5.2 N·m</td><td>0.47" (12 mm)</td><td>N</td><td>17.7 In-lbs/2.0 N·m</td><td>0.47" (12 mm)</td></tr><tr><td>GND</td><td>46.02 In-lbs/5.2 N·m</td><td>0.79" (20 mm)</td><td>GND</td><td>17.7 In-lbs/2.0 N·m</td><td>0.47" (12 mm)</td></tr></tbody></table></div>

#### Installing an Emergency Stop Button (Optional)

<p>* <strong>Ensure that a normally open emergency stop button is purchased.</strong><br/>Install in an easily accessible external location. This allows for the immediate disconnection of power to the STS load in case of an emergency.</p>

<div class="native-figure native-external-emergency-stop native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="external-emergency-stop" data-source-fragment-sha256="b9542596112a53bc7c45c991479aaa9e7f87814696c064fab7f719b12902040a" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="external-emergency-stop.semantic"><img alt="Emergency stop button - indoor and outdoor connections" class="hb-reference-art hb-composite-art" src="assets/external-emergency-stop.png"/></div></figure></div>

#### Installing the Deadfront Cover

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-open"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/symbol_warning_triangle_yellow.svg"/>Warning</span></td><td class="manual-callout-body"><p>* Confirm that all connections are correct, secure, and properly grounded.<br/>* Confirm that all screws are tightened.<br/>* Use a multimeter in Continuity setting to ensure that the hot wire is not short circuited to neutral.<br/>* Use a multimeter in Continuity setting to ensure that the hot wire is not short circuited to ground.</p></td></tr></tbody></table>

<p>First, remove the twist-outs for home loads, fill any unused open spaces on the cover, and then tighten the screws to secure the deadfront.</p>

<div class="native-figure native-deadfront-installation native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="deadfront-installation" data-source-fragment-sha256="0c4ed514450eaf72dda700fed0d70769e699f798dd92b8b41770cfd126c6ca03" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="deadfront-installation.semantic"><img alt="Install the deadfront cover" class="hb-reference-art hb-composite-art" src="assets/deadfront-installation.png"/></div></figure></div>

#### Connecting with Power Station

<p>For Jackery Explorer 5000 Plus (Max. 2 units)</p>

<div class="native-figure native-power-station-connections native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-station-connections" data-source-fragment-sha256="057112e5fbbc3d1363455f5c121de7502dac1f77d03425c04260177e7a840135" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="power-station-connections.semantic"><img alt="Power station connections - maximum two units" class="hb-reference-art hb-composite-art" src="assets/power-station-connections.png"/></div></figure></div>

#### Energizing

<p>Before energizing, ensure that the main and branch circuit breakers are in the OFF position.<br/>To energize, turn on the main breaker first, followed by each branch circuit breaker.</p>

#### Locking the Panel

<div class="native-figure native-locking-panel native-narrow"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="locking-panel" data-source-fragment-sha256="211fbb0403073aab93a897986da188aa01988703395a35b1c64fb28a42567aea"><div class="hb-reference-semantic" data-reference-id="locking-panel.semantic"><img alt="Lock the panel" class="hb-reference-art hb-composite-art" src="assets/locking-panel.png"/></div></figure></div>

<span id="native-recommended-breakers"></span>

## RECOMMENDED BREAKERS

<p>15A breakers, 20A breakers, 30A breakers; no tandem or quad breakers.<br/>Brands and models of compatible circuit breakers: GE - THQL, Siemens - Tipo QP, Square D-HOM , Eaton-BR<br/>STS is not compatible with plug-in neutral circuit breakers.</p>

<span id="native-internet-setup"></span>

## INTERNET AND INITIALIZATION SETUP

### To download the App and log in

<figure aria-label="App download" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app-store-badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Search for "Jackery" in Google Play or App Store to install the App. After that, you can register and log in.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app-download-qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternatively, scan the QR code below to download and install the App.</p></div></div></div><div class="hb-app-download-semantic"><img alt="App Store and Google Play" class="hb-app-download-semantic-art" src="assets/app-store-badges.png"/></div></figure>

### To add device

<div class="native-media"><div class="native-media-copy"><ol class="native-steps"><li>Press the IoT button to enable Wi-Fi and Bluetooth; the IoT indicator light will start flashing.</li></ol><p class="native-status-panel">Flashing - ready to connect<br/>Solid - connected successfully</p></div><div class="native-media-art"><div class="native-figure native-iot-pairing native-art"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="iot-pairing" data-source-fragment-sha256="ab1f87889c9dd0ea40afd68ffa8fc6c93b7c16f0aa755283b81fcc4d4bf7fb1f" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="iot-pairing.semantic"><img alt="IoT button pairing operation" class="hb-reference-art hb-composite-art" src="assets/iot-pairing.png"/></div></figure></div></div></div>

<div class="native-media"><div class="native-media-copy"><ol class="native-steps" start="2"><li>Tap <img alt="Add device" class="native-inline-control" src="assets/inline-add-device.png"/> in the App to add your device, which allows the app to connect to nearby devices and enable Bluetooth permissions</li></ol></div><div class="native-media-art"><div class="native-figure native-app-add-device native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add-device" data-source-fragment-sha256="50da1e4cca96ac3c2f23d05ea22b2abe67b0d36f0127f1373ec024cb699dec5b"><div class="hb-reference-semantic" data-reference-id="app-add-device.semantic"><img alt="Add a device in the Jackery App" class="hb-reference-art hb-composite-art" src="assets/app-add-device.png"/></div></figure></div></div></div>

<ol class="native-steps" start="3"><li>Tap the Smart Transfer Switch(STS) icon in the App to enter the STS main page and connect the device to the Wi-Fi network.</li></ol>

<div class="native-figure native-app-wifi native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-wifi" data-source-fragment-sha256="18c77581f5ece81a0fc657ed595e82d1424b600dcf2e3441510a2059cdd1cd37" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-wifi.semantic"><img alt="Connect the Smart Transfer Switch to Wi-Fi" class="hb-reference-art hb-composite-art" src="assets/app-wifi.png"/></div></figure></div>

### Voltage configuration

<ol class="native-steps"><li>Tap <img alt="Settings" class="native-inline-control" src="assets/inline-settings.png"/> in the STS main page.</li><li>Select Voltage configuration <img alt="Voltage configuration" class="native-inline-control" src="assets/inline-voltage-config.png"/></li></ol>

<div class="native-figure native-app-voltage-menu native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-voltage-menu" data-source-fragment-sha256="52ff5e55d99bfeec57cc091de6f854579b255acb75d75134fe563b12a8b8c74d" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-voltage-menu.semantic"><img alt="Open voltage configuration" class="hb-reference-art hb-composite-art" src="assets/app-voltage-menu.png"/></div></figure></div>

<ol class="native-steps" start="3"><li>Tap <img alt="Edit" class="native-inline-control" src="assets/inline-edit.png"/> in the upper right corner, then tap the <img alt="Link circuits" class="native-inline-control" src="assets/inline-link-circuits.png"/> to set the voltage to 240V according to the actual connection of the STS circuit, and finally tap <img alt="Save" class="native-inline-control" src="assets/inline-save.png"/> to save the settings.</li></ol>

<div class="native-figure native-app-voltage-settings native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-voltage-settings" data-source-fragment-sha256="26a8aab6c8900742475680fe63398d89299beb4ac2d41c15cc5270554885c89d" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-voltage-settings.semantic"><img alt="Set and save the circuit voltage" class="hb-reference-art hb-composite-art" src="assets/app-voltage-settings.png"/></div></figure></div>

### Edit circuit name

<ol class="native-steps"><li>Tap ‘Circuits’ in the STS main page to enter circuits main page.</li></ol>

<div class="native-figure native-app-circuit-list native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuit-list" data-source-fragment-sha256="35b8053a6d87712c1507733be750c75a35b9d953e61b8b824b15678e31975d71" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-circuit-list.semantic"><img alt="Select a circuit" class="hb-reference-art hb-composite-art" src="assets/app-circuit-list.png"/></div></figure></div>

<ol class="native-steps" start="2"><li>Select the desired circuit and tap <img alt="Edit circuit name" class="native-inline-control" src="assets/inline-edit-name.png"/> to edit its name.</li></ol>

<div class="native-figure native-app-circuit-name native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuit-name" data-source-fragment-sha256="ce1738b5f62dc174442d5aea2d71cb588a531b2df1efab524a7f088922e21e7f" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-circuit-name.semantic"><img alt="Edit the circuit name" class="hb-reference-art hb-composite-art" src="assets/app-circuit-name.png"/></div></figure></div>

<span id="native-app-quick-start"></span>

## JACKERY APP QUICK START GUIDE

### Dashboard

<div class="native-media native-media-art-first"><div class="native-media-art"><div class="native-figure native-app-dashboard native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-dashboard" data-source-fragment-sha256="25ae3af4ce9d70d887ef5030bef629637803ce5e8dd91749ad51ebe52d12e69e"><div class="hb-reference-semantic" data-reference-id="app-dashboard.semantic"><img alt="Dashboard" class="hb-reference-art hb-composite-art" src="assets/app-dashboard.png"/></div></figure></div></div><div class="native-media-copy"><p>View and monitor the real-time power consumption of the home, power station, and grid.<br/>View the current power supply for the home. Manually switch the home power supply to the power station under the following conditions:</p><ol class="native-steps"><li>Power station battery exceeds the backup reserve.</li><li>Backup-only mode is off.</li></ol><p>Daily solar power generation and home electricity consumption.</p></div></div>

### Circuits

<div class="native-figure native-app-circuits native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuits" data-source-fragment-sha256="09f58dfe920864f8f3471930304bdd19509b259f57cf538c15a04ac324df741e"><div class="hb-reference-semantic" data-reference-id="app-circuits.semantic"><img alt="Circuit list and circuit name editor" class="hb-reference-art hb-composite-art" src="assets/app-circuits.png"/></div></figure></div>

<p>Manually turn each home circuit on or off, rename them, and view the historical power consumption of each circuit.</p>

### Working Modes

<div class="native-media native-media-art-first"><div class="native-media-art"><div class="native-figure native-app-working-modes native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-working-modes" data-source-fragment-sha256="9c38b4b83f21fa75c83c5ee39db763c721df1f8f233a61207a3b927205bd1b01"><div class="hb-reference-semantic" data-reference-id="app-working-modes.semantic"><img alt="Working modes" class="hb-reference-art hb-composite-art" src="assets/app-working-modes.png"/></div></figure></div></div><div class="native-media-copy"><h3>Set backup reserve</h3><p>When the power station is discharging, the battery will discharge until it reaches the backup reserve . During a power outage, it discharges until it hits the discharge limit (0%). You can modify the level in Settings &gt; Working Modes.<br/>* The setting of backup reserve will take effect in any mode.<br/>* During a power outage, the backup reserve level will discharge to 0% in any mode.</p><h3>Automatic charging mode</h3><p>It’s commonly used for daily home backup power. <strong>The power station will automatically recharge to 100% when AC1 or AC2 is below backup reserve.</strong></p></div></div>

#### Self-powered mode

<p>Maximize the use of solar energy for your house.<br/>In this mode, the power station charges exclusively using solar energy. It will begin supplying power to the home two hours after reaching a full charge. If it is not fully charged, it will only provide power to the home during the night.</p>

#### Charging-discharging plan

<p>Suitable for situations with fluctuating electricity rate, allows for charging-discharging plans based on peak and off-peak electricity times, reducing electricity costs.<br/>Charging task: Set the period for charging.<br/>Discharging task: Set the period for discharging. In this period, if batteries exceed the backup reserve, they will discharge.<br/>When the power station is connected to Smart Transfer Switch, it temporarily disables Battery saving mode, Auto-off, Energy saving mode, Quiet charging mode, Charging plan.</p>

### Backup-only mode

<div class="native-media native-media-art-first"><div class="native-media-art"><div class="native-figure native-app-backup-only native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-backup-only" data-source-fragment-sha256="02e67fbac799ef35dc3f7e7a3bc01baff344a5c01575d4b707c8e08d47dc2248"><div class="hb-reference-semantic" data-reference-id="app-backup-only.semantic"><img alt="Backup-only mode" class="hb-reference-art hb-composite-art" src="assets/app-backup-only.png"/></div></figure></div></div><div class="native-media-copy"><p>When backup-only mode is enabled, the grid will supply power to the home while fully charging the power station, which will only supply power during an outage. The charging-discharging plan and self-powered mode will be temporarily disabled. Manual switching to the power station is unavailable in backup-only mode.</p></div></div>

### Backup priority

<div class="native-media native-media-art-first"><div class="native-media-art"><div class="native-figure native-app-backup-priority native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-backup-priority" data-source-fragment-sha256="f76ceaad17bf8b6fee4e6047a4cc30d50ebe8355835797fe9ba0bb7f377bc6ef"><div class="hb-reference-semantic" data-reference-id="app-backup-priority.semantic"><img alt="Backup priority" class="hb-reference-art hb-composite-art" src="assets/app-backup-priority.png"/></div></figure></div></div><div class="native-media-copy"><p>During an outage, the system prioritizes the supply of battery power to home circuits. Categorize your home circuits into 3 levels: must have, nice to have, and no power supply.<br/>Circuit priorities</p><ol class="native-steps"><li>Must have: As long as there's power in batteries, it will be supplied to these circuits.</li><li>Nice to have: These circuits will be powered when the battery level is equal to or higher than the percentage you set.</li><li>Non-priority circuits: These circuits won't be powered when using battery power during an outage.</li></ol></div></div>

### UPS mode

<div class="native-media native-media-art-first"><div class="native-media-art"><div class="native-figure native-app-ups-mode native-phone"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-ups-mode" data-source-fragment-sha256="24a053bbf9e84eaca2e8333bfce1eb2fad4375caa1690ef723867af58f1b0fd7"><div class="hb-reference-semantic" data-reference-id="app-ups-mode.semantic"><img alt="UPS mode" class="hb-reference-art hb-composite-art" src="assets/app-ups-mode.png"/></div></figure></div></div><div class="native-media-copy"><p>When UPS mode is enabled, if there is a power outage, STS will automatically switch to power station supply within 20 ms; if STS is charging the power station at that time, the switch time will be longer than 20 ms, and after power is restored, it will automatically switch back to grid supply.<br/>In non-UPS mode, the switch time is approximately 5 seconds only if the power station is turned on.<br/>* The STS will remain on when connected to the power station, so it is recommended not to manually turn off the power station.</p></div></div>

<span id="native-warranty"></span>

## WARRANTY

<figure aria-label="WARRANTY" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel">We only provide our warranty to customers who purchase from the official Jackery website, Jackery-branded third-party platforms, or local authorized dealers.</div><div class="hb-warranty-local-note">* Warranty period and details may vary according to local laws, regulations, and authorized dealers.</div></figure>

### Limited Warranty

<figure aria-label="Limited Warranty" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects in workmanship and material under normal consumer use during the applicable warranty period identified in the 'Warranty Period' section below, subject to the exclusions set forth below.<br/>This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, nor authorize any person to assume for us, any other liability in connection with the sale of our products.</p></figure>

### Warranty Period

<figure aria-label="Warranty Period" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>5 Years Standard Warranty: The standard warranty period for Jackery Smart Transfer Switch is 5 years. In each case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. The sales receipt from the first consumer purchase, or other reasonable documentary proof, is required in order to establish the start date of the warranty period.</p></figure>

### Repair or replacement

<figure aria-label="Repair or replacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the applicable warranty period due to a defect in workmanship or material. The repaired/replaced product assumes the remaining warranty of the original date of purchase.</p></figure>

### Limited to Original Consumer Buyer

<figure aria-label="Limited to Original Consumer Buyer" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable to any subsequent owner.</p></figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery's warranty does not apply to:<br/>Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as authorized in Jackery's current product literature.<br/>Attempted repair by anyone other than an authorized facility.<br/>Any product purchased through an online auction house.<br/>Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within seven days after you purchase the product and at least once every 6 months thereafter.</p></figure>

### Interpretation Rights

<figure aria-label="Interpretation Rights" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery Inc. reserves the right to final interpretation of the above customers' after-sales policy.</p></figure>
