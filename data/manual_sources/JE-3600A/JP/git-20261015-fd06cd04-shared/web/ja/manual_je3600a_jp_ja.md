<style>
/* JE-3600A shared-component edition: source geometry only.
   Shared Web theme owns every table, callout, card, label and figure style.
   Each figure keeps the print's label size (container-relative), nothing else. */
#furo-main-content p > img[src*="shared-contact-"] { width: 1.25em; height: 1.25em; margin: 0 0.4em 0 0; vertical-align: -0.25em; }
#furo-main-content img[src*="manufacturer-qr"] { width: 7rem !important; height: auto !important; }
#furo-main-content :is(p, li) > img:not([src*="shared-contact-"]) { width: auto; height: 1.3em; margin: 0 0.15em; vertical-align: -0.3em; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p12"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p28"] .hb-reference-live-label { font-size: 3.3180cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p28"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p28"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p29"] .hb-reference-live-label { font-size: 2.2292cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p29"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p29"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p29"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p28"] .hb-reference-live-label { font-size: 1.4013cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p28"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p28"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p28"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-download-p28"] .hb-reference-live-label { font-size: 1.9494cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-download-reminder-p30"] .hb-reference-live-label { font-size: 1.9310cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-download-reminder-p30"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-download-reminder-p30"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label { font-size: 1.6801cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.8002cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p17"] .hb-reference-live-label[data-source-line="4"] { font-size: 0.9350cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p17"] .hb-reference-live-label { font-size: 1.9346cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p17"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p17"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-ac-p20"] .hb-reference-live-label { font-size: 1.9100cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p23"] .hb-reference-live-label { font-size: 1.6842cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p23"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p23"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9648cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p22"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p22"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p22"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p22"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.7837cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p22"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p21"] .hb-reference-live-label { font-size: 1.7844cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p21"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p21"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p21"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9617cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label { font-size: 1.6159cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9100cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p14"] .hb-reference-live-label[data-source-line="2"] { font-size: 2.8013cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="frequency-p13"] .hb-reference-live-label { font-size: 4.9266cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="frequency-p13"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="frequency-p13"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="frequency-p13"] .hb-reference-live-label[data-source-line="0"] { font-size: 1.8489cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label { font-size: 1.9690cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="7"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="8"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="9"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="10"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="11"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="12"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="13"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="14"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="15"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="16"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="17"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="18"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="19"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="20"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="21"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="0"] { font-size: 1.8307cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9048cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p10"] .hb-reference-live-label[data-source-line="14"] { font-size: 1.8413cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label { font-size: 1.3750cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="7"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="8"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="9"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="10"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="11"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="12"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="13"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="14"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="15"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="16"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="17"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="18"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="19"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="20"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="21"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="22"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="23"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="24"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="25"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="26"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="27"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="28"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="29"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="30"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="31"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="32"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="33"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="34"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="35"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="36"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.2000cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="1"] { font-size: 2.2000cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="6"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="7"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="8"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="9"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="10"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="11"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="12"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="13"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="14"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="15"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="20"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="21"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="22"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="28"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="32"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="34"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-p9"] .hb-reference-live-label[data-source-line="35"] { font-size: 1.9250cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p19"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p19"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p19"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p19"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-interrupted-p19"] .hb-reference-live-label { font-size: 1.9100cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-interrupted-p19"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p18"] .hb-reference-live-label { font-size: 1.9128cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p18"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p18"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p12"] .hb-reference-live-label[data-source-line="5"] { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ups-p16"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label { font-size: 1.6808cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.9609cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p13"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.9609cqw; }

</style>

<span id="native-p3-b18-l0-0"></span>

# 安全上のご注意

<p><strong>ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。</strong></p>

<span id="native-p3-b21-l0-0"></span>

## <span>絵表示について</span>

<p>製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。<br/>内容をよく理解してから本文をお読みください。</p>

<figure aria-label="絵表示について" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">記号</th><th class="hb-symbol-signal-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="警告" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">警告</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="注意" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">注意</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が想定される内容を示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="説明" class="hb-signal-badge"><span class="hb-signal-label">説明</span></span></td><td class="hb-symbol-signal-meaning-cell">この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期しない動作が発生する可能性があることを示しています。</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ヒント" class="hb-signal-badge"><span class="hb-signal-label">ヒント</span></span></td><td class="hb-symbol-signal-meaning-cell">文章内の重要な情報や操作のヒントを補足する内容を示しています。</td></tr></tbody></table></figure>

<span id="native-p3-b20-l0-0"></span>

## <span>絵表示の説明</span>

<figure aria-label="絵表示の説明" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="潜在的な危険やリスクについて注意喚起するために、必ずお読みください。" class="hb-symbol-art" src="assets/shared-symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">潜在的な危険やリスクについて注意喚起するために、必ずお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="操作の前に取扱説明書をお読みください。" class="hb-symbol-art" src="assets/shared-symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">操作の前に取扱説明書をお読みください。</td></tr><tr><td class="hb-symbol-icon"><img alt="本製品を火気の近くに置かないでください。" class="hb-symbol-art" src="assets/shared-symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">本製品を火気の近くに置かないでください。</td></tr><tr><td class="hb-symbol-icon"><img alt="小さなお子様の手の届かない場所に保管してください。" class="hb-symbol-art" src="assets/shared-symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">小さなお子様の手の届かない場所に保管してください。</td></tr><tr><td class="hb-symbol-icon"><img alt="製品を分解、改造を禁止する記号" class="hb-symbol-art" src="assets/shared-symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">製品を分解、改造を禁止する記号</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="コンセントから電源プラグを抜く記号" class="hb-symbol-art" src="assets/shared-h1-jp-unplug.svg"/></td><td class="hb-symbol-meaning">コンセントから電源プラグを抜く記号</td></tr><tr><td class="hb-symbol-icon"><img alt="製品に濡れた手で触れることを禁止する記号" class="hb-symbol-art" src="assets/shared-h1-jp-no_wet_hands.svg"/></td><td class="hb-symbol-meaning">製品に濡れた手で触れることを禁止する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="製品を濡らすことを禁止する記号" class="hb-symbol-art" src="assets/shared-h1-jp-keep_dry.svg"/></td><td class="hb-symbol-meaning">製品を濡らすことを禁止する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="行為を指示する記号" class="hb-symbol-art" src="assets/shared-h1-jp-mandatory.svg"/></td><td class="hb-symbol-meaning">行為を指示する記号</td></tr><tr><td class="hb-symbol-icon"><img alt="行為を禁止する記号" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning">行為を禁止する記号</td></tr></tbody></table></div></div></figure>

<figure aria-label="絵表示の説明" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="充電式電池のリサイクルについて 本機はリサイクル可能な充電池を内蔵しています。" class="hb-symbol-art" src="assets/shared-symbol_li_ion.svg"/></td><td class="hb-symbol-meaning"><p><strong>充電式電池のリサイクルについて</strong> </p><p>本機はリサイクル可能な充電池を内蔵しています。<br/>この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。<br/>充電池の取りはずしはお客様自身では行わないでください。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="このシンボルは、本製品を一般家庭ごみとして廃棄せず、リサイクルのために指定の回収施設に持ち込む必要があることを示しています。" class="hb-symbol-art" src="assets/shared-symbol_weee_gray_jp.svg"/></td><td class="hb-symbol-meaning">このシンボルは、本製品を一般家庭ごみとして廃棄せず、リサイクルのために指定の回収施設に持ち込む必要があることを示しています。<br/>適切な廃棄およびリサイクルは、環境保護に役立ちます。<br/>本製品の廃棄やリサイクルについての詳細は、お住まいの自治体、廃棄物処理業者、または販売店にお問い合わせください。</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="電池および蓄電池は家庭ごみと一緒に廃棄してはいけません。" class="hb-symbol-art" src="assets/shared-battery-weee.png"/></td><td class="hb-symbol-meaning">電池および蓄電池は家庭ごみと一緒に廃棄してはいけません。<br/>消費者の皆様は、有害物質の有無にかかわらず、すべての電池および蓄電池を指定された収集場所で廃棄することが法律で義務付けられています。<br/>使用済みの電池および蓄電池は、お近くの収集拠点、リサイクルセンター、または購入した小売店にお持ちください。 適切な廃棄は環境に配慮したリサイクルを確保し、人間の健康と環境への潜在的な害を防ぎます。</td></tr></tbody></table></div></div></figure>

<span id="native-p4-b7-l0-0"></span>

## 警告

<figure aria-label="絵表示の説明" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="火のそばや炎天下の車内、熱器具の周辺など高温（45℃以上）になる場所で使用したり、放置しない 発熱や発火、破裂する原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>火のそばや炎天下の車内、熱器具</strong><strong>の周辺など高温（45℃以上）にな</strong><strong>る場所で使用したり、放置しない</strong> </p><p>発熱や発火、破裂する原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="強い衝撃を与えたり、投げつけたりしない 発熱や発火、破裂する原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>強い衝撃を与えたり、投げつけた</strong><strong>りしない</strong> </p><p>発熱や発火、破裂する原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="水など、液体を入れたり、濡らしたりしない 発熱や発火の原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-keep_dry.svg"/></td><td class="hb-symbol-meaning"><p><strong>水など、液体を入れたり、濡ら</strong><strong>したりしない</strong> </p><p>発熱や発火の原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="濡れた手で本体や接続するケーブルを触らない 火災や感電の原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-no_wet_hands.svg"/></td><td class="hb-symbol-meaning"><p><strong>濡れた手で本体や接続するケー</strong><strong>ブルを触らない</strong> </p><p>火災や感電の原因になります。</p></td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="端子部にケーブル以外の金属類を差し込まない 発熱や発火の原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>端子部にケーブル以外の金属類を</strong><strong>差し込まない</strong> </p><p>発熱や発火の原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="雷が鳴りだしたら、電源プラグにふれない (充電をしない) 感電の原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>雷が鳴りだしたら、電源プラグに</strong><strong>ふれない  (充電をしない)</strong> </p><p>感電の原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="各接続端子には確実に差し込む 差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。" class="hb-symbol-art" src="assets/shared-h1-jp-mandatory.svg"/></td><td class="hb-symbol-meaning"><p><strong>各接続端子には確実に差し込む</strong> </p><p>差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="接地接続は必ず、電源プラグを電源につなぐ前に行って下さい また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。" class="hb-symbol-art" src="assets/native-grounding-p4.svg"/></td><td class="hb-symbol-meaning"><p><strong>接地接続は必ず、電源プラグを電</strong><strong>源につなぐ前に行って下さい</strong> </p><p>また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。</p></td></tr></tbody></table></div></div></figure>

<span id="native-p5-b14-l0-0"></span>

## 警告

<figure aria-label="警告" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="万が一、次のような異常が発生したときはすぐに使用をやめる" class="hb-symbol-art" src="assets/shared-h1-jp-unplug.svg"/></td><td class="hb-symbol-meaning"><p><strong>万が一、次のような異常が発生したときはすぐに使用をやめる</strong> </p><ul><li><p>煙が出ている、異臭がする </p></li><li><p>落としたり、破損したとき  </p></li><li><p>異音がする  </p></li><li><p>内部に水や異物が入ったとき</p></li><li><p>電源コード (AC充電ケーブル)  が傷んだとき </p></li></ul><p>このような異常が発生したまま使用していると、火災や感電の原因になります。<br/>すぐにAC充電ケーブルをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。</p><p><strong>万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸</strong><strong>しにしてください。</strong> </p><p>煙が出なくなることを確認してからカスタマーサポートにご連絡ください。<br/>お客様による修理は危険ですので絶対におやめください。</p></td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="分解、改造しない" class="hb-symbol-art" src="assets/shared-symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning"><p><strong>分解、改造しない</strong> </p><p>故障、発熱、火災·感電の原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="表示された電源電圧以外で使用しない" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>表示された電源電圧以外で使用しない</strong> </p><p>故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="付属品と本製品が破損した場合は、ご自身で修理をしない" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><strong>付属品と本製品が破損した場合は、ご自身で修理をしない</strong></td></tr></tbody></table></div></div></figure>

<span id="native-p5-b15-l0-0"></span>

## 注意

<figure aria-label="注意" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="本製品の上に物を載せたり、不安定な場所に置かない" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>本製品の上に物を載せたり、不安定な場所に置かない</strong> </p><p>倒れたり、落ちたりしてけがの原因になります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><strong>データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を</strong><strong>及ぼしうる用途でのご使用はお控えください。次のようなような機器では、万が一</strong><strong>使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定されます。</strong><ul><li><p>医療機器や使用上、生命に関わるような機器 </p></li><li><p>社会的、公共的に重要な機器など </p></li><li><p>重要な事業用機器など</p></li></ul></td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">記号</th><th class="hb-symbol-meaning-heading" scope="col">意味</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="心臓にペースメーカーを装着している方は使用しない" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><p><strong>心臓にペースメーカーを装着している方は使用しない </strong> </p><p>ペースメーカーが、本製品の影響を受ける恐れがあります。</p></td></tr><tr><td class="hb-symbol-icon"><img alt="格納式ハンドルを使用してJackery ポータブル電源 3600 Plus を移動するときは、" class="hb-symbol-art" src="assets/shared-h1-jp-prohibited.svg"/></td><td class="hb-symbol-meaning"><strong>格納式ハンドルを使用してJackery ポータブル電源 3600 Plus を移動するときは、</strong><strong>積み重ねたり、上に他の物を置いたりしないでください。落下して怪我をする場合</strong><strong>があります。</strong></td></tr></tbody></table></div></div></figure>

<span id="native-p6-b27-l0-0"></span>

# 使用上のご注意

<p>Jackery ポータブル電源 3600 Plusは、定格出力3000Wです。通常時で消費電力が3000Wまでの機器に給電ができるため、多くの電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品（掃除機、ポンプ、冷蔵庫、電動丸ノコ、エアコン、洗濯機、電子レンジ、ドライヤーなど)は、起動時に「誘導負荷」が発生し、公称電力の3~7倍の電力が必要となります。<br/>定格出力3000Wは、一定の電力で動く機器への出力可能範囲を指しています。<br/>3000Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断することがあります。<br/>またAC出力ポート5つ搭載されておりますが、2つ同時にご利用頂く場合、合計して3000W以内であることをご確認の上ご利用ください。</p>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/shared-h1-jp-warning_triangle.svg"/>ご注意</span></td><td class="manual-callout-body"><p>始動電力が出力上限値( 定格出力) を大幅に超える可能性のある製品のご利用や、定格出力を超え給電がストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。</p></td></tr></tbody></table>

<span id="native-p6-b9-l0-0"></span>

## ■ 給電に関する注意事項

<p>出力上限値を超える電化製品は使用しないでください。</p>

<ul><li><p>特に、始動電力が公称電力の3~7 倍になる誘導負荷（ポンプ、ヒーター、掃除機、冷蔵庫、エアコン、電気丸ノコなどの電動道具、洗濯機、電子レンジなど）の使用にはご注意ください。</p></li><li><p>接続機器の消費電力が本製品の出力範囲内であることをご確認の上、出力ボタンを押してください。</p></li><li><p>給電中、機器の制御や環境により、急速充電にならない・給電できない場合があります。</p></li><li><p>充電または給電中、ラジオ・チューナー・テレビなどに雑音が入る場合があります。その際は、それらの機器から離してご使用ください。</p></li></ul>

<span id="native-p6-b18-l0-0"></span>

## ■ 使用環境について

<ul><li><p>本製品は防塵・防水仕様ではありません。ほこり、水、海水などがかからないようご注意ください。</p></li><li><p>ほこりの多い場所や高温多湿の場所での充電・使用・放置は避けてください。</p></li><li><p>平坦で安定した場所に設置し、不安定な場所に置かないでください。</p></li><li><p>本製品の通風孔は、安全上絶対にふさがないでください。各面から5cm 以上スペースを確保してください。</p></li><li><p>充電・給電中は本体が温かくなります。周囲に物を置かないでください。</p></li></ul>

<span id="native-p7-b7-l0-0"></span>

## ■ 接続時の注意事項

<ul><li><p>ケーブルを接続する際は、まっすぐに差し込んでください。</p></li><li><p>抜く際は必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げたりしないでください。</p></li></ul>

<span id="native-p7-b11-l0-0"></span>

## ■ お手入れについて

<ul><li><p>本体が汚れた場合は、電源プラグを抜いた状態で、柔らかい布で乾拭きしてください。</p></li><li><p>汚れがひどい場合は、水または薄めた中性洗剤で拭き取ってください。</p></li><li><p>シンナーやベンジンなどの使用は絶対に使わないでください。</p></li></ul>

<span id="native-p7-b15-l0-0"></span>

## ■ 入出力・温度・表示に関するご注意

<ul><li><p>接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。</p></li><li><p>本機は -20°C~45°C の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は-20°C~45°C で行えます。</p><ul><li><p>動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。</p></li><li><p>温度異常マークが表示された場合は、本製品を2 時間以上、動作温度範囲内の環境に置いてください。</p></li></ul></li><li><p>容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。</p></li></ul>

<span id="native-p7-b6-l0-0"></span>

# 免責事項

<ul><li><p>火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用により生じた損害に関して、当社は一切責任を負いません。</p></li><li><p>付属品と本製品が破損した場合は、ご自身で修理を行わないでください。ご自身で分解・修理したことにより生じた損害に関し、当社は一切責任を負いません。</p></li><li><p>保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。</p></li><li><p>取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。</p></li><li><p>本製品の使用、または使用不能から発生する付随的な損害( 事業利益損失含む)、当社が関与しない接続機器との組み合わせによる誤動作などから生じた損害に関して、当社は一切の責任を負いません。</p></li><li><p>本製品は病院仕様のシーパップ（CPAP）、エクモ（ECMO）、ペースメーカなど、身の安全に関わる医療救急機械の電源としての使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。上記設備の使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。</p></li></ul>

<span id="native-p8-b1-l0-0"></span>

# 同梱品

<figure aria-label="同梱品" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="three-card-responsive"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="本体" class="hb-inbox-art" src="assets/inbox-p8-card-1.svg"/><div class="hb-inbox-label"><p>本体</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC充電ケーブル" class="hb-inbox-art" src="assets/inbox-p8-card-2.svg"/><div class="hb-inbox-label"><p>AC充電ケーブル</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="取扱説明書一式" class="hb-inbox-art" src="assets/inbox-p8-card-3.svg"/><div class="hb-inbox-label"><p>取扱説明書一式</p></div></li></ol></figure>

<p><span>※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。</span></p>

<p><span>※ AC充電ケーブルは、同梱されている本体以外には使用しないでください。</span></p>

<p><span>※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。</span><br/><span>サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。</span></p>

<p><strong>本機の仕様および外観は、改善のため予告なく変更することがあります。</strong></p>

<span id="native-p9-b3-l0-0"></span>

# 各部の名称

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-p9" data-source-fragment-sha256="3d59e955d750d5b9199aae8fa5a8bac0d597a1fc56968349eada407bd5d3a5c8" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-p9.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-p9.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.4736%;--hb-y:43.2909%;--hb-width:7.9687%;--hb-height:2.2908%"><strong>右側面</strong></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.4739%;--hb-y:2.0365%;--hb-width:5.4688%;--hb-height:2.2908%"><strong>正面</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.6206%;--hb-y:17.3384%;--hb-width:18.7531%;--hb-height:3.0067%">5V⎓3A, 9V⎓3A, 12V⎓3A,  </span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.6206%;--hb-y:18.7254%;--hb-width:20.6766%;--hb-height:3.0067%">15V⎓3A, 20V⎓5A，最大100W</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.6206%;--hb-y:24.4424%;--hb-width:7.5672%;--hb-height:3.0067%">5-6V⎓3A, </span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.6206%;--hb-y:25.8295%;--hb-width:23.0625%;--hb-height:3.0067%">6-9V⎓2A, 9-12V⎓1.5A，最大18W</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:85.1775%;--hb-y:18.1828%;--hb-width:13.8584%;--hb-height:2.0604%"><strong>AC出力ポート</strong></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:82.3468%;--hb-y:20.062%;--hb-width:17.5684%;--hb-height:2.0604%"><strong>（NEMA 5-20R）</strong></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:84.6965%;--hb-y:29.5508%;--hb-width:13.9%;--hb-height:2.0604%"><strong>AC出力ボタン</strong></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.6287%;--hb-y:29.5508%;--hb-width:15.5516%;--hb-height:2.0604%"><strong>USB出力ボタン</strong></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.6287%;--hb-y:16.0316%;--hb-width:17.7566%;--hb-height:2.0604%"><strong>USB-C出力ポート</strong></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.6287%;--hb-y:23.149%;--hb-width:17.7216%;--hb-height:2.0604%"><strong>USB-A出力ポート</strong></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:82.5243%;--hb-y:4.3743%;--hb-width:16.5578%;--hb-height:2.0604%"><strong>LCDディスプレイ</strong></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:85.1778%;--hb-y:9.2649%;--hb-width:13.8584%;--hb-height:2.0604%"><strong>AC出力ポート</strong></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:82.6162%;--hb-y:11.1441%;--hb-width:16.3019%;--hb-height:2.0604%"><strong>(NEMA L5-30R)</strong></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:0.6287%;--hb-y:12.9716%;--hb-width:13.2744%;--hb-height:2.0604%"><strong>主電源ボタン</strong></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:77.1446%;--hb-y:13.2098%;--hb-width:21.7734%;--hb-height:1.5996%">100V~ 50Hz/60Hz, 定格3000W</span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:76.7571%;--hb-y:22.2132%;--hb-width:21.7734%;--hb-height:1.5996%">100V~ 50Hz/60Hz, 定格2000W</span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:84.9821%;--hb-y:23.6002%;--hb-width:13.8986%;--hb-height:1.5996%">4ポート合計3000W </span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:85.9149%;--hb-y:24.9872%;--hb-width:12.6156%;--hb-height:1.5996%">(瞬間最大6000W)</span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:84.9513%;--hb-y:76.973%;--hb-width:13.8584%;--hb-height:2.0604%"><strong>AC入力ポート</strong></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:84.3848%;--hb-y:67.6584%;--hb-width:14.0446%;--hb-height:2.0604%"><strong>DC入力ポート</strong></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:86.5044%;--hb-y:69.5376%;--hb-width:12.804%;--hb-height:2.0604%"><strong>（DC8020）</strong></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:74.1008%;--hb-y:78.9951%;--hb-width:25.0876%;--hb-height:1.5996%">100V-120V~ 50Hz/60Hz, 最大15A，</span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:90.0727%;--hb-y:80.3821%;--hb-width:8.4344%;--hb-height:1.5996%">最大1500W</span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:84.8055%;--hb-y:70.9682%;--hb-width:13.7015%;--hb-height:3.0067%">PV：16V-60V⎓12A, </span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:78.3696%;--hb-y:73.0476%;--hb-width:20.1375%;--hb-height:1.5996%">2ポート最大24A，最大1000W</span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:67.7789%;--hb-y:73.7423%;--hb-width:30.7279%;--hb-height:3.0067%">ｼｶﾞｰｿｹｯﾄ ：12V-16V⎓最大8A, 2ポート最大8A</span><span class="hb-reference-live-label" data-source-line="28" style="--hb-x:0.4987%;--hb-y:72.9383%;--hb-width:18.3015%;--hb-height:2.0604%"><strong>DC拡張ポート端子</strong></span><span class="hb-reference-live-label" data-source-line="29" style="--hb-x:0.5165%;--hb-y:75.1497%;--hb-width:16.1797%;--hb-height:1.5996%">バッテリーパックに接続</span><span class="hb-reference-live-label" data-source-line="30" style="--hb-x:0.6204%;--hb-y:64.837%;--hb-width:30.6031%;--hb-height:1.5996%">出力：100V~ 50Hz/60Hz，30A，最大3000W，</span><span class="hb-reference-live-label" data-source-line="31" style="--hb-x:0.6204%;--hb-y:66.224%;--hb-width:11.9094%;--hb-height:1.5996%">瞬間最大6000W </span><span class="hb-reference-live-label" data-source-line="32" style="--hb-x:0.6206%;--hb-y:61.0152%;--hb-width:13.8584%;--hb-height:2.0604%"><strong>AC拡張ポート</strong></span><span class="hb-reference-live-label" data-source-line="33" style="--hb-x:0%;--hb-y:63.1298%;--hb-width:13.6031%;--hb-height:1.5996%">（2台を並列接続）</span><span class="hb-reference-live-label" data-source-line="34" style="--hb-x:0.6206%;--hb-y:92.0443%;--hb-width:8.8887%;--hb-height:2.0604%"><strong>ホイール</strong></span><span class="hb-reference-live-label" data-source-line="35" style="--hb-x:0.3509%;--hb-y:49.0419%;--hb-width:22.5166%;--hb-height:2.0604%"><strong>リトラクタブルハンドル</strong></span><span class="hb-reference-live-label" data-source-line="36" style="--hb-x:0.4816%;--hb-y:51.0498%;--hb-width:27.8236%;--hb-height:1.5996%">ボタンを押し、引っ張ると長さが伸びます.</span></div></div></figure>

<span id="native-p10-b1-l0-0"></span>

# 液晶画面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map-p10" data-source-fragment-sha256="36517f255e51912ea6cbbebbd35d8af8c21cfcd2df151c10887cea276abe4560" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map-p10.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map-p10.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:96.0404%;--hb-y:43.351%;--hb-width:2.014%;--hb-height:6.2379%">21</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:95.8178%;--hb-y:56.0269%;--hb-width:2.4952%;--hb-height:6.4336%">22</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:3.5173%;--hb-y:43.8624%;--hb-width:1.5198%;--hb-height:6.6033%">9</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:2.8991%;--hb-y:57.2342%;--hb-width:2.4452%;--hb-height:6.6033%">10</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:20.0548%;--hb-y:3.7903%;--hb-width:1.1456%;--hb-height:6.6033%">1</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:19.8314%;--hb-y:92.5416%;--hb-width:1.8742%;--hb-height:6.6033%">11</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:23.6322%;--hb-y:3.7912%;--hb-width:1.5099%;--hb-height:6.6033%">2</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:23.8444%;--hb-y:92.5519%;--hb-width:2.2384%;--hb-height:6.6033%">12</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:28.701%;--hb-y:92.5594%;--hb-width:2.2483%;--hb-height:6.6033%">13</span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:44.5784%;--hb-y:92.9848%;--hb-width:2.3467%;--hb-height:6.6033%">14</span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:49.1078%;--hb-y:93.0374%;--hb-width:2.268%;--hb-height:6.6033%">15</span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:53.058%;--hb-y:93.0824%;--hb-width:2.2483%;--hb-height:6.6033%">16</span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:69.5883%;--hb-y:93.1917%;--hb-width:2.2443%;--hb-height:6.6033%">18</span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:73.858%;--hb-y:93.0886%;--hb-width:2.2089%;--hb-height:6.6033%">19</span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:78.384%;--hb-y:93.1948%;--hb-width:2.6029%;--hb-height:6.2657%">20</span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:27.3729%;--hb-y:3.7912%;--hb-width:1.5198%;--hb-height:6.6033%">3</span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:30.7211%;--hb-y:3.7912%;--hb-width:1.6182%;--hb-height:6.6033%">4</span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:34.3421%;--hb-y:3.7912%;--hb-width:1.5394%;--hb-height:6.6033%">5</span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:58.7918%;--hb-y:3.9947%;--hb-width:1.441%;--hb-height:6.6033%">7</span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:74.142%;--hb-y:3.7912%;--hb-width:1.5552%;--hb-height:6.6033%">8</span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:49.6383%;--hb-y:3.7912%;--hb-width:1.5198%;--hb-height:6.6033%">6</span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:64.2432%;--hb-y:93.1917%;--hb-width:2.1301%;--hb-height:6.6033%">17</span></div></div></figure>

<figure aria-label="液晶画面" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-wifi.png"/></td><td class="hb-lcd-name"><strong>Wi-Fi</strong></td><td class="hb-lcd-description"><p><strong>オン：</strong> Wi-Fi接続済。 </p><p><strong>点滅：</strong> Wi-Fiに接続する準備ができました。 </p><p><strong>オフ：</strong> Wi-Fi接続解除済。</p></td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-bluetooth.png"/></td><td class="hb-lcd-name"><strong>Bluetooth</strong></td><td class="hb-lcd-description"><p><strong>オン：</strong> Bluetooth接続済。 </p><p><strong>点滅：</strong> Bluetoothに接続する準備ができました。 </p><p><strong>オフ：</strong> Bluetooth接続解除済。</p></td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="静音充電モード Jackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/lcd-quiet-charging.png"/></td><td class="hb-lcd-name"><p><strong>静音充電モード</strong> </p><p>Jackeryアプリで有効/無効にできます</p></td><td class="hb-lcd-description"><p><strong>オン：</strong>充電中のノイズが大幅に低減され、充電電力が低下し、充電速度が低減します。 </p><p><strong>オフ：</strong>静音充電モードが無効になっています。<br/>（Jackeryアプリで有効/無効にできます。電源オフ時も設定は保持されます。）</p></td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="バッテリー節約モード Jackeryアプリで有効/無効にできます" class="hb-lcd-icon-art" src="assets/lcd-battery-saving-native.svg"/></td><td class="hb-lcd-name"><p><strong>バッテリー節約モード</strong> </p><p>Jackeryアプリで有効/無効にできます</p></td><td class="hb-lcd-description">バッテリー節約モード設定時は、バッテリー残量が既定値に設定されるため、バッテリーの寿命を延ばすことが可能です。<br/>（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）<br/>この機能が有効な場合、本製品はSOCを較正するために、時折フル充放電サイクルを実行します。</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="自家発電モード Jackeryアプリで設定してください" class="hb-lcd-icon-art" src="assets/lcd-self-powered-native.svg"/></td><td class="hb-lcd-name"><p><strong>自家発電モード</strong> </p><p>Jackeryアプリで設定してください</p></td><td class="hb-lcd-description"><p><strong>点灯時：</strong>自家発電モードがオンになっており、太陽光エネルギーの利用を最大化し、電力会社からの電力消費を削減して電気代を節約します。 </p><p><strong>消灯時：</strong>自家発電モードがオフ、または未設定の状態です。<br/>（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</p></td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="計画充電モード Jackeryアプリで設定してください" class="hb-lcd-icon-art" src="assets/lcd-charging-plan.png"/></td><td class="hb-lcd-name"><p><strong>計画充電モード</strong> </p><p>Jackeryアプリで設定してください</p></td><td class="hb-lcd-description">Jackery ポータブル電源 3600 Plus の充電時間をカスタマイズすることで、電気料金のピーク時間とオフピーク時間に基づいた充電プランを選択。これにより月々の電気料金を削減することができます。（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="AC 拡張インジケータ" class="hb-lcd-icon-art" src="assets/lcd-parallel.png"/></td><td class="hb-lcd-name"><strong>AC 拡張インジケータ</strong></td><td class="hb-lcd-description"><p><strong>点滅：</strong>AC出力はオンになっていますが、並列接続は設定されていません。 </p><p><strong>オン：</strong>AC出力はオンになっていますが、並列接続は正常に設定されています。</p></td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="交流電源による出力マーク（正弦波)" class="hb-lcd-icon-art" src="assets/lcd-ac-power.png"/></td><td class="hb-lcd-name"><strong>交流電源による出力マ</strong><strong>ーク（正弦波)</strong></td><td class="hb-lcd-description">AC出力（純正弦波）がオンになっています。</td></tr><tr><td class="hb-lcd-number">8</td><td class="hb-lcd-icon"><img alt="出力電圧と周波数" class="hb-lcd-icon-art" src="assets/lcd-output-voltage-frequency.png"/></td><td class="hb-lcd-name"><strong>出力電圧と周波数</strong></td><td class="hb-lcd-description">出力される電圧と周波数を表示します。</td></tr><tr><td class="hb-lcd-number">9</td><td class="hb-lcd-icon"><img alt="入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-input-power.png"/></td><td class="hb-lcd-name"><strong>入力電力表示</strong></td><td class="hb-lcd-description">入力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">10</td><td class="hb-lcd-icon"><img alt="充電残り時間" class="hb-lcd-icon-art" src="assets/lcd-remaining-charge-time.png"/></td><td class="hb-lcd-name"><strong>充電残り時間</strong></td><td class="hb-lcd-description">充電残り時間を表示します。</td></tr><tr><td class="hb-lcd-number">11</td><td class="hb-lcd-icon"><img alt="AC入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-ac-wall-charging-native.svg"/></td><td class="hb-lcd-name"><strong>AC入力電力表示</strong></td><td class="hb-lcd-description">製品は、系統電力を使用し、AC入力を介して充電されます。</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="シガーソケット入力電力表示" class="hb-lcd-icon-art" src="assets/lcd-car-charging-native.svg"/></td><td class="hb-lcd-name"><strong>シガーソケット入力電</strong><strong>力表示</strong></td><td class="hb-lcd-description">製品は、DC 12V（カーチャージ）を使用し、8020入力ポートを介して充電されています。</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="ソーラー(グリーンエネルギー)充電接続" class="hb-lcd-icon-art" src="assets/lcd-solar-charging-native.svg"/></td><td class="hb-lcd-name"><strong>ソーラー(グリーンエネ</strong><strong>ルギー)充電接続</strong></td><td class="hb-lcd-description">製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。</td></tr><tr><td class="hb-lcd-number">14</td><td class="hb-lcd-icon"><img alt="バッテリーアイコン" class="hb-lcd-icon-art" src="assets/lcd-battery-power.png"/></td><td class="hb-lcd-name"><strong>バッテリーアイコン</strong></td><td class="hb-lcd-description">製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。他のデバイスの充電時には、オレンジ色の円は点灯したままになります。</td></tr><tr><td class="hb-lcd-number">15</td><td class="hb-lcd-icon"><img alt="バッテリー残量警告灯" class="hb-lcd-icon-art" src="assets/lcd-low-battery.png"/></td><td class="hb-lcd-name"><strong>バッテリー残量警告灯</strong></td><td class="hb-lcd-description"><p><strong>オン：</strong>バッテリー残量が20％未満です。 </p><p><strong>点滅：</strong>バッテリー残量が5％未満です。 </p><p><strong>オフ：</strong>製品は充電中です。</p></td></tr><tr><td class="hb-lcd-number">16</td><td class="hb-lcd-icon"><img alt="バッテリーレベルパーセントタグ" class="hb-lcd-icon-art" src="assets/lcd-remaining-battery-percentage.png"/></td><td class="hb-lcd-name"><strong>バッテリーレベルパー</strong><strong>セントタグ</strong></td><td class="hb-lcd-description">バッテリー残量を表示します。</td></tr><tr><td class="hb-lcd-number">17</td><td class="hb-lcd-icon"><img alt="バッテリーパックインジケータと接続された量" class="hb-lcd-icon-art" src="assets/lcd-connected-batteries-native.svg"/></td><td class="hb-lcd-name"><strong>バッテリーパックインジ</strong><strong>ケータと接続された量</strong></td><td class="hb-lcd-description">本製品が指定された数の3600 Plusバッテリーパックに接続されていることを示します。</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="エラーコード" class="hb-lcd-icon-art" src="assets/lcd-fault-code.png"/></td><td class="hb-lcd-name"><strong>エラーコード</strong></td><td class="hb-lcd-description">製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="高温インジケーター" class="hb-lcd-icon-art" src="assets/lcd-high-temperature-native.svg"/></td><td class="hb-lcd-name"><strong>高温インジケーター</strong></td><td class="hb-lcd-description">高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="低温インジケーター" class="hb-lcd-icon-art" src="assets/lcd-low-temperature-native.svg"/></td><td class="hb-lcd-name"><strong>低温インジケーター</strong></td><td class="hb-lcd-description">低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="省エネモード" class="hb-lcd-icon-art" src="assets/lcd-energy-saving.png"/></td><td class="hb-lcd-name"><strong>省エネモード</strong></td><td class="hb-lcd-description"><p>ACまたはUSB出力ボタンを押して出力をオンにしたとき：<br/><strong>アイコン表示：</strong>省エネモードがオンになっています。 </p><p><strong>アイコン消える：</strong>省エネモードがオフになっています。</p></td></tr><tr><td class="hb-lcd-number">21</td><td class="hb-lcd-icon"><img alt="消費電力" class="hb-lcd-icon-art" src="assets/lcd-output-power.png"/></td><td class="hb-lcd-name"><strong>消費電力</strong></td><td class="hb-lcd-description">出力電力をワットで表示します。</td></tr><tr><td class="hb-lcd-number">22</td><td class="hb-lcd-icon"><img alt="バッテリー使用可能時間" class="hb-lcd-icon-art" src="assets/lcd-remaining-discharge-time.png"/></td><td class="hb-lcd-name"><strong>バッテリー使用可能</strong><strong>時間</strong></td><td class="hb-lcd-description">接続した機器の使用可能な時間を表示します。</td></tr></tbody></table></figure>

<span id="native-p12-b3-l0-0"></span>

# 使い方

<span id="native-p12-b1-l0-0"></span>

## 主電源ボタン/オフ

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-p12" data-source-fragment-sha256="fe3bdf43aa97ec8ff56ecae12151d5a34d8ac1c77f6ca429b557a6a77ee699c5" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power-p12.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power-p12.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:4.0322%;--hb-y:79.2797%;--hb-width:92.4099%;--hb-height:13.6526%;--hb-fill:#ebebec">省エネモードがオンのとき、AC出力またはUSB出力がオンでも、12時間連続して充放電が行われない場合は、自動的に電源がオフになります。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:74.7663%;--hb-y:10.378%;--hb-width:4.747%;--hb-height:4.8226%"><strong>オン</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:74.6727%;--hb-y:24.061%;--hb-width:4.7113%;--hb-height:4.8226%"><strong>オフ</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:74.9003%;--hb-y:15.4415%;--hb-width:7.2676%;--hb-height:4.2833%">1回押す</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:74.9003%;--hb-y:28.5522%;--hb-width:11.0876%;--hb-height:4.2833%">3秒間長押し</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:79.1022%;--hb-y:34.1452%;--hb-width:2.942%;--hb-height:5.4458%">3S</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:44.7553%;--hb-y:56.2406%;--hb-width:44.4902%;--hb-height:14.758%">本製品のデフォルトの待機時間は2時間です（充電または放電がない場合、2時間後に自動的にシャットダウンします）。 待機時間はJackeryアプリで設定できます。</span></div></div></figure>

<span id="native-p12-b2-l0-0"></span>

## AC出力のオン/オフ

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output-p12" data-source-fragment-sha256="45b97f7a7aee4142ef0d8d636893d37c31157210dc5c4cac2c02d9407a036cde" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output-p12.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output-p12.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:4.0325%;--hb-y:6.4293%;--hb-width:54.2536%;--hb-height:6.7939%;--hb-fill:#ebebec"><strong>前提：</strong>主電源ボタンがオンになっていることを確認してください。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:80.3472%;--hb-y:22.3211%;--hb-width:4.747%;--hb-height:4.5697%"><strong>オン</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:80.2536%;--hb-y:35.2863%;--hb-width:4.7113%;--hb-height:4.5697%"><strong>オフ</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:80.4812%;--hb-y:27.1189%;--hb-width:7.2675%;--hb-height:4.0586%">1回押す</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:80.4812%;--hb-y:39.5389%;--hb-width:7.2675%;--hb-height:4.0586%">1回押す</span></div></div></figure>

<span id="native-p13-b6-l0-0"></span>

## 50Hz/60Hz周波数の切り替え:

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="frequency-p13" data-source-fragment-sha256="21cd725107945df49965288a75073e5dec85f72de726c8e7e064af4174083d8e" data-web-base-art-ref="frequency" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="frequency-p13.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/frequency-p13.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:3.8813%;--hb-y:8.9919%;--hb-width:92.5943%;--hb-height:29.4329%;--hb-fill:#ebebec">※ 工場出荷時のデフォルト設定は60Hzに設定されています。自動識別: お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。手動調整: AC出力がオンの状態で、AC出力ボタンを5秒間長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:31.2047%;--hb-y:43.3773%;--hb-width:15.095%;--hb-height:10.8496%"><strong>50HZ</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:54.6005%;--hb-y:43.3773%;--hb-width:15.095%;--hb-height:10.8496%"><strong>60HZ</strong></span></div></div></figure>

<span id="native-p13-b0-l0-0"></span>

## USB出力オン/オフ

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output-p13" data-source-fragment-sha256="694fa885480bd71d52414ec090c2152a15078fd158ea4fe9a71c26825b9289d7" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-reference-id="usb-output-p13.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output-p13-crop.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:1.7111%;--hb-y:1.9492%;--hb-width:56.5732%;--hb-height:9.8681%;--hb-fill:#ebebec"><strong>前提：</strong>主電源ボタンがオンになっていることを確認してください。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:85.189%;--hb-y:14.6525%;--hb-width:4.9448%;--hb-height:6.6373%"><strong>オン</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:85.0915%;--hb-y:33.4843%;--hb-width:4.9076%;--hb-height:6.6373%"><strong>オフ</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:85.3286%;--hb-y:21.6207%;--hb-width:7.5704%;--hb-height:5.8951%">1回押す</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:85.3286%;--hb-y:39.6605%;--hb-width:7.5704%;--hb-height:5.8951%">1回押す</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li>USB-C 100Wは、USB-PD Power Source 3 (PS3) の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたはアクセサリーに耐火安全保護が備わっていることを確認してください。</li><li>Jackery ポータブル電源 3600 Plus は、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5条に準拠したデバイスまたはアクセサリーのみに接続してください。</li><li>最大出力を得るためには、USB-C to USB-C 5Aケーブル（20V DC/5A、100W）を使用してください。</li></ul></td></tr></tbody></table>

<span id="native-p14-b3-l0-0"></span>

## 省エネモード

<p>省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンになっています。AC出力が25W以下、またはUSB出力が2W以下の状態が12時間続くと、自動的に出力がオフになります。ACまたはUSB出力がオンの状態では、画面に省エネアイコン<img alt="" src="assets/native-energy-saving-12h-p14.svg"/>が表示されます。アイコンの表示時間は、設定された省エネ時間に応じて変わります。</p>

<div class="table-wrapper docutils container"><table class="manual-table"><tbody><tr><th><p><span>出力ポートタイプ</span></p></th><th><p><span>電力設定値</span></p></th><th><p><span>デフォルト設定</span></p></th></tr><tr><td><p>AC出力ポート</p></td><td><p>≤25W</p></td><td rowspan="2"><p>12時間経つとすべての出力は自動的にオフになります</p></td></tr><tr><td><p>USB出力ポート</p></td><td><p>≤2W</p></td></tr></tbody></table></div>

<p>※ 交流25Wおよび直流2W以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフにならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上の<img alt="" src="assets/native-energy-saving-12h-p14.svg"/>アイコンは表示されなくなります。</p>

<p>AC出力ボタンがオンの状態で、AC出力ボタンと主電源ボタンを同時に長押しし、省エネアイコンの表示（オン）／非表示（オフ）が切り替わるまで押し続けてください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="energy-saving-p14" data-source-fragment-sha256="e4727dc3cb8c2a7c48561c25be050024aca616b3673d8229ed28575a376dbc43" data-web-base-art-ref="energy-saving" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-reference-id="energy-saving-p14.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/energy-saving-p14-web-crop.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:57.1796%;--hb-y:72.3218%;--hb-width:2.7814%;--hb-height:6.8913%">3s</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:61.679%;--hb-y:76.0522%;--hb-width:17.4686%;--hb-height:8.2748%">両方を3秒間長押し</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:61.8659%;--hb-y:68.5645%;--hb-width:15.0479%;--hb-height:8.1503%"><strong>オン/オフ</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:48.4565%;--hb-y:46.6964%;--hb-width:11.5593%;--hb-height:5.2622%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:75.3619%;--hb-y:46.6964%;--hb-width:12.0067%;--hb-height:5.2622%">AC出力ボタン</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">説明</td><td class="manual-callout-body"><p>省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。</p></td></tr></tbody></table>

<span id="native-p15-b1-l0-0"></span>

## LCDスクリーン

<figure aria-label="LCDスクリーン" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCDスクリーン" class="hb-lcd-mode-art" src="assets/lcd-screen-p15.svg"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">短くオン</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押すか、充電入力がある場合。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">2分後にLCDは自動的に消灯し、スリープモードになります。</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">常時オン</td><td class="hb-lcd-mode-action">オンにする</td><td class="hb-lcd-mode-copy">デバイスが起動している状態で主電源ボタンを2回押します。</td></tr><tr><td class="hb-lcd-mode-action">オフにする</td><td class="hb-lcd-mode-copy">主電源ボタンを押します。</td></tr><tr><td class="hb-lcd-mode-action">自動オフ</td><td class="hb-lcd-mode-copy">常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。</td></tr></tbody></table></div></figure>

<p>Jackeryアプリで画面表示モードを設定することもできます。</p>

<span id="native-p15-b14-l0-0"></span>

## ボタン操作

<figure aria-label="ボタン / 操作 / 機能" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">ボタン</th><th class="hb-key-operation" scope="col">操作</th><th class="hb-key-function" scope="col">機能</th></tr></thead><tbody><tr><td class="hb-key-buttons">主電源ボタン+ USB出力ボタン</td><td class="hb-key-operation">3s 両方を3秒間長押し</td><td class="hb-key-function">Wi-Fiのリセット</td></tr><tr><td class="hb-key-buttons">主電源ボタン+ AC出力ボタン</td><td class="hb-key-operation">3s 両方を3秒間長押し</td><td class="hb-key-function">省エネモードのオン / オフを切り替えます</td></tr><tr><td class="hb-key-buttons">USB出力ボタン+AC出力ボタン</td><td class="hb-key-operation">1s 両方を1秒間長押し</td><td class="hb-key-function">Wi-Fi＆Bluetooth オン / オフ</td></tr></tbody></table></figure>

<span id="native-p16-b2-l0-0"></span>

# UPS 機能

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups-p16" data-source-fragment-sha256="ef9257ba6b6d3a631a2911215e4edefcc9f2c8d19b139c028b61bdc950ca1d2b" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups-p16.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups-p16.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:38.8791%;--hb-y:78.1071%;--hb-width:56.71%;--hb-height:13.9291%;--hb-fill:#ebebec">電気製品のコンセントをポータブル電源のAC出力ポートに接続し、ポータブル電源のAC入力ポートを家庭のコンセントにつなぐことで、停電時などにポータブル電源を予備電源として活用できます。</span></div></div></figure>

<p>本製品は、電気系統（家庭内の電源など）が突然停止した場合、自動的にバッテリー給電モードに切り替わるUPS（無停電電源装置）機能を備えています。切替時間は約10 ミリ秒（0.010 秒）以内です。ただし、本機能は0ms での完全な無停止給電には対応しておりません。そのため、以下のような高精度な連続電源供給を必要とする機器への接続はお控えください：</p>

<ul><li><p>データサーバー</p></li><li><p>ワークステーション</p></li><li><p>医療機器など</p></li><li><p>その他、停電・瞬断の許容時間が10ms 以下の精密機器/ 業務機器全般</p></li></ul>

<p>これらの機器でご使用を希望される場合は、事前に複数回の動作テストを実施し、機器との互換性をご確認の上でご使用ください。</p>

<p>※記載の手順に従わずに機器が正常に動作しなかったり、データ消失などの損害が発生した場合、弊社では責任を負いかねます。あらかじめご了承ください。<br/>UPSとして使用している際はパススルー機能により充電と出力が同時に行われている状態のため、ポータブル電源の最大出力は1500W に制限され、停電時には定格出力に戻ります。複数の機器をUPS モードで同時に接続する場合は、合計負荷電力がバイパス時の最大出力（1500W）を超えないようにしてください。超えると、機器が過負荷保護により停止するおそれがあります。</p>

<span id="native-p17-b1-l0-0"></span>

# 接続

<span id="native-p17-b2-l0-0"></span>

## バッテリーパック（別売）に接続

<p>本製品は最大5個のバッテリーパックに対応し、大容量電源のニーズに応えることができます。使用方法の詳細については、Jackery Battery Pack 3600の取扱説明書を参照してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-stack-p17" data-source-fragment-sha256="e0237a39fcd276ff415e78f39aa7c2e5894af1075f6bfd4745b0f9df8720300a" data-web-base-art-ref="battery-stack" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-stack-p17.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-stack-p17.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:60.3304%;--hb-y:72.6994%;--hb-width:6.9102%;--hb-height:4.3772%">≥ 20cm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:32.7478%;--hb-y:74.346%;--hb-width:6.8642%;--hb-height:4.3772%">≥20cm</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li><p>Battery packを Jackery ポータブル電源 3600 Plus に接続する前に、両方の電源がオフになっていることを確認してください。 </p></li><li><p>製品が適切に動作するよう、両側の吸気口と排気口が遮られていないことを確認してください。適切な放熱を確保するため、通気口と物との間に少なくとも20cmの空間を空けてください。</p></li></ul></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-accessories-p17" data-source-fragment-sha256="945dfa22348ff5c451322bb64e72ab55771685953c429df6d73773b9f0a109cc" data-web-base-art-ref="battery-accessories" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-accessories-p17.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-accessories-p17.svg"/><span class="hb-reference-live-label hb-reference-live-pill hb-reference-source-badge" data-source-line="0" style="--hb-x:77.5693%;--hb-y:33.2347%;--hb-width:22.2079%;--hb-height:35.018%;--hb-fill:#a8aaac;--hb-label-color:#ffffff"><img alt="" src="assets/sold-separately-cart.svg"/><strong>（別売）</strong></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:38.1315%;--hb-y:72.8765%;--hb-width:11.3391%;--hb-height:8.477%">拡張ケーブル</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.1193%;--hb-y:72.8765%;--hb-width:23.4034%;--hb-height:8.477%">Jackery Battery Pack 3600</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:60.1621%;--hb-y:72.8765%;--hb-width:10.0235%;--hb-height:8.477%">取扱説明書</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:62.257%;--hb-y:50.9002%;--hb-width:5.7899%;--hb-height:5.6368%"><strong>取扱説明書</strong></span></div></div></figure>

<span id="native-p18-b8-l0-0"></span>

## 2台のユニットを並列接続する方法

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">説明</td><td class="manual-callout-body"><ul><li><p>並列接続用 Jackeryコネクター は別売りです。公式ウェブサイトでお求めいただけます。 </p></li><li><p>並列動作中は ソーラーパネルでの充電のみ可能 です。ACコンセントからの充電には対応していません。</p></li></ul></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご使用前の確認</td><td class="manual-callout-body"><ul><li><p>並列ケーブルを接続する前に、両方のユニットのAC出力がオフであることを確認してください（AC電源ボタンのインジケーターライトが消灯状態）。</p></li><li><p>AC出力がオンの状態で接続すると、コネクターが損傷する恐れがあります。</p></li></ul></td></tr></tbody></table>

<p><strong>接続手順 </strong></p>

<ol><li><p>両方の Jackery ポータブル電源 3600 Plus の電源をオフにします。</p></li><li><p>Jackeryコネクターを使用し、各ユニットの AC充電ポート 同士を接続します。</p></li><li><p>両方のユニットの電源をオンにします。</p></li><li><p>1分以内に、それぞれのユニットの AC電源ボタン を順に押し、AC出力を有効にします。</p></li></ol>

<p><strong>接続確認</strong></p>

<ul><li><p>接続が成功すると、ディスプレイに並列アイコンが点灯表示されます。<img alt="" src="assets/lcd-parallel.png"/></p></li><li><p>設定に失敗した場合は、ディスプレイに <strong>FA</strong>コード が表示されます。<br/>その場合は、各ユニットの<strong>AC</strong>電源ボタンを再度順に押して設定をやり直してください。</p></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-p18" data-source-fragment-sha256="91f3299121e621c0d055f99802b4bd13d210e144dbe524ac75ea8925962db5de" data-web-base-art-ref="parallel" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-p18.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-p18.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:51.0795%;--hb-y:90.4855%;--hb-width:17.14%;--hb-height:4.646%">Jackery Connector</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:55.5223%;--hb-y:2.529%;--hb-width:12.1787%;--hb-height:6.3064%">AC拡張ポート</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li><p>並列接続成功後、AC出力が作動中に並列ケーブルを外さないでください。もう一方のユニートで過負荷保護が作動する可能性があります。 </p></li><li><p>AC出力有効時（AC電源ボタンインジケーター点灯中）は並列ケーブルポートに触れないでください。このポートは200V高電圧であり、感電の危険があります。</p></li></ul></td></tr></tbody></table>

<p>いずれかのユニートの<strong>AC</strong>電源ボタンが押された場合、または故障によりAC出力が中断された場合、両ユニートは直ちにAC出力を停止します。<br/>システムが自動的に並列モードを終了します。<br/>他のユニットは点滅する並列アイコンと<strong>FA</strong>コードを表示し、並列接続の失敗を示します。<br/>並列出力を再開するには、まず不具合を解消し、その後、各ユニットの<strong>AC</strong>電源ボタンを順に再度押してください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-interrupted-p19" data-source-fragment-sha256="9b1a1a11a0c69691cf3f78e9c4dc7724c9fa5b3815b6c83ec2a872944e6ca474" data-web-base-art-ref="parallel-interrupted" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-interrupted-p19.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-interrupted-p19.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:29.0815%;--hb-y:10.8568%;--hb-width:17.1152%;--hb-height:4.996%">Jackery Connector</span></div></div></figure>

<span id="native-p19-b1-l0-0"></span>

## 並列モードの終了

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-exit-p19" data-source-fragment-sha256="a76638cc10e049d6270cf806618ce7bab9380f87713cd9a0cf81bcd3c04a5f5d" data-web-base-art-ref="parallel-exit" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-exit-p19.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-exit-p19.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.0324%;--hb-y:28.5252%;--hb-width:25.808%;--hb-height:3.9731%">1. すべての負荷を切断します。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:7.0324%;--hb-y:58.7462%;--hb-width:32.8237%;--hb-height:3.9731%">2. 両ユニットのAC出力をオフにします。</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:7.0324%;--hb-y:92.5751%;--hb-width:37.4537%;--hb-height:3.9731%">3. ユニットから並列ケーブルを取り外します。</span></div></div></figure>

<span id="native-p20-b2-l0-0"></span>

# 充電方法

<p><strong>グリーンエネルギー優先モード:</strong><br/>本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電ケーブルを使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。</p>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li><p>製品の充電動作温度範囲は-20°C~45°C、放電動作温度範囲は-20℃~45℃です。上限・下限温度を超えた場合、充放電が制限され、または充放電不可の可能性があります。 </p></li><li><p>温度によって、製品の充電効率と実際の容量は異なります。</p></li></ul></td></tr></tbody></table>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li><p>はじめてお使いになるときは、本製品をフル充電してからご使用ください。 </p></li><li><p>充電池は空の状態で長期保管(3カ月~6カ月）すると、性能が劣化したり、充電できなくなる場合があります。 </p></li><li><p>長期保管中は、電池残量が0％にならないよう、3か月に一度の充電をおすすめします。</p></li></ul></td></tr></tbody></table>

<span id="native-p20-b0-l0-0"></span>

## AC充電ケーブル

<p>コンセントよりJackery ポータブル電源 3600 Plus 本体に充電する場合、電流容量が大きいため、他機器と併用したり途中接続をすると、コンセントの電流上限値を超え充電停止したり、配線やコンセント・接続部が発熱し、火災の原因となる恐れがあります。必ず電源タップなどを介して他の電気製品と併用しないでください。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-ac-p20" data-source-fragment-sha256="840c0cffbab92d2782199722540a62709ef511f3459a9868aae64e95206179ae" data-web-base-art-ref="charging-ac" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-ac-p20.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-ac-p20.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:50.0648%;--hb-y:75.5762%;--hb-width:40.2328%;--hb-height:9.4995%">付属のAC充電ケーブルをご使用ください。</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>AC充電ケーブルのプラグが製品のAC入力ポートにしっかりと、かつ完全に差し込まれていることを確認してください。差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、機器の正常な動作に支障をきたす恐れがあります。</p></td></tr></tbody></table>

<span id="native-p21-b3-l0-0"></span>

## ソーラー充電

<p>ソーラーパネル接続用のDC入力ポート（8020メス）×2を搭載しており、合計最大入力電力は1000Wです。そのため、ソーラーパネル200Wの場合は最大4枚まで。</p>

<p>■ 必要なアクセサリー</p>

<ul><li><p>1枚または2枚接続時：アクセサリー不要、直接本体に接続可能です。      </p></li><li><p>4枚接続時：別売りの「SolarSagaアダプター（Pro/Plus/New専用）」を2個ご用意いただく必要があります。</p></li></ul>

<p>※Jackery SolarSagaアダプターを使って3枚接続はできません（電圧が許容範囲を超え、故障のリスクがあります）。</p>

<ul><li><p>直接接続可能です。<br/>追加のアクセサリーは不要です。<br/>本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。</p></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar-p21" data-source-fragment-sha256="1ef7b89a4f7f8650d8ce52cd19182aa68e74c3d5d6b7b9867b2fd1bff06030e7" data-web-base-art-ref="charging-solar" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-solar-p21.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-solar-p21.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.7576%;--hb-y:80.8196%;--hb-width:15.4008%;--hb-height:5.1504%">SolarSaga 200 × 2</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:45.8337%;--hb-y:54.1963%;--hb-width:9.8025%;--hb-height:5.4374%">取り外す </span></div></div></figure>

<ul><li><p>別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。</p><ul><li><p>「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。</p></li><li><p>ソーラーパネルの8020オス端子を「Jackery SolarSaga アダプター(Pro/Plus/New専用)」の8020メス端子に接続してください。</p></li></ul></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar-four-p22" data-source-fragment-sha256="36349636ded3a366c8d6b034df550e972dc14a4cff682de29317a0da1c899dbe" data-web-base-art-ref="charging-solar-four" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-solar-four-p22.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-solar-four-p22.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:40.5879%;--hb-y:83.9279%;--hb-width:47.4474%;--hb-height:5.1627%;--hb-fill:#ffffff">SolarSaga アダプター（Pro/Plus/New専用）別売り</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:71.2515%;--hb-y:79.0814%;--hb-width:15.4929%;--hb-height:4.0336%">SolarSaga 200 × 4</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:54.1566%;--hb-y:57.2706%;--hb-width:9.304%;--hb-height:4.2583%">取り外す </span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><p>DC入力ポートの電圧を一致させてください<br/>2つのDC入力ポートに接続する電源の電圧は必ず一致させてください。電圧が異なると、製品の異常動作や故障の原因となる可能性があります。<br/>例： </p><ul><li><p>2つのDC8020入力ポートにソーラーパネルを接続する際は、同じ型番のJackery製ソーラーパネルを使用し、接続する枚数も揃えてください。異なる型番や接続枚数で接続すると、電圧が不均一になり、製品が故障するおそれがあります。 </p></li><li><p>車載充電器とソーラーパネルを同時に使用して製品を充電しないでください。車のヒューズが切れたり、充電が正常に行われなかったりする可能性があります。</p></li></ul></td></tr></tbody></table>

<p>Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryのソーラーパネルを使用することをお勧めします。ソーラーパネルの開放電圧（V<sub><span>OC</span></sub>）が、Jackeryポータブル電源 3600 PlusのDC入力電圧範囲（16V～60V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を負いません。</p>

<span id="native-p23-b2-l0-0"></span>

## シガーソケット充電

<p>■<strong>本製品は、12V/10A 出力の車載シガーソケットからの充電に対応しています。</strong><br/>ご使用の際は、以下にご注意ください：</p>

<ul><li><p>必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れがあります。</p></li><li><p>車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。</p></li><li><p>ケーブルが確実に奥まで差し込まれていることをご確認ください。</p></li><li><p>悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。</p></li><li><p>誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。</p></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-car-p23" data-source-fragment-sha256="cc0a2173b406ac498790f9647233a7786687c9db740bce510c5303e188a0e9a4" data-web-base-art-ref="charging-car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-car-p23.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-car-p23.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:51.1797%;--hb-y:75.7284%;--hb-width:42.6157%;--hb-height:8.9711%;--hb-fill:#ffffff">※ シガーソケット充電ケーブルは別売りです。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:70.5557%;--hb-y:15.3235%;--hb-width:2.7112%;--hb-height:5.7406%">車</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">ご注意</td><td class="manual-callout-body"><ul><li><p>シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性があります。 </p></li><li><p>シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に 24V 車を使用しないでください。</p></li></ul></td></tr></tbody></table>

<span id="native-p24-b3-l0-0"></span>

# トラブルシューティング

<p>次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。問題が解決しない場合は、Jackeryカスタマーサポートまでご連絡ください。</p>

<figure aria-label="エラーコード / 対処方法" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">エラーコード</th><th class="hb-troubleshooting-measures" scope="col">対処方法</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code"><p>F0 / F1</p><p>F2 / F3</p></td><td class="hb-troubleshooting-measures">製品を再起動してください。</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures"><ol><li><p>AC 電源コンセントから充電する前に、電力グリッドが安定するのを待ってください。 </p></li><li><p>吸気口および排気口が塞がれていないか確認し、製品の両側に20cm のスペースを確保してください。 </p></li><li><p>製品は日陰で通気の良い場所に設置し、周囲温度が45℃未満であることを確認してください。 </p></li><li><p>製品からすべての負荷を取り外し、アイドル状態にして、エラーが消えるまで待ってください。ご使用の機器の起動時消費電力が本製品の出力範囲を超えていないかをご確認ください。 </p></li><li><p>製品を再起動してください。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures"><ol><li><p>製品からすべてのDC入力を取り外してください。 </p></li><li><p>ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（Voc）を確認してください。本製品の最大DC入力電圧は60Vです。 </p></li><li><p>製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">販売店またはJackeryカスタマーサポートにお問い合わせください。</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">製品のUSB ポートに接続されている負荷を取り外してください。故障が消えるまで待機してください。</td></tr><tr><td class="hb-troubleshooting-code">FA</td><td class="hb-troubleshooting-measures"><ol><li><p>両ユニットのAC 出力をオフにします。 </p></li><li><p>1 分以内に各ユニットのAC 電源ボタンを再度押してください。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures"><ol><li><p>バッテリーパックとポータブル電源 3600 Plus をそれぞれ再起動します。 </p></li><li><p>障害が続く場合は、バッテリーパックをポータブル電源 3600 Plus から切断し、再度接続してください。</p></li></ol></td></tr></tbody></table></figure>

<span id="native-p25-b48-l0-0"></span>

# 主な仕様

## 基本情報

<figure aria-label="基本情報" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">製品の名称</th><td class="manual-spec-value hb-spec-value">Jackery ポータブル電源 3600 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型番</th><td class="manual-spec-value hb-spec-value">JE-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">定格容量</th><td class="manual-spec-value hb-spec-value">3584Wh (80Ah/44.8V DC)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">バッテリータイプ</th><td class="manual-spec-value hb-spec-value">LiFePO₄（リン酸鉄リチウムイオン電池）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイクル寿命</th><td class="manual-spec-value hb-spec-value">6000回（6000回の充放電後も初期容量の70％以上を維持）</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">サイズ＆重量</th><td class="manual-spec-value hb-spec-value">約385×309×491 mm (約35 kg）</td></tr></tbody></table></figure>

## 入力ポート

<figure aria-label="入力ポート" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1×AC入力ポート</th><td class="manual-spec-value hb-spec-value">100V-120V~ 50Hz/60Hz，最大15A，最大1500W<sup class="hb-spec-reference">①</sup><br/>パススルー<sup class="hb-spec-reference">②</sup>：100V-120V~ 50Hz/60Hz，最大15A，最大1500W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2×DC8020入力ポート</th><td class="manual-spec-value hb-spec-value">PV：16V-60V⎓12A, 2ポート最大24A，最大1000W<br/>ｼｶﾞｰｿｹｯﾄ ：12V-16V⎓最大8A, 2ポート最大8A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×DC拡張ポ一卜（入力）</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓最大100A</td></tr></tbody></table></figure>

## 出カポート

<figure aria-label="出カポート" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">4×AC出力ポート（NEMA 5-20R）</th><td class="manual-spec-value hb-spec-value">100V~ 50Hz/60Hz，最大20A，定格2000W，合計3000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×AC出力ポート (NEMA L5-30R)</th><td class="manual-spec-value hb-spec-value">100V~ 50Hz/60Hz，最大30A，定格3000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC出力合計</th><td class="manual-spec-value hb-spec-value">3000W，瞬間最大6000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC出力（パススルー）<sup class="hb-spec-reference">②</sup></th><td class="manual-spec-value hb-spec-value">100V-120V~ 50Hz/60Hz，最大15A，最大1500W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2×USB-A出力ポート</th><td class="manual-spec-value hb-spec-value">5-6V⎓3A，6-9V⎓2A，9-12V⎓1.5A，最大18W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2×USB-C出力ポート</th><td class="manual-spec-value hb-spec-value">5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A，最大100W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×AC拡張ポ一卜（出力）</th><td class="manual-spec-value hb-spec-value">100V~ 50Hz/60Hz，最大3000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1×DC拡張ポ一卜（出力）</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V⎓最大60A</td></tr></tbody></table></figure>

## 温度範囲

<figure aria-label="温度範囲" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">充電温度</th><td class="manual-spec-value hb-spec-value">-20°C ~ 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">動作温度</th><td class="manual-spec-value hb-spec-value">-20°C ~ 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">保存温度</th><td class="manual-spec-value hb-spec-value">1ヶ月 -20℃ ~ 45℃ ; 3ヶ月 0℃ ~ 45℃ ; 1年 0℃ ~ 25℃</td></tr></tbody></table></figure>

<p>※ USB Type-C®   and USB-C®   are registered trademarks of USB Implementers Forum.</p>

<p>① この数値は最大充電電力のみを示しています。実際の充電電力は、温度、バッテリー残量（SOC）、アプリの設定により変動する場合があります。</p>

<p>② 本製品は、ACコンセントからバッテリーを充電しながら、AC出力ポートを通じて給電することができます。</p>

<span id="native-p26-b4-l0-0"></span>

# 保証について

<p>このたびはJackery 製品をご購入いただき、誠にありがとうございます。<br/>本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。<br/>ご使用前に必ずご確認のうえ、大切に保管してください。</p>

<span id="native-p26-b15-l0-0"></span>

## 保証期間

<figure aria-label="保証期間" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>本製品の保証期間は以下の通りです。</p><ul><li><p>電源本体：ご購入日より3 年間</p></li><li><p>付属品（AC 充電ケーブルなど）：ご購入日より1 年間</p></li></ul><p>なお、延長保証にご登録いただいた場合、電源本体の保証期間はさらに2 年間延長されます。</p><p>※付属品（AC 充電ケーブルなど）は延長保証の対象外です。<br/>詳細につきましては、公式サイトをご確認ください。</p><p>※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</p></figure>

<span id="native-p26-b16-l0-0"></span>

## 保証の適用範囲

<figure aria-label="保証の適用範囲" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><ol><li><p>購入チャネルについて<br/>本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。</p><p>※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。</p></li><li><p>保証提供地域<br/>保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。</p></li></ol></figure>

<span id="native-p26-b19-l0-0"></span>

## 保証の適用条件

<figure aria-label="保証の適用条件" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>以下のすべての条件を満たす場合に、保証の適用対象となります：</p><ul><li><p>Jackery公式オンラインストアまたは正規代理店にてご購入されたこと</p></li><li><p>保証期間内であること</p></li><li><p>下記の「保証対象外」に該当しないこと</p></li></ul></figure>

<span id="native-p26-b21-l0-0"></span>

## 保証対象外となる場合

<figure aria-label="保証対象外となる場合" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：</p><ol><li><p>故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合</p></li><li><p>使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷</p></li><li><p>他機器からの影響、不適切な修理または改造による故障・損傷</p></li><li><p>移設・輸送・落下などに起因する故障・損傷</p></li><li><p>火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷</p></li><li><p>消耗部品の劣化や摩耗、または外観の汚損など</p></li></ol></figure>

<span id="native-p27-b10-l0-0"></span>

## 購入証明について

<figure aria-label="購入証明について" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：</p><ul><li><p>Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）</p></li><li><p>正規代理店での購入：購入日・販売店名の記載された領収書または納品書</p></li></ul><p>※  ご提示がない場合、保証対応いたしかねます。</p></figure>

<span id="native-p27-b14-l0-0"></span>

## 保証内容

<figure aria-label="保証内容" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p><strong>1. 初期不良による交換</strong>（ご購入日から30日以内）</p><ul><li><p>取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。</p></li><li><p>在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。</p></li></ul><p><strong>2. 無償修理</strong>（ご購入日から30日以上～保証期間内）</p><ul><li><p>保証条件を満たす自然故障については、無料で修理対応いたします。</p></li><li><p>修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いた<br/>します。</p></li></ul><p><strong>3. 有償修理</strong><br/>以下に該当する場合は、有償での修理対応となります：</p><ul><li><p>保証期間を超えた製品</p></li><li><p>保証対象外と判断された場合</p></li><li><p>Jackery公式オンラインストアまたは正規代理店以外で購入された製品</p></li></ul><p>有償修理後の保証期間は、修理完了日より90日間です。</p><p>*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。</p></figure>

<span id="native-p27-b15-l0-0"></span>

## 免責事項

<ol><li><p>弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を負いません。</p></li><li><p>本保証書は、お客様が法律上有する権利を制限するものではありません。</p></li><li><p>保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。</p></li></ol>

<p>Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。<br/>ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。</p>

<p><img alt="" src="assets/shared-contact-web.svg"/><a href="http://www.jackery.jp"><span>公式サイト: http://www.jackery.jp</span></a></p>

<p><img alt="" src="assets/shared-contact-mail.svg"/><a href="mailto:jackery.jp@jackery.com"><span>カスタマーサポート: jackery.jp@jackery.com</span></a></p>

<p><img alt="" src="assets/shared-contact-phone.svg"/><a href="tel:+815031989007"><span>お問い合わせ電話番号: 050-3198-9007</span></a></p>

<span id="native-p28-b24-l0-0"></span>

# Jackeryアプリ ユーザーマニュアル

<span id="native-p28-b15-l0-0"></span>

## 1. アプリをダウンロードしてログインするには

<figure aria-label="1. アプリをダウンロードしてログインするには" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app-download-p28-store.svg"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Google PlayまたはApp Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを行ってください。</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app-download-p28-qr.svg"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>または、下の QR コードをスキャンしてアプリをダウンロードし、インストールしてください。</p></div></div></div><div class="hb-app-download-semantic"><img alt="1. アプリをダウンロードしてログインするには" class="hb-app-download-semantic-art" src="assets/app-download-p28.svg"/></div></figure>

<span id="native-p28-b4-l0-0"></span>

## 2. デバイスを追加するには

<p>2.1    APPの右上にあるデバイス追加ボタン<span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span>をクリックします；</p>

<p><span>2.2 デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くのデバイスに接続し、Bluetoothのアクセス許可を開くことを許可します；</span></p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add-p28" data-source-fragment-sha256="d86b88d856ea027abbe06ff9afc825b4993f5c23cdb2cab2a8f17c926f0a6615" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add-p28.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-phones-native-p28-web.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:18.312%;--hb-y:91.5467%;--hb-width:6.176%;--hb-height:5.2988%">2.1</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.4558%;--hb-y:91.5467%;--hb-width:6.176%;--hb-height:5.2988%">2.2</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>電源を入れた後、アプリが2時間以内接続されていないと、デバイスは自動的にWi-FiとBluetoothをオフにします。再度Wi-FiとBluetoothをオンにするには、「USB出力ボタン」と「AC出力ボタン」を同時長押しする必要があります。</p></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-controls-p28" data-source-fragment-sha256="238fa570b31660407efc4d8c6d50034577fc3c907c61ce75953987fdacdde5c6" data-web-base-art-ref="app-controls" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-controls-p28.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-controls-p28.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:3.5542%;--hb-y:30.0279%;--hb-width:9.6847%;--hb-height:7.9444%">主電源ボタン</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:88.6358%;--hb-y:64.1283%;--hb-width:10.0575%;--hb-height:7.9444%">AC出力ボタン</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:2.0415%;--hb-y:64.4012%;--hb-width:11.2197%;--hb-height:7.9444%">USB出力ボタン</span></div></div></figure>

<p><span>2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。</span></p>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます： </p><ul><li><p>デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。 </p></li><li><p>主電源ボタンとUSBボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され、システムが再起動します。</p></li></ul></td></tr></tbody></table>

<p><span>2.4 デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは自動的にWi-Fiネットワークに接続します。</span></p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応していません。</p></td></tr></tbody></table>

<p><span>2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi アイコンは常にオンになります。</span></p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-connect-p29" data-source-fragment-sha256="efd240958aa1dc9485b617a419616aaed1824cab9a73cfc53bbff02a47e96093" data-web-base-art-ref="app-connect" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-connect-p29.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-phones-native-p29.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:85.3606%;--hb-y:86.9318%;--hb-width:4.1493%;--hb-height:5.2904%">2.5</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:12.4786%;--hb-y:86.9318%;--hb-width:4.1493%;--hb-height:5.2904%">2.3</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:48.2166%;--hb-y:86.9318%;--hb-width:4.1493%;--hb-height:5.2904%">2.4</span></div></div></figure>

<p>上記のスクリーンショットはご参考まで。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">備考</td><td class="manual-callout-body"><p>Jackeryアプリは、一度に1台のポータブル電源としかBluetooth接続できません。 デバイスリストに戻ると、自動的にBluetoothが切断されます。 リスト内のポータブル電源をもう一度タップすると、自動的に再接続されます。</p></td></tr></tbody></table>

<span id="native-p29-b5-l0-0"></span>

## 3. デバイスのバインドを解除するには

<p>デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。</p>

<span id="native-p29-b8-l0-0"></span>

## 4. ご確認

<p><span>4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）：</span></p>

<ul><li><p>デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します。</p></li><li><p>上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、USB出力ボタンとAC出力ボタンを同時長押しします。</p></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-download-reminder-p30" data-source-fragment-sha256="831dcae582dbfbd0189532fd9c7f671bfcf1aee8babba009ddfd93c1801bb629" data-web-base-art-ref="app-download-reminder" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-download-reminder-p30.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-download-reminder-p30.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.7334%;--hb-y:4.7486%;--hb-width:45.6257%;--hb-height:11.2317%">本製品はJackeryアプリケーションによるスマ</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.7334%;--hb-y:15.7266%;--hb-width:37.7743%;--hb-height:11.2317%">ートコントロールに対応しています。</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.7334%;--hb-y:30.3583%;--hb-width:46.5517%;--hb-height:11.2317%">ご利用いただくには、下記のアプリストアより</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.7334%;--hb-y:41.3364%;--hb-width:45.189%;--hb-height:11.2317%">「Jackery」で検索して「Jackery アプリ」を</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.7334%;--hb-y:52.3144%;--hb-width:28.9969%;--hb-height:11.2317%">ダウンロードしてください。</span></div></div></figure>
