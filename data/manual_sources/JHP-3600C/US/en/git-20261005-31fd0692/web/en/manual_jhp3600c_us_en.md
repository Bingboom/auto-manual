<style>
/* Native exceptions only. Chapter H1 / dot-led H2 use shared web_manual.css. */
#furo-main-content #jackery-homepower-3600-pro-max-user-manual > h1,
#furo-main-content section#fcc > h1,
#furo-main-content section#contact-us > h1,
#furo-main-content h2.hb-source-hidden-heading,
#furo-main-content section#package-list section > h3 {
  display: none;
}
#furo-main-content section#important > h2 {
  display: block;
  padding: 0;
  background: transparent !important;
  color: var(--hb-text);
  border-radius: 0;
  font-size: 1.12rem;
}
#furo-main-content section#important > h2::before {
  display: none;
}
/* Native safety subsection strips differ from ordinary dot-led sections. */
#furo-main-content section:has(> .hb-safety-instruction) > section > h2::before {
  display: none;
}
#furo-main-content section:has(> .hb-safety-instruction) > section > h2:first-of-type {
  display: block;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: var(--hb-brand-dark) !important;
  color: var(--hb-paper);
}
#furo-main-content .manual-two-col-table {
  width: 100%;
  table-layout: fixed;
}
#furo-main-content .manual-two-col-table > tbody > tr > td {
  width: 50%;
  vertical-align: top;
  padding: 0 0.7rem 0 0;
}
#furo-main-content .manual-two-col-table > tbody > tr > td + td {
  padding: 0 0 0 0.7rem;
}
#furo-main-content .hb-safety-instruction .manual-callout-label {
  width: 32% !important;
  white-space: normal;
}
#furo-main-content .hb-safety-instruction .manual-callout-body {
  width: 68% !important;
  font-size: 0.94rem;
  line-height: 1.2;
}
#furo-main-content .hb-source-risk-label {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.55rem;
  font-size: 1.1rem;
}
#furo-main-content .hb-source-risk-label img {
  margin: 0;
}
@media (max-width: 640px) {
  #furo-main-content .hb-safety-instruction .manual-callout-label,
  #furo-main-content .hb-safety-instruction .manual-callout-body { width: 100% !important; }
  #furo-main-content .hb-source-risk-label { font-size: 0.86rem; gap: 0.3rem; }
  #furo-main-content .hb-source-risk-label img { width: 1.3rem; }
}

/* Authored small source labels, distinct from level-two section markers. */
#furo-main-content .hb-source-pill-heading {
  display: inline-block;
  padding: 0.3rem 0.65rem;
  border-radius: 999px;
  background: var(--hb-surface);
  font-size: 0.88rem;
  text-transform: none;
}
#furo-main-content .hb-source-pill-heading::before,
#furo-main-content section#app-setup h2::before,
#furo-main-content section#app-setup h3::before {
  display: none;
}
#furo-main-content section#app-setup h2,
#furo-main-content section#app-setup h3 {
  display: block;
  padding: 0;
  text-transform: none;
}
#furo-main-content section[id^="jackery-battery-pack-3600-sold-separately"] > h1,
#furo-main-content section#jackery-automatic-transfer-switch-sold-separately > h1 {
  text-transform: none;
}

</style>

# Jackery HomePower 3600 Pro Max User Manual

<span id="important"></span>

## IMPORTANT

<p>Congratulations on your new Jackery HomePower 3600 Pro Max. Please read this manual carefully before using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible place for future reference.</p>

<p>In compliance with laws and regulations, the right of final interpretation of this document and all related documents of this product resides with the Company. Although every effort has been made to ensure the accuracy of this manual, Jackery Inc. assumes no responsibility for any errors that may appear.</p>

<p>Please note that no further notifications will be given in case of any update, revision, or termination. For the latest version of the product manuals, visit support.jackery.com.</p>

<p>* The images are for reference purposes only. Please refer to the actual product.</p>

<span id="safety"></span>

# IMPORTANT SAFETY INFORMATION

<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="manual-callout-table manual-callout-table hb-symbol-signal-table"><tbody><tr><td class="manual-callout-label hb-symbol-signal-label-cell"><span class="hb-source-risk-label"><img alt="" src="assets/e1746d6937db_warning_triangle_dark.svg"/><strong>WARNING</strong></span></td><td class="manual-callout-body hb-symbol-signal-meaning-cell"><p><strong>INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS</strong></p></td></tr></tbody></table></figure>

<table class="manual-two-col-table"><tbody><tr><td><p><strong>Always follow these basic precautions when using this product.</strong></p><ul><li>Read all the instructions before using the product.</li><li>Do not allow children to play on the product. Close supervision of children is necessary when the product is used near children.</li><li>Avoid placing hands or fingers inside the product.</li><li>Stop using the product immediately if it has been physically damaged or modified. Improper use of the product may cause unpredictable behavior, leading to fire, explosion, or injury.</li><li>If any of the following are observed, including but not limited to overheats, emits unusual odors or smoking, leaks, or burns, stop using the product immediately and contact the dealer or our Customer Support.</li><li>Never attempt to open, repair, or modify the product. Any tampering, reassembly, or modification of the product can result in electric shock, fire, or battery damage.</li></ul></td><td><ul><li>Be aware that liquid ejected from the product may cause irritation or burns. Inappropriate or abusive use may lead to battery leakage. Avoid direct contact with leaking liquid. If the liquid contacts your eyes, seek medical help immediately. If it contacts other body parts, flush with running water and consult a medical professional without delay.</li><li>Do not expose the product to fire or excessive temperatures. Doing so may result in an explosion if the temperature exceeds 130°C (265°F).</li><li>Any use of unrecommended or non-supplied materials or parts with the product may result in a risk of fire, electric shock, or personal injury.</li><li>Do not leave the battery charging unattended for long periods. Always monitor the charging process to ensure safe operation.</li><li>To reduce the risk of electric shock, unplug the product from any power source before attempting any technical service or troubleshooting.</li></ul></td></tr></tbody></table>

## OPERATING INSTRUCTIONS

<table class="manual-two-col-table"><tbody><tr><td><p><strong>SAVE THESE INSTRUCTIONS</strong></p><ul><li>Stop using the product immediately if it shows signs of damage. Discontinue use and contact customer support for assistance.</li><li>Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's specified operating temperature ranges:<ul><li>Charging temperature: -4°F to 113°F (-20°C to 45°C )</li><li>Discharging temperature: -4°F to 113°F (-20°C to 45°C )</li></ul></li><li>To ensure proper air circulation, keep the product vents uncovered. The area where the product is used must have adequate airflow in a cool, dry environment to prevent overheating.<ul><li>Charging in damp or poorly ventilated spaces may cause safety hazards.</li><li>Water can cause short circuits or damage to the charger, leading to safety risks.</li></ul></li><li>Unplug the power cord from a power outlet during a storm.</li><li>Immediately turn off the product by pressing the power button if it has fallen, been dropped, or exposed to vibrations.</li></ul></td><td><ul><li>Ensure the device(s) are powered off before connecting them to the product.</li><li>Do not charge the product using a damaged or broken charging cord or plug.</li><li>Do not use the product to charge any device with a damaged or broken cable or plug.</li><li>Always unplug the charging cord by pulling the plug, not the cord, to reduce the risk of damage.</li><li>Ensure the product is properly secured when transporting it in a moving vehicle.</li><li>DO NOT place the unit upside down or on its side during use or storage.</li><li>DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor during operation in a workshop or repair facility.</li><li>DO NOT use the product's accessories with other devices or equipment.</li><li>Solar charge time depends on weather conditions. Place your solar panel where it will get as much direct sunlight as possible.</li></ul></td></tr></tbody></table>

## GROUNDING INSTRUCTIONS

<p>This product must be grounded. If it should malfunction or breakdown, grounding provides a path of least resistance for electric current to reduce the risk of electric shock. This product is equipped with a cord having an equipment grounding conductor and a grounding plug. The plug must be plugged into an outlet that is properly installed and grounded in accordance with all local codes ordinances.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">WARNING</td><td class="manual-callout-body"><p>Improper connection of the equipment grounding conductor is able to result in a risk of electric shock. Check with a qualified electrician if you are in doubt as to whether the product is properly grounded. Do not modify the plug provided with the product – if it will not fit the outlet, have a proper outlet installed by a qualified electrician.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">DANGER</td><td class="manual-callout-body"><p>This device is intended for indoor use only (Please place this device in a similar indoor environment when using it outdoors, e.g., Home, RVs, tents, cabins, etc.). ※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.</p></td></tr></tbody></table>

## USER MAINTENANCE INSTRUCTIONS

<p>During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is expected. As the number of charge and discharge cycles increases and storage time extends, this degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of battery cells.</p>

<span id="symbols"></span>

# MEANING OF SYMBOLS

<figure aria-label="MEANING OF SYMBOLS" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col"><p>Symbol</p></th><th class="hb-symbol-signal-meaning-heading" scope="col"><p>Meaning</p></th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="WARNING" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">WARNING</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Hazardous practices that may result in severe injury, death, and/or property  damage.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CAUTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CAUTION</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Hazardous practices that may result in personal injury and/or property  damage.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTE" class="hb-signal-badge"><span class="hb-signal-label">NOTE</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Hazardous practices that may result in equipment damage, data loss,  performance deterioration, or unanticipated results.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="TIP" class="hb-signal-badge"><span class="hb-signal-label">TIP</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Supplements the important information or operation tips in the text.</p></td></tr></tbody></table></figure>

<figure aria-label="Safety pictograms" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks.</td></tr><tr><td class="hb-symbol-icon"><img alt="Read the user manual before operation." class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Read the user manual before operation.</td></tr><tr><td class="hb-symbol-icon"><img alt="Risk of electric shock" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Risk of electric shock</td></tr><tr><td class="hb-symbol-icon"><img alt="Battery charging" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Battery charging</td></tr><tr><td class="hb-symbol-icon"><img alt="Explosive material" class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Explosive material</td></tr><tr><td class="hb-symbol-icon"><img alt="Heavy object" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Heavy object</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Do not dismantle the product." class="hb-symbol-art" src="assets/symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">Do not dismantle the product.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep the product away from fire." class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Keep the product away from fire.</td></tr><tr><td class="hb-symbol-icon"><img alt="Keep away from children." class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Keep away from children.</td></tr><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly." class="hb-symbol-art" src="assets/symbol_li_ion.svg"/></td><td class="hb-symbol-meaning">This symbol indicates that a lithium-ion (Li-ion) battery is inside the product and should be disposed of or recycled properly.</td></tr><tr><td class="hb-symbol-icon"><img alt="This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">This symbol indicates that the product shall not be disposed of as household waste, and should be delivered to a designated collection facility for recycling. Proper disposal and recycling can help protect the environment. For more information about the disposal and recycling of this product, contact your local community, disposal service, or dealer.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/45f309ed8b3f_fcc_mark.png"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">This device complies with part 15 of the FCC Rules. Operation is subject to the following two conditions: (1) This device may not cause harmful interference, and (2) This device must accept any interference received, including interference that may cause undesired operation.</div></div></div></div><p><strong>NOTE:</strong> This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses, and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to communications. However, there is no guarantee that radio interference will not occur in a particular installation. If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Reorient or relocate the receiving antenna.</p></li><li><p>Increase the separation between the equipment and receiver.</p></li><li><p>Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.</p></li><li><p>Consult the dealer or an experienced radio/TV technician for help.</p></li></ul><p><strong>MODIFICATION:</strong> Any changes or modifications not expressly approved by the grantee of this device could void the user’s authority to operate the device.</p></div></div></figure>

<span id="inbox"></span>

# WHAT'S IN THE BOX

<figure aria-label="WHAT'S IN THE BOX" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 3600 Pro Max" class="hb-inbox-art" src="assets/inbox_unit.png"/><div class="hb-inbox-label"><p>Jackery HomePower 3600 Pro Max</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC Charging Cable" class="hb-inbox-art" src="assets/inbox_ac.png"/><div class="hb-inbox-label"><p>AC Charging Cable</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Screw terminal block" class="hb-inbox-art" src="assets/inbox_terminal.png"/><div class="hb-inbox-label"><p>Screw terminal block</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Documents" class="hb-inbox-art" src="assets/87ac44e52863_manual_icon1.png"/><div class="hb-inbox-label"><p>Documents</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">TIPS</div><div class="hb-inbox-tip-body">The car charging cable is not included but is available for purchase separately  on our website. For assistance, please contact Jackery customer service.</div></div></figure>

<span id="overview"></span>

# PRODUCT OVERVIEW

## FRONT VIEW

<img alt="LCD AC Output (NEMA 14-50R) 240V~ 60Hz, 16.7A Max, Main Power Button 4000W Max USB-C Output AC Output 100W Max, 5V⎓3A, 9V⎓3A, (NEMA 5-20R) 12V⎓3A, 15V⎓3A, 20V⎓5A 120V~ 60Hz, 16.7A Max, 2000W per port, 4000W in Total USB-A Output L1 and L2 respectively 18W Max, 5-6V⎓3A, from left to right 6-9V⎓2A, 9-12V⎓1.5A AC Power Button USB Power Button" src="assets/overview_front.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## RIGHT SIDE VIEW

<img alt="AC Expansion Port For ATS connection or cascading parallel connection Input/Output: 240V~ 60Hz, 16.7A Max, 4000W Parallel Communication For communication connection in cascade parallel operation EPO (Emergency Power Off) To connect to an external DC Expansion Port emergency stop button Connect to Battery Pack DC Input (2×DC8020 Ports) 12-16V⎓8A Max, Double to 8A Max 16-60V⎓12A Max, Double to 24A / AC Input 1200W Max 100V-120V~ 60 Hz, 15A Max" src="assets/overview_side.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<span id="lcd"></span>

# LCD DISPLAY

<img alt="Numbered LCD screen map, indicators 1–31." src="assets/lcd_map.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<figure aria-label="LCD DISPLAY" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><p>1</p></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/fc4cc02b42ef_fc4cc02b42ef_fc4cc02b42ef_1_Wi-Fi_KCcAbdDk7o4RjKx82micuKJ5nyf.png"/></td><td class="hb-lcd-name"><p>Wi-Fi</p></td><td class="hb-lcd-description"><p><strong>On:</strong> Wi-Fi connected.<br/><strong>Blink:</strong> Ready to connect to Wi-Fi.<br/><strong>Off:</strong> Wi-Fi disconnected.</p></td></tr><tr><td class="hb-lcd-number"><p>2</p></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/7e1392ba6a45_7e1392ba6a45_7e1392ba6a45_2_Bluetooth_HVgvbJhq5o4EDKxhm7McCF4FnjB.png"/></td><td class="hb-lcd-name"><p>Bluetooth</p></td><td class="hb-lcd-description"><p><strong>On:</strong> Bluetooth Connected.<br/><strong>Blink:</strong> Ready to connect to Bluetooth.<br/><strong>Off:</strong> Bluetooth disconnected.</p></td></tr><tr><td class="hb-lcd-number"><p>3</p></td><td class="hb-lcd-icon"><img alt="Quiet Charging Mode" class="hb-lcd-icon-art" src="assets/7f743182c050_7f743182c050_7f743182c050_3_Quiet_Charging_Mode_WLkMbiHS1oGsOtxUCp7cRhFAn1g.png"/></td><td class="hb-lcd-name"><p>Quiet Charging Mode</p></td><td class="hb-lcd-description"><p><strong>On:</strong> The noise during charging is significantly minimized, while the charging power is reduced, and the charging speed slows down.<br/><strong>Off:</strong> Quiet Charging Mode is disabled.<br/>Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>4</p></td><td class="hb-lcd-icon"><img alt="Battery Saving Mode" class="hb-lcd-icon-art" src="assets/e32e6ae96321_e32e6ae96321_e32e6ae96321_15_Battery_Saving_Mode_ClYfbtOGSoK5q2xySXCcgehVn8f.png"/></td><td class="hb-lcd-name"><p>Battery Saving Mode</p></td><td class="hb-lcd-description"><p><strong>On:</strong> Limits the maximum usable capacity of the battery to extend its life.<br/><strong>Off:</strong> Battery Saving Mode is disabled.<br/>Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.<br/>Note 1: This feature is not available when the product is connected to battery pack(s).<br/>Note 2: When this feature is enabled, the product occasionally performs a full charge and discharge cycle to calibrate the SOC.</p></td></tr><tr><td class="hb-lcd-number"><p>5</p></td><td class="hb-lcd-icon"><img alt="Charging Plan" class="hb-lcd-icon-art" src="assets/71017f43bab4_71017f43bab4_71017f43bab4_4_Charging_Plan_M96RbyZQxoGjRRxQHsuczeIln1b.png"/></td><td class="hb-lcd-name"><p>Charging Plan</p></td><td class="hb-lcd-description"><p>Customizes the charging time of the product. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs.<br/>Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>6</p></td><td class="hb-lcd-icon"><img alt="Charging Power Limit" class="hb-lcd-icon-art" src="assets/21b5f19ca9a6_21b5f19ca9a6_21b5f19ca9a6_16_Charging_Power_Limit_VLf2bJfrkoCL0CxJoMNcL5ZxnCt.png"/></td><td class="hb-lcd-name"><p>Charging Power Limit</p></td><td class="hb-lcd-description"><p><strong>On:</strong> Charging Power limit is enabled in the Jackery app.<br/><strong>Off:</strong> Charging Power limit is disabled in the Jackery app. The setting is retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>7</p></td><td class="hb-lcd-icon"><img alt="Self-powered Mode" class="hb-lcd-icon-art" src="assets/73225cf9faa8_73225cf9faa8_73225cf9faa8_5_Self-powered_Mode_FYTnb9vttoexjbxVMchcJaobnCg.png"/></td><td class="hb-lcd-name"><p>Self-powered Mode</p></td><td class="hb-lcd-description"><p>Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs. The power station must be connected to both solar panels and the grid simultaneously, with the load power limited by bypass power.<br/>Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>8</p></td><td class="hb-lcd-icon"><img alt="TOU Mode" class="hb-lcd-icon-art" src="assets/f4cdcb551105_f4cdcb551105_f4cdcb551105_6_TOU_Mode_BjEkbz0rFo6Bw4xiwNpcod9qnnc.png"/></td><td class="hb-lcd-name"><p>TOU Mode</p></td><td class="hb-lcd-description"><p><strong>On:</strong> TOU mode is enabled (default backup SOC: 60%). During peak periods, the product prioritizes discharging the battery to reduce peak electricity costs when the stored energy exceeds the backup SOC. During off-peak periods, the product charges the battery from the grid to achieve peak-shaving and valley-filling.<br/><strong>Off:</strong> TOU mode is disabled. The product does not follow the TOU (time-of-use) strategy and operates according to the default power supply and charging logic.<br/>Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>9</p></td><td class="hb-lcd-icon"><img alt="Parallel" class="hb-lcd-icon-art" src="assets/lcd_parallel.png"/></td><td class="hb-lcd-name"><p>Parallel</p></td><td class="hb-lcd-description"><p><strong>On:</strong> The parallel connection is set up successfully.<br/><strong>Blink:</strong> The parallel connection is setting up.<br/><strong>Off:</strong> The parallel connection is not set up.</p></td></tr><tr><td class="hb-lcd-number"><p>10</p></td><td class="hb-lcd-icon"><img alt="UPS" class="hb-lcd-icon-art" src="assets/e422a56922eb_e422a56922eb_e422a56922eb_7_UPS_Lgdgb8pvvoGwaLxSf8ec2QeHn3c.png"/></td><td class="hb-lcd-name"><p>UPS</p></td><td class="hb-lcd-description"><p>The UPS indicator remains on when grid power is available and turns off when grid power is lost.</p></td></tr><tr><td class="hb-lcd-number"><p>11</p></td><td class="hb-lcd-icon"><img alt="AC Power Indicator" class="hb-lcd-icon-art" src="assets/8be87c5a0849_8be87c5a0849_8be87c5a0849_8_AC_Power_Indicator_HFPSbvWBgosvCux69jMcuWe6nnh.png"/></td><td class="hb-lcd-name"><p>AC Power Indicator</p></td><td class="hb-lcd-description"><p>The AC output (pure sine wave) is on.</p></td></tr><tr><td class="hb-lcd-number"><p>12</p></td><td class="hb-lcd-icon"><img alt="Output Voltage and Frequency" class="hb-lcd-icon-art" src="assets/7623ef10e229_7623ef10e229_7623ef10e229_9_Output_Voltage_and_Frequency_Jh3JbmBDBoKlmOxaRJDcIMJAn6b.png"/></td><td class="hb-lcd-name"><p>Output Voltage and Frequency</p></td><td class="hb-lcd-description"><p>Displays the output voltage and frequency when the AC output is enabled via the AC power button or when the AC Extension port is supplying power. • 120V: Displayed when the product is charging from the 120V AC input while simultaneously delivering power through the AC output ports. • 120/240V: Displayed when the 240V AC output is active, or when the product is connected to a transfer switch and operating in bypass mode.</p></td></tr><tr><td class="hb-lcd-number"><p>13</p></td><td class="hb-lcd-icon"><img alt="Input Power" class="hb-lcd-icon-art" src="assets/d5100a538e96_d5100a538e96_d5100a538e96_10_Input_Power_LOAZbnxfqoHFwIxx2Myc532jnzb.png"/></td><td class="hb-lcd-name"><p>Input Power</p></td><td class="hb-lcd-description"><p>Displays the AC input power used for battery charging in watts.</p></td></tr><tr><td class="hb-lcd-number"><p>14</p></td><td class="hb-lcd-icon"><img alt="Remaining Charge Time" class="hb-lcd-icon-art" src="assets/cfb69b1ffc0b_cfb69b1ffc0b_cfb69b1ffc0b_11_Remaining_Charge_Time_KIWHbHFOvotGuBxJsxlcunSDnPf.png"/></td><td class="hb-lcd-name"><p>Remaining Charge Time</p></td><td class="hb-lcd-description"><p>Displays the remaining charging time.</p></td></tr><tr><td class="hb-lcd-number"><p>15</p></td><td class="hb-lcd-icon"><img alt="AC Wall Charging Indicator" class="hb-lcd-icon-art" src="assets/28f3cad42ae3_28f3cad42ae3_28f3cad42ae3_12_AC_Wall_Charging_Indicator_ZpOmbCjx8oYUTVxyl4JcvcTanPe.png"/></td><td class="hb-lcd-name"><p>AC Wall Charging Indicator</p></td><td class="hb-lcd-description"><p>The product is charged via the AC Input using grid power.</p></td></tr><tr><td class="hb-lcd-number"><p>16</p></td><td class="hb-lcd-icon"><img alt="Car Charging Indicator" class="hb-lcd-icon-art" src="assets/eed3299c3f6a_eed3299c3f6a_eed3299c3f6a_13_Car_Charging_Indicator_DLkibYaP1ot6d5x1S0jcUr1knlb.png"/></td><td class="hb-lcd-name"><p>Car Charging Indicator</p></td><td class="hb-lcd-description"><p>The product is charged via the DC Input (DC8020) using DC 12V (car charging).</p></td></tr><tr><td class="hb-lcd-number"><p>17</p></td><td class="hb-lcd-icon"><img alt="Solar Charging Indicator" class="hb-lcd-icon-art" src="assets/91cec82eeaa5_91cec82eeaa5_91cec82eeaa5_14_Solar_Charging_Indicator_RgAUbPXNWoRxiHxKNgkc2gqDnEb.png"/></td><td class="hb-lcd-name"><p>Solar Charging Indicator</p></td><td class="hb-lcd-description"><p>The product is charged via the DC Input (DC8020) using solar panel(s).</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>18</p></td><td class="hb-lcd-icon"><img alt="AC Expansion Indicator (Charging)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-in.png"/></td><td class="hb-lcd-name"><p>AC Expansion Indicator (Charging)</p></td><td class="hb-lcd-description"><p>The product can be charged from the grid through a Jackery Automatic Transfer Switch (ATS).</p></td></tr><tr><td class="hb-lcd-icon"><img alt="AC Expansion Indicator (Discharging)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-out.png"/></td><td class="hb-lcd-name"><p>AC Expansion Indicator (Discharging)</p></td><td class="hb-lcd-description"><p>The product supplies power to your home loads through the connected ATS.</p></td></tr><tr><td class="hb-lcd-number"><p>19</p></td><td class="hb-lcd-icon"><img alt="Transfer Switch Indicator" class="hb-lcd-icon-art" src="assets/lcd_transfer-switch.png"/></td><td class="hb-lcd-name"><p>Transfer Switch Indicator</p></td><td class="hb-lcd-description"><p><strong>On:</strong> The product is successfully connected to a transfer switch (ATS).<br/><strong>Off:</strong> The product is not connected to a transfer switch (ATS).</p></td></tr><tr><td class="hb-lcd-number"><p>20</p></td><td class="hb-lcd-icon"><img alt="EV Charging" class="hb-lcd-icon-art" src="assets/lcd_ev-charging.png"/></td><td class="hb-lcd-name"><p>EV Charging</p></td><td class="hb-lcd-description"><p>The Ground Adapter (sold separately) is connected to the product successfully.</p></td></tr><tr><td class="hb-lcd-number"><p>21</p></td><td class="hb-lcd-icon"><img alt="Battery Power Indicator" class="hb-lcd-icon-art" src="assets/85921a9ad7fb_85921a9ad7fb_85921a9ad7fb_17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"/></td><td class="hb-lcd-name"><p>Battery Power Indicator</p></td><td class="hb-lcd-description"><p>When the product is being charged, the orange circle around the battery percentage will light up in sequence. When charging other devices, the orange circle will stay on.</p></td></tr><tr><td class="hb-lcd-number"><p>22</p></td><td class="hb-lcd-icon"><img alt="Low Battery Indicator" class="hb-lcd-icon-art" src="assets/c7862a87e742_c7862a87e742_c7862a87e742_19_Low_Battery_Indicator_KDk9bhs8poHUBdx96PLckPganhd.png"/></td><td class="hb-lcd-name"><p>Low Battery Indicator</p></td><td class="hb-lcd-description"><p><strong>On:</strong> The battery level is below 20%.<br/><strong>Blink:</strong> The battery level is below 5%.<br/><strong>Off:</strong> The battery level is not below 20% or the product is charging.</p></td></tr><tr><td class="hb-lcd-number"><p>23</p></td><td class="hb-lcd-icon"><img alt="Remaining Battery Percentage" class="hb-lcd-icon-art" src="assets/747147be99d7_747147be99d7_747147be99d7_18_Remaining_Battery_Percentage_VkJcbUDbUoYC1hxrU6rc168OnJe.png"/></td><td class="hb-lcd-name"><p>Remaining Battery Percentage</p></td><td class="hb-lcd-description"><p>Displays the remaining battery percentage.</p></td></tr><tr><td class="hb-lcd-number"><p>24</p></td><td class="hb-lcd-icon"><img alt="Smart Meter indicator" class="hb-lcd-icon-art" src="assets/lcd_smart-meter.png"/></td><td class="hb-lcd-name"><p>Smart Meter indicator</p></td><td class="hb-lcd-description"><p><strong>On:</strong> A smart meter is online.<br/><strong>Off:</strong> No smart meter is added to the system, or the smart meter is offline.</p></td></tr><tr><td class="hb-lcd-number"><p>25</p></td><td class="hb-lcd-icon"><img alt="Discharge Timer" class="hb-lcd-icon-art" src="assets/6aab9a14900a_6aab9a14900a_6aab9a14900a_20_Discharge_Timer_DHPMbkjSWoiuALxJyJ8cWyQOn0e.png"/></td><td class="hb-lcd-name"><p>Discharge Timer</p></td><td class="hb-lcd-description"><p><strong>On:</strong> A discharge timer is set.<br/><strong>Off:</strong> No discharge timer is set.<br/>Enable/disable this feature in the Jackery App. The setting is not retained when the device is powered off.</p></td></tr><tr><td class="hb-lcd-number"><p>26</p></td><td class="hb-lcd-icon"><img alt="Connected Batteries" class="hb-lcd-icon-art" src="assets/lcd_connected-batteries.png"/></td><td class="hb-lcd-name"><p>Connected Batteries</p></td><td class="hb-lcd-description"><p>Displays the quantity of battery packs if any are connected.</p></td></tr><tr><td class="hb-lcd-number"><p>27</p></td><td class="hb-lcd-icon"><img alt="Energy Saving Mode" class="hb-lcd-icon-art" src="assets/c4b830c769a3_c4b830c769a3_c4b830c769a3_22_Energy_Saving_Mode_O4Jdb5pUQoCBAqx0sfQcm9Nbntd.png"/></td><td class="hb-lcd-name"><p>Energy Saving Mode</p></td><td class="hb-lcd-description"><p><strong>On:</strong> Energy Saving Mode is enabled.<br/><strong>Off:</strong> Energy Saving Mode is disabled.</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>28</p></td><td class="hb-lcd-icon"><img alt="High Temperature Indicator" class="hb-lcd-icon-art" src="assets/f548c6504f49_f548c6504f49_f548c6504f49_23_High_Temperature_Indicator_UmkEbOgCKoKyxoxDSINcfO6LnQd.png"/></td><td class="hb-lcd-name"><p>High Temperature Indicator</p></td><td class="hb-lcd-description"><p>High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</p></td></tr><tr><td class="hb-lcd-icon"><img alt="Low Temperature Indicator" class="hb-lcd-icon-art" src="assets/bdbf602db74a_bdbf602db74a_bdbf602db74a_24_Low_Temperature_Indicator_JDMEbD96noSbyWxbOnVcgip1nab.png"/></td><td class="hb-lcd-name"><p>Low Temperature Indicator</p></td><td class="hb-lcd-description"><p>Low temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</p></td></tr><tr><td class="hb-lcd-number"><p>29</p></td><td class="hb-lcd-icon"><img alt="Fault code" class="hb-lcd-icon-art" src="assets/lcd_fault-code.png"/></td><td class="hb-lcd-name"><p>Fault code</p></td><td class="hb-lcd-description"><p>A product error has occurred. Please refer to the Troubleshooting section for details.</p></td></tr><tr><td class="hb-lcd-number"><p>30</p></td><td class="hb-lcd-icon"><img alt="Output Power" class="hb-lcd-icon-art" src="assets/58c1d3604ca7_58c1d3604ca7_58c1d3604ca7_26_Output_Power_PviebR618oofvKxcKVRcHLlInqd.png"/></td><td class="hb-lcd-name"><p>Output Power</p></td><td class="hb-lcd-description"><p>Displays the total output power (AC + USB) in watts. Displays OFF for 1 second before the product powers off.</p></td></tr><tr><td class="hb-lcd-number"><p>31</p></td><td class="hb-lcd-icon"><img alt="Remaining Discharge Time" class="hb-lcd-icon-art" src="assets/9b148ea95d3a_9b148ea95d3a_9b148ea95d3a_27_Remaining_Discharge_Time_JEpobf59DoBV4dxWlnxcNtIinke.png"/></td><td class="hb-lcd-name"><p>Remaining Discharge Time</p></td><td class="hb-lcd-description"><p>Displays the remaining discharging time.</p></td></tr></tbody></table></figure>

<span id="operations"></span>

# OPERATIONS

## POWER ON/OFF

<img alt="On Press once Off Press and hold for 3s 3s Default standby time: 2 hours The product will automatically shut down after 2 hours of inactivity, with no charging or discharging. *The standby time can be set in the Jackery App. When Energy Saving Mode is enabled, the product will automatically shut down after 12 hours if the AC or USB power button is ON but the product is neither charging nor discharging." src="assets/power.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## USB OUTPUT ON/OFF

<img alt="On Prerequisite: The product is powered on. Press once Off Press once" src="assets/usb.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>USB-C 100W MAX is a USB-PD Power Source 3 (PS3) high-power output port. If the connected user device or accessory does not meet safety requirements, there may be a fire risk. Before using these ports, ensure that the connected device or accessory has fire safety protection.</li><li>Only connect the Jackery HomePower 3600 Pro Max to devices or accessories that comply with clauses 6.3, 6.4, and 6.5 of IEC/EN/UL 62368-1 (or other equivalent standards).</li><li>To obtain maximum output power, use the USB-C to USB-C 5A cable (20V DC/5A, 100W).</li></ul></td></tr></tbody></table>

## AC OUTPUT ON/OFF

<img alt="Prerequisite: The product is powered on. On Press once Off Press once" src="assets/ac.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## ENERGY SAVING MODE

<img alt="To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default. When the AC or USB output is turned on, the Energy Saving Mode icon will be displayed on the LCD screen. If no device is connected or the connected device's power consumption is below a certain threshold (25W AC output or 2W USB output) for 12 hours, the product will automatically turn off the outputs. Please set the Energy Saving Mode duration in the Jackery App. To disable the energy saving mode, press and hold both the AC power button and the main power button for more than 3 seconds. Once Energy Saving Mode is disabled, the icon will no longer appear on the LCD screen, and the product will not automatically turn off the AC or USB output. When powering low-power devices (AC ≤ 25 W or DC/USB ≤ 2 W), disable Energy Saving Mode to prevent the output from shutting down automatically during operation. Main power button AC power button On/Off 3s Press and hold for 3s" src="assets/energy_saving.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>Energy Saving Mode resumes its previous state after powering on. Manual switching is required for mode changes.</p></td></tr></tbody></table>

## LCD SCREEN

<figure aria-label="LCD SCREEN" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCD SCREEN" class="hb-lcd-mode-art" src="assets/lcd_device.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3"><p>Shortly On</p></td><td class="hb-lcd-mode-action"><p>Turn on</p></td><td class="hb-lcd-mode-copy"><p>Press the Main Power Button or when the product is charging.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Turn off</p></td><td class="hb-lcd-mode-copy"><p>Press the Main Power Button.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Auto-off</p></td><td class="hb-lcd-mode-copy"><p>The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.</p></td></tr><tr><td class="hb-lcd-mode-state" rowspan="3"><p>Steady On (in charging or discharging state)</p></td><td class="hb-lcd-mode-action"><p>Turn on</p></td><td class="hb-lcd-mode-copy"><p>Press the Main Power Button twice when the product is powered on.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Turn off</p></td><td class="hb-lcd-mode-copy"><p>Press the Main Power Button.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Auto-off</p></td><td class="hb-lcd-mode-copy"><p>The LCD turns off automatically after 2 hours of inactivity.</p></td></tr></tbody></table></div></figure>

<p>You can also set the screen display mode in the Jackery App.</p>

## KEY COMBINATION

<figure aria-label="Buttons / Operation / Function" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Buttons</th><th class="hb-key-operation" scope="col">Operation</th><th class="hb-key-function" scope="col">Function</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Main <strong>POWER</strong> button</p></div><span class="hb-key-button-plus"> + </span><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p><strong>USB</strong> power button</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Press and hold both for 3s</p></td><td class="hb-key-function">Reset Wi-Fi and Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Main <strong>POWER</strong> button</p></div><span class="hb-key-button-plus"> + </span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p><strong>AC</strong> power button</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Press and hold both for 3s</p></td><td class="hb-key-function">Turn on/off the Energy Saving Mode</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p><strong>USB</strong> power button</p></div><span class="hb-key-button-plus"> + </span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p><strong>AC</strong> power button</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">1s</p><p>Press and hold both for 1s</p></td><td class="hb-key-function">Turn on/off Wi-Fi and Bluetooth</td></tr></tbody></table></figure>

## AC AND DC OUTPUT RESUME FUNCTION

<p>This function memorizes the output status and automatically resumes AC and DC outputs under defined conditions.</p>

<figure aria-label="Auto Resume Conditions / Not Auto Resume Conditions" class="hb-auto-resume-composition" data-component-id="HB-TABLE-AUTO-RESUME" tabindex="0"><table class="hb-auto-resume-table"><colgroup><col class="hb-auto-resume-col"/><col class="hb-auto-resume-col"/></colgroup><thead><tr><th class="hb-auto-resume-left" scope="col">Auto Resume Conditions</th><th class="hb-auto-resume-right" scope="col">Not Auto Resume Conditions</th></tr></thead><tbody><tr><td class="hb-auto-resume-left">Power-on/Restart after shutdown or restart</td><td class="hb-auto-resume-right">Manual output off (button/App)</td></tr><tr><td class="hb-auto-resume-left" rowspan="2">Battery SOC ≥ discharge limit +10% after reaching limit</td><td class="hb-auto-resume-right">Energy Saving mode output off</td></tr><tr><td class="hb-auto-resume-right">Protection-triggered output off</td></tr><tr><td class="hb-auto-resume-left">OTA upgrade completed</td><td class="hb-auto-resume-right">Discharge timer-triggered output off</td></tr></tbody></table></figure>

<span id="ups"></span>

# UNINTERRUPTIBLE POWER SUPPLY (UPS)

<p>An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup electric power to a load when the mains grid power fails. In the event of a sudden loss of grid power, the HomePower 3600 Pro Max will automatically switch to stored power within 10 ms to keep your appliances running. In UPS mode, the unit's peak output varies with grid input voltages before power outages. The actual output power returns to the rated output power during outages.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>This product does not support 0 ms switching. Do not connect it to equipment that requires a 0 ms switching power supply, such as data servers or workstations.</li><li>Before use, please test compatibility with your device multiple times.</li><li>Do not connect loads exceeding the maximum output power of the product. Otherwise, overload protection will be triggered.</li></ul></td></tr></tbody></table>

## WITH 120V AC INPUT

<p>Connect the product to a 120V wall outlet using the AC charging cable. Press the AC power button to enable AC power delivery. Total Loads ≤1440 W: The product operates in AC bypass mode. All three AC ports (two NEMA 5-20R and one NEMA 14-50R) can be used. In this condition, the product supports 120 V input with both 120 V and 240 V outputs, and switches to battery power within 10 ms when grid power fails. If only one 120V port is required, use the left NEMA 5-20R (L1) port as the primary connection. Total Loads &gt;1440W: Each NEMA 5-20R port supports up to 1440 W, with a combined maximum of 2880 W across both ports. The NEMA 14-50R port supports up to 2880 W. All three AC ports together support a total output of up to 2880 W. When operating above 1440W with 120V AC input, the product still supports 120V/240V outputs. In this condition, the AC outputs consume battery power. If the battery becomes fully discharged, the connected load may experience overload shutdown and power interruption.</p>

<img alt="120V wall input, AC loads, and HomePower 3600 Pro Max connection diagram." src="assets/ups120.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## WITH 240V AC INPUT

<p>Connect the product to a 240V AC power supply using a Jackery 40A Charging Cable (sold separately). Press the AC power button to enable AC power delivery. All AC output ports support UPS operation under 240V input: NEMA 14-50R (240V~ 60Hz): Up to 9600W bypass output NEMA 5-20R ×2 (120V~ 60Hz): Up to 2400W per port, 4800W total bypass output The maximum total load allowed is 4000 W for a single unit and 8000 W for dual units (parallel connection). When the 240V grid power fails, the system automatically switches to battery power with a transfer time of &lt;10 ms. When the battery is depleted, all AC outputs turn off.</p>

<img alt="240V AC expansion input using a Jackery 40A Charging Cable (sold separately)." src="assets/ups240.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<span id="connections"></span>

# CONNECTIONS

## <span class="hb-heading-title">CONNECT TO BATTERY PACK(S)</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<p>This product supports up to 5 battery packs to meet the need for large power capacity. For details on how to use it, please refer to the Jackery Battery Pack 3600 User Manual.</p>

<img alt="≥ 0.66 ft (≈200 mm) ≥ 0.66 ft (≈200 mm)" src="assets/battery_packs.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>If you are using only one battery pack, you may place it in either of the following configurations:</p>

<img alt="Side-by-side placement Stacked placement ≥ 0.66 ft (≈200 mm)" src="assets/battery_placement.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>Ensure all products are powered off before connecting the HomePower 3600 Pro Max to the Jackery Battery Pack 3600.</li><li>To ensure proper operation of the product, make sure the air intake and exhaust vents on both sides are unobstructed. Leave at least 0.66 ft (≈200 mm) of space between the vents and any objects to allow for proper heat dissipation.</li></ul></td></tr></tbody></table>

## CASCADE PARALLEL CONNECTION

<p>Cascade connection allows 2 HomePower 3600 Pro Max units to operate as a combined system, increasing total output power.</p>

<h3 class="hb-source-pill-heading" id="required-accessories">Required Accessories</h3>

<p>Jackery 40A Charging Cable · Jackery Parallel Communication Cable — Sold separately</p>

<h3 class="hb-source-pill-heading" id="connection-steps">Connection Steps</h3>

<p>1. Ensure both units are powered OFF and completely disconnected from power sources. 2. Connect Parallel Communication ports on both units.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Do not skip this step. Without communication, the units cannot synchronize data and may be damaged.</p></td></tr></tbody></table>

<p>3. Connect the first unit's 240V Output Port (NEMA 14-50R) to the second unit's AC Expansion Port.</p>

<img alt="Connect first NEMA 14-50R output to the second AC expansion port, and connect both parallel communication ports." src="assets/cascade.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>System information will synchronize across both displays.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>After cascading, the total system output power via the NEMA 14-50R port of the second device is 8000W. The total load MUST NOT exceed total power.</p></td></tr></tbody></table>

## CONNECT TO EPO SWITCH

<p>The EPO (Emergency Power Off) interface is used to connect an external emergency-stop switch (prepared by the user). When an emergency occurs, pressing the EPO button immediately shuts down all AC and DC inputs and outputs. A screw terminal block is provided with the product for installing the external emergency-stop switch.</p>

<img alt="External EPO emergency-stop switch connected at the screw terminal block." src="assets/epo.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## BACKUP POWER CONNECTION

<h3 class="hb-source-pill-heading" id="connect-to-ats-sold-separately"><span class="hb-heading-title">CONNECT TO ATS</span> <span class="hb-sold-separately">SOLD SEPARATELY</span></h3>

<p>The HomePower 3600 Pro Max can supply backup power to home circuits through a Jackery Automatic Transfer Switch (ATS). For detailed installation and operation, refer to the Jackery ATS User Manual.</p>

<img alt="Lock Unlock 1 2 1 2 Power input/output cable in the ATS package" src="assets/ats_lock.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>When UPS mode is enabled on the ATS, the power station remains active and continuously consumes power. During a grid outage, the system switches to battery power within 20 milliseconds.</p></td></tr></tbody></table>

## <span class="hb-heading-title">CONNECT TO MTS</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<p>The HomePower 3600 Pro Max can be connected to a Manual Transfer Switch (MTS) to power selected home circuits. Choose the appropriate method based on your installation mode.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>All cables used in this section are sold separately or included with the separately sold MTS.</p></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="mts-installation-notice">MTS Installation Notice</h3>

<p>For optimal performance when using the HP3600 Pro Max with a Manual Transfer Switch (MTS), it is recommended that the AC input be connected to a non-GFCI protected circuit. If GFCI protection is required, it is recommended that GFCI devices be installed on the load side. This configuration helps improve system compatibility and supports reliable AC bypass operation.</p>

## SINGLE UNIT CONNECTION WITH MTS

<p>In automatic mode, the HomePower 3600 Pro Max receives AC input and provides UPS-like backup power through the MTS.</p>

<img alt="Power OFF the HomePower 1. 3600 Pro Max. Charging Cable in Connect the HomePower 2. the MTS package 3600 Pro Max to a 240V AC power supply. Connect the 240V Output 3. Port (NEMA 14-50R) to the MTS inlet. NEMA 14-50R Turn the load switch of the 4. MTS to backup. Turn ON the unit and enable 5. AC Output. Jackery 40A Charging Cable (sold separately)" src="assets/mts_single.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>When grid power is present, AC power passes through to the MTS. During a power outage, the system automatically switches to battery power within 10 milliseconds.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>Automatic switching requires the AC input to remain connected at all times.</p></td></tr></tbody></table>

## CASCADE PARALLEL CONNECTION WITH MTS

<p>When two units are connected in cascade parallel mode, the system can deliver higher output power to the MTS.</p>

<img alt="Complete the Cascade Parallel 1. Connection steps described earlier. Connect the second device’s 2. 240V Output Port (NEMA 14-50R) to the MTS inlet. Turn ON both units and enable 3. AC Output. Charging Cable in the MTS package Jackery 40A Charging Cable NEMA 14-50R (sold separately) Jackery Parallel Communication Cable (sold separately)" src="assets/mts_cascade.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>After cascading, the maximum output to the MTS is 8000W. The total load MUST NOT exceed total power.</p></td></tr></tbody></table>

<span id="charging"></span>

# CHARGING

<p>Green energy first: We advocate using green energy first. This product supports two modes of charging at the same time: solar charging and AC wall charging. When AC wall charging and solar charging are turned on at the same time, the product will give priority to solar charging, and both methods will be used to charge the battery at the maximum permissible power. Fully charge the product before its first use.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><ul><li>The recommended charging temperature for the product ranges from -4°F to 113°F (-20°C to 45°C), and the discharging temperature ranges from -4°F to 113°F (-20°C to 45°C). Operating the product beyond this temperature range may restrict its charging and discharging capabilities, or even prevent it from charging or discharging.</li><li>The charging power and battery capacity of the product may vary due to temperature fluctuations.</li></ul></td></tr></tbody></table>

## CHARGING VIA 120V AC WALL OUTLET

<img alt="Connect the AC charging cable to the AC input port of the product and a wall outlet." src="assets/charge120.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Connect the AC charging cable to the AC input port of the product and a wall outlet.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Make sure the AC charging cable is fully and securely plugged into the AC input port. An incomplete connection may cause unstable current, overheating, poor contact, or device malfunction.</p></td></tr></tbody></table>

## CHARGING VIA 240V AC INPUT

<p>The HomePower 3600 Pro Max supports charging through its 240V AC Expansion Port. Depending on your installation, the 240V AC input may come from a 240V AC outlet or from a Jackery Automatic Transfer Switch (ATS).</p>

<h3 class="hb-source-pill-heading" id="v-ac-outlet">240V AC Outlet</h3>

<img alt="Connect the product to a 240V AC power supply using a Jackery 40A Charging Cable (Sold Separately)." src="assets/charge240.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Connect the product to a 240V AC power supply using a Jackery 40A Charging Cable (Sold Separately).</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>Ensure the Jackery 40A Charging Cable is fully and securely plugged into both the 240V outlet and the AC Expansion Port.</li><li>An incomplete connection may cause unstable current, overheating, poor contact, or device malfunction.</li></ul></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="transfer-switch-ats">TRANSFER SWITCH (ATS)</h3>

<p>Connect your Jackery ATS to the product to enable charging via the Transfer Switch.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>The backup reserve setting applies in all operating modes of the ATS. When the remaining capacity of the HomePower 3600 Pro Max exceeds the configured backup reserve, charging will stop automatically.</p></td></tr></tbody></table>

<p>To charge it immediately, follow the instructions below: 1. Tap Power Station in the energe flow of the ATS dashboard. 2. On the Power Station page, tap Charge now.</p>

<img alt="ATS App STEP 1 and STEP 2 screens for Power Station and Charge now, with ATS-to-power-station connection artwork." src="assets/ats_app.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>Once the AC Expansion Port is successfully connected to an ATS, the AC Input port will no longer be used for charging. In this configuration, the HomePower 3600 Pro Max can be charged through the following ports: AC Expansion Port DC8020 Ports</p></td></tr></tbody></table>

## <span class="hb-heading-title">CHARGING VIA SOLAR PANELS</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<p>The Jackery HomePower 3600 Pro Max has two DC8020 input ports, and each supports either a direct connection to a 500W solar panel or a serial connection of three 200W solar panels via a connector. If one DC8020 input port needs to connect two or more solar panels simultaneously, please refer to the figure below for charging through the solar panel connector (sold separately, not included as standard).</p>

<img alt="SolarSaga 500 X × 2" src="assets/solar500.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="SolarSaga 200 × 6" src="assets/solar200.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Ensure that the input voltage for both DC input ports is the same. Failure to do so may damage the product. For example: Use the same model of Jackery solar panels and the same number of panels when connecting solar panels to both DC8020 Input ports. Do not charge the product using both a car charger and a solar panel simultaneously. Doing so may blow the car fuse or result in charging failure.</p></td></tr></tbody></table>

<p>It is recommended to use the Jackery solar panels to charge the product. Ensure that the working voltage (Vmp) of the solar panel is within the DC input range (16V-60V) of the HomePower 3600 Pro Max. Jackery is not responsible for any damage or loss resulting from the use of third-party solar panels.</p>

## <span class="hb-heading-title">CHARGING WITH A CAR CHARGER</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<p>This product can be charged using a 12V car charger. Ensure that the car charger and the 12V car power outlet (car cigarette lighter) provide a good connection.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car_charging" data-source-fragment-sha256="f9599ae31169819cc42790390af38e034fa626df0ca011212a46b36ffd4fb797" data-web-base-art-ref="assets/car_charging_framefree.svg" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.car-charging"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car_charging.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "car_charging", "web_replace_key": "reference.car-charging", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "c5bf094d9b0f2cd27cd5f6ac9e82e6ad413ac0c4f36441d76dcb7de7d7cfdfd4", "panel_top": 0, "panel_fill": "#ebecec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [67, 10.4, 15, 9]}, {"line": 1, "rect": [49.37, 75.12, 47.65, 10.07], "fill": "#ffffff"}]}}' src="assets/car_charging_framefree.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:67%;--hb-y:10.4%;--hb-width:15%;--hb-height:9%">Vehicle</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:49.37%;--hb-y:75.12%;--hb-width:47.65%;--hb-height:10.07%;--hb-fill:#ffffff">*The car charging cable is sold separately.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><ul><li>Please start the vehicle before charging your power station.</li><li>If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it causes non-standard operation. The Company will not be responsible for any loss caused by non-standard operation.</li><li>Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product in a 24V vehicle to avoid personal injury and property loss.</li></ul></td></tr></tbody></table>

<span id="troubleshooting"></span>

# TROUBLESHOOTING

<p>If any of the following fault codes appear, follow the listed corrective actions to resolve the issue. If the fault persists, please contact Jackery Customer Support.</p>

<figure aria-label="Error Code / Corrective Measures" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Error Code</th><th class="hb-troubleshooting-measures" scope="col">Corrective Measures</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0/F1 F2/F3</td><td class="hb-troubleshooting-measures">Restart the product.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Connect the product to loads to discharge its battery until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Charge the product via solar panels or an AC wall outlet until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures">1. Wait for the grid to normalize before charging the product via an AC wall outlet.<br/>2. Check whether the air intake and exhaust vents are blocked; ensure 0.66 ft (20 cm) clearance on both sides of the product.<br/>3. Place the product in a location that is not exposed to direct sunlight or high environmental temperatures.<br/>4. Disconnect all loads from the product. Keep the product idle and wait until the fault disappears.<br/>5. Restart the product.</td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures">1. Remove all DC inputs from the product.<br/>2. Check the working voltage (Vmp) of the connected solar panels. The product allows a maximum DC input voltage of 60V.<br/>3. Restart the product and keep it idle. Wait until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">Contact Jackery Customer Support</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">Remove the load connected to the USB ports of the product. Wait until the fault disappears.</td></tr><tr><td class="hb-troubleshooting-code">FA</td><td class="hb-troubleshooting-measures">1. Turn off the AC outputs and power off both units.<br/>2. Disconnect the cables between the units and connect the two units again.<br/>3. Restart both units and enable their AC outputs.</td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures">1. Restart the battery packs and the HP3600 Pro Max, respectively.<br/>2. If the fault persists, disconnect the battery pack from the HP3600 Pro Max and connect them again.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures">1. After the emergency condition is cleared, press the EPO button again.<br/>2. If you need to power AC or DC loads, press the AC or DC power button to re-enable the output.</td></tr></tbody></table></figure>

<span id="storage"></span>

# STORAGE

<p>Store the product in a dry, clean place with proper ventilation. Storage temperature and humidity:</p>

<ul><li>1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)</li><li>3 months: 32°F to 113°F / 0°C to 45°C (0-60%RH)</li><li>12 months: 32°F to 77°F / 0°C to 25°C (0-60%RH)</li></ul>

<p>If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 months.</p>

<span id="specifications"></span>

# SPECIFICATIONS

<h2 aria-level="2" class="hb-spec-group" role="heading">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">80Ah / 44.8V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 73.85 lbs/33.5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14.76 × 10.83 × 17.72 in / 37.5×27.5×45.0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">6000 Cycles (retained capacity ≥70% SOH)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">＜10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Inverter Topology</th><td class="manual-spec-value hb-spec-value">Isolated</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Power Factor</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entire Unit</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">INPUT PORTS</h2>

<figure aria-label="INPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Input</th><td class="manual-spec-value hb-spec-value">Charge Mode : 100-120V~ 60Hz, 15A Max, 1800W<br/>Bypass Mode<sup class="hb-spec-reference">①</sup> : 100V-120V~ 60Hz, 12A Max, 1440W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × DC8020 Ports</th><td class="manual-spec-value hb-spec-value">12-16V⎓8A Max, Double to 8A Max; 16-60V<sup class="hb-spec-reference">②</sup>⎓12A Max, Double to 24A, 1200W Max</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">OUTPUT PORTS</h2>

<figure aria-label="OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × AC (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120V~ 60Hz, 16.7A Max, 2000W per port, 4000W in Total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240V~ 60Hz, 16.7A Max, 4000W Rated, 8000W Surge peak</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Total AC Output<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000W Rated, 8000W Surge peak</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Output in Bypass Mode<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value">120V AC Input:<br/>NEMA 5-20R: 100V-120V~ 60Hz, 12A Max, 1440W Max per port, 1440W<sup class="hb-spec-reference">④</sup> in Total<br/>NEMA 14-50R: 240V~ 60Hz, 1440W<sup class="hb-spec-reference">④</sup> Max<br/>240V AC Input:<br/>NEMA 5-20R: 100V-120V~ 60Hz, 20A Max, 2400W per port, 4800W in Total<br/>NEMA 14-50R: 240V~ 60Hz, 40A Max, 9600W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-C Output</th><td class="manual-spec-value hb-spec-value">100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-A Output</th><td class="manual-spec-value hb-spec-value">18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">EXPANSION PORTS</h2>

<figure aria-label="EXPANSION PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Expansion Port</th><td class="manual-spec-value hb-spec-value">240V~ 60Hz, 16.7A Max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × DC Expansion Port</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓126A Max (Input)<br/>36.4V-50.4V⎓60A Max (Output)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">ENVIRONMENTAL SPECIFICATIONS</h2>

<figure aria-label="ENVIRONMENTAL SPECIFICATIONS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Discharge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitude</th><td class="manual-spec-value hb-spec-value">≤3000m</td></tr></tbody></table></figure>

<p>※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>

<p>① The product can charge the battery from the AC wall outlet or ATS while delivering power through the AC output ports.</p>

<p>② Indicates the permissible working voltage (Vmp) range for the solar panel that can be connected.</p>

<p>③ Indicates that two or more AC output ports work together.</p>

<p>④ When connected to loads higher than 1440 W under 120V AC input, the product withdraws power from the battery to meet a total load requirement of up to 2880 W.</p>

<span id="warranty"></span>

# WARRANTY

<figure aria-label="WARRANTY" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p><strong>This warranty applies only to customers who purchase from the official Jackery website, Jackery-branded third-party platforms, or local authorized dealers.</strong></p></div><div class="hb-warranty-local-note"><p>*Warranty period and details may vary according to local laws, regulations, and authorized dealers.</p></div></figure>

## Limited Warranty

<figure aria-label="Limited Warranty" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects in workmanship and material under normal consumer use during the applicable warranty period identified in the 'Warranty Period' section below, subject to the exclusions set forth below. This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, nor authorize any person to assume for us, any other liability in connection with the sale of our products.</p></figure>

## Warranty Period

<figure aria-label="Warranty Period" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 YEARS Standard Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Standard Warranty</strong></div></div><div class="hb-warranty-period-copy"><p>The standard warranty period for Jackery HomePower 3600 Pro Max is 36 months. In each case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. The sales receipt from the first consumer purchaser, or other reasonable documentary proof, is required in order to establish the start date of the warranty period.</p></div></div><div aria-label="2 YEARS Extended Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Extended Warranty</strong></div></div><div class="hb-warranty-period-copy"><p>To activate the Warranty Extension, you must register your product online or contact our customer service team at hello@jackery.com to extend the standard warranty period.</p></div></div></div></figure>

## Repair or replacement

<figure aria-label="Repair or replacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the applicable warranty period due to a defect in workmanship or materials. The repaired/replaced product assumes the remaining warranty of the original date of purchase.</p></figure>

## Limited to Original Consumer Buyer

<figure aria-label="Limited to Original Consumer Buyer" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable to any subsequent owner.</p></figure>

## Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>Jackery's warranty does not apply to:</p><ul><li>Any product that has been misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as authorized in Jackery's current product literature.</li><li>Attempted repair by anyone other than an authorized facility.</li><li>Any product purchased through an online auction house.</li><li>Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within seven days after you purchase the product and at least once every 6 months thereafter.</li></ul></figure>

## Interpretation Rights

<figure aria-label="Interpretation Rights" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery reserves the right to the final interpretation of the above after-sales policy.</p></figure>

<span id="app"></span>

# APP SETUP

## 1. Download the App and log in

<figure aria-label="1. Download the App and log in" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Search for "Jackery" in Google Play or the App Store to install the App. After that, you can register and log in.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternatively, scan the QR code below to download and install the App.</p></div></div></div><div class="hb-app-download-semantic"><img alt="Jackery App download: App Store and Google Play; QR download." class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

## 2. Add device

<p>2.1 Click the <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> button to add your device;</p>

<p>2.2 Press the <strong>POWER</strong> button on the device to turn on. The Wi-Fi and Bluetooth icons on the device flash to indicate that the device has entered the network configuration mode. Tap the <strong>"Icon Flashed"</strong> button, and allow the App to connect to nearby devices and enable Bluetooth permissions.</p>

<img alt="2.2 2.1" class="hb-app-add-device-phone-art hb-app-phone-pair" src="assets/app_add.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="Main Power Button USB Power AC Power Button Button" src="assets/app_control.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>After the device is turned on and not connected to the App within 2 hours, it will automatically turn off Wi-Fi and Bluetooth. You must then press and hold the USB power button and the AC power button to turn on Wi-Fi and Bluetooth again.</p></td></tr></tbody></table>

<p>2.3 After tapping the searched device icon, the App automatically connects the device via Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>If the message "the device has been bound" appears during the binding process, the following two ways can be used for connection:</p><ul><li>The device owner will share this device with other users through the App.</li><li>Press and hold the POWER button and USB power button for 3 seconds to reset the device's Wi-Fi and Bluetooth, and then re-bind the device.</li></ul></td></tr></tbody></table>

<p>2.4 After the device is successfully connected, enter your Wi-Fi password and tap the OK button.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTE</td><td class="manual-callout-body"><p>Please select a Wi-Fi network in 2.4 GHz band. The device does not support a Wi-Fi network in the 5 GHz band.</p></td></tr></tbody></table>

<p>2.5 After the device is successfully added to the App, the Wi-Fi icon on the device will always be on.</p>

<img alt="HomePower 3600 Pro Max HP3600 Pro Max 2.3 2.4 2.5 The above screenshots are for reference only." class="hb-app-add-device-phone-art hb-app-phone-trio" src="assets/app_result.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>The Jackery app can connect to only one power station via Bluetooth at a time. Returning to the device list automatically disconnects Bluetooth. Tap the power station in the list again to reconnect automatically.</p></td></tr></tbody></table>

## 3. Unbind the device

<p>Click the Settings icon in the upper right corner of the main interface of the device to open the settings page, and click the Unbind button at the bottom of the page to unbind the device.</p>

## 4. Notes

### 4.1 To turn on Wi-Fi & Bluetooth:

<ul><li>Wi-Fi and Bluetooth are automatically turned on after the device is on, and the Wi-Fi and Bluetooth icons on the screen light up.</li><li>Hold the USB power button and the AC power button at the same time until the Wi-Fi &amp; Bluetooth icons on the screen light up.</li></ul>

### 4.2 To turn off Wi-Fi & Bluetooth:

<ul><li>Hold the USB power button and the AC power button at the same time until the Wi-Fi and Bluetooth icons on the screen are off.</li><li>Wi-Fi and Bluetooth will be automatically turned off if no device is connected within 2 hours.</li></ul>

### 4.3 To reset Wi-Fi & Bluetooth:

<p>Hold the POWER button and USB power button at the same time for 3 seconds to reset Wi-Fi and Bluetooth to factory settings. The connected App account will be unbound.</p>

<span id="ess"></span>

# SMART HOME BACKUP SYSTEM (AC ESS)

<p>Model: HB3600C-TS05A</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">WARNING</td><td class="manual-callout-body"><p>RISK OF ELECTRIC SHOCK. ALWAYS ENSURE THAT ALL ELECTRICAL EQUIPMENT IS SAFELY DE-ENERGIZED BEFORE COMMENCING WORK.</p></td></tr></tbody></table>

<p>Use the power input/output cable in the ATS package to connect the HomePower 3600 Pro Max AC expansion port to the ATS AC input/output port. Use the expansion cable included with the battery pack package to connect the HomePower 3600 Pro Max to the battery pack, to connect its DC expansion port (A) to the battery pack's DC expansion port (B).</p>

<img alt="JHP-3600C AC expansion port to JA-TS05A ATS, and DC expansion port A to battery pack port B." src="assets/ess_connection.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Power input/output cable in the ATS package</p>

<p>Expansion cable in the battery pack package</p>

<p>For detailed installation and connection instructions, refer to the user manuals for the ATS and battery pack.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">CAUTION</td><td class="manual-callout-body"><p>Smart Home Backup System (AC ESS) Installation Position</p><ul><li>Indoor installation.</li><li>The area is completely waterproof.</li><li>The wall is flat and level.</li><li>Ambient temperature range: -4°F to 113°F / -20°C to 45°C.</li><li>The temperature and humidity are maintained at a constant level.</li><li>Install in a well-ventilated place.</li><li>Do not place in an area within the reach of children or pets.</li><li>The installation area shall avoid direct sunlight.</li><li>No flammable or explosive materials close to inverter and battery.</li></ul></td></tr></tbody></table>

<span id="ess-specifications"></span>

# SPECIFICATIONS — SMART HOME BACKUP SYSTEM

<p>Model: JHP-3600C</p>

<h2 aria-level="2" class="hb-spec-group" role="heading">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">80Ah / 44.8V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 73.85 lbs/33.5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14.76 × 10.83 × 17.72 in / 37.5×27.5×45.0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">6000 Cycles (retained capacity ≥70% SOH)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">＜10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Inverter Topology</th><td class="manual-spec-value hb-spec-value">Isolated</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Power Factor</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entire Unit</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">INPUT PORTS</h2>

<figure aria-label="INPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Input</th><td class="manual-spec-value hb-spec-value">Charge Mode : 100-120V~ 60Hz, 15A Max, 1800W<br/>Bypass Mode<sup class="hb-spec-reference">①</sup> : 100V-120V~ 60Hz, 12A Max, 1440W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × DC8020 Ports</th><td class="manual-spec-value hb-spec-value">12-16V⎓8A Max, Double to 8A Max; 16-60V<sup class="hb-spec-reference">②</sup>⎓12A Max, Double to 24A, 1200W Max</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">OUTPUT PORTS</h2>

<figure aria-label="OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × AC (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120V~ 60Hz, 16.7A Max, 2000W per port, 4000W in Total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240V~ 60Hz, 16.7A Max, 4000W Rated, 8000W Surge peak</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Total AC Output<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000W Rated, 8000W Surge peak</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Output in Bypass Mode<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value">120V AC Input:<br/>NEMA 5-20R: 100V-120V~ 60Hz, 12A Max, 1440W Max per port, 1440W⁴ in Total<br/>NEMA 14-50R: 240V~ 60Hz, 1440W⁴ Max<br/>240V AC Input:<br/>NEMA 5-20R: 100V-120V~ 60Hz, 20A Max, 2400W per port, 4800W in Total<br/>NEMA 14-50R: 240V~ 60Hz, 40A Max, 9600W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-C Output</th><td class="manual-spec-value hb-spec-value">100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × USB-A Output</th><td class="manual-spec-value hb-spec-value">18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">EXPANSION PORTS</h2>

<figure aria-label="EXPANSION PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Expansion Port</th><td class="manual-spec-value hb-spec-value">240V~ 60Hz, 16.7A Max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × DC Expansion Port</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓126A Max (Input)<br/>36.4V-50.4V⎓60A Max (Output)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">ENVIRONMENTAL SPECIFICATIONS</h2>

<figure aria-label="ENVIRONMENTAL SPECIFICATIONS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Discharge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitude</th><td class="manual-spec-value hb-spec-value">≤3000m</td></tr></tbody></table></figure>

<p>※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.</p>

<p>① The product can charge the battery from the AC wall outlet or ATS while delivering power through the AC output ports.</p>

<p>② Indicates the permissible working voltage (Vmp) range for the solar panel that can be connected.</p>

<p>③ Indicates that two or more AC output ports work together.</p>

<p>④ When connected to loads higher than 1440 W under 120V AC input, the product withdraws power from the battery to meet a total load requirement of up to 2880 W.</p>

# <span class="hb-heading-title">Jackery Battery Pack 3600</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<h2 aria-level="2" class="hb-spec-group" role="heading">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 3600</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JBP-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">80Ah/44.8Vdc (3584Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 55.1 lbs/25 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14.8 x 12.5 x 9.0 in/37.5 x 31.7x 22.9 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">6000 cycles to 70%+ capacity</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">INPUT/OUTPUT PORTS</h2>

<figure aria-label="INPUT/OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓60A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓100A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1160A/860μs</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Discharge Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr></tbody></table></figure>

# <span class="hb-heading-title">Jackery Automatic Transfer Switch</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<h2 aria-hidden="true" aria-level="2" class="hb-spec-group hb-source-hidden-heading" role="heading">Jackery Automatic Transfer Switch</h2>

<figure aria-label="Jackery Automatic Transfer Switch" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Automatic Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JA-TS05A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Voltage (Nominal)</th><td class="manual-spec-value hb-spec-value">120V/240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Feed-In Type</th><td class="manual-spec-value hb-spec-value">Split Phase</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Input Current</th><td class="manual-spec-value hb-spec-value">100A Grid / 84A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Output Current</th><td class="manual-spec-value hb-spec-value">100A Home Load / 33.4A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Input Short-Circuit Current</th><td class="manual-spec-value hb-spec-value">10 KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Power Consumption in Standby Mode</th><td class="manual-spec-value hb-spec-value">About 5W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Overvoltage Category</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">≤20 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Enclosure Type</th><td class="manual-spec-value hb-spec-value">Distribution Box: NEMA Type 3R<br/>Plug Box: NEMA Type 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Pollution Degree</th><td class="manual-spec-value hb-spec-value">III</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Main Circuit</th><td class="manual-spec-value hb-spec-value">2 AWG (100A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Load Circuit</th><td class="manual-spec-value hb-spec-value">2AWG-4/0AWG (100A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Communication</th><td class="manual-spec-value hb-spec-value">Wi-Fi and Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">27 x 14.4 x 5.7 in/68.5 x 36.5 x 14.4 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 23.1 lbs/10.5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Operating Temperature</th><td class="manual-spec-value hb-spec-value">-4°F to 122°F / -20°C to 50°C</td></tr></tbody></table></figure>

<span id="ess-package"></span>

## PACKAGE LIST

### Jackery HomePower 3600 Pro Max

<img alt="Jackery HomePower AC Charging Cable Screw terminal block Documents 3600 Pro Max" src="assets/ess_station_package.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

### Jackery Battery Pack 3600 — Sold separately

<img alt="Model: JBP-3600A Sold separately USER MANUAL Jackery Battery Pack 3600 CONTACT US: 1-888-502-2236 (US) hello@jackery.com www.jackery.com User Manual Jackery Battery Pack 3600 Expansion Cable" src="assets/ess_battery_package.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

### Jackery Automatic Transfer Switch — Sold separately

<img alt="Upward A scale of 1:1 Jackery Automatic Marking-off Template Power Input/Output Cable Neutral Wire Cable Gland Transfer Switch Model: JA-TS05A Model: JA-TS05A Quick Guide Jackery Automatic Transfer Switch Sold USER MANUAL INSTALLATION MANUAL Jackery Automatic Transfer Switch Jackery Automatic Transfer Switch separately CONTACT US: CONTACT US: 1-888-502-2236 (US) 1-888-502-2236 (US) hello@jackery.com hello@jackery.com www.jackery.com www.jackery.com Neutral-Ground Bonding Jumper (with screws) Owner's Manual Installation Manual Quick Start Guide" src="assets/ess_ats_package.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<span id="contact"></span>

# CONTACT US

<p>JACKERY INC.</p>

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>1-888-502-2236 (US)</p>

<p>hello@jackery.com</p>

<p>www.jackery.com</p>
