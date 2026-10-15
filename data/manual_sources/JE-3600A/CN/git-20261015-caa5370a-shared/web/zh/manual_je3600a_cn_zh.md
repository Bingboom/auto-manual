<style>
/* JE-3600A shared-component edition: source geometry only.
   Shared Web theme owns every table, callout, card, label and figure style.
   Each figure keeps the print's label size (container-relative), nothing else. */
#furo-main-content p > img[src*="shared-contact-"] { width: 1.25em; height: 1.25em; margin: 0 0.4em 0 0; vertical-align: -0.25em; }
#furo-main-content img[src*="manufacturer-qr"] { width: 7rem !important; height: auto !important; }
#furo-main-content :is(p, li) > img:not([src*="shared-contact-"]) { width: auto; height: 1.3em; margin: 0 0.15em; vertical-align: -0.3em; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.7508cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ac-output-p8"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.7508cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p20"] .hb-reference-live-label { font-size: 2.6323cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p20"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-add-p20"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label { font-size: 2.3291cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="3"] { font-size: 1.1646cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.4973cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="5"] { font-size: 1.4973cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-connect-p21"] .hb-reference-live-label[data-source-line="6"] { font-size: 1.1646cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p20"] .hb-reference-live-label { font-size: 2.2364cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p20"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p20"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="app-controls-p20"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p12"] .hb-reference-live-label { font-size: 2.2582cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p12"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p12"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p12"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-accessories-p12"] .hb-reference-live-label[data-source-line="0"] { font-size: 3.2260cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p12"] .hb-reference-live-label { font-size: 1.9360cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p12"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="battery-stack-p12"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p17"] .hb-reference-live-label { font-size: 2.5592cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p17"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p17"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-car-p17"] .hb-reference-live-label[data-source-line="1"] { font-size: 2.2393cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p16"] .hb-reference-live-label { font-size: 1.7837cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p16"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-four-p16"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p15"] .hb-reference-live-label { font-size: 1.7901cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="charging-solar-p15"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label { font-size: 2.2355cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.2131cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.9162cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.7565cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="energy-saving-p10"] .hb-reference-live-label[data-source-line="5"] { font-size: 1.7565cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label { font-size: 1.9628cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="7"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="8"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="9"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="10"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="11"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="12"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="13"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="14"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="15"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="16"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="17"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="18"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="19"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="20"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="21"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="0"] { font-size: 1.8249cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.8987cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="lcd-map-p5"] .hb-reference-live-label[data-source-line="14"] { font-size: 1.8354cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="7"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="8"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="9"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="10"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="11"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="12"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="13"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="14"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.5237cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="1"] { font-size: 1.5773cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.5773cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="3"] { font-size: 1.5773cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.5773cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="12"] { font-size: 1.5284cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-front-p3"] .hb-reference-live-label[data-source-line="14"] { font-size: 1.5284cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label { font-size: 1.5284cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="7"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="8"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="9"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="10"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="11"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="12"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="13"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="14"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="15"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="16"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="0"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="2"] { font-size: 2.5237cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="3"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="4"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="10"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="14"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="15"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="overview-side-p4"] .hb-reference-live-label[data-source-line="16"] { font-size: 2.0505cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p14"] .hb-reference-live-label { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p14"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p14"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p14"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-exit-p14"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-interrupted-p14"] .hb-reference-live-label { font-size: 2.2361cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-interrupted-p14"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p13"] .hb-reference-live-label { font-size: 2.2460cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p13"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p13"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p13"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="parallel-p13"] .hb-reference-live-label[data-source-line="2"] { font-size: 2.0856cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="3"] { font-size: 1.7508cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.7508cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="power-p8"] .hb-reference-live-label[data-source-line="5"] { font-size: 1.9748cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label { font-size: 2.2364cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="5"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="registration-p2"] .hb-reference-live-label[data-source-line="6"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="ups-p11"] .hb-reference-live-label { font-size: 2.2395cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="ups-p11"] .hb-reference-live-label[data-source-line="0"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label { font-size: 2.2283cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="1"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="2"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="3"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="4"] { white-space: nowrap; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="2"] { font-size: 1.7508cqw; }
#furo-main-content .hb-reference-figure[data-reference-id="usb-output-p9"] .hb-reference-live-label[data-source-line="4"] { font-size: 1.7508cqw; }

</style>

<p>感谢您选择购买电小二产品。在使用之前请您务必仔细阅读本用户指南，按照指引正确使用并妥善保管。<br/>在遵从法律法规的情况下，本公司享有对本文档及本产品所有相关文档的最终解释权。如有更新改版或终止请以官方发布最新通知为准。<br/>您现在可以通过微信注册您的产品，激活质保服务。注册过程轻松快速，注册后您将享有：</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="registration-p2" data-source-fragment-sha256="35af5fd60014caed04c18bc2dcc5f497cbaeb6b6c92216fd75de95ce5b59bee3" data-web-base-art-ref="registration" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="registration-p2.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/registration-p2.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:1.0842%;--hb-y:13.3797%;--hb-width:39.1134%;--hb-height:17.0695%">自购买日起享质保 3年 + 注册延保 2 年</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:1.0842%;--hb-y:33.7152%;--hb-width:25.0799%;--hb-height:17.0695%">电小二售后专家技术支持</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:1.0842%;--hb-y:54.0508%;--hb-width:13.8978%;--hb-height:17.0695%">真伪查询服务</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:1.0842%;--hb-y:74.3864%;--hb-width:22.8435%;--hb-height:17.0695%">售后维修进度实时查看</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:42.8396%;--hb-y:12.082%;--hb-width:42.5083%;--hb-height:17.0695%">1.打开微信，点击“发现”中的“扫一扫”</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:42.8396%;--hb-y:42.5854%;--hb-width:20.4147%;--hb-height:17.0695%">2.扫描右方的二维码</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:42.8396%;--hb-y:73.0888%;--hb-width:24.8965%;--hb-height:17.0695%">3.按照提示完成注册激活</span></div></div></figure>

<p>如您未能成功注册，您可以联系电小二官方服务热线 <strong>400-668-9293 </strong>或联系在线客服进行注册，产品具体保修条款和注册细则，请登录 <strong>电小二户外电源服务小程序 </strong>查看。<br/>以下情况不在保修范围内：产品使用后外观损坏；自行拆机或维修；因人为原因造成产品性能故障；由于自然灾害、雷电、事故等不可抗拒的因素造成的损害。</p>

<span id="native-p2-b33-l0-0"></span>

# 使用注意安全事项

<p><strong>使使用本产品时，应始终遵循基本注意事项，包括:</strong></p>

<ul><li><p>使用本产品之前，请阅读所有说明。</p></li><li><p>为了降低风险，当在儿童附近使用本产品时，需要进行密切监督。</p></li><li><p>使用非专业产品制造商推荐或销售的配件可能会导致触电的风险。</p></li><li><p>产品在未使用时，请将电源插头拔出产品插座。</p></li><li><p>禁止对产品进行拆机，产品拆机后可能会导致火灾、爆炸或触电等不可预测的风险。</p></li><li><p>禁止使用损坏的电线或插头，或损坏的输出电缆来使用产品，有触电的危险。</p></li><li><p>请在通风良好的地方对产品进行充电，请勿以任何方式限制产品的通风。</p></li><li><p>请将产品放置在干燥的地方，不得淋雨，不得使产品进水，这会有触电风险（非预定仅在室外安装使用）。</p></li><li><p>禁止将产品撞击或投入火中，这可能导致产品发生起火，爆炸等安全事故。</p></li><li><p>禁止在高温下（直热的阳光下或很热的汽车车内）使用或放置产品，否则可能会引起内部电池过热，起火或功能失效，寿命减短等风险。</p></li><li><p>首次使用时，请在使用前将设备充满电。如果本产品在电量耗尽的情况下长时间（3 个月 - 6个月）存放，其性能会下降，甚至无法充电。</p></li><li><p>使用本产品时必须接地，接地可以在发生故障时减少触电风险，本产品配备带设备接地线和接地插头的电源线，必须根据当地法规和规范正确地安装和连接插头至接地插座。</p></li></ul>

<span id="native-p3-b5-l0-0"></span>

# 包装清单

<figure aria-label="包装清单" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="three-card-responsive"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="便携式储能电源 3600 Plus" class="hb-inbox-art" src="assets/inbox-p3-card-1.svg"/><div class="hb-inbox-label"><p>便携式储能电源 3600 Plus</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC电源线" class="hb-inbox-art" src="assets/inbox-p3-card-2.svg"/><div class="hb-inbox-label"><p>AC电源线</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="用户指南" class="hb-inbox-art" src="assets/inbox-p3-card-3.svg"/><div class="hb-inbox-label"><p>用户指南</p></div></li></ol></figure>

<p>* 配套AC电源线仅用于本设备。</p>

<p>* 车载充电线需单独购买，请前往电小二官网选购或联系电小二售后客服寻求帮助。</p>

<span id="native-p3-b6-l0-0"></span>

# 产品介绍

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front-p3" data-source-fragment-sha256="79545f88fc510dd8ae1425471f766157bf8c1ffd5113e31605b0149f260a0096" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-front-p3.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front-p3.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.0495%;--hb-y:1.2023%;--hb-width:5.5205%;--hb-height:5.6273%"><strong>正面</strong></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.4123%;--hb-y:40.5926%;--hb-width:21.2603%;--hb-height:6.5561%">5V⎓3A, 9V⎓3A, 12V⎓3A,  </span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4108%;--hb-y:43.617%;--hb-width:23.4574%;--hb-height:6.5561%">15V⎓3A, 20V⎓5A，最大100W</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4108%;--hb-y:56.0828%;--hb-width:18.8675%;--hb-height:6.5561%">5-6V⎓3A，6-9V⎓2A，</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4108%;--hb-y:59.1072%;--hb-width:18.2587%;--hb-height:6.5561%">9-12V⎓1.5A，最大18W</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:87.1999%;--hb-y:66.6448%;--hb-width:12.0645%;--hb-height:4.7551%"><strong>AC输出按键</strong></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.4203%;--hb-y:67.3884%;--hb-width:13.7767%;--hb-height:4.7551%"><strong>USB输出按键</strong></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.4203%;--hb-y:37.9101%;--hb-width:24.2505%;--hb-height:4.7551%"><strong>USB-C 100W 输出端口</strong></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4203%;--hb-y:53.4308%;--hb-width:22.7618%;--hb-height:4.7551%"><strong>USB-A 18W 输出端口</strong></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:87.1923%;--hb-y:12.4903%;--hb-width:12.0707%;--hb-height:4.7551%"><strong>LCD 显示屏</strong></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:87.2005%;--hb-y:28.7499%;--hb-width:12.0645%;--hb-height:4.7551%"><strong>AC输出端口</strong></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.4204%;--hb-y:30.7316%;--hb-width:12.776%;--hb-height:4.7551%"><strong>总电源开关键</strong></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:75.1985%;--hb-y:32.9775%;--hb-width:23.7731%;--hb-height:3.7878%">220V ~ 50Hz，16A，额定3600W</span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:87.1999%;--hb-y:52.8033%;--hb-width:12.0645%;--hb-height:4.7551%"><strong>AC输出端口</strong></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:75.3837%;--hb-y:57.0317%;--hb-width:23.7968%;--hb-height:3.7878%">220V ~ 50Hz，10A，额定2200W</span></div></div></figure>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-side-p4" data-source-fragment-sha256="f7601c719f7ca0d1e478b023ad3f1e3e301b0150747d37b50d2d820294563bc8" data-web-base-art-ref="overview-side" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-side-p4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-side-p4.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:88.5457%;--hb-y:8.4089%;--hb-width:10.014%;--hb-height:2.1808%"><strong>AC总输出</strong></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:74.6557%;--hb-y:10.38%;--hb-width:23.6924%;--hb-height:1.7371%">4口合计3600W (瞬时最大7200W)</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.9579%;--hb-y:24.7142%;--hb-width:8.0442%;--hb-height:2.5808%"><strong>右侧面</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:88.1007%;--hb-y:60.7393%;--hb-width:11.8993%;--hb-height:2.1808%"><strong>AC输入端口</strong></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:75.6708%;--hb-y:51.0896%;--hb-width:24.3292%;--hb-height:2.1808%"><strong>DC输入端口（DC8020）</strong></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:77.9323%;--hb-y:62.8968%;--hb-width:21.9574%;--hb-height:1.7371%">220V-240V~ 50Hz， 最大10A</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:83.0729%;--hb-y:52.4539%;--hb-width:16.9271%;--hb-height:3.0067%">光伏：16V-60V⎓12A，</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:82.3487%;--hb-y:54.5165%;--hb-width:17.6513%;--hb-height:1.7371%">双路最大24A/最大1000W</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:81.0202%;--hb-y:55.2279%;--hb-width:18.9798%;--hb-height:3.0067%">车充：12V-16V⎓最大8A，</span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:91.7161%;--hb-y:57.2906%;--hb-width:8.2839%;--hb-height:1.7371%">双路最大8A</span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:1.5089%;--hb-y:54.1817%;--hb-width:14.8265%;--hb-height:2.1808%"><strong>加电包连接端口</strong></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:1.5757%;--hb-y:56.2998%;--hb-width:22.6061%;--hb-height:1.7371%">输入：36.4V-50.4V，最大100A</span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:1.5757%;--hb-y:57.6868%;--hb-width:21.8538%;--hb-height:1.7371%">输出：36.4V-50.4V，最大60A</span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:1.3017%;--hb-y:49.1251%;--hb-width:23.1911%;--hb-height:1.7371%">输出：220V~50Hz，额定3500W</span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:1.3017%;--hb-y:47.1286%;--hb-width:8.6751%;--hb-height:2.1808%"><strong>并机端口</strong></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:1.3017%;--hb-y:74.509%;--hb-width:6.6246%;--hb-height:2.1808%"><strong>固定轮</strong></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:1.1597%;--hb-y:33.371%;--hb-width:10.7256%;--hb-height:2.1808%"><strong>可伸缩手柄</strong></span></div></div></figure>

<span id="native-p5-b0-l0-0"></span>

# 显示屏界面

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map-p5" data-source-fragment-sha256="3af0985c5f5c2c69c699b2d67c1aee33826d46a097003b9d39d04e3c275c93f6" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map-p5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map-p5.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:93.2059%;--hb-y:41.8848%;--hb-width:2.0076%;--hb-height:5.1861%">21</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:93.0239%;--hb-y:52.4235%;--hb-width:2.4873%;--hb-height:5.3488%">22</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.9526%;--hb-y:42.4224%;--hb-width:1.5149%;--hb-height:5.49%">9</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4168%;--hb-y:53.4242%;--hb-width:2.4374%;--hb-height:5.49%">10</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:17.5006%;--hb-y:4.3035%;--hb-width:1.142%;--hb-height:5.49%">1</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:17.291%;--hb-y:90.5056%;--hb-width:1.8682%;--hb-height:5.49%">11</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:21.0667%;--hb-y:4.3058%;--hb-width:1.5051%;--hb-height:5.49%">2</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:21.1994%;--hb-y:90.4988%;--hb-width:2.2313%;--hb-height:5.49%">12</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:26.0884%;--hb-y:90.505%;--hb-width:2.2412%;--hb-height:5.49%">13</span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:41.9554%;--hb-y:90.9456%;--hb-width:2.3393%;--hb-height:5.49%">14</span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:46.4909%;--hb-y:90.9888%;--hb-width:2.2608%;--hb-height:5.49%">15</span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:50.4126%;--hb-y:90.9888%;--hb-width:2.2412%;--hb-height:5.49%">16</span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:66.9338%;--hb-y:91.0342%;--hb-width:2.2372%;--hb-height:5.49%">18</span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:71.0924%;--hb-y:91.0342%;--hb-width:2.2019%;--hb-height:5.49%">19</span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:75.6584%;--hb-y:91.0333%;--hb-width:2.5946%;--hb-height:5.2093%">20</span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:24.7956%;--hb-y:4.3058%;--hb-width:1.5149%;--hb-height:5.49%">3</span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:28.1332%;--hb-y:4.3058%;--hb-width:1.6131%;--hb-height:5.49%">4</span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:31.7428%;--hb-y:4.3058%;--hb-width:1.5346%;--hb-height:5.49%">5</span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:56.0096%;--hb-y:4.3058%;--hb-width:1.4364%;--hb-height:5.49%">7</span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:71.4756%;--hb-y:4.4835%;--hb-width:2.0998%;--hb-height:5.49%">8 </span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:47.1224%;--hb-y:4.3489%;--hb-width:1.5149%;--hb-height:5.49%">6</span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:61.5438%;--hb-y:90.9876%;--hb-width:2.1234%;--hb-height:5.49%">17</span></div></div></figure>

<figure aria-label="液晶屏" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-wifi.png"/></td><td class="hb-lcd-name"><strong>Wi-Fi</strong></td><td class="hb-lcd-description"><p>点亮：Wi-Fi 已连接。 </p><p>闪烁：准备连接 Wi-Fi。 </p><p>熄灭：Wi-Fi 未连接。</p></td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-bluetooth.png"/></td><td class="hb-lcd-name"><strong>Bluetooth</strong></td><td class="hb-lcd-description"><p>点亮：蓝牙已连接。 </p><p>闪烁：准备连接蓝牙。 </p><p>熄灭：蓝牙未连接。</p></td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="静音充电模式" class="hb-lcd-icon-art" src="assets/lcd-quiet-charging.png"/></td><td class="hb-lcd-name"><strong>静音充电模式</strong></td><td class="hb-lcd-description"><p>点亮：静音充电模式已开启。<br/>充电功率降低，充电速度变慢，同时显著降低充电时的噪音。 </p><p>熄灭：静音充电模式未开启/已关闭。<br/>（请在 APP 中开启/关闭该功能，关机可记忆保存）。</p></td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="节省电池模式" class="hb-lcd-icon-art" src="assets/lcd-battery-saving-native.svg"/></td><td class="hb-lcd-name"><strong>节省电池模式</strong></td><td class="hb-lcd-description"><p>点亮：节省电池模式已开启，通过限制电池的最大可用容量来延长电池使用寿命。 </p><p>熄灭：节省电池模式未开启/已关闭。<br/>（请在 APP 中开启/关闭该功能，关机可记忆保存）。<br/>注：开启后偶尔会满充满放，用于校准SOC。</p></td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="自发自用模式" class="hb-lcd-icon-art" src="assets/lcd-self-powered-native.svg"/></td><td class="hb-lcd-name"><strong>自发自用模式</strong></td><td class="hb-lcd-description"><p>点亮：自发自用模式已开启，最大化利用太阳能，减少电网电力消耗，减少用电成本。 </p><p>熄灭：自发自用模式未开启/已关闭。<br/>（请在 APP 中开启/关闭该功能，关机可记忆保存）。</p></td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="充电计划" class="hb-lcd-icon-art" src="assets/lcd-charging-plan.png"/></td><td class="hb-lcd-name"><strong>充电计划</strong></td><td class="hb-lcd-description">自定义便携式储能电源 3600 Plus的充电计划，适用于电价有波动的情况，可根据电价峰谷时间段制定充电计划，减少用电成本。<br/>（请在 APP 中开启/关闭该功能，关机可记忆保存）。</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="并机模式" class="hb-lcd-icon-art" src="assets/lcd-parallel.png"/></td><td class="hb-lcd-name"><strong>并机模式</strong></td><td class="hb-lcd-description"><p>点亮：AC输出打开，设备已成功并机。 </p><p>闪烁：AC输出打开，设备未成功并机。</p></td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="交流输出符号" class="hb-lcd-icon-art" src="assets/lcd-ac-power.png"/></td><td class="hb-lcd-name"><strong>交流输出符号</strong></td><td class="hb-lcd-description">AC输出（纯正弦波）已开启。</td></tr><tr><td class="hb-lcd-number">8</td><td class="hb-lcd-icon"><img alt="输出电压和频率" class="hb-lcd-icon-art" src="assets/lcd-output-voltage-frequency.png"/></td><td class="hb-lcd-name"><strong>输出电压和频率</strong></td><td class="hb-lcd-description">显示AC输出口的输出电压和频率。</td></tr><tr><td class="hb-lcd-number">9</td><td class="hb-lcd-icon"><img alt="充电功率显示" class="hb-lcd-icon-art" src="assets/lcd-input-power.png"/></td><td class="hb-lcd-name"><strong>充电功率显示</strong></td><td class="hb-lcd-description">显示当前充电功率。</td></tr><tr><td class="hb-lcd-number">10</td><td class="hb-lcd-icon"><img alt="剩余充电时间" class="hb-lcd-icon-art" src="assets/lcd-remaining-charge-time.png"/></td><td class="hb-lcd-name"><strong>剩余充电时间</strong></td><td class="hb-lcd-description">显示剩余充电时间。</td></tr><tr><td class="hb-lcd-number">11</td><td class="hb-lcd-icon"><img alt="市电充电接入" class="hb-lcd-icon-art" src="assets/lcd-ac-wall-charging-native.svg"/></td><td class="hb-lcd-name"><strong>市电充电接入</strong></td><td class="hb-lcd-description">产品通过市电进行充电。</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="车充充电接入" class="hb-lcd-icon-art" src="assets/lcd-car-charging-native.svg"/></td><td class="hb-lcd-name"><strong>车充充电接入</strong></td><td class="hb-lcd-description">产品通过 DC 输入端口（DC8020）连接 12V 车载充电线进行充电。</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="太阳能（绿色能源）充电接入" class="hb-lcd-icon-art" src="assets/lcd-solar-charging-native.svg"/></td><td class="hb-lcd-name"><strong>太阳能（绿色能源）充电接入</strong></td><td class="hb-lcd-description">产品通过 DC 输入端口（DC8020）连接太阳能板进行充电。</td></tr><tr><td class="hb-lcd-number">14</td><td class="hb-lcd-icon"><img alt="电池电量图标" class="hb-lcd-icon-art" src="assets/lcd-battery-power.png"/></td><td class="hb-lcd-name"><strong>电池电量图标</strong></td><td class="hb-lcd-description">当本产品处于充电状态时，该图标顺时针转动；<br/>当产品处于放电状态时，该图标显示当前电量。</td></tr><tr><td class="hb-lcd-number">15</td><td class="hb-lcd-icon"><img alt="低电量提醒" class="hb-lcd-icon-art" src="assets/lcd-low-battery.png"/></td><td class="hb-lcd-name"><strong>低电量提醒</strong></td><td class="hb-lcd-description"><p>点亮：当前电池电量低于 20%。 </p><p>闪烁：当前电池电量低于 5%。 </p><p>熄灭：设备正在充电中。</p></td></tr><tr><td class="hb-lcd-number">16</td><td class="hb-lcd-icon"><img alt="电池电量百分比" class="hb-lcd-icon-art" src="assets/lcd-remaining-battery-percentage.png"/></td><td class="hb-lcd-name"><strong>电池电量百分比</strong></td><td class="hb-lcd-description">显示当前电池电量。</td></tr><tr><td class="hb-lcd-number">17</td><td class="hb-lcd-icon"><img alt="加电包接入及数量" class="hb-lcd-icon-art" src="assets/lcd-connected-batteries-native.svg"/></td><td class="hb-lcd-name"><strong>加电包接入及数量</strong></td><td class="hb-lcd-description">显示加电包的接入状态及数量。</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="故障代码" class="hb-lcd-icon-art" src="assets/lcd-fault-code.png"/></td><td class="hb-lcd-name"><strong>故障代码</strong></td><td class="hb-lcd-description">产品发生故障，请参考故障代码模块内容了解详情。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="高温警告" class="hb-lcd-icon-art" src="assets/lcd-high-temperature-native.svg"/></td><td class="hb-lcd-name"><strong>高温警告</strong></td><td class="hb-lcd-description">如果屏幕上出现，请勿担心，电池降温后可自行恢复。</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="低温警告" class="hb-lcd-icon-art" src="assets/lcd-low-temperature-native.svg"/></td><td class="hb-lcd-name"><strong>低温警告</strong></td><td class="hb-lcd-description">如果屏幕上出现，请勿担心，环境温度恢复后自动恢复。</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="节能模式" class="hb-lcd-icon-art" src="assets/lcd-energy-saving.png"/></td><td class="hb-lcd-name"><strong>节能模式</strong></td><td class="hb-lcd-description"><p>AC 输出按键 或USB 输出按键时打开时：<br/>点亮：节能模式开启。 </p><p>熄灭：节能模式关闭。</p></td></tr><tr><td class="hb-lcd-number">21</td><td class="hb-lcd-icon"><img alt="放电功率显示" class="hb-lcd-icon-art" src="assets/lcd-output-power.png"/></td><td class="hb-lcd-name"><strong>放电功率显示</strong></td><td class="hb-lcd-description">显示当前放电功率。</td></tr><tr><td class="hb-lcd-number">22</td><td class="hb-lcd-icon"><img alt="剩余放电时间" class="hb-lcd-icon-art" src="assets/lcd-remaining-discharge-time.png"/></td><td class="hb-lcd-name"><strong>剩余放电时间</strong></td><td class="hb-lcd-description">显示剩余放电时间。</td></tr></tbody></table></figure>

<span id="native-p8-b0-l0-0"></span>

# 产品使用

<span id="native-p8-b10-l0-0"></span>

## 电源开机/关机

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-p8" data-source-fragment-sha256="ddb9c4682dc11ba31250899a6bc9ccff2aa3e290275f3585c51bcc838b773eee" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power-p8.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power-p8.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:41.9185%;--hb-y:53.4939%;--hb-width:54.7698%;--hb-height:17.7717%;--hb-fill:#ebebec">* 本产品的默认待机时间为2小时，若产品无任何充电输入或放电输出，2小时后将自动关机，自动关机时间可以在App上设置。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.056%;--hb-y:19.219%;--hb-width:4.9342%;--hb-height:5.4038%"><strong>开机</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:75.056%;--hb-y:29.7726%;--hb-width:4.9342%;--hb-height:5.4038%"><strong>关机</strong></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:75.056%;--hb-y:23.9898%;--hb-width:7.4809%;--hb-height:4.3576%">短按一次</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:75.0564%;--hb-y:34.2543%;--hb-width:6.8103%;--hb-height:4.3577%">长按3秒</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:78.8729%;--hb-y:39.4597%;--hb-width:2.4207%;--hb-height:4.9337%">3s</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:43.9242%;--hb-y:7.2452%;--hb-width:13.8475%;--hb-height:5.4038%"><strong>总电源开关键</strong></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:5.5567%;--hb-y:81.629%;--hb-width:90.6362%;--hb-height:11.0061%">节能模式下，开启AC或USB输出，若产品无任何充电输入或放电输出，12小时后将关闭AC或USB输出（节能模式时间可以在App 上设置）。</span></div></div></figure>

<span id="native-p8-b11-l0-0"></span>

## AC输出开/关

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output-p8" data-source-fragment-sha256="8e3b6b3a8123b3851a974490d577ba0809f6c200b5c5cefa48d9e308e2e463d8" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output-p8.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output-p8.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.5438%;--hb-y:5.2232%;--hb-width:29.5211%;--hb-height:7.2561%;--hb-fill:#f2f2f3">确保总电源开关键已打开。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:80.3435%;--hb-y:21.3626%;--hb-width:4.9342%;--hb-height:5.0253%"><strong>开启</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:80.3435%;--hb-y:25.7993%;--hb-width:7.4809%;--hb-height:4.0524%">短按一次</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:80.3435%;--hb-y:33.8604%;--hb-width:4.9342%;--hb-height:5.0253%"><strong>关闭</strong></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:80.3435%;--hb-y:38.2971%;--hb-width:7.4809%;--hb-height:4.0524%">短按一次</span></div></div></figure>

<span id="native-p9-b5-l0-0"></span>

## USB输出开 / 关

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output-p9" data-source-fragment-sha256="329650d50ddaeb695112262e435dfb958a331eaac55fdc02ce4104c209cb9f04" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="usb-output-p9.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output-p9.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.5437%;--hb-y:4.7595%;--hb-width:29.5211%;--hb-height:8.3194%;--hb-fill:#f2f2f3">确保总电源开关键已打开。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:81.5944%;--hb-y:16.4078%;--hb-width:4.9342%;--hb-height:5.7616%"><strong>开启</strong></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:81.5944%;--hb-y:21.4946%;--hb-width:7.4809%;--hb-height:4.6462%">短按一次</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:81.5944%;--hb-y:30.737%;--hb-width:4.9342%;--hb-height:5.7616%"><strong>关闭</strong></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:81.5944%;--hb-y:35.8239%;--hb-width:7.4809%;--hb-height:4.6462%">短按一次</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><ul><li><p>USB-C 100W输出端口属于 PS3 高功率端口，用户设备或配件连接到这些端口存在火灾风险；使用这些端口前，应确保所连接的设备或配件具备防火安全措施。 </p></li><li><p>仅将便携式电源连接到符合GB4943.1第 6.3、6.4 和 6.5 条款（或其它等效标准）的设备或配件。 </p></li><li><p>此外，为了实现最大输出功率，请使用电小二官方USB-C to USB-C 5A 数据线（20V  DC/5A，100W）。</p></li></ul></td></tr></tbody></table>

<span id="native-p9-b4-l0-0"></span>

## 屏幕显示

<figure aria-label="LCD屏幕" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCD屏幕" class="hb-lcd-mode-art" src="assets/lcd-screen-p9.svg"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3"><strong>屏幕</strong><br/><strong>短亮</strong></td><td class="hb-lcd-mode-action">打开</td><td class="hb-lcd-mode-copy">短按总电源开关键或有充电输入。</td></tr><tr><td class="hb-lcd-mode-action">关闭</td><td class="hb-lcd-mode-copy">短按总电源开关键。</td></tr><tr><td class="hb-lcd-mode-action">自动关闭</td><td class="hb-lcd-mode-copy">2分钟后显示屏将自动熄灭，进入休眠模式。</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3"><strong>屏幕</strong><br/><strong>常亮</strong></td><td class="hb-lcd-mode-action">打开</td><td class="hb-lcd-mode-copy">开机状态下，双击总电源开关键。</td></tr><tr><td class="hb-lcd-mode-action">关闭</td><td class="hb-lcd-mode-copy">短按总电源开关键。</td></tr><tr><td class="hb-lcd-mode-action">自动关闭</td><td class="hb-lcd-mode-copy">在常亮模式下，无充放电情况，屏幕将在 2 小时后自动熄灭。</td></tr></tbody></table></div></figure>

<span id="native-p10-b2-l0-0"></span>

## 节能模式

<p>为防止因忘记关闭输出而造成电池电量的额外消耗，产品默认开启节能模式。当未连接设备，或已连接设备的功率低于设定值（AC 输出 25W；USB输出 2W）时，产品将在 12 小时后关闭输出。AC或DC输出开启状态下，屏幕将显示节能图标“12H”。该图标的显示时长将根据app设定的节能时间而变化。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="energy-saving-p10" data-source-fragment-sha256="b1ffa32fda895d3f135091c5eab7f0b072b565eda4251c340dc8a6e79f401664" data-web-base-art-ref="energy-saving" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="energy-saving-p10.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/energy-saving-p10.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.3739%;--hb-y:6.1897%;--hb-width:94.0218%;--hb-height:13.7298%;--hb-fill:#f2f2f3">在AC输出按键开启状态下，同时长按AC输出按键与总电源开关键，持续按压直至节能图标显示（开启）与隐藏（关闭）状态切换。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:58.1364%;--hb-y:83.3851%;--hb-width:2.6788%;--hb-height:6.3251%">3s</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.9622%;--hb-y:87.1574%;--hb-width:7.4099%;--hb-height:5.4238%">长按3秒</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:61.6628%;--hb-y:80.7682%;--hb-width:10.1277%;--hb-height:6.2911%"><strong>开启/关闭</strong></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:48.0658%;--hb-y:59.9578%;--hb-width:11.018%;--hb-height:5.0732%">总电源开关键</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:75.0825%;--hb-y:59.9578%;--hb-width:10.1942%;--hb-height:5.0732%">AC输出按键</span></div></div></figure>

<p>※ 使用交流25W及直流2W以下低功耗设备时，请关闭节能模式以避免输出中途自动关闭。关闭节能模式后，屏幕将不再显示“12H”图标。此时，输出不会自动关闭。</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">说明</td><td class="manual-callout-body"><p>节能模式在设备重新上电后会恢复至上次的状态。如需更改模式，需手动切换。</p></td></tr></tbody></table>

<span id="native-p10-b0-l0-0"></span>

## 组合按键

<figure aria-label="按键 / 操作 / 功能" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">按键</th><th class="hb-key-operation" scope="col">操作</th><th class="hb-key-function" scope="col">功能</th></tr></thead><tbody><tr><td class="hb-key-buttons">总电源开关键+ AC 输出按键</td><td class="hb-key-operation">3s 长按3秒</td><td class="hb-key-function">切换节能模式</td></tr><tr><td class="hb-key-buttons">USB输出按键+ AC 输出按键</td><td class="hb-key-operation">1s 长按1秒</td><td class="hb-key-function">Wi-Fi＆蓝牙开关</td></tr><tr><td class="hb-key-buttons">总电源开关键+ USB输出按键</td><td class="hb-key-operation">3s 长按3秒</td><td class="hb-key-function">Wi-Fi&amp;蓝牙重置</td></tr></tbody></table></figure>

<span id="native-p11-b3-l0-0"></span>

# 不间断电源（UPS）

<p>本产品通过AC电源线连接电网，电器可以使用本产品的交流输出端口工作（此时交流电来自电网，而不是电池），当电网突然断电后，本产品可以在10 ms内自动换为本产品电池供电模式。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups-p11" data-source-fragment-sha256="ac6f4160d98d006e70678d4a343b0201dee4ee5a9048b700266cfb06a6f19c05" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups-p11.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups-p11.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:44.0714%;--hb-y:69.4458%;--hb-width:28.9887%;--hb-height:4.257%">* 确保总电源开关键已打开。</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><ul><li><p>本产品不支持0ms切换，请勿接到要求0ms切换供电的设备上，例如数据服务器或工作站，请充分测试确认兼容性后使用。 </p></li><li><p>使用UPS功能连接负载时，请勿超出设备最大输出功率，以防触发过载保护。 </p></li><li><p>因未按说明操作导致设备异常或数据丢失，本公司不承担相关责任。</p></li></ul></td></tr></tbody></table>

<span id="native-p12-b3-l0-0"></span>

# 连接

<span id="native-p12-b4-l0-0"></span>

## <span class="native-plain-title">与加电包连接（单独售卖）</span>

<p>本产品最多搭载5个加电包，可满足大容量的需求。<br/>关于加电包的使用说明，详见加电包 3600说明书。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-stack-p12" data-source-fragment-sha256="170913664d86d6f9005ede5f718a964d2b908d0c052fe95815548d7552721f0d" data-web-base-art-ref="battery-stack" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-stack-p12.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-stack-p12.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:25.992%;--hb-y:76.2329%;--hb-width:18.8429%;--hb-height:4.2006%">间隔至少200mm距离</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:54.4916%;--hb-y:76.2329%;--hb-width:18.8429%;--hb-height:4.2006%">间隔至少200mm距离</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><ul><li><p>在便携式储能电源 3600 Plus连接加电包之前，请确保所有设备的电源处于关闭状态。 </p></li><li><p>为保证设备的正常运行，请勿堵塞设备两侧的进气口和排气口。建议进气口和排气口外部至少留出200mm的空间，以保证设备充分散热。</p></li></ul></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-accessories-p12" data-source-fragment-sha256="0e825750604accb92b596e7dfe5ddeafaa3060bdf5c68fc254bf3498881e7a6f" data-web-base-art-ref="battery-accessories" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-accessories-p12.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-accessories-p12.svg"/><span class="hb-reference-live-label hb-reference-live-pill hb-reference-source-badge" data-source-line="0" style="--hb-x:75.7305%;--hb-y:33.2347%;--hb-width:24.0436%;--hb-height:35.018%;--hb-fill:#a8aaac;--hb-label-color:#ffffff"><img alt="" src="assets/sold-separately-cart.svg"/><strong>单独售卖</strong></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:35.7716%;--hb-y:71.8555%;--hb-width:13.7623%;--hb-height:10.4367%">加电包连接线</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:8.5803%;--hb-y:71.8555%;--hb-width:13.0961%;--hb-height:10.4367%">加电包 3600</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:60.183%;--hb-y:71.8555%;--hb-width:9.3542%;--hb-height:10.4367%">用户指南</span></div></div></figure>

<span id="native-p13-b8-l0-0"></span>

# 并机连接

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">说明</td><td class="manual-callout-body"><ul><li><p>并机插排单独售卖，请到电小二官网进行购买。 </p></li><li><p>设备并机运行期间，仅支持太阳能充电，不支持市电充电。</p></li></ul></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">提示</td><td class="manual-callout-body"><p>在连接并机插排前，请确保设备的AC输出已关闭（AC输出按键的指示灯熄灭），以防激活AC输出时损坏设备。</p></td></tr></tbody></table>

<ol><li><p>确保所有设备的电源处于关闭状态。</p></li><li><p>用并机连接器连接每个设备的并机端口。</p></li><li><p>按下主电源按钮，将设备开机。</p></li><li><p>1分钟内，依次按下每个设备的AC输出按键启动交流输出。</p></li></ol>

<ul><li><p>连接成功时，LCD屏幕<img alt="" src="assets/native-inline-parallel-connected-p13.svg"/>图标点亮。</p></li><li><p>连接失败时，LCD显示屏显示对应的故障代码<img alt="" src="assets/native-inline-parallel-fault-p13.svg"/>。再次按下每个设备上的AC输出按键可尝试解决此故障。</p></li></ul>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-p13" data-source-fragment-sha256="38661340e43de78186c757ae4ef4bc983d3375f9cb65be22fa8e033507a7e11e" data-web-base-art-ref="parallel" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-p13.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-p13.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:13.0551%;--hb-y:75.4252%;--hb-width:27.8512%;--hb-height:4.6228%">便携式储能电源 3600 Plus</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:48.6859%;--hb-y:86.2695%;--hb-width:16.2034%;--hb-height:4.6228%">电小二并机排插</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:53.3935%;--hb-y:3.0297%;--hb-width:8.8236%;--hb-height:4.4029%"><span>并机端口</span></span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><ul><li><p>并机成功后，请勿在并机AC输出工作时断开并机连接线，否则其他设备可能触发过载保护。 </p></li><li><p>设备AC输出口工作（AC输出按钮指示灯亮），请勿触摸并机连接线端口。并机连接线端口电压为220V，有触电风险。</p></li></ul></td></tr></tbody></table>

<p>如果按下任一设备的交流输出按钮，或因故障中断AC输出，所有设备都将立即停止AC输出，系统自动退出并机模式。其他设备LCD显示屏上的并机图标闪烁，代表并机连接失败。<br/>再次按下每个设备上的AC输出按键，恢复并机输出。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-interrupted-p14" data-source-fragment-sha256="165f6c0cf672a0e2d5bdc078e2dfb64eac51df8641b7310caf6370b8288232b2" data-web-base-art-ref="parallel-interrupted" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-interrupted-p14.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-interrupted-p14.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:27.8312%;--hb-y:7.2708%;--hb-width:16.1321%;--hb-height:5.469%">电小二并机排插</span></div></div></figure>

<span id="native-p14-b4-l0-0"></span>

## 退出并机模式

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="parallel-exit-p14" data-source-fragment-sha256="5452377ca0b8bb467265e026104f41e97404ac2a454b0e2b6c893e0a398db652" data-web-base-art-ref="parallel-exit" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="parallel-exit-p14.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/parallel-exit-p14.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:6.0712%;--hb-y:31.1719%;--hb-width:18.4602%;--hb-height:4.5875%">1. 断开所有负载。</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:6.0712%;--hb-y:58.9446%;--hb-width:28.8265%;--hb-height:4.5875%">2. 关闭所有设备的AC输出。</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.0712%;--hb-y:90.8912%;--hb-width:29.8805%;--hb-height:4.5875%">3. 移除设备上的并机连接线。</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:82.9989%;--hb-y:19.5646%;--hb-width:11.6192%;--hb-height:4.5875%">大功率设备</span></div></div></figure>

<span id="native-p15-b5-l0-0"></span>

# 充电方式

<p><strong>绿色能源优先模式：</strong>本产品倡导优先使用绿色能源，本产品支持太阳能充电与市电充电同时使用。当同时开启市电充电与太阳能充电时，产品会优先太阳能充电且太阳能充电与市电充电同时以电池最大允许功率充电。</p>

<p><img alt="" src="assets/shared-symbol_warning_triangle.svg"/><strong>首次使用前请先将本设备充满电！</strong></p>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">提示</td><td class="manual-callout-body"><ul><li><p>产品充放电环境温度为 -20℃~45℃，超出此温度范围会限制产品充放电，甚至无法充放电。 </p></li><li><p>产品的充电功率和电池能量会因温度的变化有所差异。</p></li></ul></td></tr></tbody></table>

<span id="native-p15-b8-l0-0"></span>

## 市电充电

<p>请使用官方标配的AC电源线。</p>

<img alt="charging-ac" src="assets/charging-ac-p15.svg"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>请确保 AC 充电线插头牢固且完全插入产品的 AC 输入接口，避免因插入不完全引发电流不稳、发热或接触不良等问题，影响设备正常运行。</p></td></tr></tbody></table>

<span id="native-p15-b9-l0-0"></span>

## 太阳能充电

<p>本产品有两个DC8020 直流输入端口，最大支持1000W输入，可搭配电小二SolarSaga 系列太阳能板使用。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar-p15" data-source-fragment-sha256="3a430da1aa4a54229314b1f89eac22a7893f543e5a0bf2e13d4a1979c0e98010" data-web-base-art-ref="charging-solar" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-solar-p15.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-solar-p15.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.9934%;--hb-y:88.5834%;--hb-width:15.45%;--hb-height:6.4478%">SolarSaga 200 × 2</span></div></div></figure>

<p>如果单个DC8020直流输入端口需要同时连接两个太阳能板，请参考下图，需使用太阳能串联转接盒（单独售卖）。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-solar-four-p16" data-source-fragment-sha256="bf0301395478e7b209a83891989c2296732c91a329f73bc320d05ddeeb217438" data-web-base-art-ref="charging-solar-four" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-solar-four-p16.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-solar-four-p16.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:40.588%;--hb-y:82.1067%;--hb-width:33.3073%;--hb-height:4.4255%;--hb-fill:#ffffff">太阳能串联转接盒（单独售卖）</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:71.2515%;--hb-y:76.3315%;--hb-width:15.4929%;--hb-height:3.4576%">SolarSaga 200 × 4</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>单个DC8020输入端口请勿连接两个以上光伏板。</p></td></tr></tbody></table>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>同时连接到两个DC输入端口的电源，其电压必须保持一致，否则可能导致产品异常或损坏。例如： </p><ul><li><p>连接太阳能板至两个DC8020输入端口时，请使用相同型号的太阳能板，并确保连接的数量一致。 </p></li><li><p>给产品充电时，请勿同时使用车载充电与光伏充电，否则可能烧坏车内保险丝或无法充电。</p></li></ul></td></tr></tbody></table>

<p>建议使用电小二的太阳能板为本产品充电。请确保所用太阳能板的开路电压（V<sub>oc</sub>）在3600 Plus的直流输入电压范围内（16V -60V）。因使用第三方太阳能板或配件而导致的任何损坏或损失，电小二概不负责。</p>

<span id="native-p17-b11-l0-0"></span>

## 车充充电

<p>本产品适用 12V 车型车充口对本产品进行充电，请确保汽车车充口和车充线的点烟器接触良好，确保点烟器完全插入到位。</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charging-car-p17" data-source-fragment-sha256="5d4d3bbd178f4a217cd9ec35e0dbd05a4249184290aa9ba053d57d5fc3c41858" data-web-base-art-ref="charging-car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charging-car-p17.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/charging-car-p17.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.1983%;--hb-y:19.5207%;--hb-width:5.5983%;--hb-height:6.7179%">车辆</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:63.3853%;--hb-y:76.2842%;--hb-width:26.1269%;--hb-height:6.0278%">*车载充电线需单独购买。</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><ul><li><p>请在汽车点火启动后使用车充充电，以免造成汽车电瓶亏电无法启动。 </p></li><li><p>汽车在行驶过程中，路况颠簸，禁止使用车充充电，防止车充接触不良，引起接触点烧坏。若因不按规范操作而造成损失，本公司不予承担相应责任。 </p></li><li><p>车充充电只支持 12V 车型，不支持 24V 车型，请勿使用 24V 车型的车给本产品充电以免造成人身伤害及财产损失。</p></li></ul></td></tr></tbody></table>

<span id="native-p17-b1-l0-0"></span>

# 存储

<p>请将产品存放在干燥、清洁、通风良好的环境中。存储温度和湿度要求如下：</p>

<ul><li><p>1 个月： -20℃ ～ 45℃（0 - 60%RH）</p></li><li><p>3 个月： 0℃ ～ 45℃（0 - 60%RH）</p></li><li><p>12 个月： 0℃ ～ 25℃（0 - 60%RH）</p></li></ul>

<p>若产品在电量耗尽的情况下长时间（3～6 个月）存放，可能会导致无法再次充电。为避免此情况并保持电池健康，建议每隔三个月检查并为产品充电一次，并在 <strong>6～12 个月内至少进行一次完整的充放电循环。</strong></p>

<span id="native-p18-b1-l0-0"></span>

# 故障处理

<p>如果出现以下任一故障代码，请按照所列的处理方法进行处理。如故障仍然存在，请联系电小二客户支持。</p>

<figure aria-label="故障代码 / 处理方法" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">故障代码</th><th class="hb-troubleshooting-measures" scope="col">处理方法</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0</td><td class="hb-troubleshooting-measures">重启产品。</td></tr><tr><td class="hb-troubleshooting-code">F1</td><td class="hb-troubleshooting-measures">重启产品。</td></tr><tr><td class="hb-troubleshooting-code">F2</td><td class="hb-troubleshooting-measures">重启产品。</td></tr><tr><td class="hb-troubleshooting-code">F3</td><td class="hb-troubleshooting-measures">重启产品。</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">将产品连接负载，放电直至故障消失。</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">通过太阳能板或交流墙充为产品充电，直至故障消失。</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures"><ol><li><p>待电网恢复正常后再通过交流墙插为产品充电。 </p></li><li><p>检查进风口和出风口是否堵塞；确保产品两侧有 20 厘米的间隙。 </p></li><li><p>将产品放置在避免阳光直射、环境温度低于45℃的地方。 </p></li><li><p>断开产品连接的所有负载，保持产品空闲待机，等待故障消失。检查负载的启动功率是否超出本产品的输出范围。 </p></li><li><p>重启产品。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures"><ol><li><p>移除连接到产品的所有太阳能板。 </p></li><li><p>检查连接到产品的太阳能板的开路电压（V<sub>oc</sub>）。产品允许的最大直流输入电压为 60V。 </p></li><li><p>重启产品，保持产品空闲待机，等待故障消失。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">请联系经销商或电小二客户支持。</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">移除连接到产品 USB 端口的负载，等待故障消失。</td></tr><tr><td class="hb-troubleshooting-code">FA</td><td class="hb-troubleshooting-measures"><ol><li><p>关闭两台设备的交流输出。 </p></li><li><p>在 1 分钟内依次再次按下每台设备的交流电源按钮。</p></li></ol></td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures">重启产品。</td></tr></tbody></table></figure>

<span id="native-p19-b24-l0-0"></span>

# 技术参数

## 基本规格

<figure aria-label="基本规格" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">名称</th><td class="manual-spec-value hb-spec-value">便携式储能电源</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">型号</th><td class="manual-spec-value hb-spec-value">JE-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">电芯类型</th><td class="manual-spec-value hb-spec-value">磷酸铁锂电芯</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">电池能量</th><td class="manual-spec-value hb-spec-value">3584 Wh</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC 额定输出能量</th><td class="manual-spec-value hb-spec-value">2795 Wh</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">尺寸</th><td class="manual-spec-value hb-spec-value">约385×309×491 mm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">重量</th><td class="manual-spec-value hb-spec-value">约 35 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">循环寿命</th><td class="manual-spec-value hb-spec-value">6000 次循环，≥70%SOH</td></tr></tbody></table></figure>

## 输入

<figure aria-label="输入" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC</th><td class="manual-spec-value hb-spec-value">220V-240V~ 50Hz, 最大10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × DC输入(8020端口)</th><td class="manual-spec-value hb-spec-value">光伏：16V-60V⎓12A，双路最大24A/最大1000W 车充：12V-16V⎓最大8A，双路最大8A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">加电包连接端口</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V，最大100A</td></tr></tbody></table></figure>

## 输出

<figure aria-label="输出" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × AC输出</th><td class="manual-spec-value hb-spec-value">220V~ 50Hz，16.36A，额定3600W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC总输出</th><td class="manual-spec-value hb-spec-value">额定3600W，瞬时最大7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC旁路输出<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value">220V-240V~ 50Hz，最大10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-C 100W</th><td class="manual-spec-value hb-spec-value">5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A, 最大100W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-A 18W</th><td class="manual-spec-value hb-spec-value">5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A, 最大18W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">并机端口</th><td class="manual-spec-value hb-spec-value">220V~ 50Hz，额定3500W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC并机输出<sup class="hb-spec-reference">②</sup></th><td class="manual-spec-value hb-spec-value">220V~ 50Hz，32A，最大7000W，瞬时最大14000W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">加电包连接端口</th><td class="manual-spec-value hb-spec-value">36.4V-50.4V，最大60A</td></tr></tbody></table></figure>

## 工作环境温度

<figure aria-label="工作环境温度" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">充电温度</th><td class="manual-spec-value hb-spec-value">-20°C ~ 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">放电温度</th><td class="manual-spec-value hb-spec-value">-20°C ~ 45°C</td></tr></tbody></table></figure>

<p>※USB Type-C<sup>®</sup> 和 USB-C<sup>®</sup> 是 USB Implementers Forum 的注册商标。</p>

<p>①：产品支持边充边放。</p>

<p>②：产品支持两台设备并机。</p>

<span id="native-p20-b15-l0-0"></span>

# APP操作说明书

<span id="native-p20-b0-l0-0"></span>

## 1. 下载并登录App

<figure aria-label="1. 下载并登录App" class="hb-app-download-composition hb-app-download-qr-only" data-component-id="HB-SPECIAL-APP"><p class="hb-app-download-copy">在App Store或者国内各大应用市场搜索<br/>“电小二”App安装并注册登录。<br/>或扫描右边二维码下载电小二App。</p><img alt="电小二 App 下载二维码" class="hb-app-download-art-qr" src="assets/app-qr-native.png"/></figure>

<span id="native-p20-b4-l0-0"></span>

## 2. 添加设备

<p>2.1 在App内点击 <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> 添加设备。</p>

<p><span>2.2 长按设备上的“总电源开关键”开机，设备上的Wi-Fi和蓝牙图标闪烁后表示设备已进入配网模式，在App内点击“图标已快闪”按钮并允许应用连接附近的设备和打开蓝牙权限。</span></p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add-p20" data-source-fragment-sha256="d6e340e61d1c5a59243e89f31c43a17ad3250513d4e13055208285b5a376fc53" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add-p20.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-phones-native-p20.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:16.9599%;--hb-y:92.3772%;--hb-width:4.5193%;--hb-height:4.606%">2.1</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:78.6785%;--hb-y:92.3772%;--hb-width:4.8378%;--hb-height:4.606%">2.2</span></div></div></figure>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">备注</td><td class="manual-callout-body"><p>打开设备，如果两小时内未连接到APP，设备会自动关闭Wi-Fi和蓝牙。</p></td></tr></tbody></table>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-controls-p20" data-source-fragment-sha256="aea6fbe83cc3fc74b8fd7a2d114691b9f51ead6ee71c42ceed8099871fa0a7d4" data-web-base-art-ref="app-controls" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-controls-p20.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-controls-p20-web.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:75.9113%;--hb-y:63.6323%;--hb-width:12.8489%;--hb-height:10.071%">AC输出按键</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:7.5149%;--hb-y:37.1023%;--hb-width:13.8978%;--hb-height:10.071%">总电源开关键</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:7.5149%;--hb-y:63.8283%;--hb-width:14.553%;--hb-height:10.071%">USB输出按键</span></div></div></figure>

<p><span>2.3 点击搜索到的设备图标后App通过蓝牙自动连接设备。</span></p>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">备注</td><td class="manual-callout-body"><p>如果在绑定过程中提示“设备已被绑定”，可通过以下两种方式连接:</p><ul><li><p>设备拥有者通过App将此设备分享给其他用户；</p></li><li><p>同时长按“总电源开关按键”和“USB输出按键”重置设备Wi-Fi后可重新绑定设备。</p></li></ul></td></tr></tbody></table>

<p><span>2.4 设备连接成功后输入设备将要连接的Wi-Fi名称和密码，设备自动连接到Wi-Fi网络。</span></p>

<table class="manual-callout-table"><tbody><tr><td class="manual-callout-label">备注</td><td class="manual-callout-body"><p>请选择2.4GHz频段的Wi-Fi网络，设备不支持5GHz频段的Wi-Fi网络。</p></td></tr></tbody></table>

<p><span>2.5 设备添加成功后进入设备主页面，设备上的Wi-Fi图标会常亮。</span></p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-connect-p21" data-source-fragment-sha256="52c19129b151da82b7dcc38337578e994d57e8e4ad89c1f0d5f437f03a70e7eb" data-web-base-art-ref="app-connect" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-connect-p21.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-phones-native-p21.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:83.7939%;--hb-y:90.8639%;--hb-width:4.0301%;--hb-height:5.2995%">2.5</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:12.6595%;--hb-y:90.8639%;--hb-width:4.065%;--hb-height:5.2995%">2.3</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:48.2092%;--hb-y:90.8639%;--hb-width:4.0837%;--hb-height:5.2995%">2.4</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:75.4695%;--hb-y:5.6038%;--hb-width:5.6652%;--hb-height:6.3125%">3600 Plus</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:77.5949%;--hb-y:47.845%;--hb-width:4.3981%;--hb-height:7.8106%"><strong>800W</strong></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:77.2625%;--hb-y:57.2222%;--hb-width:5.2516%;--hb-height:7.8106%"><strong>1000W</strong></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:6.9089%;--hb-y:61.4006%;--hb-width:5.3636%;--hb-height:6.3125%">1000 Lite</span></div></div></figure>

<p>图片仅供参考</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">注意</td><td class="manual-callout-body"><p>App 通过蓝牙与储能设备连接，每次仅支持一台设备。连接后返回设备列表时，蓝牙连接将自动断开。再次点击储能设备图标时，App 会自动重新连接。</p></td></tr></tbody></table>

<span id="native-p21-b2-l0-0"></span>

## 3. 解绑设备

<p>     点击设备主界面右上角的设置按钮进入设置页面，点击页面最下方的解除绑定按钮解绑设备。</p>

<span id="native-p22-b4-l0-0"></span>

## 4. 其他说明

<p><span>4.1 打开Wi-Fi&amp;蓝牙：</span></p>

<p>开机后自动打开Wi-Fi&amp;蓝牙，屏幕上的Wi-Fi&amp;蓝牙图标点亮表示Wi-Fi&amp;蓝牙已被打开。<br/>同时长按“AC输出按键”和“USB输出按键”1秒手动打开Wi-Fi和蓝牙。</p>

<p><span>4.2 关闭Wi-Fi&amp;蓝牙：</span></p>

<p>两小时内未连接WiFi或蓝牙，设备上的Wi-Fi&amp;蓝牙会自动关闭。<br/>同时长按“ AC输出按键”和“USB输出按键”1秒手动关闭Wi-Fi和蓝牙。</p>

<p><span>4.3 重置Wi-Fi&amp;蓝牙：</span></p>

<p>同时长按“总电源开关按键”和“USB输出按键”将重置 Wi-Fi和蓝牙，同时清除App中的自定义设置。</p>

## 合格证

<table class="manual-table"><tbody><tr><td><p>检验员：</p></td><td><p>QC PASS 01</p></td></tr><tr><td><p>检验日期：</p></td><td></td></tr></tbody></table>

<p>广东电小二科技有限公司</p>

<img alt="电小二品牌公众号二维码" src="assets/manufacturer-qr-native.png"/>

<p><span>关注官方品牌公众号</span></p>

<p><span>获取更多资讯服务</span></p>

<p><span>制造商/生产厂：深圳市华宝新能源股份有限公司</span></p>

<p><span>地址：深圳市龙华区大浪街道同胜社区华繁路东侧嘉安达科技工业园</span></p>
