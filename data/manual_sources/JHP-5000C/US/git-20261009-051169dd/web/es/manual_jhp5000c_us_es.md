<style>
/* Native figure geometry only. Shared Web theme owns headings/tables/callouts. */
.native-figure { max-width:760px; margin:1rem auto; min-width:0; }
.native-figure .hb-reference-figure { margin:0; max-width:none; }
#furo-main-content .native-figure img { width:100% !important; height:auto !important; max-height:none; }

.native-dense {max-width:780px;}
.native-lcd-map {max-width:680px;}
#furo-main-content .native-figure .hb-reference-live-label {font-size:1.75cqw;line-height:1;align-items:flex-start;justify-content:flex-start;text-align:left;padding:.1cqw;}
.native-figure .hb-reference-live-label > span {width:100%;}
.native-overview-front .hb-reference-live-label,.native-overview-left .hb-reference-live-label,.native-overview-right .hb-reference-live-label {font-size:1.55cqw!important;}
.native-figure .hb-reference-live-label strong {font-weight:700;}
.native-operation {border:1px solid var(--hb-line-soft);border-radius:var(--hb-panel-radius);}
.native-inbox-main {max-width:180px;}
.native-app-add {max-width:480px;}
.native-app-results {max-width:700px;}
.native-lcd-side {display:grid;grid-template-columns:1fr 1.45fr;gap:1rem;align-items:stretch;}
.native-lcd-side .native-figure {margin:0;}
.native-lcd-side > .native-figure img {height:100%!important;object-fit:contain;}
.native-figure .hb-reference-live-pill {border-radius:.8cqw;}
@media(max-width:760px){
 .native-dense{overflow-x:auto;padding-bottom:.4rem;}
 .native-dense > .hb-reference-figure{min-width:680px;}
 .native-lcd-side{display:block;}
 .native-lcd-side > .native-figure{max-width:330px;margin:0 auto 1rem;}
}

.native-figure .hb-reference-live-label {white-space:nowrap;}

.native-inline-plus{display:inline-grid;place-items:center;width:1.1em;height:1.1em;border-radius:50%;background:#444;color:#fff;line-height:1;font-weight:700;vertical-align:baseline;}
.native-lcd-note{font-weight:400;font-size:.92em;}

/* Source speech tails are CSS shapes, never leftover blank artwork. */
.native-power .hb-reference-art-panel::after,.native-ups .hb-reference-art-panel::after,.native-sts-connect .hb-reference-art-panel::after {content:"";position:absolute;z-index:1;pointer-events:none;width:5.9%;height:5.5%;background:#f2f2f3;clip-path:polygon(50% 0,100% 100%,0 100%);}
.native-power .hb-reference-art-panel::after{left:45.36%;top:53.65%;width:4.61%;height:4.87%;clip-path:polygon(47.13% 0,100% 100%,0 100%);}
.native-ups .hb-reference-art-panel::after{left:40.60%;top:65.72%;width:5.82%;height:4.95%;clip-path:polygon(47.13% 0,100% 100%,0 100%);}
.native-sts-connect .hb-reference-art-panel::after{left:40.64%;top:33.16%;width:5.82%;height:5.77%;background:#fff;clip-path:polygon(0 0,100% 0,47.13% 100%);}
.native-package-battery,.native-package-sts{border-style:dashed;border-radius:0;}
/* Source-derived label geometry */
html[lang="fr"] .native-overview-front [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="3"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="4"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="5"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="6"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="7"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="8"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="9"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="10"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="11"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="12"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="13"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="14"] {font-size:1.4365cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="15"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="16"] {font-size:1.4365cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="17"] {font-size:1.4365cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="18"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="19"] {font-size:1.4365cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="20"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="21"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="22"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="23"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="24"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="25"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="26"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-front [data-source-line="27"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="2"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="3"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="4"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="6"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="7"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="8"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="9"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="10"] {font-size:1.8927cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="11"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="12"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="13"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="14"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="15"] {font-size:1.6719cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="16"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-left [data-source-line="17"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="1"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="3"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="4"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="6"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="7"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="8"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="9"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="10"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="11"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="12"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="13"] {font-size:1.5773cqw!important;}
html[lang="fr"] .native-overview-right [data-source-line="14"] {font-size:2.2082cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="0"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="1"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="2"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="3"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="4"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="5"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="6"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="7"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="8"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="9"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="10"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="11"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="12"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="13"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="14"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="15"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="16"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="17"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="18"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="19"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="20"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="21"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-lcd-map [data-source-line="22"] {font-size:2.1995cqw!important;}
html[lang="fr"] .native-power [data-source-line="0"] {font-size:3.1847cqw!important;}
html[lang="fr"] .native-power [data-source-line="1"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-power [data-source-line="2"] {font-size:3.1847cqw!important;}
html[lang="fr"] .native-power [data-source-line="3"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-power [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-power [data-source-line="5"] {font-size:2.2293cqw!important;}
html[lang="fr"] .native-power [data-source-line="6"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-power [data-source-line="6"] {padding:1.6703cqw 1.7347cqw!important;}
html[lang="fr"] .native-power [data-source-line="6"] {border-radius:1.9108cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="0"] {font-size:2.1019cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="0"] {padding:0.8120cqw 1.7486cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="1"] {font-size:3.1847cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="3"] {font-size:3.1847cqw!important;}
html[lang="fr"] .native-ac-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="0"] {padding:0.7966cqw 1.7485cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="1"] {font-size:2.5478cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="3"] {font-size:2.5478cqw!important;}
html[lang="fr"] .native-usb-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="0"] {padding:0.7966cqw 1.7485cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="1"] {font-size:2.5478cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="3"] {font-size:2.5478cqw!important;}
html[lang="fr"] .native-dc-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-ups [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="fr"] .native-ups [data-source-line="0"] {padding:2.8392cqw 2.6258cqw!important;}
html[lang="fr"] .native-ups [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="fr"] .native-battery-packs [data-source-line="0"] {font-size:1.9355cqw!important;}
html[lang="fr"] .native-battery-packs [data-source-line="1"] {font-size:1.9355cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="0"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="0"] {padding:2.5038cqw 2.4362cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="0"] {border-radius:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="1"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="2"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="3"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="4"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="5"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="6"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="7"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="8"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-sts-connect [data-source-line="9"] {font-size:1.9090cqw!important;}
html[lang="fr"] .native-ac-charge [data-source-line="0"] {font-size:1.9096cqw!important;}
html[lang="fr"] .native-ac-charge [data-source-line="1"] {font-size:1.9096cqw!important;}
html[lang="fr"] .native-ac-charge [data-source-line="2"] {font-size:1.9096cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="0"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="1"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="2"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="3"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="4"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="5"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="6"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="7"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="8"] {font-size:0.5308cqw!important;}
html[lang="fr"] .native-sts-charge [data-source-line="9"] {font-size:1.9102cqw!important;}
html[lang="fr"] .native-low-pv-500 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="fr"] .native-low-pv-500 [data-source-line="1"] {font-size:1.6243cqw!important;}
html[lang="fr"] .native-low-pv-200 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="fr"] .native-low-pv-200 [data-source-line="1"] {font-size:1.4327cqw!important;}
html[lang="fr"] .native-low-pv-200 [data-source-line="2"] {font-size:1.6243cqw!important;}
html[lang="fr"] .native-high-pv [data-source-line="0"] {font-size:1.9507cqw!important;}
html[lang="fr"] .native-high-pv [data-source-line="1"] {font-size:1.9507cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="0"] {font-size:2.5592cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="1"] {font-size:2.5592cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="2"] {font-size:1.9194cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="3"] {font-size:1.9194cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="4"] {font-size:1.9194cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="5"] {font-size:1.9194cqw!important;}
html[lang="fr"] .native-high-pv-lock [data-source-line="6"] {font-size:1.9194cqw!important;}
html[lang="fr"] .native-car [data-source-line="0"] {font-size:2.2283cqw!important;}
html[lang="fr"] .native-car [data-source-line="1"] {font-size:1.5917cqw!important;}
html[lang="fr"] .native-car [data-source-line="1"] {padding:1.1709cqw 1.0996cqw!important;}
html[lang="fr"] .native-car [data-source-line="1"] {border-radius:1.9100cqw!important;}
html[lang="fr"] .native-app-add [data-source-line="0"] {font-size:3.1735cqw!important;}
html[lang="fr"] .native-app-add [data-source-line="1"] {font-size:3.1735cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="0"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="1"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="2"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="3"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="4"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="5"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="6"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-control [data-source-line="7"] {font-size:1.9887cqw!important;}
html[lang="fr"] .native-app-results [data-source-line="0"] {font-size:2.0509cqw!important;}
html[lang="fr"] .native-app-results [data-source-line="1"] {font-size:2.0509cqw!important;}
html[lang="fr"] .native-app-results [data-source-line="2"] {font-size:2.0509cqw!important;}
html[lang="fr"] .native-ess [data-source-line="0"] {font-size:1.9374cqw!important;}
html[lang="fr"] .native-ess [data-source-line="1"] {font-size:1.9374cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="0"] {font-size:0.1680cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="1"] {font-size:0.7963cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="2"] {font-size:0.3676cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="3"] {font-size:0.2471cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="4"] {font-size:0.5295cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="5"] {font-size:0.1667cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="6"] {font-size:0.1667cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="7"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-host [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="0"] {font-size:0.1654cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="1"] {font-size:1.9396cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="1"] {padding:2.8465cqw 10.5169cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="1"] {border-radius:4.8046cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="1"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="fr"] .native-package-battery [data-source-line="2"] {font-size:0.8441cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="3"] {font-size:0.3867cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="4"] {font-size:0.2432cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="5"] {font-size:0.5212cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="6"] {font-size:0.1641cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="7"] {font-size:0.1641cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-battery [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="0"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="1"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="2"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="3"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="4"] {font-size:0.2548cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="5"] {font-size:0.2038cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="6"] {font-size:0.2038cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="7"] {font-size:0.1960cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="8"] {font-size:0.9239cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="9"] {font-size:0.5618cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="10"] {font-size:0.0944cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="11"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="12"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="13"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="14"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="15"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="16"] {font-size:0.2794cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="17"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="18"] {font-size:0.0492cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="19"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="20"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="21"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="22"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="23"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="24"] {font-size:0.8885cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="25"] {font-size:0.4152cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="26"] {font-size:0.1960cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="27"] {font-size:0.1960cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="28"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="29"] {font-size:0.1960cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="30"] {font-size:0.1960cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="31"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="32"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="33"] {font-size:0.1458cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="34"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="35"] {font-size:0.1631cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="36"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="37"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="38"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="39"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="40"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="41"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="42"] {font-size:1.9396cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="42"] {padding:2.8466cqw 10.5169cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="42"] {border-radius:4.8046cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="42"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="fr"] .native-package-sts [data-source-line="43"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="44"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="45"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="46"] {font-size:1.6015cqw!important;}
html[lang="fr"] .native-package-sts [data-source-line="47"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="3"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="4"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="6"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="7"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="8"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="9"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="10"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="11"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="12"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="13"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="14"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="15"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="16"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="17"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="18"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="19"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="20"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="21"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="22"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-front [data-source-line="23"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="2"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="3"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="4"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="6"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="7"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="8"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="9"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="10"] {font-size:1.8927cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="11"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="12"] {font-size:1.6719cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="13"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="14"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="15"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="16"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-left [data-source-line="17"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="1"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="3"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="4"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="6"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="7"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="8"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="9"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="10"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="11"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="12"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="13"] {font-size:1.5773cqw!important;}
html[lang="en"] .native-overview-right [data-source-line="14"] {font-size:2.2082cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="0"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="1"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="2"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="3"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="4"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="5"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="6"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="7"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="8"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="9"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="10"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="11"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="12"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="13"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="14"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="15"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="16"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="17"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="18"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="19"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="20"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="21"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-lcd-map [data-source-line="22"] {font-size:2.1995cqw!important;}
html[lang="en"] .native-power [data-source-line="0"] {font-size:3.1847cqw!important;}
html[lang="en"] .native-power [data-source-line="1"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-power [data-source-line="2"] {font-size:3.1847cqw!important;}
html[lang="en"] .native-power [data-source-line="3"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-power [data-source-line="4"] {font-size:2.2293cqw!important;}
html[lang="en"] .native-power [data-source-line="5"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-power [data-source-line="5"] {padding:2.3073cqw 2.8525cqw!important;}
html[lang="en"] .native-power [data-source-line="5"] {border-radius:1.9108cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="0"] {font-size:2.1019cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="0"] {padding:0.8120cqw 1.7485cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="1"] {font-size:3.1847cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="3"] {font-size:3.1847cqw!important;}
html[lang="en"] .native-ac-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="0"] {padding:0.7966cqw 1.7483cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="1"] {font-size:2.8413cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="3"] {font-size:2.8413cqw!important;}
html[lang="en"] .native-usb-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="0"] {padding:0.7966cqw 1.7483cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="1"] {font-size:2.8413cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="3"] {font-size:2.8413cqw!important;}
html[lang="en"] .native-dc-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-ups [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="en"] .native-ups [data-source-line="0"] {padding:2.8390cqw 2.6258cqw!important;}
html[lang="en"] .native-ups [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="en"] .native-battery-packs [data-source-line="0"] {font-size:1.9355cqw!important;}
html[lang="en"] .native-battery-packs [data-source-line="1"] {font-size:1.9355cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="0"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="0"] {padding:2.7857cqw 2.0619cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="0"] {border-radius:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="1"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="2"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="3"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="4"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="5"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="6"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="7"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-sts-connect [data-source-line="8"] {font-size:1.9096cqw!important;}
html[lang="en"] .native-ac-charge [data-source-line="0"] {font-size:1.9102cqw!important;}
html[lang="en"] .native-ac-charge [data-source-line="1"] {font-size:1.9102cqw!important;}
html[lang="en"] .native-ac-charge [data-source-line="2"] {font-size:1.9102cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="0"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="1"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="2"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="3"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="4"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="5"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="6"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="7"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="8"] {font-size:0.5305cqw!important;}
html[lang="en"] .native-sts-charge [data-source-line="9"] {font-size:1.9090cqw!important;}
html[lang="en"] .native-low-pv-500 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="en"] .native-low-pv-500 [data-source-line="1"] {font-size:1.4327cqw!important;}
html[lang="en"] .native-low-pv-200 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="en"] .native-low-pv-200 [data-source-line="1"] {font-size:1.4327cqw!important;}
html[lang="en"] .native-low-pv-200 [data-source-line="2"] {font-size:1.4327cqw!important;}
html[lang="en"] .native-high-pv [data-source-line="0"] {font-size:1.9507cqw!important;}
html[lang="en"] .native-high-pv [data-source-line="1"] {font-size:1.9507cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="0"] {font-size:2.5592cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="1"] {font-size:2.5592cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="2"] {font-size:1.9194cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="3"] {font-size:1.9194cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="4"] {font-size:1.9194cqw!important;}
html[lang="en"] .native-high-pv-lock [data-source-line="5"] {font-size:1.9194cqw!important;}
html[lang="en"] .native-car [data-source-line="0"] {font-size:2.2286cqw!important;}
html[lang="en"] .native-car [data-source-line="1"] {font-size:1.9899cqw!important;}
html[lang="en"] .native-car [data-source-line="1"] {padding:0.9502cqw 1.5028cqw!important;}
html[lang="en"] .native-car [data-source-line="1"] {border-radius:1.9102cqw!important;}
html[lang="en"] .native-app-add [data-source-line="0"] {font-size:3.7267cqw!important;}
html[lang="en"] .native-app-add [data-source-line="1"] {font-size:3.7267cqw!important;}
html[lang="en"] .native-app-control [data-source-line="0"] {font-size:1.9887cqw!important;}
html[lang="en"] .native-app-control [data-source-line="1"] {font-size:1.9887cqw!important;}
html[lang="en"] .native-app-control [data-source-line="2"] {font-size:1.9887cqw!important;}
html[lang="en"] .native-app-control [data-source-line="3"] {font-size:1.9887cqw!important;}
html[lang="en"] .native-app-results [data-source-line="0"] {font-size:2.3077cqw!important;}
html[lang="en"] .native-app-results [data-source-line="1"] {font-size:2.3077cqw!important;}
html[lang="en"] .native-app-results [data-source-line="2"] {font-size:2.3077cqw!important;}
html[lang="en"] .native-ess [data-source-line="0"] {font-size:1.9374cqw!important;}
html[lang="en"] .native-ess [data-source-line="1"] {font-size:1.9374cqw!important;}
html[lang="en"] .native-package-host [data-source-line="0"] {font-size:0.1680cqw!important;}
html[lang="en"] .native-package-host [data-source-line="1"] {font-size:0.7963cqw!important;}
html[lang="en"] .native-package-host [data-source-line="2"] {font-size:0.3676cqw!important;}
html[lang="en"] .native-package-host [data-source-line="3"] {font-size:0.2471cqw!important;}
html[lang="en"] .native-package-host [data-source-line="4"] {font-size:0.5295cqw!important;}
html[lang="en"] .native-package-host [data-source-line="5"] {font-size:0.1667cqw!important;}
html[lang="en"] .native-package-host [data-source-line="6"] {font-size:0.1667cqw!important;}
html[lang="en"] .native-package-host [data-source-line="7"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-host [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-host [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-host [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="0"] {font-size:0.1654cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="1"] {font-size:1.9396cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="1"] {padding:2.8466cqw 10.5169cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="1"] {border-radius:4.8046cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="1"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="en"] .native-package-battery [data-source-line="2"] {font-size:0.8441cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="3"] {font-size:0.3867cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="4"] {font-size:0.2432cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="5"] {font-size:0.5212cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="6"] {font-size:0.1641cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="7"] {font-size:0.1641cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-battery [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="0"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="1"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="2"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="3"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="4"] {font-size:0.2548cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="5"] {font-size:0.2038cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="6"] {font-size:0.2038cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="7"] {font-size:0.1960cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="8"] {font-size:0.9239cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="9"] {font-size:0.5618cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="10"] {font-size:0.0944cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="11"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="12"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="13"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="14"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="15"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="16"] {font-size:0.2662cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="17"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="18"] {font-size:0.0492cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="19"] {font-size:0.8885cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="20"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="21"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="22"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="23"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="24"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="25"] {font-size:0.4152cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="26"] {font-size:0.1960cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="27"] {font-size:0.1960cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="28"] {font-size:0.1960cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="29"] {font-size:0.1960cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="30"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="31"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="32"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="33"] {font-size:0.1389cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="34"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="35"] {font-size:0.1631cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="36"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="37"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="38"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="39"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="40"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="41"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="42"] {font-size:1.9396cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="42"] {padding:2.8465cqw 10.5169cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="42"] {border-radius:4.8046cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="42"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="en"] .native-package-sts [data-source-line="43"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="44"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="45"] {font-size:1.6015cqw!important;}
html[lang="en"] .native-package-sts [data-source-line="46"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="3"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="4"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="5"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="6"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="7"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="8"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="9"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="10"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="11"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="12"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="13"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="14"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="15"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="16"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="17"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="18"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="19"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="20"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="21"] {font-size:1.4365cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="22"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="23"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="24"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="25"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="26"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-front [data-source-line="27"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="1"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="2"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="3"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="4"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="6"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="7"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="8"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="9"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="10"] {font-size:1.8927cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="11"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="12"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="13"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="14"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="15"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="16"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-left [data-source-line="17"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="0"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="1"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="2"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="3"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="4"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="5"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="6"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="7"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="8"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="9"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="10"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="11"] {font-size:1.5142cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="12"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="13"] {font-size:1.5773cqw!important;}
html[lang="es"] .native-overview-right [data-source-line="14"] {font-size:2.2082cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="0"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="1"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="2"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="3"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="4"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="5"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="6"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="7"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="8"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="9"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="10"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="11"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="12"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="13"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="14"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="15"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="16"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="17"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="18"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="19"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="20"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="21"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-lcd-map [data-source-line="22"] {font-size:2.1995cqw!important;}
html[lang="es"] .native-power [data-source-line="0"] {font-size:3.1847cqw!important;}
html[lang="es"] .native-power [data-source-line="1"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-power [data-source-line="2"] {font-size:3.1847cqw!important;}
html[lang="es"] .native-power [data-source-line="3"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-power [data-source-line="4"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-power [data-source-line="5"] {font-size:2.2293cqw!important;}
html[lang="es"] .native-power [data-source-line="6"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-power [data-source-line="6"] {padding:1.6702cqw 1.9191cqw!important;}
html[lang="es"] .native-power [data-source-line="6"] {border-radius:1.9108cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="0"] {font-size:2.1019cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="0"] {padding:0.8120cqw 1.7485cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="1"] {font-size:3.1847cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="2"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="3"] {font-size:3.1847cqw!important;}
html[lang="es"] .native-ac-output [data-source-line="4"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="0"] {padding:0.7967cqw 1.7484cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="1"] {font-size:2.8413cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="2"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="3"] {font-size:2.8413cqw!important;}
html[lang="es"] .native-usb-output [data-source-line="4"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="0"] {padding:0.7966cqw 1.7484cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="1"] {font-size:2.8413cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="2"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="3"] {font-size:2.8413cqw!important;}
html[lang="es"] .native-dc-output [data-source-line="4"] {font-size:1.7197cqw!important;}
html[lang="es"] .native-ups [data-source-line="0"] {font-size:1.9108cqw!important;}
html[lang="es"] .native-ups [data-source-line="0"] {padding:2.3703cqw 2.6258cqw!important;}
html[lang="es"] .native-ups [data-source-line="0"] {border-radius:1.9108cqw!important;}
html[lang="es"] .native-battery-packs [data-source-line="0"] {font-size:1.9355cqw!important;}
html[lang="es"] .native-battery-packs [data-source-line="1"] {font-size:1.9355cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="0"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="0"] {padding:2.5037cqw 2.4362cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="0"] {border-radius:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="1"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="2"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="3"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="4"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="5"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="6"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="7"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="8"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-sts-connect [data-source-line="9"] {font-size:1.9090cqw!important;}
html[lang="es"] .native-ac-charge [data-source-line="0"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-ac-charge [data-source-line="1"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-ac-charge [data-source-line="2"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="0"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="1"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="2"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="3"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="4"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="5"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="6"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="7"] {font-size:0.5308cqw!important;}
html[lang="es"] .native-sts-charge [data-source-line="8"] {font-size:1.9102cqw!important;}
html[lang="es"] .native-low-pv-500 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="es"] .native-low-pv-500 [data-source-line="1"] {font-size:1.6243cqw!important;}
html[lang="es"] .native-low-pv-200 [data-source-line="0"] {font-size:1.4327cqw!important;}
html[lang="es"] .native-low-pv-200 [data-source-line="1"] {font-size:1.4327cqw!important;}
html[lang="es"] .native-low-pv-200 [data-source-line="2"] {font-size:1.7839cqw!important;}
html[lang="es"] .native-high-pv [data-source-line="0"] {font-size:1.9507cqw!important;}
html[lang="es"] .native-high-pv [data-source-line="1"] {font-size:1.9507cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="0"] {font-size:2.5592cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="1"] {font-size:2.5592cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="2"] {font-size:1.9194cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="3"] {font-size:1.9194cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="4"] {font-size:1.9194cqw!important;}
html[lang="es"] .native-high-pv-lock [data-source-line="5"] {font-size:1.9194cqw!important;}
html[lang="es"] .native-car [data-source-line="0"] {font-size:2.2283cqw!important;}
html[lang="es"] .native-car [data-source-line="1"] {font-size:1.9100cqw!important;}
html[lang="es"] .native-car [data-source-line="1"] {padding:1.0266cqw 2.1118cqw!important;}
html[lang="es"] .native-car [data-source-line="1"] {border-radius:1.9100cqw!important;}
html[lang="es"] .native-app-add [data-source-line="0"] {font-size:3.2687cqw!important;}
html[lang="es"] .native-app-add [data-source-line="1"] {font-size:3.2687cqw!important;}
html[lang="es"] .native-app-control [data-source-line="0"] {font-size:1.9887cqw!important;}
html[lang="es"] .native-app-control [data-source-line="1"] {font-size:1.9887cqw!important;}
html[lang="es"] .native-app-control [data-source-line="2"] {font-size:1.9887cqw!important;}
html[lang="es"] .native-app-control [data-source-line="3"] {font-size:1.9887cqw!important;}
html[lang="es"] .native-app-control [data-source-line="4"] {font-size:1.9887cqw!important;}
html[lang="es"] .native-app-results [data-source-line="0"] {font-size:2.3166cqw!important;}
html[lang="es"] .native-app-results [data-source-line="1"] {font-size:2.3166cqw!important;}
html[lang="es"] .native-app-results [data-source-line="2"] {font-size:2.3166cqw!important;}
html[lang="es"] .native-ess [data-source-line="0"] {font-size:1.9374cqw!important;}
html[lang="es"] .native-ess [data-source-line="1"] {font-size:1.9374cqw!important;}
html[lang="es"] .native-package-host [data-source-line="0"] {font-size:0.1680cqw!important;}
html[lang="es"] .native-package-host [data-source-line="1"] {font-size:0.7963cqw!important;}
html[lang="es"] .native-package-host [data-source-line="2"] {font-size:0.3676cqw!important;}
html[lang="es"] .native-package-host [data-source-line="3"] {font-size:0.2471cqw!important;}
html[lang="es"] .native-package-host [data-source-line="4"] {font-size:0.5295cqw!important;}
html[lang="es"] .native-package-host [data-source-line="5"] {font-size:0.1667cqw!important;}
html[lang="es"] .native-package-host [data-source-line="6"] {font-size:0.1667cqw!important;}
html[lang="es"] .native-package-host [data-source-line="7"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-host [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-host [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-host [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="0"] {font-size:0.1654cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="1"] {font-size:1.9396cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="1"] {padding:2.8463cqw 10.5170cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="1"] {border-radius:4.8046cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="1"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="es"] .native-package-battery [data-source-line="2"] {font-size:0.8441cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="3"] {font-size:0.3867cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="4"] {font-size:0.2432cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="5"] {font-size:0.5212cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="6"] {font-size:0.1641cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="7"] {font-size:0.1641cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="8"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="9"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-battery [data-source-line="10"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="0"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="1"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="2"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="3"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="4"] {font-size:0.2548cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="5"] {font-size:0.2038cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="6"] {font-size:0.2038cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="7"] {font-size:0.1960cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="8"] {font-size:0.9239cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="9"] {font-size:0.5618cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="10"] {font-size:0.0944cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="11"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="12"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="13"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="14"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="15"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="16"] {font-size:0.2662cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="17"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="18"] {font-size:0.0492cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="19"] {font-size:0.8885cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="20"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="21"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="22"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="23"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="24"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="25"] {font-size:0.4152cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="26"] {font-size:0.1960cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="27"] {font-size:0.1960cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="28"] {font-size:0.1960cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="29"] {font-size:0.1960cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="30"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="31"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="32"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="33"] {font-size:0.1389cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="34"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="35"] {font-size:0.1631cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="36"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="37"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="38"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="39"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="40"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="41"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="42"] {font-size:1.9396cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="42"] {padding:2.8464cqw 10.5170cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="42"] {border-radius:4.8046cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="42"]::after {content:"";position:absolute;left:8%;top:12%;width:33%;height:76%;background:url("assets/sold-separately-cart.svg") center/contain no-repeat;}
html[lang="es"] .native-package-sts [data-source-line="43"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="44"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="45"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="46"] {font-size:1.6015cqw!important;}
html[lang="es"] .native-package-sts [data-source-line="47"] {font-size:1.6015cqw!important;}

</style>

<h1 class="hb-preface-heading" id="native-preface"><span class="hb-preface-region">ES</span> IMPORTANTE</h1>

<div class="hb-preface-prose"><p>Felicidades por su nuevo Jackery HomePower 5000 Plus. Lea atentamente este manual antes de utilizar el producto, en particular las precauciones pertinentes para garantizar un uso correcto. Guarde este manual en un lugar accesible para consultarlo con frecuencia.</p><p>En cumplimiento de las leyes y reglamentos, el derecho de interpretación final de este documento y de todos los documentos relacionados con este producto corresponde a la Empresa.</p><p>Tenga en cuenta que no se realizarán más notificaciones en caso de actualización, revisión o finalización.</p></div>

<span id="native-safety"></span>

## INSTRUCCIONES DE SEGURIDAD IMPORTANTES

### INSTRUCCIONES RELATIVAS AL RIESGO DE INCENDIO, DESCARGA ELÉCTRICA O LESIONES PERSONALES

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ADVERTENCIA</td><td class="manual-callout-body"><p>Al utilizar este producto, deben seguirse siempre las precauciones básicas. Entre ellas, se incluyen</p></td></tr></tbody></table>

<ul><li>Lee todas las instrucciones antes de usar el producto.</li><li>No permitas que los niños jueguen sobre o dentro del producto. Se requiere la supresión cercana de adultos cuando se use cerca de niños.</li><li>Evita colocar las manos o los dedos dentro del producto.</li><li>Deja de usar el producto de inmediato si ha sufrido daños físicos o modificados. El uso inadecuado puede causar un comportamiento impredecible, provocando incendio, explosión o lesiones.</li><li>Si se observan los siguientes síntomas —(incluyendo sobrecalentamiento, olores extraños o humo, fugas o quemaduras)— deja de usar el producto de inmediato y contacta al distribuidor o a nuestro servicio al cliente.</li><li>Nunca intentes abrir, reparar o modificar el producto. Cualquier manipulación, re ensamblaje o modificación puede resultar en descarga eléctrica, incendio o daños a la batería.</li><li>Ten en cuenta que el líquido expulsado del producto puede causar irritación o quemaduras. El uso inapropiado o abusivo puede causar fugas en la batería. Evita el contacto directo con líquidos que se filtren. Si el líquido entra en contacto con los ojos, busca atención médica de inmediato. Si entra en contacto con otras partes del cuerpo, enjuaga con agua corriente y consulta a un médico de inmediato.</li><li>No expongas el producto al fuego o a temperaturas extremas. Hacerlo puede provocar una explosión si la temperatura supera los 130°C (265 °F).</li><li>El uso de materiales o piezas no recomendadas o no suministradas puede implicar riesgo de incendio, descarga eléctrica o lesiones personales.</li><li>No dejes la batería cargando sin supervisión durante periodos prolongados. Supervisa siempre el proceso de carga para garantizar un funcionamiento seguro.</li><li>Para reducir el riesgo de descarga eléctrica, desconecta el producto de cualquier fuente de energía antes de realizar servicio técnico o resolución de problemas.</li></ul>

### INSTRUCCIONES DE USO

<p><strong>GUARDE ESTAS INSTRUCCIONES</strong></p>

<ul><li>Deja de usar el producto de inmediato si muestra signos de daño. Suspende el uso y contacta al servicio al cliente para recibir asistencia.</li><li>No cargues la batería en ambientes extremadamente calientes o fríos y cumple estrictamente con los rangos de temperatura especificados por el producto:<ul><li>Temperatura de carga: 32°F a 113°F (0°C a 45°C);</li><li>Temperatura de descarga: 5°F a 113°F (-15°C a 45°C);</li></ul></li><li>Para garantizar una circulación de aire adecuada, no cubras las rejillas de ventilación del producto. El área donde se use el producto debe tener un flujo de aire adecuado en un entorno fresco y seco para evitar el sobrecalentamiento.<ul><li>Cargar en espacios húmedos o mal ventilados puede representar riesgos para la seguridad.</li><li>El agua puede provocar cortocircuitos o dañar el cargador, generando riesgos de seguridad.</li></ul></li><li>Desconecta el cable de alimentación de la toma de corriente durante tormentas eléctricas.</li><li>Apaga el producto de inmediato presionando el botón de encendido si se ha caído, golpeado o expuesto a vibraciones.</li><li>Asegúrate de que los dispositivos estén apagados antes de conectarlos al producto.</li><li>No cargues el producto con un cable o enchufe dañado o roto.</li><li>No uses el producto para cargar dispositivos con cable o enchufe dañado o roto.</li><li>Siempre desconecta el cable de carga tirando del enchufe, no del cable, para evitar daños.</li><li>Asegúrate de que el producto esté bien asegurado al transportarlo en un vehículo en movimiento.</li><li>NO coloques la unidad boca abajo ni de lado durante el uso o almacenamiento.</li><li>NO coloques el producto en el suelo o a una altura menor de 18 pulgadas (457 mm) sobre el suelo durante el funcionamiento en un taller o centro de reparación.</li><li>NO uses los accesorios del producto con otros dispositivos o equipos.</li><li>Los tiempos de carga solar dependen de las condiciones meteorológicas. Coloque su panel solar donde reciba la mayor cantidad posible de luz solar directa.</li></ul>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PELIGRO</td><td class="manual-callout-body"><p>Cet appareil est destiné uniquement à une utilisation en intérieur (Veuillez le placer dans un environnement intérieur similaire lors d’une utilisation à l’extérieur, par exemple : maisons, véhicules récréatifs (VR), tentes, chalets, etc.). ※ Cet appareil n'est pas étanche ni résistant à la poussière. Évitez la pluie et les environnements humides pendant l'utilisation. PELIGRO</p></td></tr></tbody></table>

<span id="native-maintenance"></span>

## INSTRUCCIONES DE MANTENIMIENTO PARA EL USUARIO

<p>Durante el ciclo de vida útil de los productos de almacenamiento de energía, se producirá cierto grado de degradación de capacidad y energía. A medida que aumenta el número de ciclos de uso y se extiende el tiempo de almacenamiento, esta degradación se intensificará gradualmente, lo cual es un fenómeno normal acorde con el patrón de envejecimiento natural de las celdas de la batería.</p>

<span id="native-symbols"></span>

## SIGNIFICADO DE LOS SÍMBOLOS

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Símbolo</th><th class="hb-symbol-signal-meaning-heading" scope="col">Significado</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ADVERTENCIA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ADVERTENCIA</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en lesiones graves, muerte y/o daños a la propiedad.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="PRECAUCIÓN" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">PRECAUCIÓN</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en daño al equipo, pérdida de datos, deterioro del rendimiento o resultados inesperados.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significado</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Símbolos de advertencia y precaución Debe leer para alertar a las personas sobre posibles peligros o riesgos." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Símbolos de advertencia y precaución Debe leer para alertar a las personas sobre posibles peligros o riesgos.</td></tr><tr><td class="hb-symbol-icon"><img alt="Símbolo de peligro de choque eléctrico para la advertencia de peligro eléctrico." class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Símbolo de peligro de choque eléctrico para la advertencia de peligro eléctrico.</td></tr><tr><td class="hb-symbol-icon"><img alt="El símbolo de carga de la batería indica que se está cargando una batería." class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">El símbolo de carga de la batería indica que se está cargando una batería.</td></tr><tr><td class="hb-symbol-icon"><img alt="Símbolo de material explosivo para advertencia de riesgo de explosión." class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Símbolo de material explosivo para advertencia de riesgo de explosión.</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significado</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Símbolo de objeto pesado para precauciones de manipulación." class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Símbolo de objeto pesado para precauciones de manipulación.</td></tr><tr><td class="hb-symbol-icon"><img alt="Símbolo de no fumar o sin llamas abiertas para la prevención de incendios." class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Símbolo de no fumar o sin llamas abiertas para la prevención de incendios.</td></tr><tr><td class="hb-symbol-icon"><img alt="Símbolo de no se permite el acceso a niños para la prevención de riesgos." class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Símbolo de no se permite el acceso a niños para la prevención de riesgos.</td></tr><tr><td class="hb-symbol-icon"><img alt="Símbolo de leer el manual para un funcionamiento seguro." class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Símbolo de leer el manual para un funcionamiento seguro.</td></tr></tbody></table></div></div></figure>

<span id="native-fcc"></span>

## FCC

<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"></div></div></div><p><strong>Nota:</strong> Este aparato ha sido probado y cumple con los límites para un dispositivo digital de Clase B, de acuerdo con el Apartado 15 de las Reglas de la FCC. Estos límites están diseñados para proporcionar una protección razonable contra interferencias perjudiciales en una instalación residencial. Este aparato genera, usa y puede irradiar energía de radiofrecuencia y, si no se instala y utiliza de acuerdo con las instrucciones, puede causar interferencias perjudiciales en las comunicaciones por radio. Sin embargo, no hay garantía de que no se produzcan interferencias en una instalación concreta. Si este aparato causa interferencias dañinas en la recepción de radio o televisión, lo cual puede determinarse encendiendo y apagando el equipo, se recomienda al usuario que intente corregir la interferencia mediante una o varias de las siguientes medidas:</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Reorientar o reubicar la antena receptora.</p></li><li><p>Aumentar la separación entre el equipo y el receptor.</p></li><li><p>Conecte el aparato a una toma de corriente en un circuito diferente al que está conectado el receptor.</p></li><li><p>Consulte con el distribuidor o con un técnico de radio o TV experimentado para recibir ayuda.</p></li></ul><p><strong>MODIFICACIÓN:</strong> Cualquier cambio o modificación no aprobado expresamente por el cesionario de este dispositivo podría anular la autoridad del usuario para utilizar el dispositivo.</p></div></div></figure>

<span id="native-inbox"></span>

## CONTENIDO DEL PAQUETE

<figure aria-label="CONTENIDO DEL PAQUETE" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 5000 Plus" class="hb-inbox-art" src="assets/inbox-main.svg"/><div class="hb-inbox-label"><p>Jackery HomePower 5000 Plus</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Cable de carga de CA" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label"><p>Cable de carga de CA</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Llave MC4" class="hb-inbox-art" src="assets/inbox-mc4.svg"/><div class="hb-inbox-label"><p>Llave MC4</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Manual de usuario" class="hb-inbox-art" src="assets/inbox-manual.svg"/><div class="hb-inbox-label"><p>Manual de usuario</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">* Nota</div><div class="hb-inbox-tip-body">El cable de carga para automóvil no está incluido, pero está disponible para su compra por separado en nuestro sitio web. Para obtener asistencia, comunícate con el servicio al cliente de Jackery.</div></div></figure>

<span id="native-overview"></span>

## DESCRIPCIÓN GENERAL DEL PRODUCTO

### VISTA FRONTAL

<div class="native-figure native-overview-front native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="89c3e347d5578905ab8ff4d9df1c752a46e42ac36f106b17d0ef93a8ba056570" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-front.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.5137%;--hb-y:1.9674%;--hb-width:4.447%;--hb-height:4.5384%"><span><strong>LCD</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:68.6941%;--hb-y:2.508%;--hb-width:30.5744%;--hb-height:4.5384%"><span><strong>Botón</strong> <strong>de</strong> <strong>encendido</strong> <strong>principal</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.5137%;--hb-y:12.3268%;--hb-width:9.559%;--hb-height:4.5384%"><span><strong>Botón</strong> <strong>de</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:85.0724%;--hb-y:13.3237%;--hb-width:14.1962%;--hb-height:4.5384%"><span><strong>Salida</strong> <strong>USB-C</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.5137%;--hb-y:15.8987%;--hb-width:11.935%;--hb-height:4.5384%"><span><strong>energía</strong> <strong>CC</strong></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:91.6583%;--hb-y:17.4196%;--hb-width:7.5472%;--hb-height:3.2411%"><span>100W Máx</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.5137%;--hb-y:29.7612%;--hb-width:12.5465%;--hb-height:4.5384%"><span><strong>Puerto</strong> <strong>para</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:85.2689%;--hb-y:31.708%;--hb-width:13.9997%;--hb-height:4.5384%"><span><strong>Salida</strong> <strong>USB-A</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5137%;--hb-y:33.333%;--hb-width:12.7233%;--hb-height:4.5384%"><span><strong>encendedor</strong></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:92.7212%;--hb-y:35.4946%;--hb-width:6.4843%;--hb-height:3.2411%"><span>18W Máx</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.5137%;--hb-y:36.9049%;--hb-width:13.5404%;--hb-height:4.5384%"><span><strong>de</strong> <strong>cigarrillos</strong></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:89.9127%;--hb-y:38.9362%;--hb-width:9.559%;--hb-height:4.5384%"><span><strong>Botón</strong> <strong>de</strong></span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.5137%;--hb-y:41.7195%;--hb-width:6.4352%;--hb-height:4.5737%"><span>12V⎓10A</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:83.6569%;--hb-y:42.5071%;--hb-width:15.8148%;--hb-height:4.5384%"><span><strong>encendido</strong> <strong>USB</strong></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:85.5736%;--hb-y:46.6237%;--hb-width:13.6952%;--hb-height:4.5384%"><span><strong>Salida</strong> <strong>de</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:88.2166%;--hb-y:50.285%;--hb-width:11.0492%;--hb-height:3.9188%"><span>(NEMA 5-20)</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:88.6043%;--hb-y:53.98%;--hb-width:10.4059%;--hb-height:3.2411%"><span>1 salida de CA:</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:86.4859%;--hb-y:56.7486%;--hb-width:12.5242%;--hb-height:3.2411%"><span>120V, 20A, 2400W</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:0.5137%;--hb-y:56.883%;--hb-width:9.559%;--hb-height:4.5384%"><span><strong>Botón</strong> <strong>de</strong></span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:87.9002%;--hb-y:59.5171%;--hb-width:11.11%;--hb-height:3.2411%"><span>CA Salida total:</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:0.5137%;--hb-y:60.4549%;--hb-width:11.816%;--hb-height:4.5384%"><span><strong>energía</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:78.3759%;--hb-y:62.2834%;--hb-width:20.6344%;--hb-height:3.2411%"><span>Máximo 7200W, Pico de 14400W</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:0.5137%;--hb-y:80.9286%;--hb-width:10.5346%;--hb-height:3.9857%"><span><strong>Salida</strong> <strong>total</strong></span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:88.1836%;--hb-y:80.9286%;--hb-width:10.5346%;--hb-height:3.9857%"><span><strong>Salida</strong> <strong>total</strong></span></span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:0.5137%;--hb-y:84.1653%;--hb-width:16.8437%;--hb-height:3.3482%"><span>120V, 30A, 3600W Máx.</span></span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:81.4798%;--hb-y:84.1653%;--hb-width:16.8437%;--hb-height:3.3482%"><span>120V, 30A, 3600W Máx.</span></span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:0.5137%;--hb-y:86.9332%;--hb-width:11.6151%;--hb-height:3.3482%"><span>Pico de 7200 W</span></span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:87.1028%;--hb-y:86.9332%;--hb-width:11.6152%;--hb-height:3.3482%"><span>Pico de 7200 W</span></span></div></div></figure></div>

### VISTA LATERAL IZQUIERDA

<div class="native-figure native-overview-left native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="562c5d922a5302d6e603fba3c83b357c6f2019133a311ce94277455eb5030efc" data-web-base-art-ref="overview-left" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-left.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-left.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.6078%;--hb-y:0.844%;--hb-width:7.258%;--hb-height:4.8641%"><span><strong>Manija</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.6078%;--hb-y:8.3755%;--hb-width:28.2622%;--hb-height:4.8641%"><span><strong>Puerto</strong> <strong>de</strong> <strong>expansión</strong> <strong>de</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.6082%;--hb-y:12.6712%;--hb-width:29.4768%;--hb-height:4.2%"><span>conectar al Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.6078%;--hb-y:16.128%;--hb-width:25.8896%;--hb-height:3.5885%"><span>Entrada: 240 V, 16,7 A Máx., 4000 W</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.6078%;--hb-y:19.0945%;--hb-width:19.8956%;--hb-height:3.5885%"><span>Salida: 240 V, 30 A, 7200 W</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.5372%;--hb-y:25.2157%;--hb-width:39.0824%;--hb-height:4.8641%"><span><strong>Puerto</strong> <strong>de</strong> <strong>salida</strong> <strong>de</strong> <strong>CA</strong> <strong>NEMA</strong> <strong>L14-30R</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.5382%;--hb-y:29.0606%;--hb-width:25.1314%;--hb-height:4.2%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.5384%;--hb-y:33.262%;--hb-width:55.5929%;--hb-height:3.5885%"><span>Alimenta dispositivos de alta potencia y se conecta a una caja de entrada o</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5384%;--hb-y:36.2285%;--hb-width:56.2413%;--hb-height:3.5885%"><span>a un interruptor de transferencia manual para suministro eléctrico en el hogar.</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.5372%;--hb-y:47.6726%;--hb-width:36.8082%;--hb-height:4.8641%"><span><strong>Puerto</strong> <strong>de</strong> <strong>salida</strong> <strong>de</strong> <strong>CA</strong> <strong>NEMA</strong> <strong>14-50</strong></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.5382%;--hb-y:52.4348%;--hb-width:25.1312%;--hb-height:4.2%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.7007%;--hb-y:56.2946%;--hb-width:55.5927%;--hb-height:3.5885%"><span>Alimenta dispositivos de alta potencia y se conecta a una caja de entrada o</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.7007%;--hb-y:59.2612%;--hb-width:56.2413%;--hb-height:3.5885%"><span>a un interruptor de transferencia manual para suministro eléctrico en el hogar.</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.6078%;--hb-y:64.6947%;--hb-width:31.4668%;--hb-height:4.8641%"><span><strong>Salida</strong> <strong>de</strong> <strong>CA</strong> <strong>Botón</strong> <strong>de</strong> <strong>reinicio</strong></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.6079%;--hb-y:69.1869%;--hb-width:40.4621%;--hb-height:3.5885%"><span>Cuando el botón de reinicio salta, es necesario quitar la</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:0.6079%;--hb-y:72.1534%;--hb-width:29.3861%;--hb-height:3.5885%"><span>carga y presionar el botón para reiniciar.</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:0.6078%;--hb-y:78.6545%;--hb-width:16.9607%;--hb-height:4.8641%"><span><strong>Freno</strong> <strong>de</strong> <strong>ruedas</strong></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:0.6078%;--hb-y:87.433%;--hb-width:7.9779%;--hb-height:4.8641%"><span><strong>Ruedas</strong></span></span></div></div></figure></div>

### VISTA LATERAL DERECHA

<div class="native-figure native-overview-right native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-right" data-source-fragment-sha256="ade91f9aa74dfd99d7aa09cba2f0a7d49ef8eef84c49d5e861e014f8d28d65ce" data-web-base-art-ref="overview-right" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-right.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-right.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.4689%;--hb-y:0.2565%;--hb-width:15.8786%;--hb-height:4.6848%"><span><strong>Manija</strong> <strong>retráctil</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.4689%;--hb-y:4.5145%;--hb-width:41.5601%;--hb-height:3.4562%"><span>Pulse el botón de la manija retráctil y tire para extenderla</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4689%;--hb-y:10.4318%;--hb-width:40.5204%;--hb-height:4.6848%"><span><strong>Alimentación</strong> <strong>de</strong> <strong>baja</strong> <strong>tensión</strong> <strong>FV</strong> <strong>(8020)</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4689%;--hb-y:15.1228%;--hb-width:54.0674%;--hb-height:4.6485%"><span>2 puertos DC 8mm: 16 V - 60 V⎓10,5 A máx., Doble hasta 21 A/1200 W máx.</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4683%;--hb-y:17.98%;--hb-width:41.6656%;--hb-height:4.6486%"><span>11V-16V (voltaje operativo)⎓8A máx., Doble hasta 8A máx.</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.4689%;--hb-y:26.2738%;--hb-width:39.4605%;--hb-height:4.6848%"><span><strong>Alimentación</strong> <strong>de</strong> <strong>alta</strong> <strong>tensión</strong> <strong>FV</strong> <strong>(MC4)</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.4691%;--hb-y:31.1915%;--hb-width:24.7475%;--hb-height:4.7212%"><span>135V-450V⎓15A Max, 4000W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.4689%;--hb-y:37.0738%;--hb-width:27.2091%;--hb-height:4.6848%"><span><strong>Interruptor</strong> <strong>alta</strong> <strong>tensión</strong> <strong>FV</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4691%;--hb-y:41.6201%;--hb-width:26.2543%;--hb-height:3.4562%"><span>Activa/desactiva el interruptor para</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.4691%;--hb-y:44.4772%;--hb-width:35.2068%;--hb-height:3.4562%"><span>activar/desactivar la carga solar alta tensión FV</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.7825%;--hb-y:51.3996%;--hb-width:20.6314%;--hb-height:4.6848%"><span><strong>Alimentación</strong> <strong>de</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.4689%;--hb-y:55.5022%;--hb-width:10.1456%;--hb-height:5.7523%"><span>120V, 15A Max</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.4689%;--hb-y:66.4512%;--hb-width:39.6499%;--hb-height:4.6848%"><span><strong>Puerto</strong> <strong>de</strong> <strong>expansión</strong> <strong>de</strong> <strong>CC</strong> <strong>Terminal</strong> <strong>A</strong></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.4689%;--hb-y:70.5063%;--hb-width:22.9527%;--hb-height:3.4562%"><span>Conecte al paquete de batería</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.5153%;--hb-y:83.0641%;--hb-width:11.9284%;--hb-height:4.6848%"><span><strong>Asa</strong> <strong>inferior</strong></span></span></div></div></figure></div>

<span id="native-lcd"></span>

## PANTALLA LCD

<div class="native-figure native-lcd-map native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="0b53ab70e9b932a0f805f70e0723e3ddea254a435406b8f79754836e488857d9" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:19.5703%;--hb-y:3.6015%;--hb-width:1.4712%;--hb-height:5.4368%"><span>2</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:23.7492%;--hb-y:3.6015%;--hb-width:1.4822%;--hb-height:5.4368%"><span>3</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:27.4898%;--hb-y:3.6015%;--hb-width:1.5922%;--hb-height:5.4368%"><span>4</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:31.5345%;--hb-y:3.6015%;--hb-width:1.5042%;--hb-height:5.4368%"><span>5</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:35.4945%;--hb-y:3.6015%;--hb-width:1.4822%;--hb-height:5.4368%"><span>6</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:59.4669%;--hb-y:3.6015%;--hb-width:1.3942%;--hb-height:5.4368%"><span>7</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:15.5746%;--hb-y:3.604%;--hb-width:1.0643%;--hb-height:5.4368%"><span>1</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.9631%;--hb-y:45.595%;--hb-width:1.5218%;--hb-height:5.4368%"><span>8</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:96.2427%;--hb-y:45.9306%;--hb-width:2.648%;--hb-height:5.4368%"><span>22</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:96.1988%;--hb-y:57.0963%;--hb-width:2.637%;--hb-height:5.4368%"><span>23</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.873%;--hb-y:57.6336%;--hb-width:1.4822%;--hb-height:5.4368%"><span>9</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:15.2126%;--hb-y:92.2968%;--hb-width:2.516%;--hb-height:5.4368%"><span>10</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:19.9297%;--hb-y:92.2968%;--hb-width:1.8781%;--hb-height:5.4368%"><span>11</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:25.1096%;--hb-y:92.2968%;--hb-width:2.285%;--hb-height:5.4368%"><span>12</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:31.6575%;--hb-y:92.2968%;--hb-width:2.296%;--hb-height:5.4368%"><span>13</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:37.1052%;--hb-y:92.2968%;--hb-width:2.406%;--hb-height:5.4368%"><span>14</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:42.9698%;--hb-y:92.2968%;--hb-width:2.318%;--hb-height:5.4368%"><span>15</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:48.0492%;--hb-y:92.2968%;--hb-width:2.296%;--hb-height:5.4368%"><span>16</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:52.4684%;--hb-y:92.2968%;--hb-width:2.208%;--hb-height:5.4368%"><span>17</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:60.6101%;--hb-y:92.2968%;--hb-width:2.3356%;--hb-height:5.4368%"><span>18</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:70.9009%;--hb-y:92.2968%;--hb-width:2.252%;--hb-height:5.4368%"><span>19</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:75.2703%;--hb-y:92.2968%;--hb-width:2.8569%;--hb-height:5.4368%"><span>20</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:80.796%;--hb-y:92.2968%;--hb-width:2.241%;--hb-height:5.4368%"><span>21</span></span></div></div></figure></div>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-native-01.svg"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description"><strong>Encendido</strong>: Wi-Fi conectado <strong>Parpadeando</strong>: Listo para conectarse a Wi-Fi <strong>Apagado</strong>: Wi-Fi desconectado</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-native-02.svg"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description"><strong>Encendido</strong>: Bluetooth conectado <strong>Parpadeando</strong>: Listo para conectarse a Bluetooth <strong>Apagado</strong>: Bluetooth desconectado</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="Modo de carga silenciosa Se puede activar/desactivar desde la aplicación Jackery" class="hb-lcd-icon-art" src="assets/lcd-native-03.svg"/></td><td class="hb-lcd-name">Modo de carga silenciosa<br/><span class="native-lcd-note">Se puede activar/desactivar desde la aplicación Jackery</span></td><td class="hb-lcd-description"><strong>Encendido</strong>: el ruido durante la carga se minimiza significativamente, mientras que la potencia de carga y la velocidad de carga se desacelera <strong>Apagado</strong>: modo de carga silenciosa <strong>desactivado</strong></td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="Modo de ahorro de batería Se puede activar/desactivar desde la aplicación Jackery" class="hb-lcd-icon-art" src="assets/lcd-native-04.svg"/></td><td class="hb-lcd-name">Modo de ahorro de batería<br/><span class="native-lcd-note">Se puede activar/desactivar desde la aplicación Jackery</span></td><td class="hb-lcd-description"><strong>Encendido</strong>: Ayuda a prolongar la vida útil de la batería al limitar su capacidad máxima utilizable. <strong>Apagado</strong>: modo de ahorro de batería <strong>desactivado</strong></td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="Indicador de plan de carga/descarga Se puede configurar desde la app Jackery en el STS" class="hb-lcd-icon-art" src="assets/lcd-native-05.svg"/></td><td class="hb-lcd-name">Indicador de plan de carga/descarga<br/><span class="native-lcd-note">Se puede configurar desde la app Jackery en el STS</span></td><td class="hb-lcd-description">Indica que el producto está operando bajo el Plan de Carga/Descarga del STS (Interruptor de Transferencia Inteligente) Esto solo ocurre cuando el producto esta conectado exitosamente al STS y el plan carga/descarga ha sido configurado desde la aplicación STS</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="SAI en línea Se puede configurar en la aplicación Jackery" class="hb-lcd-icon-art" src="assets/lcd-native-06.svg"/></td><td class="hb-lcd-name">SAI en línea<br/><span class="native-lcd-note">Se puede configurar en la aplicación Jackery</span></td><td class="hb-lcd-description"><strong>Encendido</strong>: el producto está en modo UPS en línea (0 ms) <strong>Apagado</strong>: modo UPS de respaldo (predeterminado)</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="Indicador de alimentación de CA" class="hb-lcd-icon-art" src="assets/lcd-native-07.svg"/></td><td class="hb-lcd-name">Indicador de alimentación de CA</td><td class="hb-lcd-description">La salida CA (onda sinusoidal pura) está activada.</td></tr><tr><td class="hb-lcd-number">8</td><td class="hb-lcd-icon"><img alt="Potencia de alimentación" class="hb-lcd-icon-art" src="assets/lcd-native-08.svg"/></td><td class="hb-lcd-name">Potencia de alimentación</td><td class="hb-lcd-description">Muestra la potencia de entrada en vatios.</td></tr><tr><td class="hb-lcd-number">9</td><td class="hb-lcd-icon"><img alt="Tiempo de carga restante" class="hb-lcd-icon-art" src="assets/lcd-native-09.svg"/></td><td class="hb-lcd-name">Tiempo de carga restante</td><td class="hb-lcd-description">Muestra el tiempo restante de carga</td></tr><tr><td class="hb-lcd-number">10</td><td class="hb-lcd-icon"><img alt="Indicador de carga de red de CA" class="hb-lcd-icon-art" src="assets/lcd-native-10.svg"/></td><td class="hb-lcd-name">Indicador de carga de red de CA</td><td class="hb-lcd-description">El producto se carga mediante la entrada de CA utilizando la energía de la red eléctrica.</td></tr><tr><td class="hb-lcd-number">11</td><td class="hb-lcd-icon"><img alt="Indicador de carga de coche" class="hb-lcd-icon-art" src="assets/lcd-native-11.svg"/></td><td class="hb-lcd-name">Indicador de carga de coche</td><td class="hb-lcd-description">El producto se carga a través de la entrada de alta tensión FV (MC4) utilizando panel(es) solar(es)</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="Indicador de alimentación de alta tensión FV" class="hb-lcd-icon-art" src="assets/lcd-native-12.svg"/></td><td class="hb-lcd-name">Indicador de alimentación de alta tensión FV</td><td class="hb-lcd-description">El producto se carga a través de la entrada de alta tensión FV (MC4) utilizando panel(es) solar(es)</td></tr><tr><td class="hb-lcd-number">12</td><td class="hb-lcd-icon"><img alt="Indicador de alimentación de baja tensión FV Indicador de" class="hb-lcd-icon-art" src="assets/lcd-native-13.svg"/></td><td class="hb-lcd-name">Indicador de alimentación de baja tensión FV Indicador de</td><td class="hb-lcd-description">El producto se carga a traves de la entrada Low-PV (8020) utilizando el panel(es) solar(es)</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="expansión de CA (Carregamento) Asegúrese de que el STS esté exitosamente conectado antes de continuar" class="hb-lcd-icon-art" src="assets/lcd-native-14.svg"/></td><td class="hb-lcd-name">expansión de CA (Carregamento)<br/><span class="native-lcd-note">Asegúrese de que el STS esté exitosamente conectado antes de continuar</span></td><td class="hb-lcd-description">El producto se está cargando mediante STS con energía de red</td></tr><tr><td class="hb-lcd-number">13</td><td class="hb-lcd-icon"><img alt="Indicador de expansión de CA (Descarregando) Asegúrese de que el STS esté exitosamente conectado antes de continuar" class="hb-lcd-icon-art" src="assets/lcd-native-15.svg"/></td><td class="hb-lcd-name">Indicador de expansión de CA (Descarregando)<br/><span class="native-lcd-note">Asegúrese de que el STS esté exitosamente conectado antes de continuar</span></td><td class="hb-lcd-description">El producto está alimentando la carga de su hogar a traves del interruptor de transferencia inteligente el STS</td></tr><tr><td class="hb-lcd-number">14</td><td class="hb-lcd-icon"><img alt="Indicador del Smart Transfer Switch" class="hb-lcd-icon-art" src="assets/lcd-native-16.svg"/></td><td class="hb-lcd-name">Indicador del Smart Transfer Switch</td><td class="hb-lcd-description">El producto está conectado exitosamente al STS</td></tr><tr><td class="hb-lcd-number">15</td><td class="hb-lcd-icon"><img alt="Indicador de carga de batería" class="hb-lcd-icon-art" src="assets/lcd-native-17.svg"/></td><td class="hb-lcd-name">Indicador de carga de batería</td><td class="hb-lcd-description">Cuando el producto se está cargando, el círculo naranja que rodea el porcentaje de la batería se encenderá en secuencia. Al cargar otros dispositivos, el círculo naranja permanecerá encendido.</td></tr><tr><td class="hb-lcd-number">16</td><td class="hb-lcd-icon"><img alt="Indicador de batería baja" class="hb-lcd-icon-art" src="assets/lcd-native-18.svg"/></td><td class="hb-lcd-name">Indicador de batería baja</td><td class="hb-lcd-description"><strong>Activado</strong> : El Nivel de batería esta por debajo del 20% <strong>Parpadeando</strong>: El Nivel de batería esta por debajo del 5% <strong>Desactivado</strong> : El productoestá cargando</td></tr><tr><td class="hb-lcd-number">17</td><td class="hb-lcd-icon"><img alt="Porcentaje de batería restante" class="hb-lcd-icon-art" src="assets/lcd-native-19.svg"/></td><td class="hb-lcd-name">Porcentaje de batería restante</td><td class="hb-lcd-description">Muestra el porcentaje restante de batería.</td></tr><tr><td class="hb-lcd-number">18</td><td class="hb-lcd-icon"><img alt="Indicador de paquete de baterías y número de baterías conectadas" class="hb-lcd-icon-art" src="assets/lcd-native-20.svg"/></td><td class="hb-lcd-name">Indicador de paquete de baterías y número de baterías conectadas</td><td class="hb-lcd-description">Indica que el producto está conectado al número especificado de baterías adicionales 5000 Plus</td></tr><tr><td class="hb-lcd-number">19</td><td class="hb-lcd-icon"><img alt="Código de fallo" class="hb-lcd-icon-art" src="assets/lcd-native-21.svg"/></td><td class="hb-lcd-name">Código de fallo</td><td class="hb-lcd-description">Se ha producido un error en el producto. Consulte la sección de solución de problemas para más detalles.</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="Indicador de alta temperatura" class="hb-lcd-icon-art" src="assets/lcd-native-22.svg"/></td><td class="hb-lcd-name">Indicador de alta temperatura</td><td class="hb-lcd-description">Se ha activado la protección por alta temperatura. El producto podría dejar de funcionar hasta que su temperatura regrese al rango normal de operación funcionamiento.</td></tr><tr><td class="hb-lcd-number">20</td><td class="hb-lcd-icon"><img alt="Indicador de baja temperatura" class="hb-lcd-icon-art" src="assets/lcd-native-23.svg"/></td><td class="hb-lcd-name">Indicador de baja temperatura</td><td class="hb-lcd-description">Se ha activado la protección por baja temperatura. El producto podría dejar de funcionar hasta que su temperatura regrese al rango normal de operación funcionamiento.</td></tr><tr><td class="hb-lcd-number">21</td><td class="hb-lcd-icon"><img alt="Modo de ahorro de energía" class="hb-lcd-icon-art" src="assets/lcd-native-24.svg"/></td><td class="hb-lcd-name">Modo de ahorro de energía</td><td class="hb-lcd-description">Para evitar el consumo innecesario de batería por olvidar apagar la salida encendida, el producto habilita el modo de ahorro de energía se activa por defecto. Si no hay dispositivos conectados o el consumo de energía del dispositivo conectado esta por debajo de un cierto limite (salida CA ≤ 25W; salida USB ≤ 2W; salida auto ≤ 2W), se apagará automáticamente todas las salidas después de 12 horas. <strong>Encendido</strong>/<strong>Apagado</strong>: Mantenga presionados los botones de encendido principal y de salida CA</td></tr><tr><td class="hb-lcd-number">22</td><td class="hb-lcd-icon"><img alt="Potencia de salida" class="hb-lcd-icon-art" src="assets/lcd-native-25.svg"/></td><td class="hb-lcd-name">Potencia de salida</td><td class="hb-lcd-description">Muestra la potencia de salida en vatios.</td></tr><tr><td class="hb-lcd-number">23</td><td class="hb-lcd-icon"><img alt="Tiempo de descarga restante" class="hb-lcd-icon-art" src="assets/lcd-native-26.svg"/></td><td class="hb-lcd-name">Tiempo de descarga restante</td><td class="hb-lcd-description">Muestra el tiempo restante de descarga</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## OPERACIONES

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Nota</td><td class="manual-callout-body"><p>Cuando el modo de ahorro de energía está activado, si el botón de encendido de salida CC, CA o USB está encendido pero la estación de energía no está cargando ni descargando, se apagará automáticamente después de 12 horas.</p></td></tr></tbody></table>

### ENCENDIDO/APAGADO

<div class="native-figure native-power native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="a37d5c0e8fe3f610709d8e8b9f50538a55c33b91777257cdec973c04d04bc313" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power-es.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76.1008%;--hb-y:7.6076%;--hb-width:16.0669%;--hb-height:8.9146%"><span><strong>encendido</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.2059%;--hb-y:14.8222%;--hb-width:15.1541%;--hb-height:5.5877%"><span>Presiona una vez</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:76.0084%;--hb-y:24.8138%;--hb-width:14.172%;--hb-height:8.9146%"><span><strong>apagado</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:76.2059%;--hb-y:32.7143%;--hb-width:17.5102%;--hb-height:5.5877%"><span>Mantén presionado</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:76.2059%;--hb-y:36.5678%;--hb-width:17.8541%;--hb-height:5.5877%"><span>durante 3 segundos</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:80.4096%;--hb-y:43.9466%;--hb-width:2.5121%;--hb-height:6.3584%"><span>3s</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="6" style="--hb-x:43.2899%;--hb-y:57.9462%;--hb-width:51.8618%;--hb-height:31.4656%;--hb-fill:#f2f2f3"><span><strong>Tiempo</strong> <strong>de</strong> <strong>espera</strong> <strong>predeterminado:</strong> 2 horas<br/>· El producto se apagará automáticamente después<br/>de 2 horas de inactividad, sin carga ni descarga.<br/>· El tiempo de espera puede configurarse desde la app<br/>Jackery</span></span></div></div></figure></div>

### ENCENDIDO/APAGADO DE SALIDA CA

<div class="native-figure native-ac-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output" data-source-fragment-sha256="aa03cd8135a73642c8088fae42b1832d798af894ece438743f645be7e469a459" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.5176%;--hb-y:3.9789%;--hb-width:83.4134%;--hb-height:6.9052%;--hb-fill:#f2f2f3"><span><strong>Requisito</strong> <strong>previo</strong> <strong>:</strong> Asegúrate de que el botón de <strong>encendido</strong> principal esté activado.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.6348%;--hb-y:16.4446%;--hb-width:16.0669%;--hb-height:6.9995%"><span><strong>encendido</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:79.8097%;--hb-y:22.698%;--hb-width:15.1541%;--hb-height:4.3873%"><span>Presiona una vez</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:79.5424%;--hb-y:28.1087%;--hb-width:14.172%;--hb-height:6.9995%"><span><strong>apagado</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:79.5461%;--hb-y:34.8765%;--hb-width:15.1541%;--hb-height:4.3873%"><span>Presiona una vez</span></span></div></div></figure></div>

### ENCENDIDO/APAGADO DE SALIDA USB

<div class="native-figure native-usb-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output" data-source-fragment-sha256="1eececed726623a6ff5b136d74e690c62296a68cd047dc55cb85294ca33d5bd9" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="usb-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:0.9807%;--hb-y:2.3709%;--hb-width:75.5796%;--hb-height:11.1145%;--hb-fill:#f2f2f3"><span><strong>Requisito</strong> <strong>previo</strong> <strong>:</strong> Asegúrate de que el botón de <strong>encendido</strong> principal esté activado.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.0826%;--hb-y:14.9392%;--hb-width:14.3686%;--hb-height:11.2209%"><span><strong>encendido</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:79.0022%;--hb-y:24.4386%;--hb-width:15.1541%;--hb-height:7.7818%"><span>Presiona una vez</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:78.9973%;--hb-y:31.362%;--hb-width:12.678%;--hb-height:11.2209%"><span><strong>apagado</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:79.0022%;--hb-y:41.3223%;--hb-width:15.1541%;--hb-height:7.7818%"><span>Presiona una vez</span></span></div></div></figure></div>

### ENCENDIDO/APAGADO DE SALIDA CC

<div class="native-figure native-dc-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc-output" data-source-fragment-sha256="5cb30b914d78d6fdc7bd7e240239c429498e12758cc4a5af32bccb9296e39fde" data-web-base-art-ref="dc-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="dc-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/dc-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:1.2355%;--hb-y:3.2705%;--hb-width:75.5796%;--hb-height:11.2148%;--hb-fill:#f2f2f3"><span><strong>Requisito</strong> <strong>previo</strong> <strong>:</strong> Asegúrate de que el botón de <strong>encendido</strong> principal esté activado.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.3374%;--hb-y:14.3573%;--hb-width:14.3686%;--hb-height:11.3221%"><span><strong>encendido</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:79.257%;--hb-y:23.9432%;--hb-width:15.1541%;--hb-height:7.852%"><span>Presiona una vez</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:79.2521%;--hb-y:30.9283%;--hb-width:12.678%;--hb-height:11.3221%"><span><strong>apagado</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:79.257%;--hb-y:40.9794%;--hb-width:15.1541%;--hb-height:7.852%"><span>Presiona una vez</span></span></div></div></figure></div>

<p>El producto puede cargar la batería de su automóvil utilizando el cable de carga de batería Nota para automóvil Jackery 12V, que se vende por separado y está disponible en nuestro sitio web.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><ul><li>El puerto del encendedor de cigarrillos solo es compatible con baterías de automóvil de 12 V y no es adecuado para sistemas de 24 V.</li><li>No arranque el automóvil mientras el producto está cargando la batería del automóvil a través del puerto de salida CC de 12 V (puerto del encendedor de cigarrillos), ya que esto podría dañar el producto.</li><li>Esta función está diseñada únicamente para uso de emergencia y no puede cargar una batería de automóvil descargada o dañada.</li></ul></td></tr></tbody></table>

### PANTALLA LCD

<div class="native-figure native-lcd-button native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-button" data-source-fragment-sha256="22165c38b79163050bee2321f09215d035560c75a005b9667f54c316d9fff84d"><div class="hb-reference-semantic" data-reference-id="lcd-button.semantic"><img alt="lcd-button" class="hb-reference-art hb-composite-art" src="assets/lcd-button.svg"/></div></figure></div>

<p>descarga)</p>

<p>después de 2 horas de inactividad.</p>

<p>automático</p>

<p>Presione el Botón de Encendido Principal o cuando el producto se está cargando.</p>

<p>Encender</p>

<p>Presione el Botón de Encendido Principal.</p>

<p>Pantalla LCD</p>

<p>Apagar</p>

<p>La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad.</p>

<p>Apagado automático</p>

<p>Haga doble clic en el Botón de Encendido Principal cuando la pantalla LCD esté encendida.</p>

<p>Modo de pantalla siempre encendida (en estado de carga o</p>

<p>Encender</p>

<p>Presione el Botón de Encendido Principal.</p>

<p>Apagar</p>

<p>El Modo de Pantalla Siempre Activa se apaga automáticamente</p>

<p>Apagado</p>

### COMBINACIONES DE TECLAS

<figure aria-label="Botones / Operación / Función" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Botones</th><th class="hb-key-operation" scope="col">Operación</th><th class="hb-key-function" scope="col">Función</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Botón de encendido principal</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>Botón de encendido USB</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Mantenga presionados ambos durante 3 segundos</p></td><td class="hb-key-function">Restablecer Wi-Fi y Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Botón de encendido principal</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Botón de energía CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Mantenga presionados ambos durante 3 segundos</p></td><td class="hb-key-function">Encender/apagar el modo de ahorro de energía</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>Botón de encendido USB</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Botón de energía CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">1s</span><p>Mantenga presionados ambos durante 1 segundos</p></td><td class="hb-key-function">Encender/apagar Wi-Fi y Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-dc-bottom.svg"/><p>Botón de energía CC</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Botón de energía CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Mantenga presionados ambos durante 3 segundos</p></td><td class="hb-key-function">Cambiar entre UPS en línea y UPS de respaldo</td></tr></tbody></table></figure>

<span id="native-troubleshooting"></span>

## RESOLUCIÓN DE PROBLEMAS

<div class="table-wrapper docutils container"><table class="manual-table native-troubleshooting"><thead><tr><th>Código de Error</th><th>Nombre</th><th>Descripción (solo para mantenimiento interno por fallas)</th></tr></thead><tbody><tr><td>F0</td><td>Error de comunicación de datos del BMS</td><td>Fallo de comunicación entre el BMS y la placa base</td></tr><tr><td>F1</td><td>Error de comunicación de datos del inversor</td><td>Fallo de comunicación entre el inversor y la placa base</td></tr><tr><td>F2</td><td>Error de comunicación de datos en entrada de CC</td><td>Fallo de comunicación entre el módulo de carga de CC y el BMS</td></tr><tr><td>F3</td><td>Falla del BMS o de la batería</td><td>Falla del BMS o de la batería</td></tr><tr><td>F4</td><td>Sobretensión de batería</td><td>Sobretensión de batería</td></tr><tr><td>F5</td><td>Subtensión de batería</td><td>Subtensión de batería</td></tr><tr><td>F6</td><td>Falla del inversor</td><td>Sobre-corriente / sobrecarga / cortocircuito en la salida de CA; Sobre-tensión / tensión de entrada de red / frecuencia demasiado alta o baja; Protección por sobretemperatura del inversor activada Fallo en la detección de aislamiento</td></tr><tr><td>F7</td><td>Falla de entrada de CC</td><td>Sobre-tensión en la entrada fotoeléctrica (PV); Protección contra sobre-temperatura del módulo de carga de CC activada; Protección contra sobre-corriente en la salida del módulo de carga de CC activada</td></tr><tr><td>F8</td><td>Sobre-corriente / cortocircuito durante la carga/descarga de batería</td><td>Protección contra sobre-corriente / cortocircuito del BMS activada</td></tr><tr><td>F9</td><td>Sobre-corriente / cortocircuito en salida de CC</td><td>Protección contra cortocircuito USB activada</td></tr><tr><td>FA</td><td>Error de comunicación de unidad en paralelo</td><td>Fallo en la comunicación entre dos unidades 5000 Plus causado por defecto en ambas unidades</td></tr><tr><td>FC</td><td>Error de comunicación del paquete de batería</td><td>Fallo en la comunicación de datos entre el 5000 Plus y el/los paquete(s) de batería</td></tr></tbody></table></div>

<span id="native-ups"></span>

## FUENTE DE ALIMENTACIÓN ININTERRUMPIDA

<p>Un UPS (Sistema de Alimentación Ininterrumpida) es un tipo de sistema de energía de respaldo que proporciona energía automática a una carga en caso de falla del suministro eléctrico principal. El HomePower 5000 Plus está equipado con dos modos UPS: Respaldo y En línea.</p>

### UPS DE RESPALDO

<p>La función UPS de respaldo está habilitada de manera predeterminada. En caso de una pérdida repentina de energía de la red, el HomePower 5000 Plus cambiará automáticamente a la energía almacenada en un plazo de 20 ms para mantener tus dispositivos en funcionamiento.</p>

<p>En modo UPS de respaldo, el pico de salida alcanza 1440W antes de un corte eléctrico Como la carga/descarga simultánea está habilitada en modo Bypass, la salida real es menor que la nominal, pero vuelve a la nominal durante cortes eléctricos.</p>

<div class="native-figure native-ups native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="1a696db8d386038b3968c8f8f395eb6dc8242c17dc70c00f0cd7486669ab87c0" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:37.9791%;--hb-y:69.6388%;--hb-width:56.7344%;--hb-height:22.0072%;--hb-fill:#f2f2f3"><span>Conecte el producto a una toma de corriente con el cable<br/>de carga de CA, luego presione el botón de salida CA y<br/>cargue sus electrodomésticos al mismo tiempo.</span></span></div></div></figure></div>

### UPS EN LÍNEA

<p>El modo UPS en línea, que permite conmutación de 0 ms, puede activarse de dos formas:</p>

<p>1. Habilite el UPS en línea desde la aplicación de Jackery. 2. Mantenga presionados los botones de encendido CC y CA en el HomePower 5000 Plus.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Nota</td><td class="manual-callout-body"><p>1. Las configuraciones del sistema volverán al modo UPS de respaldo cuando el producto este en modo en modo en línea y se reinicie. En el modo UPS de respaldo, la potencia de salida está limitada por la potencia de derivación , con una potencia de salida máxima de 1440W. 2. En modo UPS, las tomas de corriente s NEMA L14-30R y NEMA 14-50 proporcionan una salida de 120V cada una, cuando el producto está conectado a una toma de corriente con el cable de carga CA. 3. En el modo UPS en línea, se permite conmutación de 0 ms con salida máxima de 3600W.</p></td></tr></tbody></table>

### (UPS)

<span id="native-connections"></span>

## CONNECTIONS

### CONECTAR AL PAQUETE DE BATERÍAS

<p>SE VENDE POR SEPARADO</p>

<p>Este producto admite hasta 5 paquetes de baterías para cubrir la necesidad de una gran capacidad de energía. Para más detalles sobre cómo usarlo, por favor consulte el manual de usuario del Jackery Battery Pack 5000 Plus.</p>

<div class="native-figure native-battery-packs native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-packs" data-source-fragment-sha256="5ec3d04c7d2a1185a7e7788bb104aa093cc17cf2cb7ab256f6e19cb9aa317730" data-web-base-art-ref="battery-packs" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-packs.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-packs.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:24.3721%;--hb-y:90.2137%;--hb-width:17.9894%;--hb-height:5.7097%"><span>mínimo 1 pie (30 cm)</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.3501%;--hb-y:90.2137%;--hb-width:17.9894%;--hb-height:5.7097%"><span>mínimo 1 pie (30 cm)</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><p>1. Asegúrese de apagar todos los productos antes de conectar el HomePower 5000 Plus a los paquetes de batería del 5000 plus. 2. Asegúrese de que las rejillas de ventilación de entrada y salida de aire ambos lados esten libres de obstrucciones. Deje al menos 1 pie (30 cm) de espacio entre las rejillas de ventilación y cualquier objeto para permitir una circulación de aire adecuada y una disipación de calor efectiva.</p></td></tr></tbody></table>

### CONECTAR A UN STS (SMART TRANSFER SWITCH)

<p>SE VENDE POR SEPARADO</p>

<div class="native-figure native-sts-connect native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-connect" data-source-fragment-sha256="f5bad27b5d15672d66b4c99036cb63c741e03df3916ad48fb3c1afc51e5aab60" data-web-base-art-ref="sts-connect" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-connect.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-connect.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:36.7944%;--hb-y:8.6219%;--hb-width:57.9211%;--hb-height:25.7035%;--hb-fill:#ffffff"><span>Jackery HomePower 5000 Plus puede alimentar las cargas<br/>de su hogar a través del interruptor STS Para más<br/>información, consulte el manual del STS de Jackery.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:55.2347%;--hb-y:39.1938%;--hb-width:34.0866%;--hb-height:5.2002%"><span>Cuando el modo UPS está activado, la</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:55.2347%;--hb-y:43.9745%;--hb-width:37.7843%;--hb-height:5.2002%"><span>estación de energía portátil permanece en</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:55.2347%;--hb-y:48.7551%;--hb-width:39.3632%;--hb-height:5.2002%"><span>funcionamiento y consume energía de forma</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:55.2347%;--hb-y:53.5357%;--hb-width:38.6321%;--hb-height:5.2002%"><span>continua. En caso de un corte de energía, el</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:55.2347%;--hb-y:58.3164%;--hb-width:39.7794%;--hb-height:5.2002%"><span>sistema cambiará a alimentación por batería</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:55.2347%;--hb-y:63.097%;--hb-width:17.3734%;--hb-height:5.2002%"><span>en 20 milisegundos.</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:55.2347%;--hb-y:67.8776%;--hb-width:37.1163%;--hb-height:5.2002%"><span>Cuando el modo UPS está desactivado, el</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:55.2347%;--hb-y:72.6583%;--hb-width:39.4226%;--hb-height:5.2002%"><span>cambio a alimentación por batería se realiza</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:55.2347%;--hb-y:77.4389%;--hb-width:13.4197%;--hb-height:5.2002%"><span>en 5 segundos.</span></span></div></div></figure></div>

<span id="native-charging"></span>

## CARGANDO

<p>Energía renovable primero: abogamos por utilizar primero energía renovable. Este producto admite dos modos de carga al mismo tiempo: carga solar y carga de pared de CA. Cuando la carga en la pared de CA y la carga solar están activadas al mismo tiempo, el producto dará prioridad a la carga solar y se utilizarán ambos métodos para cargar la batería a la máxima potencia permitida.</p>

<p>Cargue completamente el dispositivo antes de usarlo por primera vez.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Nota</td><td class="manual-callout-body"><p>1. La temperatura recomendada para cargar el producto es entre 0 °C y 45 °C (32 °F a 113 °F), y la temperatura de descarga es entre -15 °C y 45 °C (5 °F a 113 °F). Operar el producto fuera de este rango de temperatura puede restringir su capacidad de carga y descarga, o impedir que cargue o descargue. 2. La potencia de carga y la capacidad de la batería del producto pueden variar debido a fluctuaciones de temperatura. Cuando la temperatura ambiente esté entre -15 °C y -10 °C (5 °F a 14 °F), la potencia de salida máxima disminuye a 3600 W.</p></td></tr></tbody></table>

### CARGA A TRAVÉS DE UNA TOMA DE CORRIENTE DE RED DE CA

<div class="native-figure native-ac-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="d05b746941566487dd968607ec043b6694b5de181a1761408022e9a7b05220b6" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:62.5157%;--hb-y:49.8676%;--hb-width:28.6427%;--hb-height:7.6991%"><span>Conecte el cable de carga CA a</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62.5157%;--hb-y:57.8322%;--hb-width:28.7785%;--hb-height:7.6991%"><span>la entrada del HomePower 5000</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.5157%;--hb-y:65.7968%;--hb-width:25.5772%;--hb-height:7.6991%"><span>Plus y una toma de corriente.</span></span></div></div></figure></div>

### CARGA CON STS

<div class="native-figure native-sts-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-charge" data-source-fragment-sha256="bda48e84c6b4d408708c7d7d38afb06be540fd038a972540e9417394f45ae47f" data-web-base-art-ref="sts-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:40.5492%;--hb-y:6.6994%;--hb-width:56.2496%;--hb-height:4.9743%"><span>Conecte su STS Jackery para habilitar la carga mediante el STS.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:40.5473%;--hb-y:12.6273%;--hb-width:55.3663%;--hb-height:4.9743%"><span>*La configuración de reserva de respaldo funciona en todos los</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:40.5473%;--hb-y:17.2002%;--hb-width:53.429%;--hb-height:4.9743%"><span>modos del STS Por lo tanto, el Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:40.5473%;--hb-y:21.7731%;--hb-width:53.3507%;--hb-height:4.9743%"><span>dejará de cargarse cuando supere el umbral de reserva Para</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:40.5473%;--hb-y:26.9189%;--hb-width:42.4368%;--hb-height:4.9743%"><span>cargarlo de inmediato, siga los pasos indicados.</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:40.9313%;--hb-y:34.5313%;--hb-width:6.5648%;--hb-height:5.1046%"><span><strong>PASO</strong> <strong>1</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:59.7431%;--hb-y:34.5313%;--hb-width:6.8399%;--hb-height:5.1046%"><span><strong>PASO</strong> <strong>2</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:63.2818%;--hb-y:78.1368%;--hb-width:3.2482%;--hb-height:2.014%"><span>HP5000Plus</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:77.4528%;--hb-y:88.7199%;--hb-width:8.1522%;--hb-height:4.9743%"><span>*App STS</span></span></div></div></figure></div>

<p>Cuando el puerto de expansión de CA está conectado al STS, la entrada CA no se utilizara para cargar. En ese caso, la estación de energía se puede cargar mediante los siguientes puertos: puerto de expansión de CA, alta tensión FV , baja tensión FV.</p>

### Nota

### CARGA CON PANELES SOLARES

<p>Cuando conecte paneles solares en serie, asegúrese de que la tensión máxima de salida de todos Precaución los paneles esté entre 16V-60V para el puerto de entrada de baja tensión FV y 135V-450V para el puerto de entrada de alta tensión FV.</p>

<p>Conecte al puerto de alimentación de baja tensión FV</p>

<p>Rango de voltaje entrada baja tensión FV: 16V a 60V</p>

<p>El Jackery HomePower 5000 Plus tiene dos puertos de entrada de baja tensión FV, cada uno admite la conexión directa de un panel solar de 500W o tres paneles solares de 200W. Si un puerto de alimentación de baja tensión FV necesita conectar dos o más paneles solares simultáneamente, consulte la siguiente figura para cargar a través del conector del panel solar (se vende por separado, no se incluye por defecto).</p>

<div class="native-figure native-low-pv-500 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-500" data-source-fragment-sha256="c15fbfa8cf0f1dde0f0d3dbc98396dec1fbf186981f8a665885d7e1ed2bef6ff" data-web-base-art-ref="low-pv-500" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-500.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-500.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.958%;--hb-y:9.639%;--hb-width:5.7165%;--hb-height:5.1339%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.971%;--hb-y:87.2762%;--hb-width:15.2748%;--hb-height:5.6714%"><span>SolarSaga 500 X × 2</span></span></div></div></figure></div>

<div class="native-figure native-low-pv-200 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-200" data-source-fragment-sha256="fad18b7b2c402a027b5a4d822a86fc0b91020111738fc1bb20149f6038143401" data-web-base-art-ref="low-pv-200" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-200.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-200.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.1609%;--hb-y:9.0212%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.6889%;--hb-y:9.0215%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:78.3203%;--hb-y:92.5261%;--hb-width:15.2462%;--hb-height:5.512%"><span>SolarSaga 200 × 6</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><p>1. Asegúrese de que el voltaje de entrada para ambos puertos de entrada CC sea el mismo. De lo contrario, podría dañar el producto. Por ejemplo:</p><ul><li>Se recomienda utilizar paneles solares Jackery del mismo modelo y la misma cantidad de paneles al conectar paneles solares a ambos puertos de entrada DC8020.</li><li>No cargue el producto utilizando simultáneamente un cargador de automóvil y un panel solar. Hacerlo podría quemar el fusible del automóvil o resultar en un fallo de carga. 2. Il est recommandé d’utiliser le panneau solaire Jackery pour charger l’HomePower 5000 Plus. Jackery décline toute responsabilité en cas de dommages causés par l’utilisation de panneaux solaires d’autres marques.</li></ul></td></tr></tbody></table>

<p>Conecte al puerto de alimentación de alta tensión FV</p>

<p>Rango de voltaje entrada alta tensión FV: 135V a 450V</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><p>1. Mantenha o interrutor de alta tensão desligado antes de ligar a entrada de alta tensão ou durante a manutenção. 2. Antes de utilizar los puertos de alimentación de alta tensión FV, asegúrese de que el interruptor FV esté encendido. 3. Asegúrese de que el interruptor de alto PV esté en la posición 'OFF ' o 'LOCK' antes de usar la llave MC4 provista para desmontar los conectores MC4.</p></td></tr></tbody></table>

<div class="native-figure native-high-pv native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv" data-source-fragment-sha256="2ab1d3f89ed00eb0d614d7bd953d73b4b1f43be10ebea2a7f7c5a251262a29a5" data-web-base-art-ref="high-pv" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.1774%;--hb-y:7.4109%;--hb-width:31.2781%;--hb-height:4.0058%"><span>Desmonte los conectores MC4 con</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:7.1774%;--hb-y:11.6113%;--hb-width:25.5823%;--hb-height:4.0058%"><span>la llave MC4 proporcionada.</span></span></div></div></figure></div>

<div class="native-figure native-high-pv-lock native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv-lock" data-source-fragment-sha256="a5500df5cc3fd49349451dd2c42aa49e485547bdc73234698fe3e74da9fb04f3" data-web-base-art-ref="high-pv-lock" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv-lock.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.1126%;--hb-y:14.2495%;--hb-width:11.0889%;--hb-height:8.3363%"><span><strong>Bloquear</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:54.0559%;--hb-y:14.8955%;--hb-width:15.5803%;--hb-height:8.3363%"><span><strong>Desbloquear</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.9177%;--hb-y:24.6047%;--hb-width:40.2623%;--hb-height:6.3597%"><span>Gire el interruptor de alto voltaje a la posición</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:54.0491%;--hb-y:25.2504%;--hb-width:42.1663%;--hb-height:6.3597%"><span>Suelte el mecanismo de bloqueo y el interruptor</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:6.9177%;--hb-y:30.4512%;--hb-width:39.485%;--hb-height:6.3597%"><span>"LOCK" y presione el mecanismo de bloqueo.</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:54.0491%;--hb-y:31.0969%;--hb-width:23.807%;--hb-height:6.3597%"><span>volverá a la posición "OFF".</span></span></div></div></figure></div>

<p>Alimentación de alta tensión FV + baja tensión FV</p>

<p>Rango de tensión de alimentación baja FV: 16V a 60V</p>

<p>Rango de tensión para alimentación de tensión FV alta: 135V a 450V</p>

<div class="native-figure native-dual-pv native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dual-pv" data-source-fragment-sha256="0c66ccafa23616c19ca1e92a43b633566946a182d8ab4130ddfc6de832746e75"><div class="hb-reference-semantic" data-reference-id="dual-pv.semantic"><img alt="dual-pv" class="hb-reference-art hb-composite-art" src="assets/dual-pv.svg"/></div></figure></div>

### CARGA CON EL CARGADOR DE AUTO

<p>Este producto se puede cargar un cargador de auto de 12 V. Asegúrate de que el cargador de auto y el encendedor de cigarrillos del auto tengan una buena conexión.</p>

<div class="native-figure native-car native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="e6e5cc29a303532bc16eff99d27facd2b12aecbfb281aa9b496a1781267c9cb1" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car-es.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71.4472%;--hb-y:18.391%;--hb-width:8.6969%;--hb-height:7.0656%"><span>vehículo</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:39.143%;--hb-y:83.6458%;--hb-width:58.3542%;--hb-height:9.7726%;--hb-fill:#ffffff"><span>*El cable de carga para automóvil se vende por separado.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><p>1. Inicia el vehículo antes de cargar tu estación de energía. 2. Si el vehículo circula por carreteras llenas de altibajos, está prohibido utilizar el cargador del coche por si se quema debido a una mala conexión. La Compañía no será responsable de ninguna pérdida causada por un funcionamiento no estándar. 3. La carga de vehículos solo es aplicable en vehículos de 12 V, no en los de 24 V. Por favor, no cargue este producto con un vehículo de 24 V para evitar daños personales y pérdidas materiales.</p></td></tr></tbody></table>

<span id="native-storage"></span>

## ALMACENAMIENTO

<p>Almacene el producto en un lugar seco y limpio con ventilación adecuada.Temperatura y humedad de</p>

<p>almacenamiento:</p>

<ul><li>1 mes: -20 a 45 °C (0-60 % HR)</li></ul>

<ul><li>3 meses: 0 a 45 °C (0-60 % HR)</li></ul>

<ul><li>12 meses: 0 a 25 °C (0-60 % HR)</li></ul>

<p>Si este producto se almacena durante un período prolongado (de 3 a 6 meses) con la batería descargada,</p>

<p>podría volverse imposible recargarlo.Para evitar esto y mantener la salud de la batería, se recomienda revisar y</p>

<p>recargar el producto cada tres meses, y realizar un ciclo completo de carga y descarga al menos una vez</p>

<p>cada 6 a 12 meses.</p>

<span id="native-app"></span>

## CONFIGURACIÓN DE LA APLICACIÓN

### 1. Para descargar la aplicación e iniciar sesión

<figure aria-label="App download" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Busca "Jackery" en Google Play o App Store para instalar la aplicación. Después, podrá registrarte e iniciar sesión.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternativamente, escanee el código QR a continuación para descargar e instalar la aplicación.</p></div></div></div><div class="hb-app-download-semantic"><img alt="App download" class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

### 2.Añadir un dispositivo

<p>2.1 Haga clic en el botón Añadir dispositivo <span class="native-inline-plus">+</span> ;</p>

<p>2.2 Mantenga pulsado el botón de "encendido" del dispositivo para encenderlo. Los iconos del wifi y del Bluetooth del dispositivo parpadearán para indicar que el dispositivo ha entrado en el modo de configuración de red. A continuación, pulse el botón "icono parpadeante" y permita que la aplicación se conecte a los dispositivos cercanos y abra los permisos de Bluetooth;</p>

<div class="native-figure native-app-add native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add" data-source-fragment-sha256="708b58634468539a0aee8bf378096f323c4e49e1dbbae5f6333fba125a633831" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-add-es.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:19.2055%;--hb-y:94.5288%;--hb-width:4.1654%;--hb-height:5.0597%"><span>2.1</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.7967%;--hb-y:94.5288%;--hb-width:4.7701%;--hb-height:5.0597%"><span>2.2</span></span></div></div></figure></div>

<div class="native-figure native-app-control native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="8b3c480505a6a53ff6019eef2fdbd72ce3a3fb2e46fa788fba4f4056ae9b09bf" data-web-base-art-ref="app-control" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-control.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-control.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.4553%;--hb-y:17.961%;--hb-width:20.702%;--hb-height:11.2403%"><span>Bouton d’alimentation</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:3.0706%;--hb-y:24.3873%;--hb-width:19.7077%;--hb-height:11.2403%"><span>Botón de energía CC</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:73.4553%;--hb-y:27.0023%;--hb-width:9.3484%;--hb-height:11.2403%"><span>principale</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:73.3818%;--hb-y:43.8989%;--hb-width:23.2237%;--hb-height:11.2403%"><span>Botón de <strong>encendido</strong> USB</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:3.0702%;--hb-y:57.7517%;--hb-width:19.479%;--hb-height:11.2403%"><span>Botón de energía CA</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Observaciones</td><td class="manual-callout-body"><p>Después de encenderse, si la APP no se conecta en 2 horas, el dispositivo apagará automáticamente el Wi-Fi y el Bluetooth. A continuación, es necesario mantener pulsado el Botón USB y el Botón CA para volver a activar el Wi-Fi y Bluetooth.</p></td></tr></tbody></table>

<p>2.3 Tras hacer clic en el icono del dispositivo buscado, la aplicación conecta automáticamente el dispositivo a través de Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Observaciones</td><td class="manual-callout-body"><p>Si durante el proceso de vinculación se indica que "el dispositivo ha sido vinculado", se pueden utilizar las dos formas siguientes para la conexión:</p><ul><li>El propietario del dispositivo lo compartirá con otros usuarios a través de la App.</li><li>Mantenga pulsados el Botón POWER y el Botón USB durante 3 segundos para reiniciar el dispositivo y, a continuación, vuelva a vincularlo.</li></ul></td></tr></tbody></table>

<p>2.4 Una vez que el dispositivo se haya conectado correctamente, es necesario introducir el nombre y la contraseña de la red Wi-Fi a la que se conectará el dispositivo. Una vez introducidos, el dispositivo se conectará automáticamente a la red Wi-Fi;</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Observaciones</td><td class="manual-callout-body"><p>Selecciona una red Wi-Fi en la banda de 2,4 GHz. El dispositivo no admite una red Wi-Fi en la banda de 5 GHz.</p></td></tr></tbody></table>

<p>2.5 Una vez que el dispositivo se haya añadido correctamente en la página de inicio del dispositivo, el icono Wi-Fi del dispositivo estará siempre encendido;</p>

<div class="native-figure native-app-results native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-results" data-source-fragment-sha256="4b0abcf4f3dc9d0e8711acc7e64e70273219606452cc604306b7ad716a8b8825" data-web-base-art-ref="app-results" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-results.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-results-es.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:12.1529%;--hb-y:94.6804%;--hb-width:3.3629%;--hb-height:5.5949%"><span>2.3</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:48.6834%;--hb-y:94.6804%;--hb-width:3.4788%;--hb-height:5.5949%"><span>2.4</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:85.4224%;--hb-y:94.6804%;--hb-width:3.3861%;--hb-height:5.5949%"><span>2.5</span></span></div></div></figure></div>

<p>Las capturas de pantalla anteriores sirven solo de referencia.</p>

### 3. Desvincular el dispositivo

<p>Haga clic en el botón «Configuración» situado en la esquina superior derecha de la interfaz principal del dispositivo para entrar en la página de configuración. Después, haga clic en el botón «Desvincular» situado en la parte inferior de la página para desvincular el dispositivo.</p>

### 4. Notas

<p>4.1 Para activar Wi-Fi y Bluetooth:</p>

<ul><li>El wifi y el Bluetooth se encienden automáticamente al encender el dispositivo y se iluminan los iconos de wifi y Bluetooth de la pantalla;</li><li>Pulse el botón de alimentación de salida USB y el botón de alimentación de salida CA al mismo tiempo hasta que se enciendan los iconos de wifi y Bluetooth en la pantalla;</li></ul>

<p>4.2 Para desactivar Wi-Fi y Bluetooth:</p>

<ul><li>Pulse el botón de alimentación de salida USB y el botón de alimentación de salida CA al mismo tiempo hasta que se apaguen los iconos de wifi y Bluetooth en la pantalla;</li></ul>

<ul><li>El Wi-Fi y el Bluetooth se apagarán automáticamente si se conecta ningún dispositivo en 2 horas;</li></ul>

<p>4.3 Para restablecer Wi-Fi y Bluetooth：</p>

<ul><li>Pulsa el botón POWER y el botón USB al mismo tiempo durante 3 segundos para restablecer los ajustes de fábrica de Wi-Fi y Bluetooth y reiniciar el sistema. Se desvinculará la cuenta de la</li></ul>

<span id="native-warranty"></span>

## GARANTÍA

<figure aria-label="GARANTÍA" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>Solo ofrecemos nuestra garantía a los clientes que compren en el sitio web oficial de Jackery, plataformas de terceros con la marca Jackery o distribuidores autorizados locales.</strong></div><div class="hb-warranty-local-note">* El período y los detalles de la garantía pueden variar según las leyes locales, regulaciones y distribuidores autorizados.</div></figure>

### Garantía limitada

<figure aria-label="Garantía limitada" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1">Jackery Inc. garantiza al consumidor original que el producto Jackery estará libre de defectos relativos al acabado y a los materiales en condiciones normales de uso por parte del consumidor durante el período de garantía aplicable identificado en la sección "Período de garantía" que figura a continuación, sujeto a las exclusiones que se establecen a continuación. Esta declaración de garantía establece la obligación de garantía total y exclusiva de Jackery. No asumiremos ni autorizaremos que ninguna persona asuma por nosotros ninguna otra responsabilidad en relación con la venta de nuestros productos.</figure>

### Período de garantía

<figure aria-label="Período de garantía" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="5 AÑOS El periodo de garantía estándar de Jackery HomePower 5000 Garantía estándar" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">5</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">El periodo de garantía estándar de Jackery HomePower 5000 Garantía estándar</strong></div></div><div class="hb-warranty-period-copy">Plus es de 60 meses. En cada caso, el período de garantía se mide a partir de la fecha de compra por parte del comprador consumidor original. Para establecer la fecha de inicio del período de garantía, se necesita el recibo de venta de la primera compra del consumidor u otra prueba documental razonable.</div></div><div aria-label="2 AÑOS Se requiere una tarifa adicional para Garantía extendida" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Se requiere una tarifa adicional para Garantía extendida</strong></div></div><div class="hb-warranty-period-copy">la garantía extendida. Para obtener detalles sobre la garantía extendida, visite el sitio web de Jackery o comuníquese con el servicio de atención al cliente de Jackery.</div></div></div></figure>

### Reparación o reemplazo

<figure aria-label="Reparación o reemplazo" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3">Jackery reparará o reemplazará (a cargo de Jackery) cualquier producto Jackery que no funcione durante el período de garantía aplicable debido a un defecto de mano de obra o material. El producto reparado/reemplazado asume la garantía restante de la fecha de compra original.</figure>

### Limitado al comprador consumidor original

<figure aria-label="Limitado al comprador consumidor original" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4">La garantía del producto de Jackery se limita al consumidor original y no es transferible a ningún propietario posterior.</figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5">La garantía de Jackery no se aplica a: Mal uso, abuso, modificación, daño por accidente, o uso para cualquier cosa que no sea el uso normal del consumidor según lo autorizado en los folletos actuales del producto de Jackery. Intento de reparación por cualquier persona que no sea un centro autorizado. Cualquier producto adquirido a través de una casa de subastas en línea. La garantía de Jackery no se aplica a la célula de la batería a menos que usted la cargue completamente en los siete días siguientes a la compra del producto y, a partir de entonces, al menos una vez cada 6 meses.</figure>

### Derechos de interpretación

<figure aria-label="Derechos de interpretación" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6">Jackery Inc. se reserva el derecho a la interpretación final de la política posventa de los clientes anterior.</figure>

<span id="native-specifications"></span>

## ESPECIFICACIONES

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química de celda</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Alrededor de 134,5 lbs/61 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">16,5×15,5×25 pulgadas / 41,8×39,5×63,5 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">4000 ciclos al 70%+ capacidad</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">SAI</th><td class="manual-spec-value hb-spec-value">SAI de respaldo: ＜20ms SAI en línea: 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topología de inversor</th><td class="manual-spec-value hb-spec-value">No aislada</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Factor de potencia</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unidad entera</th><td class="manual-spec-value hb-spec-value">Tipo 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE ALIMENTACIÓN</h2>

<figure aria-label="PUERTOS DE ALIMENTACIÓN" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CA en Modo de Carga</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A Máx. (Tiempo de duración &lt; 3h cuando la corriente supera los 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CA en Modo de Derivación</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Máx. (Tiempo de duración &lt; 3h cuando la corriente supera los 12A) 240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CA (Entrada)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CC</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Alta tensión FV</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A Máx., 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Baja tensión FV</th><td class="manual-spec-value hb-spec-value">2 x Puertos CC 8mm; 16V-60V⎓10,5A Máx., Doble a 21A/1200W Máx. 11V-16V (Tensión de servicio)⎓8A Máx., Doble a 8A Máx</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE SALIDA</h2>

<figure aria-label="PUERTOS DE SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA del Modo de derivación</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Máx. 240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × Salida de CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA Totall</th><td class="manual-spec-value hb-spec-value">7200W Máx., 14400W Transitoria</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salida USB-C</th><td class="manual-spec-value hb-spec-value">100W Máx., 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salida USB-A</th><td class="manual-spec-value hb-spec-value">18W Máx., 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1,5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto para encendedor de cigarrillos</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CA (Salida)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A Máx.</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">RIESGO DE INGESTA: Este Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">producto contiene una batería de botón o de moneda. -15°C~45°C (5°F~113°F) -15°C~-10°C (5°F~14°F) Potencia de salida: 3600 W</td></tr></tbody></table></figure>

<p>® ® ※ USB Tipo-C y USB-C son marcas registradas del Foro de Implementadores USB.</p>

<span id="native-ess"></span>

## GUÍA DE INSTALACIÓN DEL SISTEMA DE RESPALDO INTELIGENTE PARA EL HOGAR (AC ESS)

<p>Para conectar el Jackery HomePower 5000 Plus al Smart Transfer Switch (STS), use el cable de expansión para enlazar el puerto de expansión CA del Explorer 5000 Plus al puerto de entrada/salida CA del STS.</p>

<p>Para conectar el Jackery HomePower 5000 Plus al paquete de baterías, use el cable de expansión para conectar su puerto de expansión CC (A) al puerto de expansión CC (B) del paquete de baterías.</p>

<div class="native-figure native-ess native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ess" data-source-fragment-sha256="98100e4ba97163059965b98673a3e65557406b92e2fa569b1534f79ad0b0fb07" data-web-base-art-ref="ess" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ess.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ess.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.4026%;--hb-y:90.9293%;--hb-width:91.8038%;--hb-height:3.2818%"><span>Para obtener instrucciones detalladas sobre la instalación y conexión, consulte los manuales de usuario</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.4026%;--hb-y:93.9463%;--hb-width:30.7857%;--hb-height:3.2818%"><span>del STS y del paquete de baterías.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Precaución</td><td class="manual-callout-body"><p>Posición de instalación del sistema de respaldo inteligente para el hogar (AC ESS) Instalación en interiores. El área debe ser completamente impermeable. La pared debe ser plana y nivelada. Rango de temperatura ambiente: -15°C~45°C. La temperatura y la humedad deben mantenerse en un nivel constante. Instale en un lugar bien ventilado. No instale en un área accesible para niños o mascotas. El área de instalación debe evitar la luz solar directa. No debe haber materiales inflamables o explosivos cerca del inversor y la batería.</p></td></tr></tbody></table>

<p>Modelo del sistema</p>

<p>HB5000C-TS02A</p>

<span id="native-ess-host"></span>

## Jackery HomePower 5000 Plus

### ESPECIFICACIONES

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química de celda</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Alrededor de 134,5 lbs/61 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">16,5×15,5×25 pulgadas / 41,8×39,5×63,5 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">4000 ciclos al 70%+ capacidad</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">SAI</th><td class="manual-spec-value hb-spec-value">SAI de respaldo: ＜20ms SAI en línea: 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topología de inversor</th><td class="manual-spec-value hb-spec-value">No aislada</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Factor de potencia</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unidad entera</th><td class="manual-spec-value hb-spec-value">Tipo 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE ALIMENTACIÓN</h2>

<figure aria-label="PUERTOS DE ALIMENTACIÓN" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CA en Modo de Carga</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A Máx. (Tiempo de duración &lt; 3h cuando la corriente supera los 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CA en Modo de Derivación</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Máx. (Tiempo de duración &lt; 3h cuando la corriente supera los 12A) 240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CA (Entrada)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrada de CC</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Alta tensión FV</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A Máx., 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Baja tensión FV</th><td class="manual-spec-value hb-spec-value">2 x Puertos CC 8mm; 16V-60V⎓10,5A Máx., Doble a 21A/1200W Máx. 11V-16V (Tensión de servicio)⎓8A Máx., Doble a 8A Máx</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE SALIDA</h2>

<figure aria-label="PUERTOS DE SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA del Modo de derivación</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Máx. 240V~60Hz, 16,7A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × Salida de CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida de CA Totall</th><td class="manual-spec-value hb-spec-value">7200W Máx., 14400W Transitoria</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salida USB-C</th><td class="manual-spec-value hb-spec-value">100W Máx., 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salida USB-A</th><td class="manual-spec-value hb-spec-value">18W Máx., 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1,5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto para encendedor de cigarrillos</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CA (Salida)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A Máx.</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F) -15°C~-10°C (5°F~14°F) Potencia de salida: 3600 W</td></tr></tbody></table></figure>

<p>RIESGO DE INGESTA: Este producto contiene una batería de botón o de moneda. ® ® ※ USB Tipo-C y USB-C son marcas registradas del Foro de Implementadores USB.</p>

### Modelo: JHP-5000C

<span id="native-ess-battery"></span>

## Jackery Battery Pack 5000 Plus

<h3 class="hb-heading-label-pair"><span class="hb-heading-title">ESPECIFICACIONES</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span></h3>

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre de producto</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JBP-5000A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química de celda</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Alrededor de 81,57 libras/37 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">16,5 x 13,5 x 13,2 pulgadas/41.8 x 34.4 x 33.6 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">4000 ciclos al 70%+ capacidad</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente máxima de cortocircuito y duración</th><td class="manual-spec-value hb-spec-value">2600A/5ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Protección contra la entrada de agua</th><td class="manual-spec-value hb-spec-value">IP20</td></tr></tbody></table></figure>

<p>Utilizar únicamente junto con Jackery Explorer 5000 Plus y Jackery HomePower 5000 Plus.</p>

<h2 class="hb-spec-group">PUERTOS DE ALIMENTACIÓN/SALIDA</h2>

<figure aria-label="PUERTOS DE ALIMENTACIÓN/SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A Máx.</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA AMBIENTAL DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr></tbody></table></figure>

<p>RIESGO DE INGESTA: Este producto contiene una batería de botón o de moneda.</p>

<span id="native-ess-sts"></span>

## Jackery Smart Transfer Switch

<h3 class="hb-heading-label-pair"><span class="hb-heading-title">ESPECIFICACIONES</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span></h3>

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre de producto</th><td class="manual-spec-value hb-spec-value">Jackery Smart Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JA-TS02A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Voltaje CA (Nominal)</th><td class="manual-spec-value hb-spec-value">120V/240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tipo de Alimentación</th><td class="manual-spec-value hb-spec-value">Fase Dividida</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Entrada Máxima</th><td class="manual-spec-value hb-spec-value">Red de 100A / Estación de Energía de 60A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Salida Máxima</th><td class="manual-spec-value hb-spec-value">Carga Doméstica de 60A / Estación de Energía de 33,4A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente Máxima de Cortocircuito de Entrada</th><td class="manual-spec-value hb-spec-value">10KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Categoría de Sobretensión</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">≤20ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tipo de Caja (Panel de Distribución)</th><td class="manual-spec-value hb-spec-value">NEMA Tipo 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Número de Ramas de Carga</th><td class="manual-spec-value hb-spec-value">12</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito Principal</th><td class="manual-spec-value hb-spec-value">2 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito Derivado</th><td class="manual-spec-value hb-spec-value">14 AWG 12 AWG 10 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Comunicación</th><td class="manual-spec-value hb-spec-value">Wi-Fi y Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de Funcionamiento</th><td class="manual-spec-value hb-spec-value">-20°C~40°C (-4°F~104°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">22 x 14,7 x 7,87 pulgadas/ 56 x 37,4 x 20 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 25,57 libras/11,6 kg</td></tr></tbody></table></figure>

### Modelo: JBP-5000A

### Modelo: JA-TS02A

<p>Cuando utilice el producto, asegúrese de que esté conectado a una tensión de red de fase partida de 240 V.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Nota</td><td class="manual-callout-body"><p>SISTEMA DE RESPALDO INTELIGENTE PARA EL HOGAR (AC ESS) Aproximadamente 575.16 lbs/260.89 kg</p></td></tr></tbody></table>

<span id="native-ess-package"></span>

## LISTA DE PAQUETES

<div class="native-figure native-package-host native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-host" data-source-fragment-sha256="5a8c8f5e01e31c3c9975acffa4a5cf533499295614f192db8c439d1a0023f21d" data-web-base-art-ref="package-host" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-host.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-host.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:88.3071%;--hb-y:40.8533%;--hb-width:1.8037%;--hb-height:1.9358%"><span>Model :JHP-5000C</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:82.8015%;--hb-y:66.9539%;--hb-width:5.5676%;--hb-height:4.1614%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:82.8131%;--hb-y:69.7343%;--hb-width:5.5441%;--hb-height:2.6155%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:81.0598%;--hb-y:73.9503%;--hb-width:1.9679%;--hb-height:2.2318%"><span><strong>CONTACT</strong> <strong>US</strong> <strong>:</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:82.007%;--hb-y:75.4367%;--hb-width:4.9025%;--hb-height:3.224%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:87.9677%;--hb-y:75.6067%;--hb-width:1.7489%;--hb-height:1.9376%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:87.9677%;--hb-y:76.4925%;--hb-width:1.6781%;--hb-height:1.9376%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:5.6436%;--hb-y:85.5465%;--hb-width:22.8663%;--hb-height:6.8182%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:35.2095%;--hb-y:85.5465%;--hb-width:16.8897%;--hb-height:6.8182%"><span>Cable de carga de CA</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:61.5388%;--hb-y:85.5465%;--hb-width:7.9774%;--hb-height:6.8182%"><span>Llave MC4</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:78.6545%;--hb-y:85.5465%;--hb-width:13.8389%;--hb-height:6.8182%"><span>Manual de usuario</span></span></div></div></figure></div>

<div class="native-figure native-package-battery native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-battery" data-source-fragment-sha256="42fe8039f40e6dd29aefa0d03c57631ef2adde2528e6a01b7d3017895b26c5e6" data-web-base-art-ref="package-battery" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-battery.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-battery.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:68.3595%;--hb-y:17.3714%;--hb-width:1.7514%;--hb-height:2.5785%"><span>Model: JBP-5000A</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:77.4335%;--hb-y:28.5688%;--hb-width:22.3546%;--hb-height:41.1083%;--hb-fill:#b5b5b6"><span><strong>Vendu</strong><br/><strong>séparément</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.6274%;--hb-y:47.8596%;--hb-width:5.8832%;--hb-height:5.794%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62.5793%;--hb-y:51.8107%;--hb-width:5.9802%;--hb-height:3.6064%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:61.096%;--hb-y:60.9685%;--hb-width:1.8815%;--hb-height:2.9684%"><span><strong>CONTACT</strong> <strong>US:</strong></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:62.0284%;--hb-y:62.9253%;--hb-width:4.8309%;--hb-height:4.2754%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:67.8953%;--hb-y:63.1502%;--hb-width:1.7266%;--hb-height:2.5808%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:67.8953%;--hb-y:64.3169%;--hb-width:1.6569%;--hb-height:2.5808%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:5.3687%;--hb-y:77.9001%;--hb-width:23.4172%;--hb-height:9.1241%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:36.091%;--hb-y:77.9001%;--hb-width:15.1265%;--hb-height:9.1241%"><span>Cable de expansión</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:58.6086%;--hb-y:77.9001%;--hb-width:13.8389%;--hb-height:9.1241%"><span>Manual de usuario</span></span></div></div></figure></div>

<div class="native-figure native-package-sts native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-sts" data-source-fragment-sha256="716a3f35f5cadc41f1867c1a8bb0de6447db67464f46dd4938be26eb52a578ee" data-web-base-art-ref="package-sts" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-sts.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-sts.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:36.234%;--hb-y:13.0442%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:38.0504%;--hb-y:13.0442%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:36.234%;--hb-y:13.716%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:38.0504%;--hb-y:13.716%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:33.6812%;--hb-y:14.1471%;--hb-width:1.2332%;--hb-height:1.8075%"><span>Upward</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:33.2154%;--hb-y:15.2531%;--hb-width:1.4638%;--hb-height:1.6669%"><span>A scale of 1:1</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:33.2154%;--hb-y:15.9611%;--hb-width:1.1306%;--hb-height:1.6669%"><span>Unit: mm</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:74.8022%;--hb-y:19.204%;--hb-width:1.8751%;--hb-height:1.6443%"><span>Model: JA-TS02A</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:83.6805%;--hb-y:31.5175%;--hb-width:5.5775%;--hb-height:3.6757%"><span>Quick Guide</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:82.8597%;--hb-y:34.0701%;--hb-width:7.4119%;--hb-height:2.6681%"><span>HomePower Energy System</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:71.4975%;--hb-y:34.4853%;--hb-width:1.258%;--hb-height:1.367%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:71.0373%;--hb-y:36.0648%;--hb-width:0.4048%;--hb-height:1.2415%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:71.4599%;--hb-y:36.0648%;--hb-width:0.4368%;--hb-height:1.2415%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:71.9197%;--hb-y:36.0648%;--hb-width:0.3964%;--hb-height:1.2415%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:72.3236%;--hb-y:36.0648%;--hb-width:0.4762%;--hb-height:1.2415%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:72.7944%;--hb-y:36.0648%;--hb-width:0.4129%;--hb-height:1.2415%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:15.5954%;--hb-y:36.9326%;--hb-width:2.9591%;--hb-height:1.8464%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:71.8929%;--hb-y:38.5712%;--hb-width:0.4928%;--hb-height:1.2415%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:71.8003%;--hb-y:38.728%;--hb-width:0.6728%;--hb-height:1.2415%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:69.0455%;--hb-y:41.1793%;--hb-width:6.1448%;--hb-height:3.577%"><span>USER MANUAL</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:14.2894%;--hb-y:41.4559%;--hb-width:0.5584%;--hb-height:1.4916%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:15.495%;--hb-y:41.4559%;--hb-width:0.6481%;--hb-height:1.4916%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:16.808%;--hb-y:41.4559%;--hb-width:0.5349%;--hb-height:1.4916%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:17.9607%;--hb-y:41.4559%;--hb-width:0.7593%;--hb-height:1.4916%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:19.3049%;--hb-y:41.4559%;--hb-width:0.5806%;--hb-height:1.4916%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:69.0455%;--hb-y:43.6667%;--hb-width:6.145%;--hb-height:2.26%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:67.5809%;--hb-y:47.5446%;--hb-width:1.3788%;--hb-height:1.6614%"><span><strong>Contact</strong> <strong>us:</strong></span></span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:67.5809%;--hb-y:48.0911%;--hb-width:1.9922%;--hb-height:1.6443%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="28" style="--hb-x:74.4363%;--hb-y:48.6095%;--hb-width:2.2612%;--hb-height:1.6443%"><span>Version: JAK-UM-V1.0</span></span><span class="hb-reference-live-label" data-source-line="29" style="--hb-x:67.5809%;--hb-y:48.6308%;--hb-width:2.111%;--hb-height:1.6443%"><span>1-888-502-2236(US)</span></span><span class="hb-reference-live-label" data-source-line="30" style="--hb-x:16.7309%;--hb-y:48.6398%;--hb-width:0.806%;--hb-height:1.4916%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="31" style="--hb-x:36.2337%;--hb-y:48.6634%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="32" style="--hb-x:38.0504%;--hb-y:48.6634%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="33" style="--hb-x:16.4672%;--hb-y:49.0888%;--hb-width:1.3127%;--hb-height:1.4916%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="34" style="--hb-x:36.234%;--hb-y:49.4685%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="35" style="--hb-x:38.0504%;--hb-y:49.4685%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="36" style="--hb-x:65.1999%;--hb-y:57.8258%;--hb-width:13.8389%;--hb-height:5.5228%"><span>Manual de usuario</span></span><span class="hb-reference-live-label" data-source-line="37" style="--hb-x:81.8447%;--hb-y:57.8258%;--hb-width:9.0934%;--hb-height:5.5228%"><span>Guía rápida</span></span><span class="hb-reference-live-label" data-source-line="38" style="--hb-x:5.9674%;--hb-y:57.8262%;--hb-width:22.2194%;--hb-height:5.5228%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="39" style="--hb-x:30.1394%;--hb-y:57.8262%;--hb-width:15.5094%;--hb-height:5.5228%"><span>Plantilla de Marcado</span></span><span class="hb-reference-live-label" data-source-line="40" style="--hb-x:49.0264%;--hb-y:57.8262%;--hb-width:14.0309%;--hb-height:5.5228%"><span>Entrada/Salida de</span></span><span class="hb-reference-live-label" data-source-line="41" style="--hb-x:50.8889%;--hb-y:62.2445%;--hb-width:10.7079%;--hb-height:5.5228%"><span>Energía Cable</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="42" style="--hb-x:77.4335%;--hb-y:64.9624%;--hb-width:22.3546%;--hb-height:24.8829%;--hb-fill:#b5b5b6"><span><strong>Vendu</strong><br/><strong>séparément</strong></span></span><span class="hb-reference-live-label" data-source-line="43" style="--hb-x:48.9219%;--hb-y:82.132%;--hb-width:25.8903%;--hb-height:5.5228%"><span>4 Tornillos de Cabeza Plana Phillips</span></span><span class="hb-reference-live-label" data-source-line="44" style="--hb-x:30.8742%;--hb-y:86.2778%;--hb-width:14.5287%;--hb-height:5.5228%"><span>2 Soporte de Pared</span></span><span class="hb-reference-live-label" data-source-line="45" style="--hb-x:10.4642%;--hb-y:86.2795%;--hb-width:14.611%;--hb-height:5.5228%"><span>etiqueta de circuito</span></span><span class="hb-reference-live-label" data-source-line="46" style="--hb-x:50.0686%;--hb-y:86.5502%;--hb-width:23.5972%;--hb-height:5.5228%"><span>M4 (fije los soportes de pared al</span></span><span class="hb-reference-live-label" data-source-line="47" style="--hb-x:53.6256%;--hb-y:90.9685%;--hb-width:16.483%;--hb-height:5.5228%"><span>Smart Transfer Switch)</span></span></div></div></figure></div>

<span id="native-contact"></span>

## CONTÁCTENOS

### JACKERY INC.

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>hello@jackery.com 1-888-502-2236 (US) www.jackery.com</p>
