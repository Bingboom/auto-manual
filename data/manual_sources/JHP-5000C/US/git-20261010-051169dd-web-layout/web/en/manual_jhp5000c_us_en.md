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

/* ===== Web-layout edition (git-20261010-051169dd-web-layout): print structure ===== */
/* Each rule styles markup that derive_web_layout.py records in source/<lang>/web_layout.json. */

/* Overview label columns at the frame's right edge are right-aligned in print. */
#furo-main-content .native-figure .hb-reference-live-label:has(> .native-edge-right) { justify-content: flex-end; text-align: right; }
#furo-main-content .native-figure .hb-reference-live-label > span.native-edge-right { width: max-content; }
/* The Web face sets wider and taller than the print face at the same size; overview
   labels draw at 95% so stacked lines keep the print's clear leading at every width. */
#furo-main-content :is(.native-overview-front, .native-overview-left, .native-overview-right) .hb-reference-live-label {
  transform: scale(0.95);
  transform-origin: left top;
}
#furo-main-content .native-figure .hb-reference-live-label:has(> .native-edge-right) { transform-origin: right top; }

/* Safety sub-sections print as dark pills inside the safety chapter (p4-p5). */
#furo-main-content h2:has(> .native-band) {
  max-width: var(--hb-component-band-max);
  padding: 0.36rem 0.95rem;
  border-radius: 999px;
  background: var(--hb-brand-dark);
  color: var(--hb-paper);
  font-size: clamp(0.92rem, 1.5vw, 1.02rem);
}
#furo-main-content h2:has(> .native-band)::before { display: none; }
#furo-main-content h2:has(> .native-band) .headerlink { color: rgba(255, 255, 255, 0.7); }

/* DANGER: outlined white panel with the print's dark triangle; its body prints bold. */
#furo-main-content table.hb-source-warning-lockup { border-color: var(--hb-brand-dark) !important; background: var(--hb-paper); }
#furo-main-content .hb-source-warning-lockup .manual-callout-label { width: 30% !important; }
#furo-main-content .hb-source-warning-lockup .manual-callout-body {
  background: var(--hb-paper) !important;
  vertical-align: middle !important;
}
#furo-main-content .hb-source-warning-lockup .hb-warning-lockup {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font-size: 1.2rem;
}
#furo-main-content .hb-source-warning-lockup .hb-warning-lockup img {
  flex: 0 0 auto;
  width: 2.5rem !important;
  height: auto;
  margin: 0 !important;
}
@media (max-width: 40rem) {
  #furo-main-content .hb-source-warning-lockup :is(.manual-callout-label, .manual-callout-body) { width: 100% !important; }
}

/* Product sections inside the AC ESS guide print as mixed-case bands with the model at the right. */
#furo-main-content :is(h1, h2):has(> .hb-heading-model) {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.35rem 0.8rem;
}
#furo-main-content h2:has(> .hb-heading-model) {
  max-width: var(--hb-component-band-max);
  margin: 1.6rem 0 1rem;
  padding: 0.55rem 1rem;
  border-radius: var(--hb-h1-radius);
  background: var(--hb-brand-dark);
  color: var(--hb-paper);
  font-size: clamp(1.08rem, 2vw, 1.28rem);
  text-transform: none;
}
#furo-main-content h2:has(> .hb-heading-model)::before { display: none; }
#furo-main-content :is(h1, h2):has(> .hb-heading-model) > .headerlink {
  position: absolute;
  right: 0.25rem;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.7);
}
#furo-main-content .hb-heading-title { flex: 0 1 auto; }
#furo-main-content .hb-heading-model {
  margin-left: auto;
  padding-right: 1rem;
  font-size: 0.66em;
  line-height: 1.2;
  text-align: right;
  text-transform: none;
  white-space: nowrap;
}
#furo-main-content h1 .hb-heading-model { font-weight: 400; }
#furo-main-content h1 .hb-heading-model strong { font-weight: 700; }

/* 'SPECIFICATIONS' under a product band is a plain bold title in print. */
#furo-main-content h3:has(> .native-plain-title) { margin-top: 0.4rem; font-size: 1.1rem; }
#furo-main-content h3:has(> .native-plain-title)::before { display: none; }

/* Accessory availability is a dark capsule beside its title (p14, p26). */
#furo-main-content :is(h1, h2, h3):has(> .hb-sold-separately) { flex-wrap: wrap; }
#furo-main-content .hb-sold-separately {
  display: inline-block;
  flex: none;
  padding: 0.32em 0.8em;
  border-radius: 999px;
  background: var(--hb-brand-dark);
  color: var(--hb-paper);
  font-size: 0.78em;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}
#furo-main-content h4.hb-heading-label-pair {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
  margin: 0.5rem 0 0.8rem;
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1.2;
}
#furo-main-content .hb-heading-label-pair > .hb-heading-title { background: transparent; padding: 0; }
/* Navigation keeps the title only; the capsule and model label are in-page marks. */
:is(.toc-tree, .sidebar-tree) :is(.hb-heading-model, .hb-sold-separately) { display: none; }

/* 'Fully charge … before its first use.' prints white on a dark capsule. */
#furo-main-content p.hb-prose-pill {
  display: table;
  max-width: 100%;
  box-sizing: border-box;
  margin: 0.75rem 0;
  padding: 0.22em 0.7em;
  border-radius: 999px;
  background: var(--hb-brand-dark);
  color: var(--hb-paper);
  font-weight: 700;
  line-height: 1.35;
}
#furo-main-content p.hb-prose-pill strong { color: inherit; }

/* LCD SCREEN: device art beside its state table (p11). */
#furo-main-content .native-lcd-panel .hb-lcd-mode-composition { grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.4fr); }
#furo-main-content .native-lcd-panel .hb-lcd-mode-art { width: min(100%, 16rem) !important; }
@media (max-width: 40rem) {
  #furo-main-content .native-lcd-panel .hb-lcd-mode-composition { grid-template-columns: minmax(0, 1fr); }
}

/* LCD glossary: circled entry numbers; notes small and regular; one state per line. */
#furo-main-content td.hb-lcd-number { text-align: center; vertical-align: middle !important; }
#furo-main-content .native-lcd-number {
  display: inline-grid;
  place-items: center;
  min-width: 1.5em;
  height: 1.5em;
  padding: 0 0.12em;
  box-sizing: border-box;
  border: 1px solid currentColor;
  border-radius: 999px;
  font-size: 0.86em;
  line-height: 1;
}
#furo-main-content .native-lcd-note { color: var(--hb-text-muted); font-size: 0.82em; font-weight: 400; }

/* Key combinations: the print's '+' between the two buttons, inside the reading width. */
#furo-main-content .hb-key-button-pair {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: start;
  gap: 0.3rem;
  text-align: center;
}
#furo-main-content .hb-key-button { display: grid; justify-items: center; gap: 0.3rem; }
#furo-main-content .hb-key-button img { width: 3.4rem !important; height: auto !important; margin: 0 !important; }
#furo-main-content .hb-key-button p { margin: 0; font-size: 0.86rem; line-height: 1.2; }
#furo-main-content .hb-key-button-plus { display: grid; height: 3.4rem; align-items: center; }
#furo-main-content .hb-key-button-plus::before { content: "+"; font-size: 1.9rem; font-weight: 800; line-height: 1; }
#furo-main-content table.hb-key-combination-table:has(.hb-key-button-pair) { min-width: 36rem; }
#furo-main-content table.hb-key-combination-table:has(.hb-key-button-pair) td { padding: 0.6rem 0.55rem !important; }
#furo-main-content .hb-key-col-buttons { width: 46%; }
#furo-main-content .hb-key-col-operation { width: 26%; }
#furo-main-content .hb-key-col-function { width: 28%; }

/* Troubleshooting: bold codes centred, bold names, one cause per line (p12). */
#furo-main-content table.native-troubleshooting tbody td:first-child { text-align: center; font-size: 1.05em; }
#furo-main-content table.native-troubleshooting tbody td { vertical-align: middle; }

/* Specification group labels with no value (e.g. 'DC Input') print as grey rows. */
#furo-main-content table.hb-spec-table tr:has(> td.hb-spec-value:empty) > * { background: var(--hb-surface) !important; }

/* Hazard and trademark notes under the specification tables. */
#furo-main-content p.native-ingestion img {
  display: inline-block;
  width: 1.55rem !important;
  height: auto;
  margin: 0 0.45rem 0 0 !important;
  vertical-align: middle;
}
#furo-main-content p.native-trademark { color: var(--hb-text-muted); font-size: 0.88rem; }

/* Back cover (p76): company, address, one contact panel. */
#furo-main-content .native-contact-card { margin: 2.2rem 0 1rem; }
#furo-main-content p.native-contact-company { margin: 0; font-size: 1.25rem; }
#furo-main-content p.native-contact-address { margin: 0.15rem 0 0.75rem; }
#furo-main-content .native-contact-row { display: flex; flex-wrap: wrap; align-items: stretch; gap: 0.6rem; }
#furo-main-content .native-contact-panel {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.6rem 1.4rem;
  padding: 0.75rem 1.2rem;
  border: 1px solid var(--hb-line-soft);
  border-radius: 0.9rem;
}
#furo-main-content .native-contact-qr {
  display: grid;
  place-items: center;
  padding: 0.35rem;
  border: 1px solid var(--hb-line-soft);
  border-radius: 0.6rem;
}
#furo-main-content .native-contact-qr img { width: 3.6rem !important; height: auto !important; margin: 0 !important; }
#furo-main-content p.native-contact-phone { margin: 0; font-size: 1.55rem; line-height: 1.1; }
#furo-main-content .native-contact-region { font-size: 0.55em; font-weight: 400; }
#furo-main-content .native-contact-links { padding-left: 1.2rem; border-left: 1px solid var(--hb-line-soft); }
#furo-main-content .native-contact-links p { margin: 0; line-height: 1.5; }
#furo-main-content img.native-contact-glyph { display: inline-block; width: auto !important; height: 1.05em !important; margin: 0 0.45em 0 0 !important; vertical-align: -0.12em; }
#furo-main-content p.native-contact-phone img.native-contact-glyph { height: 1.15em !important; vertical-align: -0.2em; margin-right: 0.3em !important; }

</style>

<h1 class="hb-preface-heading" id="native-preface"><span class="hb-preface-region">US</span> IMPORTANT</h1>

<div class="hb-preface-prose"><p>Congratulations on your new Jackery HomePower 5000 Plus. Please read this manual carefully before using the product, particularly the relevant precautions to ensure proper use. Keep this manual in an accessible place for frequent reference.</p><p>In compliance with laws and regulations, the right of final interpretation of this document and all related documents of this product resides with the Company.</p><p>Please kindly notice that no further notifications will be given in case of any update, revision or termination.</p></div>

<span id="native-safety"></span>

## IMPORTANT SAFETY INFORMATION

<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="hb-symbol-signal-table"><colgroup><col style="width:7%"/><col style="width:93%"/></colgroup><tbody><tr><td><img alt="" src="assets/warning_triangle_dark.svg" style="width:30px;height:auto" width="30"/></td><td><p><strong>INSTRUCTIONS PERTAINING TO RISK OF FIRE, ELECTRIC SHOCK, OR INJURY TO PERSONS</strong></p></td></tr></tbody></table></figure>

<table class="manual-two-col-table" style="width:100%; border-collapse:separate; border-spacing:12px 0; margin:0 0 16px 0;"><colgroup><col style="width: 50%"/><col style="width: 50%"/></colgroup><tbody><tr><td style="width: 50%; border: none; padding: 0 8px 0 0; vertical-align: top"><figure class="hb-symbol-signal-composition hb-safety-lead"><table class="hb-symbol-signal-table"><colgroup><col style="width:20%"/><col style="width:80%"/></colgroup><tbody><tr><td class="hb-symbol-signal-label-cell"><span class="hb-signal-badge"><img alt="" src="assets/warning_triangle_white.svg" style="width:48px;height:auto" width="48"/></span></td><td class="hb-symbol-signal-meaning-cell"><p><strong>WARNING</strong></p><p><strong>Always follow these basic precautions when using this product.</strong></p></td></tr></tbody></table></figure><ul><li>Read all the instructions before using the product.</li><li>Do not allow children to play on the product. Close supervision of children is necessary when the product is used near children.</li><li>Avoid placing hands or fingers inside the product.</li><li>Stop using the product immediately if it has been physically damaged or modified. Improper use of the product may cause unpredictable behavior, leading to fire, explosion, or injury.</li><li>If any of the following are observed, including but not limited to overheats, emits unusual odors or smoking, leaks, or burns, stop using the product immediately and contact the dealer or our Customer Support.</li><li>Never attempt to open, repair, or modify the product. Any tampering, reassembly, or modification of the product can result in electric shock, fire, or battery damage.</li></ul></td><td style="width: 50%; border: none; padding: 0 0 0 8px; vertical-align: top"><ul><li>Be aware that liquid ejected from the product may cause irritation or burns. Inappropriate or abusive use may lead to battery leakage. Avoid direct contact with leaking liquid. If the liquid contacts your eyes, seek medical help immediately. If it contacts other body parts, flush with running water and consult a medical professional without delay.</li><li>Do not expose the product to fire or excessive temperatures. Doing so may result in an explosion if the temperature exceeds 130°C (265°F).</li><li>Any use of unrecommended or non-supplied materials or parts with the product may result in a risk of fire, electric shock, or personal injury.</li><li>Do not leave the battery charging unattended for long periods. Always monitor the charging process to ensure safe operation.</li><li>To reduce the risk of electric shock, unplug the product from any power source before attempting any technical service or troubleshooting.</li></ul></td></tr></tbody></table>

### <span class="native-band">OPERATING INSTRUCTIONS</span>

<table class="manual-two-col-table" style="width:100%; border-collapse:separate; border-spacing:12px 0; margin:0 0 16px 0;"><colgroup><col style="width: 50%"/><col style="width: 50%"/></colgroup><tbody><tr><td style="width: 50%; border: none; padding: 0 8px 0 0; vertical-align: top"><p><strong>SAVE THESE INSTRUCTIONS</strong></p><ul><li>Stop using the product immediately if it shows signs of damage. Discontinue use and contact customer support for assistance.</li><li>Do not charge the battery in extremely hot or cold environments and strictly adhere to the product's specified operating temperature ranges：<ul><li>Charging temperature: 32°F to 113°F (0°C to 45°C);</li><li>Discharging temperature: 5°F to 113°F (-15°C to 45°C);</li></ul></li><li>To ensure proper air circulation, keep the product vents uncovered. The area where the product is used must have adequate airflow in a cool, dry environment to prevent overheating.<ul><li>Charging in damp or poorly ventilated spaces may cause safety hazards.</li><li>Water can cause short circuits or damage to the charger, leading to safety risks.</li></ul></li><li>Unplug the power cord from a power outlet during a storm.</li><li>Immediately turn off the product by pressing the power button if it has fallen, been dropped, or exposed to vibrations.</li></ul></td><td style="width: 50%; border: none; padding: 0 0 0 8px; vertical-align: top"><ul><li>Ensure the device(s) are powered off before connecting it to the product.</li><li>Do not charge the product using a damaged or broken charging cord or plug.</li><li>Do not use the product to charge any device with a damaged or broken cable or plug.</li><li>Always unplug the charging cord by pulling the plug, not the cord, to reduce the risk of damage.</li><li>Ensure the product is properly secured when transporting it in a moving vehicle.</li><li>DO NOT place the unit upside down or on its side during use or storage.</li><li>DO NOT place the product on the floor or at a height less than 18 inches (457 mm) above the floor during operation in a workshop or repair facility.</li><li>DO NOT use the product's accessories with other devices or equipment.</li><li>Solar charge time depends on weather conditions, place your solar panel where it will get as much direct sunlight as possible.</li></ul></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-outlined"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/warning_triangle_dark.svg"/>DANGER</span></td><td class="manual-callout-body"><p><strong>This device is intended for indoor use only (Please place this device in a similar indoor environment when using it outdoors，e.g. Home RVs, tents, cabins, etc.).</strong><br/><strong>※ This device is not waterproof or dustproof. Keep away from rain and humid environments during use.</strong></p></td></tr></tbody></table>

<span id="native-maintenance"></span>

### <span class="native-band">USER MAINTENANCE INSTRUCTIONS</span>

<p>During the lifecycle of energy storage products, a certain degree of capacity and energy degradation is expected. As the number of charge and discharge cycles increases and storage time extends, this degradation will gradually intensify, which is a normal phenomenon consistent with the natural aging of battery cells.</p>

<span id="native-symbols"></span>

### <span class="native-band">MEANING OF SYMBOLS</span>

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbol</th><th class="hb-symbol-signal-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="WARNING" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">WARNING</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in severe injury, death, and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CAUTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CAUTION</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in personal injury and/or property damage.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="Note" class="hb-signal-badge"><span class="hb-signal-label">Note</span></span></td><td class="hb-symbol-signal-meaning-cell">Hazardous practices that may result in equipment damage, data loss, performance deterioration, or unanticipated results.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Warning and Caution Symbols. Must read to alert individuals to potential hazards or risks.</td></tr><tr><td class="hb-symbol-icon"><img alt="Electric Shock Hazard Symbol for electrical danger warning." class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Electric Shock Hazard Symbol for electrical danger warning.</td></tr><tr><td class="hb-symbol-icon"><img alt="Battery Charging Symbol indicates a battery is being charged." class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Battery Charging Symbol indicates a battery is being charged.</td></tr><tr><td class="hb-symbol-icon"><img alt="Explosive Material Symbol for explosion risk warning." class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Explosive Material Symbol for explosion risk warning.</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbol</th><th class="hb-symbol-meaning-heading" scope="col">Meaning</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Heavy Object Symbol for handling precautions." class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Heavy Object Symbol for handling precautions.</td></tr><tr><td class="hb-symbol-icon"><img alt="Non-smoking or Open Flame Symbol for fire hazards prevention." class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Non-smoking or Open Flame Symbol for fire hazards prevention.</td></tr><tr><td class="hb-symbol-icon"><img alt="No Children Allowed Symbol for safety risk prevention." class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">No Children Allowed Symbol for safety risk prevention.</td></tr><tr><td class="hb-symbol-icon"><img alt="Read the Manual Symbol for safe operation." class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Read the Manual Symbol for safe operation.</td></tr></tbody></table></div></div></figure>

<div class="native-fcc-panel" id="native-fcc"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"></div></div></div><p><strong>NOTE:</strong> This equipment has been tested and found to comply with the limits for a Class B digital device, pursuant to part 15 of the FCC Rules. These limits are designed to provide reasonable protection against harmful interference in a residential installation. This equipment generates, uses and can radiate radio frequency energy and, if not installed and used in accordance with the instructions, may cause harmful interference to radio communications. However, there is no guarantee that interference will not occur in a particular installation. If this equipment does cause harmful interference to radio or television reception, which can be determined by turning the equipment off and on, the user is encouraged to try to correct the interference by one or more of the following measures:</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Reorient or relocate the receiving antenna.</p></li><li><p>Increase the separation between the equipment and receiver.</p></li><li><p>Connect the equipment into an outlet on a circuit different from that to which the receiver is connected.</p></li><li><p>Consult the dealer or an experienced radio/TV technician for help.</p></li></ul><p><strong>MODIFICATION:</strong> Any changes or modifications not expressly approved by the grantee of this device could void the user’s authority to operate the device.</p></div></div></figure></div>

<span id="native-inbox"></span>

## WHAT'S IN THE BOX

<figure aria-label="WHAT'S IN THE BOX" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 5000 Plus" class="hb-inbox-art" src="assets/inbox-main.svg"/><div class="hb-inbox-label"><p>Jackery HomePower 5000 Plus</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="AC Charging Cable" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label"><p>AC Charging Cable</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="MC4 Wrench" class="hb-inbox-art" src="assets/inbox-mc4.svg"/><div class="hb-inbox-label"><p>MC4 Wrench</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="User Manual" class="hb-inbox-art" src="assets/inbox-manual.svg"/><div class="hb-inbox-label"><p>User Manual</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">Note</div><div class="hb-inbox-tip-body">The car charging cable is not included but is available for purchase separately on our website. For assistance, please contact Jackery customer service.</div></div></figure>

<span id="native-overview"></span>

## PRODUCT OVERVIEW

### FRONT VIEW

<div class="native-figure native-overview-front native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="d39181be977bd945fcc1e107c80b8baa9bb3c3fae126a2d49193a67007a8dfe1" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-front.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.5137%;--hb-y:1.9245%;--hb-width:4.447%;--hb-height:4.4393%"><span><strong>LCD</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.8146%;--hb-y:2.4533%;--hb-width:19.4539%;--hb-height:4.4393%"><span class="native-edge-right"><strong>Main</strong> <strong>Power</strong> <strong>Button</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.2377%;--hb-y:13.2284%;--hb-width:15.0309%;--hb-height:4.4393%"><span class="native-edge-right"><strong>USB-C</strong> <strong>Output</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.5137%;--hb-y:15.9153%;--hb-width:17.63%;--hb-height:4.4393%"><span><strong>DC</strong> <strong>Power</strong> <strong>Button</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:91.357%;--hb-y:17.148%;--hb-width:7.8486%;--hb-height:3.2751%"><span class="native-edge-right">100W Max</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:84.4342%;--hb-y:30.6979%;--hb-width:14.8344%;--hb-height:4.4393%"><span class="native-edge-right"><strong>USB-A</strong> <strong>Output</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.5137%;--hb-y:32.7123%;--hb-width:10.0954%;--hb-height:4.4393%"><span><strong>Cigarette</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:92.4643%;--hb-y:34.3467%;--hb-width:6.7413%;--hb-height:3.2751%"><span class="native-edge-right">18W Max</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5137%;--hb-y:36.2062%;--hb-width:12.2133%;--hb-height:4.4393%"><span><strong>Lighter</strong> <strong>Port</strong></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.5137%;--hb-y:40.8086%;--hb-width:6.4352%;--hb-height:4.4738%"><span>12V⎓10A</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:80.7619%;--hb-y:40.7363%;--hb-width:18.5064%;--hb-height:4.4393%"><span class="native-edge-right"><strong>USB</strong> <strong>Power</strong> <strong>Button</strong></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:87.9872%;--hb-y:45.6088%;--hb-width:11.2814%;--hb-height:4.4393%"><span class="native-edge-right"><strong>AC</strong> <strong>Output</strong></span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:88.2166%;--hb-y:49.1871%;--hb-width:11.0492%;--hb-height:3.8332%"><span class="native-edge-right">(NEMA 5-20)</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:88.7124%;--hb-y:52.7169%;--hb-width:10.5536%;--hb-height:3.2751%"><span class="native-edge-right">1 x AC Output:</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:86.2329%;--hb-y:55.4243%;--hb-width:13.0331%;--hb-height:3.2751%"><span class="native-edge-right">120V, 20A, 2400W</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:86.9254%;--hb-y:58.1317%;--hb-width:12.3405%;--hb-height:3.2751%"><span class="native-edge-right">AC Total Output:</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:0.5137%;--hb-y:59.9817%;--hb-width:17.4754%;--hb-height:4.4393%"><span><strong>AC</strong> <strong>Power</strong> <strong>Button</strong></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:79.1572%;--hb-y:60.8392%;--hb-width:20.1087%;--hb-height:3.2751%"><span class="native-edge-right">7200W Max, 14400W Surge</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:87.3035%;--hb-y:79.1616%;--hb-width:11.4145%;--hb-height:3.8987%"><span class="native-edge-right"><strong>Total</strong> <strong>Output</strong></span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:0.7229%;--hb-y:79.9331%;--hb-width:11.4145%;--hb-height:3.8987%"><span><strong>Total</strong> <strong>Output</strong></span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:81.4641%;--hb-y:82.3276%;--hb-width:16.8595%;--hb-height:3.2751%"><span class="native-edge-right">120V, 30A, 3600W Max,</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:0.7229%;--hb-y:83.0991%;--hb-width:16.8595%;--hb-height:3.2751%"><span>120V, 30A, 3600W Max,</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:88.7606%;--hb-y:85.0351%;--hb-width:9.9574%;--hb-height:3.2751%"><span class="native-edge-right">7200W Surge</span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:0.7229%;--hb-y:85.8065%;--hb-width:9.9576%;--hb-height:3.2751%"><span>7200W Surge</span></span></div></div></figure></div>

### LEFT SIDE VIEW

<div class="native-figure native-overview-left native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="dce68b6ecf11e37fd8325013aa125d36cef2fd3afa93dd21a0bc318d79e62147" data-web-base-art-ref="overview-left" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-left.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-left.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.6078%;--hb-y:0.8242%;--hb-width:7.6511%;--hb-height:4.7505%"><span><strong>Handle</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.6078%;--hb-y:8.1798%;--hb-width:19.1667%;--hb-height:4.7505%"><span><strong>AC</strong> <strong>Expansion</strong> <strong>Port</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.6081%;--hb-y:12.375%;--hb-width:29.335%;--hb-height:3.4009%"><span>Connect to Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.6078%;--hb-y:15.6166%;--hb-width:23.4484%;--hb-height:3.6729%"><span>Input: 240V, 16.7A Max, 4000W</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.6078%;--hb-y:18.5143%;--hb-width:20.3772%;--hb-height:3.6729%"><span>Output: 240V, 30A, 7200W</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.5372%;--hb-y:24.6266%;--hb-width:31.1905%;--hb-height:4.7505%"><span><strong>NEMA</strong> <strong>L14-30R</strong> <strong>AC</strong> <strong>Output</strong> <strong>Port</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.538%;--hb-y:28.3815%;--hb-width:25.1312%;--hb-height:4.1019%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.5376%;--hb-y:32.3513%;--hb-width:51.6751%;--hb-height:3.6729%"><span>Powers high-power devices and connects to an inlet box or manual</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5376%;--hb-y:35.2489%;--hb-width:32.1073%;--hb-height:3.6729%"><span>transfer switch for home electricity supply.</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.5372%;--hb-y:43.4448%;--hb-width:28.9161%;--hb-height:4.7505%"><span><strong>NEMA</strong> <strong>14-50</strong> <strong>AC</strong> <strong>Output</strong> <strong>Port</strong></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.538%;--hb-y:47.632%;--hb-width:25.1312%;--hb-height:4.1019%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.5376%;--hb-y:51.5972%;--hb-width:51.6753%;--hb-height:3.6729%"><span>Powers high-power devices and connects to an inlet box or manual</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.5376%;--hb-y:54.4948%;--hb-width:32.1071%;--hb-height:3.6729%"><span>transfer switch for home electricity supply.</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.6078%;--hb-y:63.1831%;--hb-width:24.8351%;--hb-height:4.7505%"><span><strong>AC</strong> <strong>Output</strong> <strong>Reset</strong> <strong>Button</strong></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.6079%;--hb-y:67.5704%;--hb-width:41.0838%;--hb-height:3.5047%"><span>When the Reset Button pops up, you need to remove the</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:0.6079%;--hb-y:70.4676%;--hb-width:29.5407%;--hb-height:3.5047%"><span>load and press the Reset Button to reset.</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:0.6078%;--hb-y:76.8168%;--hb-width:13.231%;--hb-height:4.7505%"><span><strong>Wheel</strong> <strong>Brake</strong></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:0.6078%;--hb-y:85.3901%;--hb-width:7.8719%;--hb-height:4.7505%"><span><strong>Wheels</strong></span></span></div></div></figure></div>

### RIGHT SIDE VIEW

<div class="native-figure native-overview-right native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-right" data-source-fragment-sha256="9c80bcc99b500d5fb3d00f80a5ba7dd87ab62aec0f71704a6f01252628a698b0" data-web-base-art-ref="overview-right" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-right.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-right.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.4689%;--hb-y:14.119%;--hb-width:20.2973%;--hb-height:3.8218%"><span><strong>Retractable</strong> <strong>Handle</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.4689%;--hb-y:17.5926%;--hb-width:46.9951%;--hb-height:2.8195%"><span>Press the button on the retractable handle and pull up to extend.</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4689%;--hb-y:22.42%;--hb-width:21.086%;--hb-height:3.8218%"><span><strong>Low-PV</strong> <strong>Input</strong> <strong>(8020)</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4691%;--hb-y:26.2465%;--hb-width:47.8454%;--hb-height:3.8515%"><span>2 x DC 8mm Ports; 16V-60V⎓10.5A Max, Double to 21A/1200W Max</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4691%;--hb-y:28.5773%;--hb-width:38.4051%;--hb-height:3.8515%"><span>11V-16V(Working Voltage)⎓8A Max, Double to 8A Max</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.4689%;--hb-y:35.4542%;--hb-width:21.3243%;--hb-height:3.8218%"><span><strong>High-PV</strong> <strong>Input</strong> <strong>(MC4)</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.4691%;--hb-y:39.4645%;--hb-width:24.7475%;--hb-height:3.8515%"><span>135V-450V⎓15A Max, 4000W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.4689%;--hb-y:44.1542%;--hb-width:16.0977%;--hb-height:3.8218%"><span><strong>High-PV</strong> <strong>Switch</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4691%;--hb-y:47.863%;--hb-width:33.5678%;--hb-height:2.8195%"><span>Turns on/off the switch to enable/disable high</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.4691%;--hb-y:50.1938%;--hb-width:16.5145%;--hb-height:2.8195%"><span>voltage solar charging</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.4689%;--hb-y:55.1489%;--hb-width:9.2631%;--hb-height:3.8218%"><span><strong>AC</strong> <strong>Input</strong></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.4691%;--hb-y:58.9608%;--hb-width:10.0615%;--hb-height:2.8195%"><span>120V, 15A Max</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.4689%;--hb-y:67.87%;--hb-width:30.5897%;--hb-height:3.8218%"><span><strong>DC</strong> <strong>Expansion</strong> <strong>Port</strong> <strong>Terminal</strong> <strong>A</strong></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.4691%;--hb-y:71.566%;--hb-width:18.0913%;--hb-height:2.8195%"><span>Connect to Battery Pack</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.5152%;--hb-y:81.6726%;--hb-width:15.6271%;--hb-height:3.8218%"><span><strong>Bottom</strong> <strong>Handle</strong></span></span></div></div></figure></div>

<span id="native-lcd"></span>

## LCD DISPLAY

<div class="native-figure native-lcd-map native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="0b53ab70e9b932a0f805f70e0723e3ddea254a435406b8f79754836e488857d9" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:19.6073%;--hb-y:3.5691%;--hb-width:1.4712%;--hb-height:5.4368%"><span>2</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:23.7861%;--hb-y:3.5691%;--hb-width:1.4822%;--hb-height:5.4368%"><span>3</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:27.5267%;--hb-y:3.5691%;--hb-width:1.5922%;--hb-height:5.4368%"><span>4</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:31.5714%;--hb-y:3.5691%;--hb-width:1.5042%;--hb-height:5.4368%"><span>5</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:35.5314%;--hb-y:3.5691%;--hb-width:1.4822%;--hb-height:5.4368%"><span>6</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:59.5039%;--hb-y:3.5691%;--hb-width:1.3942%;--hb-height:5.4368%"><span>7</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:15.6115%;--hb-y:3.5717%;--hb-width:1.0643%;--hb-height:5.4368%"><span>1</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:1.0001%;--hb-y:45.5627%;--hb-width:1.5218%;--hb-height:5.4368%"><span>8</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:96.2797%;--hb-y:45.8982%;--hb-width:2.648%;--hb-height:5.4368%"><span>22</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:96.2358%;--hb-y:57.064%;--hb-width:2.637%;--hb-height:5.4368%"><span>23</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.9099%;--hb-y:57.6012%;--hb-width:1.4822%;--hb-height:5.4368%"><span>9</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:15.2495%;--hb-y:92.2644%;--hb-width:2.516%;--hb-height:5.4368%"><span>10</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:19.9667%;--hb-y:92.2644%;--hb-width:1.8781%;--hb-height:5.4368%"><span>11</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:25.1465%;--hb-y:92.2644%;--hb-width:2.285%;--hb-height:5.4368%"><span>12</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:31.6944%;--hb-y:92.2644%;--hb-width:2.296%;--hb-height:5.4368%"><span>13</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:37.1421%;--hb-y:92.2644%;--hb-width:2.406%;--hb-height:5.4368%"><span>14</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:43.0068%;--hb-y:92.2644%;--hb-width:2.318%;--hb-height:5.4368%"><span>15</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:48.0861%;--hb-y:92.2644%;--hb-width:2.296%;--hb-height:5.4368%"><span>16</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:52.5054%;--hb-y:92.2644%;--hb-width:2.208%;--hb-height:5.4368%"><span>17</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:60.647%;--hb-y:92.2644%;--hb-width:2.3356%;--hb-height:5.4368%"><span>18</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:70.9378%;--hb-y:92.2644%;--hb-width:2.252%;--hb-height:5.4368%"><span>19</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:75.3072%;--hb-y:92.2644%;--hb-width:2.8569%;--hb-height:5.4368%"><span>20</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:80.8328%;--hb-y:92.2644%;--hb-width:2.241%;--hb-height:5.4368%"><span>21</span></span></div></div></figure></div>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><span class="native-lcd-number">1</span></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-native-01.svg"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description"><strong>On</strong>: Wi-Fi connected.<br/><strong>Blink</strong>: Ready to connect to Wi-Fi.<br/><strong>Off</strong>: Wi-Fi disconnected.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">2</span></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-native-02.svg"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description"><strong>On</strong>: Bluetooth connected.<br/><strong>Blink</strong>: Ready to connect to Bluetooth.<br/><strong>Off</strong>: Bluetooth disconnected.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">3</span></td><td class="hb-lcd-icon"><img alt="Quiet Charging Mode can be enabled / disabled in the Jackery APP" class="hb-lcd-icon-art" src="assets/lcd-native-03.svg"/></td><td class="hb-lcd-name">Quiet Charging Mode<br/><span class="native-lcd-note">can be enabled / disabled in the Jackery APP</span></td><td class="hb-lcd-description"><strong>On</strong>: The noise during charging is significantly minimized, while the charging power is reduced and the charging speed slows down.<br/><strong>Off</strong>: Quiet Charging Mode is disabled.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">4</span></td><td class="hb-lcd-icon"><img alt="Battery Saving Mode can be enabled / disabled in the Jackery APP" class="hb-lcd-icon-art" src="assets/lcd-native-04.svg"/></td><td class="hb-lcd-name">Battery Saving Mode<br/><span class="native-lcd-note">can be enabled / disabled in the Jackery APP</span></td><td class="hb-lcd-description"><strong>On</strong>: Limits the maximum usable battery capacity to extend battery life.<br/><strong>Off</strong>: Battery Saving Mode is disabled.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">5</span></td><td class="hb-lcd-icon"><img alt="Charging/Discharging Plan Indicator can be set in the Jackery APP on STS" class="hb-lcd-icon-art" src="assets/lcd-native-05.svg"/></td><td class="hb-lcd-name">Charging/Discharging Plan Indicator<br/><span class="native-lcd-note">can be set in the Jackery APP on STS</span></td><td class="hb-lcd-description">Indicates that the product is operating under the Smart Transfer Switch (STS) Charging/Discharging Plan. This occurs only when the product is successfully connected to the STS and the Charging/Discharging Plan is set in the STS App.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">6</span></td><td class="hb-lcd-icon"><img alt="Online UPS can be set in the Jackery APP" class="hb-lcd-icon-art" src="assets/lcd-native-06.svg"/></td><td class="hb-lcd-name">Online UPS<br/><span class="native-lcd-note">can be set in the Jackery APP</span></td><td class="hb-lcd-description"><strong>On</strong>: The product is on online UPS mode (0 ms).<br/><strong>Off</strong>: Backup UPS mode (Default).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">7</span></td><td class="hb-lcd-icon"><img alt="AC Power Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-07.svg"/></td><td class="hb-lcd-name">AC Power Indicator</td><td class="hb-lcd-description">The AC output (pure sine wave) is on.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">8</span></td><td class="hb-lcd-icon"><img alt="Input Power" class="hb-lcd-icon-art" src="assets/lcd-native-08.svg"/></td><td class="hb-lcd-name">Input Power</td><td class="hb-lcd-description">Displays the input power in watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">9</span></td><td class="hb-lcd-icon"><img alt="Remaining Charge Time" class="hb-lcd-icon-art" src="assets/lcd-native-09.svg"/></td><td class="hb-lcd-name">Remaining Charge Time</td><td class="hb-lcd-description">Displays the remaining charging time.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">10</span></td><td class="hb-lcd-icon"><img alt="AC Wall Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-10.svg"/></td><td class="hb-lcd-name">AC Wall Charging Indicator</td><td class="hb-lcd-description">The product is charged via the AC input using grid power.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">11</span></td><td class="hb-lcd-icon"><img alt="Car Charging Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-11.svg"/></td><td class="hb-lcd-name">Car Charging Indicator</td><td class="hb-lcd-description">The product is charged via the Low-PV Input (8020) using DC 12V (car charging).</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">12</span></td><td class="hb-lcd-icon"><img alt="High-PV Input Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-12.svg"/></td><td class="hb-lcd-name">High-PV Input Indicator</td><td class="hb-lcd-description">The product is charged via the High-PV Input (MC4) using solar panel(s).</td></tr><tr><td class="hb-lcd-icon"><img alt="Low-PV Input Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-13.svg"/></td><td class="hb-lcd-name">Low-PV Input Indicator</td><td class="hb-lcd-description">The product is charged via the Low-PV Input (8020) using solar panel(s).</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">13</span></td><td class="hb-lcd-icon"><img alt="AC Expansion Indicator (Charging) Ensure the STS is successfully connected before proceeding." class="hb-lcd-icon-art" src="assets/lcd-native-14.svg"/></td><td class="hb-lcd-name">AC Expansion Indicator (Charging)<br/><span class="native-lcd-note">Ensure the STS is successfully connected before proceeding.</span></td><td class="hb-lcd-description">The product is charged via the Smart Transfer Switch (STS) using grid power.</td></tr><tr><td class="hb-lcd-icon"><img alt="AC Expansion Indicator (Discharging) Ensure the STS is successfully connected before proceeding." class="hb-lcd-icon-art" src="assets/lcd-native-15.svg"/></td><td class="hb-lcd-name">AC Expansion Indicator (Discharging)<br/><span class="native-lcd-note">Ensure the STS is successfully connected before proceeding.</span></td><td class="hb-lcd-description">The product is powering your home loads via the Smart Transfer Switch (STS).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">14</span></td><td class="hb-lcd-icon"><img alt="Smart Transfer Switch Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-16.svg"/></td><td class="hb-lcd-name">Smart Transfer Switch Indicator</td><td class="hb-lcd-description">The product is successfully connected to the Smart Transfer Switch.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">15</span></td><td class="hb-lcd-icon"><img alt="Battery Power Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-17.svg"/></td><td class="hb-lcd-name">Battery Power Indicator</td><td class="hb-lcd-description">When the product is being charged, the orange circle around the battery percentage will light up in sequence. When charging other devices, the orange circle will stay on.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">16</span></td><td class="hb-lcd-icon"><img alt="Low Battery Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-18.svg"/></td><td class="hb-lcd-name">Low Battery Indicator</td><td class="hb-lcd-description"><strong>On</strong>: The battery level is below 20%.<br/><strong>Blink</strong>: The battery level is below 5%.<br/><strong>Off</strong>: The product is charging.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">17</span></td><td class="hb-lcd-icon"><img alt="Remaining Battery Percentage" class="hb-lcd-icon-art" src="assets/lcd-native-19.svg"/></td><td class="hb-lcd-name">Remaining Battery Percentage</td><td class="hb-lcd-description">Displays the remaining battery percentage.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">18</span></td><td class="hb-lcd-icon"><img alt="Battery Pack Indicator and Number of Connected Batteries" class="hb-lcd-icon-art" src="assets/lcd-native-20.svg"/></td><td class="hb-lcd-name">Battery Pack Indicator and Number of Connected Batteries</td><td class="hb-lcd-description">Indicates that the product is connected to the specified number of 5000 Plus Battery Pack(s).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">19</span></td><td class="hb-lcd-icon"><img alt="Fault Code" class="hb-lcd-icon-art" src="assets/lcd-native-21.svg"/></td><td class="hb-lcd-name">Fault Code</td><td class="hb-lcd-description">A product error has occurred. Please refer to the Troubleshooting section for details.</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">20</span></td><td class="hb-lcd-icon"><img alt="High Temperature Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-22.svg"/></td><td class="hb-lcd-name">High Temperature Indicator</td><td class="hb-lcd-description">High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</td></tr><tr><td class="hb-lcd-icon"><img alt="Low Temperature Indicator" class="hb-lcd-icon-art" src="assets/lcd-native-23.svg"/></td><td class="hb-lcd-name">Low Temperature Indicator</td><td class="hb-lcd-description">Low temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">21</span></td><td class="hb-lcd-icon"><img alt="Energy Saving Mode" class="hb-lcd-icon-art" src="assets/lcd-native-24.svg"/></td><td class="hb-lcd-name">Energy Saving Mode</td><td class="hb-lcd-description">To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default. If no device is connected or the connected device's power consumption is below a certain threshold (AC output≤25W; USB output≤2W; Car output≤2W), the device will automatically turn off all outputs after 12 hours. <strong>On</strong>/<br/><strong>Off</strong>: Press and hold both the AC Power Button and Main Power Button</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">22</span></td><td class="hb-lcd-icon"><img alt="Output Power" class="hb-lcd-icon-art" src="assets/lcd-native-25.svg"/></td><td class="hb-lcd-name">Output Power</td><td class="hb-lcd-description">Displays the output power in watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">23</span></td><td class="hb-lcd-icon"><img alt="Remaining Discharge Time" class="hb-lcd-icon-art" src="assets/lcd-native-26.svg"/></td><td class="hb-lcd-name">Remaining Discharge Time</td><td class="hb-lcd-description">Displays the remaining discharging time.</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## OPERATIONS

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><p>When Energy Saving Mode is on, if the DC Output, AC Output, or USB Output Power Button is ON but the product is not charging or discharging, it will automatically shut down after 12 hours.</p></td></tr></tbody></table>

### POWER ON/OFF

<div class="native-figure native-power native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="07b15eef0eafedc4c373993d9b400363b5361bb6b3f3027e5fdc361437747681" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76.1008%;--hb-y:7.7699%;--hb-width:4.6783%;--hb-height:8.8127%"><span><strong>On</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.2059%;--hb-y:15.8836%;--hb-width:9.7694%;--hb-height:5.5238%"><span>Press once</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:76.0084%;--hb-y:24.3604%;--hb-width:4.7675%;--hb-height:8.8127%"><span><strong>Off</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:76.2059%;--hb-y:32.0778%;--hb-width:18.3873%;--hb-height:5.5238%"><span>Press and hold for 3s</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:80.4096%;--hb-y:39.3465%;--hb-width:2.5121%;--hb-height:6.2857%"><span>3s</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="5" style="--hb-x:42.1643%;--hb-y:58.5153%;--hb-width:53.6006%;--hb-height:31.106%;--hb-fill:#f2f2f3"><span><strong>Default</strong> <strong>standby</strong> <strong>time:</strong> 2 hours<br/>· The product will automatically shut down after 2 hours<br/>of inactivity, with no charging or discharging.<br/>· The standby time can be set in the Jackery App.</span></span></div></div></figure></div>

### AC OUTPUT ON/OFF

<div class="native-figure native-ac-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output" data-source-fragment-sha256="5a07e08447eb56d7a7ad50c3f8c2594f7c8047f6cf15ede554272c69edbc2202" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.5176%;--hb-y:4.335%;--hb-width:49.9328%;--hb-height:7.4177%;--hb-fill:#f2f2f3"><span><strong>Prerequisite:</strong> Ensure the Main Power Button is on.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:83.469%;--hb-y:10.2283%;--hb-width:4.6783%;--hb-height:7.519%"><span><strong>On</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:83.6448%;--hb-y:16.9472%;--hb-width:9.7694%;--hb-height:3.9003%"><span>Press once</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:83.3767%;--hb-y:22.7581%;--hb-width:4.7675%;--hb-height:7.519%"><span><strong>Off</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:83.3811%;--hb-y:30.0296%;--hb-width:9.7694%;--hb-height:3.9003%"><span>Press once</span></span></div></div></figure></div>

### USB OUTPUT ON/OFF

<div class="native-figure native-usb-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output" data-source-fragment-sha256="7d4c200acee02f7e02ec1a4957ef16d8d1cdf8a34c0cc7678be99b5394e80f42" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="usb-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.4391%;--hb-y:7.2326%;--hb-width:45.3111%;--hb-height:11.1145%;--hb-fill:#f2f2f3"><span><strong>Prerequisite:</strong> Ensure the Main Power Button is on.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:78.8372%;--hb-y:16.5993%;--hb-width:4.2082%;--hb-height:11.2209%"><span><strong>On</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:78.757%;--hb-y:26.4502%;--hb-width:9.7694%;--hb-height:7.7818%"><span>Press once</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:78.752%;--hb-y:36.2699%;--hb-width:4.2877%;--hb-height:11.2209%"><span><strong>Off</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:78.757%;--hb-y:45.9421%;--hb-width:9.7694%;--hb-height:7.7818%"><span>Press once</span></span></div></div></figure></div>

### DC OUTPUT ON/OFF

<div class="native-figure native-dc-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc-output" data-source-fragment-sha256="7b03a119ed425afe62f3ae6e52c996ab50e3439e5caf3a81f59468e37a56d879" data-web-base-art-ref="dc-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="dc-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/dc-output.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.4391%;--hb-y:5.8041%;--hb-width:45.3111%;--hb-height:11.5591%;--hb-fill:#f2f2f3"><span><strong>Prerequisite:</strong> Ensure the Main Power Button is on.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.5811%;--hb-y:13.397%;--hb-width:4.2082%;--hb-height:11.6697%"><span><strong>On</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:79.7888%;--hb-y:24.2952%;--hb-width:9.7694%;--hb-height:8.093%"><span>Press once</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:79.4959%;--hb-y:32.5929%;--hb-width:4.2877%;--hb-height:11.6697%"><span><strong>Off</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:79.7888%;--hb-y:44.5668%;--hb-width:9.7694%;--hb-height:8.093%"><span>Press once</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><p>The product can charge your car battery using the Jackery 12V automobile battery charging cable, which is sold separately and available on our website.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><ul><li>The cigarette lighter port is only compatible with 12V car batteries and not suitable for 24V systems.</li><li>Do not start the car while the product is charging the car battery through the 12V DC output port (cigarette lighter port), as this may damage the product.</li><li>This feature is intended for emergency use only and cannot charge a dead or damaged car battery.</li></ul></td></tr></tbody></table>

### LCD SCREEN

<div class="native-lcd-panel"><figure aria-label="LCD SCREEN" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="LCD SCREEN" class="hb-lcd-mode-art" src="assets/lcd-button.svg"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">LCD Screen</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Press the Main Power Button or when the product is charging.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Always-on Display Mode (under charging or discharging state)</td><td class="hb-lcd-mode-action">Turn on</td><td class="hb-lcd-mode-copy">Double-click the Main Power Button when the LCD screen is ON.</td></tr><tr><td class="hb-lcd-mode-action">Turn off</td><td class="hb-lcd-mode-copy">Press the Main Power Button.</td></tr><tr><td class="hb-lcd-mode-action">Auto-off</td><td class="hb-lcd-mode-copy">The Always-on Display Mode turns off automatically after 2 hours of inactivity.</td></tr></tbody></table></div></figure></div>

### KEY COMBINATIONS

<figure aria-label="Buttons / Operation / Function" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Buttons</th><th class="hb-key-operation" scope="col">Operation</th><th class="hb-key-function" scope="col">Function</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Main Power Button</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>USB Power Button</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Press and hold both for 3s</p></td><td class="hb-key-function">Reset Wi-Fi &amp; Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Main Power Button</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC Power Button</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Press and hold both for 3s</p></td><td class="hb-key-function">Turn on/off the Energy Saving Mode</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>USB Power Button</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC Power Button</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">1s</span><p>Press and hold both for 1s</p></td><td class="hb-key-function">Turn on/off Wi-Fi &amp; Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-dc-bottom.svg"/><p>DC Power Button</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>AC Power Button</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3s</span><p>Press and hold both for 3s</p></td><td class="hb-key-function">Switch to online UPS or Backup UPS</td></tr></tbody></table></figure>

<span id="native-troubleshooting"></span>

## TROUBLESHOOTING

<div class="table-wrapper docutils container"><table class="manual-table native-troubleshooting"><thead><tr><th>Error Code</th><th>Name</th><th>Description (For Internal Fault Maintenance Only)</th></tr></thead><tbody><tr><td><strong>F0</strong></td><td><strong>BMS Data Communication Error</strong></td><td>Data communication fault between the BMS and mainboard</td></tr><tr><td><strong>F1</strong></td><td><strong>Inverter Data Communication Error</strong></td><td>Data communication fault between the inverter and mainboard</td></tr><tr><td><strong>F2</strong></td><td><strong>DC Input Data Communication Error</strong></td><td>Data communication fault between the DC charging module and BMS</td></tr><tr><td><strong>F3</strong></td><td><strong>BMS or Battery Failure</strong></td><td>BMS or battery failuare</td></tr><tr><td><strong>F4</strong></td><td><strong>Battery Overvoltage</strong></td><td>Battery overvoltage</td></tr><tr><td><strong>F5</strong></td><td><strong>Battery Undervoltage</strong></td><td>Battery undervoltage</td></tr><tr><td><strong>F6</strong></td><td><strong>Inverter Failure</strong></td><td>AC output overcurrent / overload / short circuit;<br/>Grid input overvoltage / undervoltage / overfrequency / underfrequency;<br/>Inverter over-temperature protection on (triggered)<br/>Insulation detection failure</td></tr><tr><td><strong>F7</strong></td><td><strong>DC Input Failure</strong></td><td>PV input overvoltage;<br/>DC charging module overtemperature protection on/triggered;<br/>Output overcurrent protection of the DC charging module on/triggered</td></tr><tr><td><strong>F8</strong></td><td><strong>Battery Charging / Discharging Overcurrent / Short Circuit</strong></td><td>BMS overcurrent / short circuit protection on/triggered</td></tr><tr><td><strong>F9</strong></td><td><strong>DC Output Overcurrent / Short Circuit</strong></td><td>USB short circuit protection on/triggered</td></tr><tr><td><strong>FA</strong></td><td><strong>Parallel Unit Communication Error</strong></td><td>Data communication failure between two 5000 Plus failure caused by both units defective.</td></tr><tr><td><strong>FC</strong></td><td><strong>Battery Pack Communication Error</strong></td><td>Data communication failure between the 5000 Plus and battery pack(s)</td></tr></tbody></table></div>

<span id="native-ups"></span>

## UNINTERRUPTIBLE POWER SUPPLY (UPS)

<p>An uninterruptible power supply (UPS) is a type of continual power system that provides automated backup electric power to a load when the mains grid power fails.</p>

<p>The HomePower 5000 Plus is equipped with two UPS modes: Backup UPS and Online UPS.</p>

### BACKUP UPS

<p>The backup UPS function is enabled by default. In the event of a sudden loss of grid power, the HomePower 5000 Plus will automatically switch to stored power within 20 ms to keep your appliances running.</p>

<p>In Backup UPS mode, the unit's peak output reaches 1440W before power outages. As simultaneous charging/discharging is enabled in Bypass Mode, the actual output power is lower than the rated output power in this mode but returns to rated output power during outages.</p>

<div class="native-figure native-ups native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="03d4c0feff533afd13c071a375144e486616968e01c1acfad2194e4a9de03f2f" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:37.9791%;--hb-y:69.6388%;--hb-width:56.7344%;--hb-height:22.0072%;--hb-fill:#f2f2f3"><span>Connect the product to a wall outlet with the AC charging<br/>cable, then press the AC output button and power your<br/>appliances at the same time .</span></span></div></div></figure></div>

### ONLINE UPS

<p>The online UPS mode, which enables 0 ms switching, can be activated in two ways:</p>

<ol><li>Enable Online UPS in the Jackery App.</li><li>Press the DC and AC Power Buttons simultaneously on the HomePower 5000 Plus.</li></ol>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><ol><li>The system settings will revert to Backup UPS mode when the product is in Online mode and is restarted. In Backup UPS mode, the output power is limited by the bypass power, with a maximum output power of 1440W.</li><li>In UPS mode, the NEMA L14-30R and NEMA 14-50 outlets each provide a 120V output when the product is connected to a wall outlet using the AC charging cable.</li><li>In Online UPS mode, it supports 0 ms switching with a maximum output power of 3600W.</li></ol></td></tr></tbody></table>

<span id="native-connections"></span>

## CONNECTIONS

### <span class="hb-heading-title">CONNECT TO BATTERY PACK(S)</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<p>This product can support up to 5 battery packs to meet the need for large power capacity. For details on how to use it, please refer to the Jackery Battery Pack 5000 Plus User Manual.</p>

<div class="native-figure native-battery-packs native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-packs" data-source-fragment-sha256="6d0d40205c4f8cd21677add4579dd24369742aaac71160f3666906425a15f1b0" data-web-base-art-ref="battery-packs" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-packs.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-packs.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:24.3765%;--hb-y:90.151%;--hb-width:18.3552%;--hb-height:5.7023%"><span>at least 1 ft (300mm)</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.3545%;--hb-y:90.151%;--hb-width:18.3552%;--hb-height:5.7023%"><span>at least 1 ft (300mm)</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><ol><li>Ensure all products are powered off before connecting the HomePower 5000 Plus to the 5000 Plus Battery Pack(s).</li><li>To ensure proper operation of the product, make sure the air intake and exhaust vents on both sides are unobstructed. Leave at least 1 ft of space between the vents and any objects to allow for adequate air circulation and effective heat dissipation.</li></ol></td></tr></tbody></table>

### <span class="hb-heading-title">CONNECT TO A SMART TRANSFER SWITCH</span> <span class="hb-sold-separately">SOLD SEPARATELY</span>

<div class="native-figure native-sts-connect native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-connect" data-source-fragment-sha256="2c5cdf2b10b66787988658430d905f4b149bcaf562b28ad711e5c15ea8cb450f" data-web-base-art-ref="sts-connect" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-connect.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-connect.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:36.779%;--hb-y:8.6667%;--hb-width:57.9395%;--hb-height:25.6882%;--hb-fill:#ffffff"><span>Jackery HomePower 5000 Plus can power your home loads<br/>via the Smart Transfer Switch. For details on how to use it,<br/>please refer to the Jackery Smart Transfer Switch user manual.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:56.7244%;--hb-y:38.9239%;--hb-width:36.3908%;--hb-height:5.1971%"><span>When UPS mode is enabled, the portable</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:56.7244%;--hb-y:43.7017%;--hb-width:29.4834%;--hb-height:5.1971%"><span>power station remains active and</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:56.7244%;--hb-y:48.4794%;--hb-width:39.7191%;--hb-height:5.1971%"><span>continuously consumes power. In the event of</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:56.7244%;--hb-y:53.2572%;--hb-width:35.9554%;--hb-height:5.1971%"><span>a power outage, the system will switch to</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:56.7244%;--hb-y:58.035%;--hb-width:32.3686%;--hb-height:5.1971%"><span>battery power within 20 milliseconds.</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:56.7244%;--hb-y:62.8128%;--hb-width:35.0278%;--hb-height:5.1971%"><span>When UPS mode is disabled, the system</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:56.7244%;--hb-y:67.5906%;--hb-width:37.7866%;--hb-height:5.1971%"><span>switches to battery power within 5 seconds</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:56.7244%;--hb-y:72.3683%;--hb-width:20.7874%;--hb-height:5.1971%"><span>during a power outage.</span></span></div></div></figure></div>

<span id="native-charging"></span>

## CHARGING

<p>Green energy first: We advocate to use the green energy first. This product supports two modes of charging at the same time: solar charging and AC wall charging.</p>

<p>When AC wall charging and solar charging are turned on at the same time, the product will give priority to solar charging and both methods will be used to charge the battery at the maximum permissible power.</p>

<p class="hb-prose-pill"><strong>Fully charge the product before its first use.</strong></p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><ol><li>The recommended charging temperature for the product is between 0°C to 45°C (32°F to 113°F), and the discharging temperature is between -15°C to 45°C (5°F to 113°F). Operating the product outside this temperature range may restrict its charging and discharging capabilities, prevent it from charging or discharging.</li><li>The charging power and battery capacity of the product may vary due to temperature fluctuations. When the ambient temperature is between -15°C to -10°C (5°F to 14°F), the maximum output power decreases to 3600W.</li></ol></td></tr></tbody></table>

### CHARGING VIA AC WALL OUTLET

<div class="native-figure native-ac-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="677853b510392446b4c9aabe61a8c145b6b79e6871c82ac487caa47502df2f3a" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:59.7044%;--hb-y:47.5816%;--hb-width:28.0452%;--hb-height:8.0184%"><span>Connect the AC charging cable</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:59.7044%;--hb-y:55.8765%;--hb-width:28.5856%;--hb-height:8.0184%"><span>to the HomePower 5000 Plus AC</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:59.7044%;--hb-y:64.1714%;--hb-width:24.5915%;--hb-height:8.0184%"><span>input port and a wall outlet.</span></span></div></div></figure></div>

### CHARGING WITH A SMART TRANSFER SWITCH

<div class="native-figure native-sts-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-charge" data-source-fragment-sha256="92126993b0e18d20bac83165192eae5bbf137d70fc9d23bedcc613fe575a7ca2" data-web-base-art-ref="sts-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-charge.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:39.5595%;--hb-y:4.6556%;--hb-width:54.1151%;--hb-height:4.9771%"><span>Connect your Jackery Smart Transfer Switch to the product to</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:39.5595%;--hb-y:8.6613%;--hb-width:48.125%;--hb-height:4.9771%"><span>enable charging via the Jackery Smart Transfer Switch.</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:39.5595%;--hb-y:14.6304%;--hb-width:52.1146%;--hb-height:4.9771%"><span>*The backup reserve setting works in all modes of the Smart</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:39.5595%;--hb-y:19.206%;--hb-width:53.562%;--hb-height:4.9771%"><span>Transfer Switch. Therefore, the Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:39.5595%;--hb-y:23.7815%;--hb-width:56.6008%;--hb-height:4.9771%"><span>stops charging when its remaining capacity exceeds the backup</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:39.5595%;--hb-y:28.357%;--hb-width:54.5222%;--hb-height:4.9771%"><span>reserve. To charge it immediately, follow the instructions below.</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:39.6606%;--hb-y:35.5343%;--hb-width:5.8161%;--hb-height:5.1076%"><span><strong>STEP</strong> <strong>1</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:60.7093%;--hb-y:35.5343%;--hb-width:6.091%;--hb-height:5.1076%"><span><strong>STEP</strong> <strong>2</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:62.0551%;--hb-y:79.1706%;--hb-width:3.2461%;--hb-height:2.0151%"><span>HP5000Plus</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:76.1589%;--hb-y:89.754%;--hb-width:8.2806%;--hb-height:4.9771%"><span>*STS App</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><p>When the AC Expansion Port is successfully connected to the STS, the AC Input port will not be used for charging. In this case, the portable power station can be charged via the following ports: AC Expansion Port, High-PV, and Low-PV.</p></td></tr></tbody></table>

### CHARGING WITH SOLAR PANELS

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><p>When connecting solar panels in series, ensure that the maximum voltage output of all panels is within 16V-60V for the low-PV input port, and 135V-450V for the high-PV input port.</p></td></tr></tbody></table>

<ul><li><strong>Connect to Low-PV Input Port</strong></li></ul>

<p>Low-PV input voltage range: 16V to 60V</p>

<p>The Jackery HomePower 5000 Plus has two low-PV input ports, each one supports direct connection of one 500W or three 200W solar panels. If one low-PV input port needs to connect two or more solar panels simultaneously, please refer to the figure below for charging through the solar panel connector (sold separately, not included as standard).</p>

<div class="native-figure native-low-pv-500 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-500" data-source-fragment-sha256="c15fbfa8cf0f1dde0f0d3dbc98396dec1fbf186981f8a665885d7e1ed2bef6ff" data-web-base-art-ref="low-pv-500" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-500.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-500.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.9344%;--hb-y:6.1481%;--hb-width:5.7165%;--hb-height:5.1339%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:78.8982%;--hb-y:81.6798%;--hb-width:13.5106%;--hb-height:5.1339%"><span>SolarSaga 500 X × 2</span></span></div></div></figure></div>

<div class="native-figure native-low-pv-200 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-200" data-source-fragment-sha256="fad18b7b2c402a027b5a4d822a86fc0b91020111738fc1bb20149f6038143401" data-web-base-art-ref="low-pv-200" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-200.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-200.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.1609%;--hb-y:5.8661%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.6889%;--hb-y:5.8661%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:80.1014%;--hb-y:90.1159%;--hb-width:12.3072%;--hb-height:4.6247%"><span>SolarSaga 200 × 6</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><ol><li>Ensure that the input voltage for both DC input ports is the same. Failure to do so may damage the product. For example:</li></ol><ul><li>It is recommended to use the same model of Jackery solar panels and the same number of panels when connecting solar panels to both DC8020 Input ports.</li><li>Do not charge the product using both a car charger and a solar panel simultaneously. Doing so may blow the car fuse or result in charging failure.</li></ul><ol start="2"><li>It is recommended to use the Jackery Solar Panel to charge the HomePower 5000 Plus. Jackery is not responsible for any losses caused by using solar panels from other brands.</li></ol></td></tr></tbody></table>

<ul><li><strong>Connect to High-PV Input Port</strong></li></ul>

<p>High-PV input voltage range: 135V to 450V</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><ol><li>Make sure the High-PV switch is turned off before connecting the High-PV input or performing maintenance.</li><li>Before using the High-PV input ports, make sure the PV switch is turned on.</li><li>Make sure the High-PV switch is in the 'OFF' or 'LOCK' position before using the provided MC4 wrench to disconnect the MC4 connectors.</li></ol></td></tr></tbody></table>

<div class="native-figure native-high-pv native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv" data-source-fragment-sha256="8f194a9b949be30a56d84ad3ffb63f7ccaacfffa56676d59c0dbb659b1b28cda" data-web-base-art-ref="high-pv" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.646%;--hb-y:6.3093%;--hb-width:29.6438%;--hb-height:3.9716%"><span>Disconnect MC4 connectors with</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.646%;--hb-y:10.4739%;--hb-width:23.7387%;--hb-height:3.9716%"><span>the provided MC4 wrench.</span></span></div></div></figure></div>

<div class="native-figure native-high-pv-lock native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv-lock" data-source-fragment-sha256="93b6c939f81d35855676070b5bfaf77d9e637dd50b72e9b706ca7fc2d1eec3d5" data-web-base-art-ref="high-pv-lock" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv-lock.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.1126%;--hb-y:14.2499%;--hb-width:5.7556%;--hb-height:8.3363%"><span><strong>Lock</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:54.0559%;--hb-y:14.8955%;--hb-width:8.325%;--hb-height:8.3363%"><span><strong>Unlock</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.9175%;--hb-y:24.6044%;--hb-width:40.045%;--hb-height:6.3597%"><span>Turn the high-PV switch to the 'LOCK' position</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:54.049%;--hb-y:25.2508%;--hb-width:35.318%;--hb-height:6.3597%"><span>Release the locking mechanism and the</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:6.9175%;--hb-y:30.4509%;--hb-width:29.9571%;--hb-height:6.3597%"><span>and press the locking mechanism.</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:54.049%;--hb-y:31.0973%;--hb-width:30.456%;--hb-height:6.3597%"><span>switch returns to the 'OFF' position.</span></span></div></div></figure></div>

<ul><li><strong>High-PV + Low-PV Input</strong></li></ul>

<p>Voltage range for low-PV input: 16V to 60V</p>

<p>Voltage range for high-PV input: 135V to 450V</p>

<div class="native-figure native-dual-pv native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dual-pv" data-source-fragment-sha256="0c66ccafa23616c19ca1e92a43b633566946a182d8ab4130ddfc6de832746e75"><div class="hb-reference-semantic" data-reference-id="dual-pv.semantic"><img alt="dual-pv" class="hb-reference-art hb-composite-art" src="assets/dual-pv.svg"/></div></figure></div>

### CHARGING WITH A CAR CHARGER

<p>This product can be charged using a 12V car charger. Ensure that the car charger and the car cigarette lighter provide a good connection.</p>

<div class="native-figure native-car native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="7c0f1164655a604a3ef32ab52539bce70c36cc5e3e2170a34b9416c91a0f2533" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71.4512%;--hb-y:22.9952%;--hb-width:7.5345%;--hb-height:6.6667%"><span>Vehicle</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:51.8937%;--hb-y:84.567%;--hb-width:45.6103%;--hb-height:9.2209%;--hb-fill:#ffffff"><span>*The car charging cable is sold separately.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><ol><li>Please start the vehicle before charging your power station.</li><li>If the vehicle is running on bumpy roads, it is forbidden to use the car charger in case it burns due to a poor connection. The Company will not be responsible for any loss caused by non-standard operation.</li><li>Vehicle charging is only applicable to vehicles with 12V DC, not 24V DC. Please do not charge this product in 24V vehicle to avoid personal injury and property loss.</li></ol></td></tr></tbody></table>

<span id="native-storage"></span>

## STORAGE

<p>Store the product in a dry clean place with proper ventilation. Storage temperature and humidity:</p>

<ul><li>1 month: -4°F to 113°F / -20°C to 45°C (0-60%RH)</li><li>3 months: 32°F to 113°F / 0°C to 45°C (0-60%RH)</li><li>12 months: 32°F to 77°F / 0°C to 25°C (0-60%RH)</li></ul>

<p>If this product is stored for a long period of time (3 months - 6 months) with the power depleted, it may become unchargeable. To prevent this and maintain battery health, it is recommended to check and recharge the product every three months and perform a full charge and discharge cycle at least once every 6 to 12 months.</p>

<span id="native-app"></span>

## APP SETUP

### 1. To download the App and log in

<figure aria-label="App download" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Search for "Jackery" in Google Play or App Store to install the App. After that, you can register and log in.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternatively, scan the QR code below to download and install the App.</p></div></div></div><div class="hb-app-download-semantic"><img alt="App download" class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

### 2. To add device

<p>2.1 Click the button <span class="native-inline-plus">+</span> to add your device;</p>

<p>2.2 Turn on the product by long-pressing the Main Power Button. When the Wi-Fi and Bluetooth icons appear and flash on the product, your product enters the network configuring mode. Open Bluetooth permission and tap the Icon Flashed button on your APP to connect the product;</p>

<div class="native-figure native-app-add native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add" data-source-fragment-sha256="bdc3fd18101f0cff875da9b75b8c5303c79b4077ccc63fd2182f9f4fc396fc28" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-add.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:74.1518%;--hb-y:94.002%;--hb-width:5.3913%;--hb-height:5.3539%"><span>2.2</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:20.7444%;--hb-y:94.183%;--hb-width:4.7019%;--hb-height:5.3539%"><span>2.1</span></span></div></div></figure></div>

<div class="native-figure native-app-control native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="b0f3e868ba6715c828d06c3f9db3819ea21e1015b074f4f99ac6bb2b8e368ae0" data-web-base-art-ref="app-control" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-control.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-control.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:75.8708%;--hb-y:20.5456%;--hb-width:17.5459%;--hb-height:11.2403%"><span>Main Power Button</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:7.7556%;--hb-y:24.3872%;--hb-width:16.0842%;--hb-height:11.2403%"><span>DC Power Button</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:75.8708%;--hb-y:43.3286%;--hb-width:16.8618%;--hb-height:11.2403%"><span>USB Power Button</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:7.4982%;--hb-y:57.4681%;--hb-width:15.9052%;--hb-height:11.2403%"><span>AC Power Button</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarks</td><td class="manual-callout-body"><p>After being turned on, if the APP is not connected within 2 hours, the device will automatically turn off Wi-Fi and Bluetooth. Now, it is required to press and hold USB Power Button and AC Power Button to turn on Wi-Fi and Bluetooth again.</p></td></tr></tbody></table>

<p>2.3 After clicking the searched device icon, the App automatically connects the device via Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarks</td><td class="manual-callout-body"><p>If “the device has been bound” is prompted during the binding process, the following two ways can be used for connection:</p><ul><li>The device owner will share this device with other users through the App.</li><li>Press and hold the Main Power Button and USB Power Button for 3 seconds to reset the device, and then re-bind the device.</li></ul></td></tr></tbody></table>

<p>2.4 After the device is successfully connected, it is necessary to enter your Wi-Fi password and tap the OK button;</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarks</td><td class="manual-callout-body"><p>Please select a Wi-Fi network in 2.4GHz band. The device does not support a Wi-Fi network in 5GHz band.</p></td></tr></tbody></table>

<p>2.5 After the device is successfully added on the home page of the device, the Wi-Fi icon on the device will be always on;</p>

<div class="native-figure native-app-results native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-results" data-source-fragment-sha256="4b0abcf4f3dc9d0e8711acc7e64e70273219606452cc604306b7ad716a8b8825" data-web-base-art-ref="app-results" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-results.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-results.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:11.9834%;--hb-y:94.6633%;--hb-width:3.35%;--hb-height:5.6129%"><span>2.3</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:48.3734%;--hb-y:94.6633%;--hb-width:3.4654%;--hb-height:5.6129%"><span>2.4</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.9711%;--hb-y:94.6633%;--hb-width:3.3731%;--hb-height:5.6129%"><span>2.5</span></span></div></div></figure></div>

<p>The above screenshots are for reference only.</p>

### 3. To unbind the device

<p>Click the Settings button in the upper right corner of the main interface of the device to enter the settings page, and click the Unbind button at the bottom of the page to unbind the device.</p>

### 4. Notes

<p><strong>4.1 To turn on Wi-Fi &amp; Bluetooth:</strong></p>

<ul><li>Wi-Fi &amp; Bluetooth are automatically turned on after the device is on, and the Wi-Fi &amp; Bluetooth icons on the screen light up;</li><li>Press the USB Power Button and the AC Power Button at the same time until the Wi-Fi &amp; Bluetooth icons on the screen light up;</li></ul>

<p><strong>4.2 To turn off Wi-Fi &amp; Bluetooth:</strong></p>

<ul><li>Press the USB Power Button and AC Power Button at the same time until the Wi-Fi &amp; Bluetooth icons on the screen are off;</li><li>Wi-Fi &amp; Bluetooth will be automatically turned off if no device is connected within 2 hours;</li></ul>

<p><strong>4.3 To reset Wi-Fi &amp; Bluetooth：</strong></p>

<ul><li>Press the Main Power Button and USB Power Button at the same time for 3 seconds to reset Wi-Fi &amp; Bluetooth to factory settings and reboot the system. The connected App account will be unbound.</li></ul>

<span id="native-warranty"></span>

## WARRANTY

<figure aria-label="WARRANTY" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>We only provide our warranty to customers who purchase from the official Jackery website, Jackery-branded third-party platforms, or local authorized dealers.</strong></div><div class="hb-warranty-local-note">* Warranty period and details may vary according to local laws, regulations, and authorized dealers.</div></figure>

### Limited Warranty

<figure aria-label="Limited Warranty" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. warrants to the original consumer purchaser that the Jackery product will be free from defects in workmanship and material under normal consumer use during the applicable warranty period identified in the 'Warranty Period' section below, subject to the exclusions set forth below.</p><p>This warranty statement sets forth Jackery's total and exclusive warranty obligation. We will not assume, nor authorize any person to assume for us, any other liability in connection with the sale of our products.</p></figure>

### Warranty Period

<figure aria-label="Warranty Period" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="5 YEARS Standard Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">5</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Standard Warranty</strong></div></div><div class="hb-warranty-period-copy">The standard warranty period for Jackery HomePower 5000 Plus is 60 months. In each case, the warranty period is measured starting on the date of purchase by the original consumer purchaser. The sales receipt from the first consumer purchase, or other reasonable documentary proof, is required in order to establish the start date of the warranty period.</div></div><div aria-label="2 YEARS Extended Warranty" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">YEARS</strong><strong class="hb-warranty-period-label">Extended Warranty</strong></div></div><div class="hb-warranty-period-copy">An additional fee is required for the extended warranty. For details on the extended warranty, please visit the Jackery website or contact Jackery customer service.</div></div></div></figure>

### Repair or replacement

<figure aria-label="Repair or replacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3">Jackery will repair or replace (at Jackery's expense) any Jackery product that fails to operate during the applicable warranty period due to a defect in workmanship or material. The repaired/replaced product assumes the remaining warranty of the original date of purchase.</figure>

### Limited to Original Consumer Buyer

<figure aria-label="Limited to Original Consumer Buyer" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4">The warranty on Jackery's product is limited to the original consumer purchaser and is not transferable to any subsequent owner.</figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery's warranty does not apply to:</p><p>Misused, abused, modified, damaged by accident, or used for anything other than normal consumer use as authorized in Jackery's current product literature.</p><p>Attempted repair by anyone other than an authorized facility.</p><p>Any product purchased through an online auction house.</p><p>Jackery's warranty does not apply to the battery cell unless the battery cell is fully charged by you within seven days after you purchase the product and at least once every 6 months thereafter.</p></figure>

### Interpretation Rights

<figure aria-label="Interpretation Rights" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6">Jackery Inc. reserves the right to final interpretation of the above customers' after-sales policy.</figure>

<span id="native-specifications"></span>

## SPECIFICATIONS

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 134.5 lbs/61 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">16.5×15.5×25 in/41.8×39.5×63.5 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">4000 cycles to 70%+ capacity</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">Backup UPS: ＜20ms Onine UPS: 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Inverter Topology</th><td class="manual-spec-value hb-spec-value">Non-isolated</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Power Factor</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entire Unit</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">INPUT PORTS</h2>

<figure aria-label="INPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Mode AC Input</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A Max (Duration time &lt; 3h when current exceeds 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Bypass Mode AC Input</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Max (Duration time &lt; 3h when current exceeds 12A)</td></tr><tr><td class="manual-spec-value hb-spec-value">240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x AC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Input</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x DC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓98A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">High-PV</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A Max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Low-PV</th><td class="manual-spec-value hb-spec-value">2 x DC 8mm Ports; 16V-60V⎓10.5A Max, Double to 21A/1200W Max</td></tr><tr><td class="manual-spec-value hb-spec-value">11V-16V (Working Voltage)⎓8A Max, Double to 8A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">OUTPUT PORTS</h2>

<figure aria-label="OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Output (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Bypass Mode AC Output</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Max 240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × AC Output</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Total Output</th><td class="manual-spec-value hb-spec-value">7200W Max, 14400W Surge</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-C Output</th><td class="manual-spec-value hb-spec-value">100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-A Output</th><td class="manual-spec-value hb-spec-value">18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cigarette Lighter Port</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × DC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓41A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charging Temperature</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Discharging Temperature</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><td class="manual-spec-value hb-spec-value">-15°C~-10°C (5°F~14°F) Output Power: 3600W</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>INGESTION HAZARD:</strong> This product contains a button cell or coin battery.</p>

<p class="native-trademark">※ USB Type-C<sup>®</sup> and USB-C<sup>®</sup> are registered trademarks of USB Implementers Forum.</p>

<span id="native-ess"></span>

## <span class="hb-heading-title">SMART HOME BACKUP SYSTEM (AC ESS) INSTALLATION GUIDE</span> <span class="hb-heading-model"><strong>System Model</strong><br/>HB5000C-TS02A</span>

<p>To connect the Jackery HomePower 5000 Plus to the Smart Transfer Switch (STS), use the expansion cable to link the Explorer 5000 Plus AC expansion port to the STS AC power input/output port.</p>

<p>To connect the Jackery HomePower 5000 Plus to the battery pack, use the expansion cable to connect its DC expansion port (A) to the battery pack's DC expansion port (B).</p>

<div class="native-figure native-ess native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ess" data-source-fragment-sha256="d58f02ac90a1b44ea61d4d6fbff34beef9948f22818af00ba44cbd1002281490" data-web-base-art-ref="ess" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ess.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ess.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.4008%;--hb-y:88.1423%;--hb-width:56.7772%;--hb-height:3.1522%"><span>For detailed installation and connection instructions, refer to the</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.4008%;--hb-y:91.7662%;--hb-width:38.4366%;--hb-height:3.1522%"><span>user manuals for the STS and battery pack.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Caution</td><td class="manual-callout-body"><p>Smart home backup system (AC ESS) Installation Position</p><p>Indoor installation.</p><p>The area is completely water proof.</p><p>The wall is flat and level.</p><p>Ambient temperature range:-15°C~45°C.</p><p>The temperature and humidity are maintained at a constant level. Install in a well-ventilated place.</p><p>Do not place at a children or pet touchable area.</p><p>The installation area shall avoid of direct sunlight.</p><p>No flammable or explosive materials close to inverter and battery.</p></td></tr></tbody></table>

<span id="native-ess-host"></span>

### <span class="hb-heading-title">Jackery HomePower 5000 Plus</span> <span class="hb-heading-model">Model: JHP-5000C</span>

#### <span class="native-plain-title">SPECIFICATIONS</span>

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 134.5 lbs/61 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">16.5×15.5×25 in/41.8×39.5×63.5 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">4000 cycles to 70%+ capacity</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">Backup UPS: ＜20ms Onine UPS: 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Inverter Topology</th><td class="manual-spec-value hb-spec-value">Non-isolated</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Power Factor</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entire Unit</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">INPUT PORTS</h2>

<figure aria-label="INPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charge Mode AC Input</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A Max (Duration time &lt; 3h when current exceeds 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Bypass Mode AC Input</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Max (Duration time &lt; 3h when current exceeds 12A)</td></tr><tr><td class="manual-spec-value hb-spec-value">240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x AC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Input</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x DC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓98A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">High-PV</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A Max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Low-PV</th><td class="manual-spec-value hb-spec-value">2 x DC 8mm Ports; 16V-60V⎓10.5A Max, Double to 21A/1200W Max</td></tr><tr><td class="manual-spec-value hb-spec-value">11V-16V (Working Voltage)⎓8A Max, Double to 8A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">OUTPUT PORTS</h2>

<figure aria-label="OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Output (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Bypass Mode AC Output</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A Max 240V~60Hz, 16.7A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × AC Output</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Total Output</th><td class="manual-spec-value hb-spec-value">7200W Max, 14400W Surge</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-C Output</th><td class="manual-spec-value hb-spec-value">100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × USB-A Output</th><td class="manual-spec-value hb-spec-value">18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cigarette Lighter Port</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × AC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × DC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓41A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charging Temperature</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Discharging Temperature</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><td class="manual-spec-value hb-spec-value">-15°C~-10°C (5°F~14°F) Output Power: 3600W</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>INGESTION HAZARD:</strong> This product contains a button cell or coin battery.</p>

<p class="native-trademark">※ USB Type-C<sup>®</sup> and USB-C<sup>®</sup> are registered trademarks of USB Implementers Forum.</p>

<span id="native-ess-battery"></span>

### <span class="hb-heading-title">Jackery Battery Pack 5000 Plus</span> <span class="hb-heading-model">Model: JBP-5000A</span>

<h4 class="hb-heading-label-pair"><span class="hb-heading-title">SPECIFICATIONS</span> <span class="hb-sold-separately">SOLD SEPARATELY</span></h4>

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JBP-5000A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacity</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cell Chemistry</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 81.57 lbs/37 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">16.5 x 13.5 x 13.2 in/41.8 x 34.4 x 33.6 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cycle Life</th><td class="manual-spec-value hb-spec-value">4000 cycles to 70%+ capacity</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">2600A/5ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ingress Protection</th><td class="manual-spec-value hb-spec-value">IP20</td></tr></tbody></table></figure>

<p>Only use together with Jackery Explorer 5000 Plus and Jackery HomePower 5000 Plus.</p>

<h2 class="hb-spec-group">INPUT/OUTPUT PORTS</h2>

<figure aria-label="INPUT/OUTPUT PORTS" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Input)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓41A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">DC Expansion Port (Output)</th><td class="manual-spec-value hb-spec-value">80.5V-126V⎓98A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">ENVIRONMENTAL OPERATING TEMPERATURE</h2>

<figure aria-label="ENVIRONMENTAL OPERATING TEMPERATURE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Charging Temperature</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Discharging Temperature</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>INGESTION HAZARD:</strong> This product contains a button cell or coin battery.</p>

<span id="native-ess-sts"></span>

### <span class="hb-heading-title">Jackery Smart Transfer Switch</span> <span class="hb-heading-model">Model: JA-TS02A</span>

<h4 class="hb-heading-label-pair"><span class="hb-heading-title">SPECIFICATIONS</span> <span class="hb-sold-separately">SOLD SEPARATELY</span></h4>

<h2 class="hb-spec-group">GENERAL INFO</h2>

<figure aria-label="GENERAL INFO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Product Name</th><td class="manual-spec-value hb-spec-value">Jackery Smart Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Model No.</th><td class="manual-spec-value hb-spec-value">JA-TS02A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">AC Voltage (Nominal)</th><td class="manual-spec-value hb-spec-value">120V/240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Feed-In Type</th><td class="manual-spec-value hb-spec-value">Split Phase</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Input Current</th><td class="manual-spec-value hb-spec-value">100A Grid / 60A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Output Current</th><td class="manual-spec-value hb-spec-value">60A Home Load / 33.4A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Input Short-Circuit Current</th><td class="manual-spec-value hb-spec-value">10KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Overvoltage Category</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">≤20ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Enclosure Type (Distribution Panel)</th><td class="manual-spec-value hb-spec-value">NEMA Type 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Number of Load Branches</th><td class="manual-spec-value hb-spec-value">12</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Main Circuit</th><td class="manual-spec-value hb-spec-value">2 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Branch Circuit</th><td class="manual-spec-value hb-spec-value">14 AWG 12 AWG 10 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Communication</th><td class="manual-spec-value hb-spec-value">Wi-Fi and Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Operating Temperature</th><td class="manual-spec-value hb-spec-value">-20°C~40°C (-4°F~104°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">22 x 14.7 x 7.87 in/56 x 37.4 x 20 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Weight</th><td class="manual-spec-value hb-spec-value">About 25.57 lbs/11.6 kg</td></tr></tbody></table></figure>

<p>When using the product, ensure it is connected to a 240V split phase mains voltage.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Note</td><td class="manual-callout-body"><p>SMART HOME BACKUP SYSTEM (AC ESS) About 575.16 lbs/260.89kg</p></td></tr></tbody></table>

<span id="native-ess-package"></span>

### PACKAGE LIST

<div class="native-figure native-package-host native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-host" data-source-fragment-sha256="e63d39190e20a6a734ca5c6224551b3d9d8b7ed42c35b97809e1114130b46888" data-web-base-art-ref="package-host" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-host.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-host.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:88.3063%;--hb-y:40.8534%;--hb-width:1.8037%;--hb-height:1.9358%"><span>Model :JHP-5000C</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:82.8007%;--hb-y:66.954%;--hb-width:5.5676%;--hb-height:4.1614%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:82.8123%;--hb-y:69.7345%;--hb-width:5.5441%;--hb-height:2.6155%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:81.0591%;--hb-y:73.9504%;--hb-width:1.9679%;--hb-height:2.2318%"><span><strong>CONTACT</strong> <strong>US</strong> <strong>:</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:82.0062%;--hb-y:75.4368%;--hb-width:4.9025%;--hb-height:3.224%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:87.9669%;--hb-y:75.6069%;--hb-width:1.7489%;--hb-height:1.9376%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:87.9669%;--hb-y:76.4927%;--hb-width:1.6781%;--hb-height:1.9376%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:5.6434%;--hb-y:85.5466%;--hb-width:22.8663%;--hb-height:6.8182%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:36.5579%;--hb-y:85.5466%;--hb-width:14.5916%;--hb-height:6.8182%"><span>AC Charging Cable</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:60.6659%;--hb-y:85.5466%;--hb-width:9.7228%;--hb-height:6.8182%"><span>MC4 Wrench</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:80.8997%;--hb-y:85.5466%;--hb-width:9.3466%;--hb-height:6.8182%"><span>User Manual</span></span></div></div></figure></div>

<div class="native-figure native-package-battery native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-battery" data-source-fragment-sha256="b0a1ab1961fad9f87d97c96e34037340be3486009d2ab3d4dc3109e3be0cd944" data-web-base-art-ref="package-battery" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-battery.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-battery.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:68.3587%;--hb-y:17.371%;--hb-width:1.7514%;--hb-height:2.5785%"><span>Model: JBP-5000A</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:77.4329%;--hb-y:28.568%;--hb-width:22.3546%;--hb-height:41.1083%;--hb-fill:#b5b5b6"><span><strong>Sold</strong><br/><strong>separately</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.6267%;--hb-y:47.8592%;--hb-width:5.8832%;--hb-height:5.794%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62.5785%;--hb-y:51.8103%;--hb-width:5.9802%;--hb-height:3.6064%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:61.0952%;--hb-y:60.9681%;--hb-width:1.8815%;--hb-height:2.9684%"><span><strong>CONTACT</strong> <strong>US:</strong></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:62.0277%;--hb-y:62.9249%;--hb-width:4.8308%;--hb-height:4.2754%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:67.8946%;--hb-y:63.1498%;--hb-width:1.7266%;--hb-height:2.5808%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:67.8946%;--hb-y:64.3165%;--hb-width:1.6569%;--hb-height:2.5808%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:5.3679%;--hb-y:77.8993%;--hb-width:23.4174%;--hb-height:9.1241%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:37.2946%;--hb-y:77.8993%;--hb-width:12.7178%;--hb-height:9.1241%"><span>Expansion Cable</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:60.8532%;--hb-y:77.8993%;--hb-width:9.3466%;--hb-height:9.1241%"><span>User Manual</span></span></div></div></figure></div>

<div class="native-figure native-package-sts native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-sts" data-source-fragment-sha256="ffacd2f330861e27c8cca228fb8e89641701410eced1838ee6a1776b12cc680a" data-web-base-art-ref="package-sts" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-sts.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-sts.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:36.2332%;--hb-y:13.044%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:38.0496%;--hb-y:13.044%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:36.2332%;--hb-y:13.7158%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:38.0496%;--hb-y:13.7158%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:33.6805%;--hb-y:14.1468%;--hb-width:1.2332%;--hb-height:1.8075%"><span>Upward</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:33.2147%;--hb-y:15.2528%;--hb-width:1.4638%;--hb-height:1.6669%"><span>A scale of 1:1</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:33.2147%;--hb-y:15.9609%;--hb-width:1.1306%;--hb-height:1.6669%"><span>Unit: mm</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:74.8015%;--hb-y:19.2038%;--hb-width:1.8751%;--hb-height:1.6443%"><span>Model: JA-TS02A</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:83.6797%;--hb-y:31.5173%;--hb-width:5.5775%;--hb-height:3.6757%"><span>Quick Guide</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:82.8589%;--hb-y:34.0699%;--hb-width:7.4119%;--hb-height:2.6681%"><span>HomePower Energy System</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:71.4968%;--hb-y:34.4851%;--hb-width:1.258%;--hb-height:1.367%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:71.0365%;--hb-y:36.0645%;--hb-width:0.4048%;--hb-height:1.2415%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:71.4591%;--hb-y:36.0645%;--hb-width:0.4368%;--hb-height:1.2415%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:71.919%;--hb-y:36.0645%;--hb-width:0.3964%;--hb-height:1.2415%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:72.3228%;--hb-y:36.0645%;--hb-width:0.4762%;--hb-height:1.2415%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:72.7936%;--hb-y:36.0645%;--hb-width:0.4129%;--hb-height:1.2415%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:15.5947%;--hb-y:36.9324%;--hb-width:2.9591%;--hb-height:1.8464%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:71.8922%;--hb-y:38.571%;--hb-width:0.4928%;--hb-height:1.2415%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:71.7996%;--hb-y:38.7278%;--hb-width:0.6728%;--hb-height:1.2415%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:69.0447%;--hb-y:41.1791%;--hb-width:6.1448%;--hb-height:3.577%"><span>USER MANUAL</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:14.2886%;--hb-y:41.4556%;--hb-width:0.5584%;--hb-height:1.4916%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:15.4943%;--hb-y:41.4556%;--hb-width:0.6481%;--hb-height:1.4916%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:16.8072%;--hb-y:41.4556%;--hb-width:0.5349%;--hb-height:1.4916%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:17.96%;--hb-y:41.4556%;--hb-width:0.7593%;--hb-height:1.4916%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:19.3042%;--hb-y:41.4556%;--hb-width:0.5806%;--hb-height:1.4916%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:69.0447%;--hb-y:43.6665%;--hb-width:6.145%;--hb-height:2.26%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:67.5802%;--hb-y:47.5444%;--hb-width:1.3788%;--hb-height:1.6614%"><span><strong>Contact</strong> <strong>us:</strong></span></span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:67.5802%;--hb-y:48.0908%;--hb-width:1.9922%;--hb-height:1.6443%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="28" style="--hb-x:74.4355%;--hb-y:48.6092%;--hb-width:2.2612%;--hb-height:1.6443%"><span>Version: JAK-UM-V1.0</span></span><span class="hb-reference-live-label" data-source-line="29" style="--hb-x:67.5802%;--hb-y:48.6306%;--hb-width:2.111%;--hb-height:1.6443%"><span>1-888-502-2236(US)</span></span><span class="hb-reference-live-label" data-source-line="30" style="--hb-x:16.7301%;--hb-y:48.6397%;--hb-width:0.806%;--hb-height:1.4916%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="31" style="--hb-x:36.2329%;--hb-y:48.6631%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="32" style="--hb-x:38.0496%;--hb-y:48.6631%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="33" style="--hb-x:16.4664%;--hb-y:49.0886%;--hb-width:1.3127%;--hb-height:1.4916%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="34" style="--hb-x:36.2332%;--hb-y:49.4683%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="35" style="--hb-x:38.0496%;--hb-y:49.4683%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="36" style="--hb-x:5.9667%;--hb-y:57.826%;--hb-width:22.2194%;--hb-height:5.5228%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="37" style="--hb-x:29.7735%;--hb-y:57.826%;--hb-width:16.2381%;--hb-height:5.5228%"><span>Marking-off Template</span></span><span class="hb-reference-live-label" data-source-line="38" style="--hb-x:48.4875%;--hb-y:57.826%;--hb-width:15.1055%;--hb-height:5.5228%"><span>Power Input/Output</span></span><span class="hb-reference-live-label" data-source-line="39" style="--hb-x:67.4454%;--hb-y:57.826%;--hb-width:9.3466%;--hb-height:5.5228%"><span>User Manual</span></span><span class="hb-reference-live-label" data-source-line="40" style="--hb-x:81.7039%;--hb-y:57.826%;--hb-width:9.3724%;--hb-height:5.5228%"><span>Quick Guide</span></span><span class="hb-reference-live-label" data-source-line="41" style="--hb-x:53.8366%;--hb-y:62.2443%;--hb-width:4.8078%;--hb-height:5.5228%"><span>Cable</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="42" style="--hb-x:77.4329%;--hb-y:64.962%;--hb-width:22.3546%;--hb-height:24.8829%;--hb-fill:#b5b5b6"><span><strong>Sold</strong><br/><strong>separately</strong></span></span><span class="hb-reference-live-label" data-source-line="43" style="--hb-x:32.6726%;--hb-y:86.2772%;--hb-width:10.9308%;--hb-height:5.5228%"><span>2*Wall Bracket</span></span><span class="hb-reference-live-label" data-source-line="44" style="--hb-x:52.5813%;--hb-y:86.2772%;--hb-width:21.6818%;--hb-height:5.5228%"><span>4*M4 Phillips Flat Head Screw</span></span><span class="hb-reference-live-label" data-source-line="45" style="--hb-x:12.1587%;--hb-y:86.2796%;--hb-width:9.4539%;--hb-height:5.5228%"><span>Circuit Label</span></span><span class="hb-reference-live-label" data-source-line="46" style="--hb-x:46.4234%;--hb-y:90.9421%;--hb-width:33.9975%;--hb-height:4.4183%"><span>(secure wall brackets to Smart Transfer Switch)</span></span></div></div></figure></div>

<div class="native-contact-card" id="native-contact"><p class="native-contact-company"><strong>JACKERY INC.</strong></p><p class="native-contact-address">5310 Bunche Dr., Fremont, CA 94538-8301</p><div class="native-contact-row"><div class="native-contact-panel"><p class="native-contact-phone"><img alt="" class="native-contact-glyph" src="assets/contact-phone.svg"/><strong>1-888-502-2236</strong> <span class="native-contact-region">(US)</span></p><div class="native-contact-links"><p class="native-contact-email"><img alt="" class="native-contact-glyph" src="assets/contact-mail.svg"/>hello@jackery.com</p><p class="native-contact-web"><img alt="" class="native-contact-glyph" src="assets/contact-web.svg"/>www.jackery.com</p></div></div><div class="native-contact-qr"><img alt="" src="assets/contact-qr.svg"/></div></div></div>
