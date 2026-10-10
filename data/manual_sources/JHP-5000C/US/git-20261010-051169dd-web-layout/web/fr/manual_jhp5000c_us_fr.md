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

/* The risk banner is one outlined box with the filled warning triangle. */
#furo-main-content .hb-source-safety-heading {
  display: flex;
  align-items: center;
  gap: 0.7rem;
  max-width: var(--hb-component-band-max);
  margin: 1.1rem 0 0.9rem;
  padding: 0.55rem 0.85rem;
  border: 2px solid var(--hb-brand-dark);
  border-radius: var(--hb-panel-radius);
}
#furo-main-content .hb-source-safety-heading > img { flex: 0 0 auto; width: 2.4rem !important; height: auto; margin: 0 !important; }
#furo-main-content .hb-source-safety-heading > p { margin: 0; line-height: 1.3; }

/* WARNING: icon panel in reverse; DANGER: outlined white panel. Both bodies print bold. */
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
#furo-main-content table.native-lockup-inverse .manual-callout-label {
  background: var(--hb-brand-dark) !important;
  color: var(--hb-paper);
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

<h1 class="hb-preface-heading" id="native-preface"><span class="hb-preface-region">FR</span> IMPORTANT</h1>

<div class="hb-preface-prose"><p>Félicitations d’avoir fait l’acquisition du nouveau Jackery HomePower 5000 Plus. Veuillez lire attentivement ce manuel avant d’utiliser le dispositif, en particulier les précautions à prendre afin de garantir une bonne utilisation.</p><p>Conservez ce manuel dans un endroit accessible pour pouvoir vous y référer fréquemment.</p><p>Conformément aux lois et réglementations, le droit d’interprétation finale de ce document et de tous les documents relatifs à ce produit appartient à l’entreprise.</p><p>Veuillez noter qu’aucune autre notification ne sera donnée en cas de mise à jour, de révision ou de résiliation.</p></div>

<span id="native-safety"></span>

## INSTRUCTIONS DE SÉCURITÉ IMPORTANTES

<div class="hb-source-safety-heading"><img alt="" src="assets/warning_triangle_dark.svg"/><p><strong>INSTRUCTIONS RELATIVES AUX RISQUES D'INCENDIE, DE CHOC ÉLECTRIQUE OU DE BLESSURE CORPORELLE</strong></p></div>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-inverse"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/warning_triangle_white.svg"/>ATTENTION</span></td><td class="manual-callout-body"><p><strong>En utilisation ce produit, il est nécessaire de suivre certaines précautions de base, y compris</strong></p></td></tr></tbody></table>

<ul><li>Lisez toutes les instructions avant d'utiliser le produit</li><li>Ne laissez pas les enfants jouer sur ou dans le produit. Une surveillance constante des enfants est nécessaire lorsque le produit est utilisé à proximité.</li><li>Évitez de placer les mains ou les doigts à l'intérieur du produit.</li><li>Cessez immédiatement d'utiliser le produit s'il a été physiquement endommagé ou modifié. Une utilisation inappropriée du produit peut entraîner un comportement imprévisible, pouvant provoquer un incendie, une explosion ou des blessures.</li><li>Si l'un des éléments suivants est observé, y compris mais sans s'y limiter : surchauffe, émission d'odeurs inhabituelles ou de fumée, fuites ou brûlures, cessez immédiatement d'utiliser le produit et contactez le revendeur ou notre service clientèle.</li><li>Ne tentez jamais d'ouvrir, de réparer ou de modifier le produit. Toute altération, réassemblage ou modification du produit peut entraîner un choc électrique, un incendie ou des dommages à la batterie.</li><li>Soyez conscient que le liquide éjecté du produit peut provoquer des irritations ou des brûlures. Une utilisation inappropriée ou abusive peut entraîner des fuites de batterie. Évitez tout contact direct en cas de fuite. Si le liquide entre en contact avec vos yeux, consultez immédiatement un médecin. S'il entre en contact avec d'autres parties du corps, rincez à l'eau courante et consultez un professionnel de la santé sans délai.</li><li>N'exposez pas le produit au feu ou à des températures excessives. Cela pourrait entraîner une explosion si la température dépasse 130 °C (265 °F).</li><li>Toute utilisation de matériaux ou de pièces non recommandés ou non fournis avec le produit peut entraîner un risque d'incendie, de choc électrique ou de blessure.</li><li>Ne laissez pas la batterie se charger sans surveillance pendant de longues périodes. Surveillez toujours le processus de charge pour garantir un fonctionnement sûr.</li><li>Pour réduire le risque de choc électrique, débranchez le produit de toute source d'alimentation avant d'effectuer tout service technique ou dépannage.</li></ul>

### <span class="native-band">NOTICE D’UTILISATION</span>

<p><strong>CONSERVEZ CES CONSIGNES</strong></p>

<ul><li>Cessez immédiatement d'utiliser le produit s'il présente des signes de dommages. Cessez de l'utiliser et contactez le service à la clientèle pour obtenir de l'aide.</li><li>Ne chargez pas la batterie dans des environnements extrêmement chauds ou froids et respectez strictement les plages de température de fonctionnement spécifiées du produit :<ul><li>Température de charge : 32°F à 113°F (0°C à 45°C) ;</li><li>Température de décharge : 5°F à 113°F (-15°C à 45°C);</li></ul></li><li>Pour assurer une circulation d'air adéquate, maintenez les orifices de ventilation du produit dégagés. L'endroit où le produit est utilisé doit avoir un flux d'air adéquat dans un environnement frais et sec pour éviter la surchauffe.<ul><li>La charge dans des espaces humides ou mal ventilés peut entraîner des risques pour la sécurité.</li><li>L'eau peut provoquer des courts-circuits ou endommager le chargeur, entraînant des risques pour la sécurité.</li></ul></li><li>Débranchez le cordon d'alimentation de la prise de courant pendant un orage.</li><li>Éteignez immédiatement le produit en appuyant sur le bouton d'alimentation s'il est tombé, a été heurté ou exposé à des vibrations.</li><li>Assurez-vous que l'appareil ou les appareils sont éteints avant de les connecter au produit.</li><li>Ne chargez pas le produit en utilisant un cordon ou une fiche d’alimentation endommagé ou cassé.</li><li>N'utilisez pas le produit pour charger un appareil avec un câble ou une fiche endommagé ou cassé.</li><li>Débranchez toujours le cordon de charge en tirant sur la fiche, pas sur le cordon, pour réduire le risque de dommages.</li><li>Assurez-vous que le produit est correctement sécurisé lors de son transport dans un véhicule en mouvement.</li><li>NE PAS placer l'unité à l'envers ou sur le côté pendant son utilisation ou son stockage.</li><li>NE PAS placer le produit sur le sol ou à une hauteur inférieure à 18 pouces (457 mm) au-dessus du sol lorsqu'il est utilisé dans un atelier ou une installation de réparation.</li><li>NE PAS utiliser les accessoires du produit avec d'autres appareils ou équipements.</li><li>La durée de la recharge à l’énergie solaire dépend des conditions météorologiques. Placer le panneau solaire à un endroit où il recevra autant de lumière du soleil que possible.</li></ul>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup native-lockup-outlined"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/warning_triangle_dark.svg"/>DANGER</span></td><td class="manual-callout-body"><p><strong>Este dispositivo está diseñado únicamente para uso en interiores (si se utiliza en exteriores, colóquelo en un entorno similar a un interior, por ejemplo: casas rodantes, tiendas de campaña, cabañas, etc.).</strong><br/><strong>※ Este dispositivo no es resistente al agua ni al polvo. Manténgalo alejado de la lluvia y de ambientes húmedos durante su uso.</strong></p></td></tr></tbody></table>

<span id="native-maintenance"></span>

### <span class="native-band">INSTRUCTIONS D'ENTRETIEN POUR L'UTILISATEUR</span>

<p>Au cours du cycle d'utilisation des produits de stockage d'énergie, une certaine dégradation de la capacité et de l'énergie se produira. À mesure que le nombre de cycles d'utilisation augmente et que la durée de stockage s'allonge, cette dégradation s'intensifiera progressivement, ce qui est un phénomène normal conforme au modèle de vieillissement naturel des cellules de batterie.</p>

<span id="native-symbols"></span>

### <span class="native-band">SIGNIFICATION DES SYMBOLES</span>

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbole</th><th class="hb-symbol-signal-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="MISE EN GARDE" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">MISE EN GARDE</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="AVERTISSEMENT" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">AVERTISSEMENT</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures corporelles et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="Remarque" class="hb-signal-badge"><span class="hb-signal-label">Remarque</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des dommages à l'équipement, une perte de données, une détérioration des performances ou des résultats inattendus.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Symboles d'avertissement et de mise en garde. Doivent être lus pour alerter les utilisateurs de dangers ou de risques potentiels." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Symboles d'avertissement et de mise en garde. Doivent être lus pour alerter les utilisateurs de dangers ou de risques potentiels.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole de danger de choc électrique pour avertissement de danger électrique." class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Symbole de danger de choc électrique pour avertissement de danger électrique.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole de charge de batterie indiquant qu'une batterie est en cours de charge." class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Symbole de charge de batterie indiquant qu'une batterie est en cours de charge.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole de matériau explosif pour avertissement de risque d'explosion." class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Symbole de matériau explosif pour avertissement de risque d'explosion.</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Symbole d'objet lourd pour précautions de manutention." class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Symbole d'objet lourd pour précautions de manutention.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole de non-fumeur ou de flamme nue pour prévenir les risques d'incendie." class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Symbole de non-fumeur ou de flamme nue pour prévenir les risques d'incendie.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole d’interdiction d’accès aux enfants pour prévenir les risques de sécurité." class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Symbole d’interdiction d’accès aux enfants pour prévenir les risques de sécurité.</td></tr><tr><td class="hb-symbol-icon"><img alt="Symbole de lecture du manuel pour une utilisation sécuritaire." class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Symbole de lecture du manuel pour une utilisation sécuritaire.</td></tr></tbody></table></div></div></figure>

<div class="native-fcc-panel" id="native-fcc"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"></div></div></div><p><strong>REMARQUE :</strong> Cet équipement a été testé et déclaré conforme aux limites concernant les appareils numériques de classe B, conformément à la partie 15 du règlement de la FCC. Ces limites sont conçues pour offrir une protection raisonnable contre les interférences dangereuses dans le cadre d'une installation résidentielle. Cet équipement génère, utilise et émet des ondes radios qui peuvent, si cet équipement n'est pas installé et utilisé conformément aux instructions, perturber les communications radios. Toutefois, il n'y a aucune garantie qu'aucune interférence ne se produise lors d'une installation particulière. Si cet équipement trouble la réception de la radio ou de la télévision, ce qui peut être déterminé en éteignant et en allumant cet équipement, l'utilisateur est encouragé à tenter de corriger ces interférences en essayant une ou plusieurs des mesures suivantes :</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Réorientez ou déplacez l'antenne de réception.</p></li><li><p>Éloignez l'équipement du récepteur.</p></li><li><p>Connectez l'équipement à une prise d'un autre circuit que celui auquel le récepteur est connecté.</p></li><li><p>Consultez le revendeur ou bien demandez de l'aide à un technicien de radio/télévision expérimenté.</p></li></ul><p><strong>MODIFICATION:</strong> Tout changement ou modification non expressément approuvé par le titulaire de cet appareil pourrait annuler l'autorisation de l'utilisateur à utiliser l'appareil.</p></div></div></figure></div>

<span id="native-inbox"></span>

## CONTENU DE LA BOÎTE

<figure aria-label="CONTENU DE LA BOÎTE" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 5000 Plus" class="hb-inbox-art" src="assets/inbox-main.svg"/><div class="hb-inbox-label"><p>Jackery HomePower 5000 Plus</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Câble de chargement CA" class="hb-inbox-art" src="assets/inbox-cable.png"/><div class="hb-inbox-label"><p>Câble de chargement CA</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Clé MC4" class="hb-inbox-art" src="assets/inbox-mc4.svg"/><div class="hb-inbox-label"><p>Clé MC4</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Manuel d’utilisation" class="hb-inbox-art" src="assets/inbox-manual.svg"/><div class="hb-inbox-label"><p>Manuel d’utilisation</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">Remarque</div><div class="hb-inbox-tip-body">Le câble de chargement pour voiture n’est pas inclus, mais peut être acheté séparément sur notre site Web. Pour obtenir de l’aide, veuillez contacter le service à la clientèle de Jackery.</div></div></figure>

<span id="native-overview"></span>

## APERÇU DU PRODUIT

### VUE DE FACE

<div class="native-figure native-overview-front native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="99e330a7d8bb339390444f70d8c210bbaf5a5e035484b8776b2c06f61712ac25" data-web-base-art-ref="overview-front" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-front.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-front-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.5137%;--hb-y:1.9236%;--hb-width:4.447%;--hb-height:4.4393%"><span><strong>LCD</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:65.3487%;--hb-y:2.4524%;--hb-width:33.9225%;--hb-height:4.4393%"><span class="native-edge-right"><strong>Bouton</strong> <strong>d’alimentation</strong> <strong>principale</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.5137%;--hb-y:12.2035%;--hb-width:7.6401%;--hb-height:4.4393%"><span><strong>Bouton</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:85.5228%;--hb-y:13.2245%;--hb-width:13.7477%;--hb-height:4.4393%"><span class="native-edge-right"><strong>Sortie</strong> <strong>USB-C</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.5137%;--hb-y:15.6974%;--hb-width:18.9174%;--hb-height:4.4393%"><span><strong>d’alimentation</strong> <strong>CC</strong></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:91.357%;--hb-y:17.1462%;--hb-width:7.8486%;--hb-height:3.2751%"><span class="native-edge-right">100W Max</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:85.7194%;--hb-y:30.8835%;--hb-width:13.5516%;--hb-height:4.4393%"><span class="native-edge-right"><strong>Sortie</strong> <strong>USB-A</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:92.4643%;--hb-y:34.5851%;--hb-width:6.7413%;--hb-height:3.2751%"><span class="native-edge-right">18W Max</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5137%;--hb-y:36.6424%;--hb-width:19.6151%;--hb-height:4.4393%"><span><strong>Port</strong> <strong>allume-cigare</strong></span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:91.6307%;--hb-y:38.4704%;--hb-width:7.6401%;--hb-height:4.4393%"><span class="native-edge-right"><strong>Bouton</strong></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.5137%;--hb-y:40.8086%;--hb-width:6.4352%;--hb-height:4.4738%"><span>12V⎓10A</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:79.4724%;--hb-y:41.9642%;--hb-width:19.7984%;--hb-height:4.4393%"><span class="native-edge-right"><strong>d’alimentation</strong> <strong>USB</strong></span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:78.1651%;--hb-y:48.8542%;--hb-width:10.0293%;--hb-height:4.4393%"><span><strong>Sortie</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:88.288%;--hb-y:49.2536%;--hb-width:11.0492%;--hb-height:3.8332%"><span class="native-edge-right">(NEMA 5-20)</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:90.387%;--hb-y:53.107%;--hb-width:8.6716%;--hb-height:3.0655%"><span class="native-edge-right">1 x Sortie CA:</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:0.5137%;--hb-y:55.2184%;--hb-width:7.6401%;--hb-height:4.4393%"><span><strong>Bouton</strong></span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:87.2769%;--hb-y:55.8148%;--hb-width:11.782%;--hb-height:3.0655%"><span class="native-edge-right">120V, 20A, 2400W</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:88.1586%;--hb-y:58.5225%;--hb-width:10.9003%;--hb-height:3.0655%"><span class="native-edge-right">Total Sorties CA:</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:0.5137%;--hb-y:58.7123%;--hb-width:18.7979%;--hb-height:4.4393%"><span><strong>d’alimentation</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:77.9865%;--hb-y:61.2303%;--hb-width:21.0724%;--hb-height:3.0655%"><span class="native-edge-right">7200W max, surtension 14400W</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:87.4681%;--hb-y:79.1616%;--hb-width:11.2496%;--hb-height:3.8987%"><span class="native-edge-right"><strong>Sortie</strong> <strong>totale</strong></span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:0.7229%;--hb-y:79.9331%;--hb-width:11.2497%;--hb-height:3.8987%"><span><strong>Sortie</strong> <strong>totale</strong></span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:81.4641%;--hb-y:82.3276%;--hb-width:16.8595%;--hb-height:3.2751%"><span class="native-edge-right">120V, 30A, 3600W Max,</span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:0.7229%;--hb-y:83.0991%;--hb-width:16.8595%;--hb-height:3.2751%"><span>120V, 30A, 3600W Max,</span></span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:83.9956%;--hb-y:85.0351%;--hb-width:14.3283%;--hb-height:3.2751%"><span class="native-edge-right">Crête de surtension</span></span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:0.7229%;--hb-y:85.8065%;--hb-width:14.3282%;--hb-height:3.2751%"><span>Crête de surtension</span></span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:90.9972%;--hb-y:87.7425%;--hb-width:7.7208%;--hb-height:3.2751%"><span class="native-edge-right">de 7200W</span></span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:0.7229%;--hb-y:88.5139%;--hb-width:7.7208%;--hb-height:3.2751%"><span>de 7200W</span></span></div></div></figure></div>

### VUE LATÉRALE GAUCHE

<div class="native-figure native-overview-left native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="8d433884f40b1346fe041b6bc3655b8f0ac34724336da74f312b88391bc73ea0" data-web-base-art-ref="overview-left" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-left.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-left-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.6078%;--hb-y:0.8242%;--hb-width:8.6159%;--hb-height:4.7505%"><span><strong>Poignée</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.6078%;--hb-y:8.1798%;--hb-width:20.386%;--hb-height:4.7505%"><span><strong>Port</strong> <strong>d’extension</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.6081%;--hb-y:12.3741%;--hb-width:31.6063%;--hb-height:4.1019%"><span>Connexion au Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.6078%;--hb-y:15.6166%;--hb-width:26.685%;--hb-height:3.6729%"><span>Entrée : 240 V, 16,7 A max., 4000 W</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.6078%;--hb-y:18.5143%;--hb-width:21.1124%;--hb-height:3.6729%"><span>Sortie : 240 V, 30 A, 7200 W</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.5372%;--hb-y:24.6266%;--hb-width:32.8379%;--hb-height:4.7505%"><span><strong>Port</strong> <strong>de</strong> <strong>sortie</strong> <strong>CA</strong> <strong>NEMA</strong> <strong>L14-30R</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.538%;--hb-y:28.3807%;--hb-width:25.1312%;--hb-height:4.1019%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.5376%;--hb-y:32.3513%;--hb-width:58.9084%;--hb-height:3.6729%"><span>Alimente des appareils à forte puissance et se connecte à une boîte d’entrée</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.5376%;--hb-y:35.2489%;--hb-width:56.6859%;--hb-height:3.6729%"><span>ou à un commutateur de transfert manuel pour l’alimentation domestique.</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.5372%;--hb-y:46.2284%;--hb-width:30.5634%;--hb-height:4.7505%"><span><strong>Port</strong> <strong>de</strong> <strong>sortie</strong> <strong>CA</strong> <strong>NEMA</strong> <strong>14-50</strong></span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.538%;--hb-y:50.4124%;--hb-width:25.1312%;--hb-height:4.1019%"><span>120V/240V, 30A, 7200W Max</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.7936%;--hb-y:54.5069%;--hb-width:58.9075%;--hb-height:3.6729%"><span>Alimente des appareils à forte puissance et se connecte à une boîte d’entrée</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.7936%;--hb-y:57.4045%;--hb-width:56.6856%;--hb-height:3.6729%"><span>ou à un commutateur de transfert manuel pour l’alimentation domestique.</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.6078%;--hb-y:63.1831%;--hb-width:36.2557%;--hb-height:4.7505%"><span><strong>Sortie</strong> <strong>CA</strong> <strong>Bouton</strong> <strong>de</strong> <strong>réinitialisation</strong></span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.6078%;--hb-y:67.5549%;--hb-width:53.7839%;--hb-height:3.6729%"><span>Lorsque le bouton de réinitialisation saute, vous devez retirer la charge</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:0.6078%;--hb-y:70.4526%;--hb-width:33.4799%;--hb-height:3.6729%"><span>et appuyer sur le bouton pour le réinitialiser.</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:0.6078%;--hb-y:76.8168%;--hb-width:13.6905%;--hb-height:4.7505%"><span><strong>Frein</strong> <strong>de</strong> <strong>roue</strong></span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:0.6078%;--hb-y:85.3901%;--hb-width:6.4675%;--hb-height:4.7505%"><span><strong>Roues</strong></span></span></div></div></figure></div>

### VUE LATÉRALE DROITE

<div class="native-figure native-overview-right native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-right" data-source-fragment-sha256="2203b359fa839105a85e71a404b9f2f3dd77178881a76f453cf5da4d4db3eb3f" data-web-base-art-ref="overview-right" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview-right.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview-right.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:0.4689%;--hb-y:14.119%;--hb-width:20.7062%;--hb-height:3.8218%"><span><strong>Poignée</strong> <strong>rétractable</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:0.4689%;--hb-y:17.5926%;--hb-width:50.7822%;--hb-height:2.8195%"><span>Appuyez sur le bouton de la poignée rétractable et tirez pour l’étendre</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:0.4689%;--hb-y:22.9174%;--hb-width:23.5987%;--hb-height:3.8218%"><span><strong>Entrée</strong> <strong>PV</strong> <strong>faible</strong> <strong>(8020)</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:0.4689%;--hb-y:26.2457%;--hb-width:47.9683%;--hb-height:3.8515%"><span>2 x ports 8mm CC ; 16V-60V⎓10,5A max, double à 21A/1200W max</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:0.4689%;--hb-y:28.5765%;--hb-width:45.765%;--hb-height:3.8515%"><span>11V-16V (tension de fonctionnement)⎓8A max, double à 8A max</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:0.4689%;--hb-y:36.4226%;--hb-width:24.0715%;--hb-height:3.8218%"><span><strong>Entrée</strong> <strong>PV</strong> <strong>élevée</strong> <strong>(MC4)</strong></span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:0.4689%;--hb-y:39.6855%;--hb-width:24.7473%;--hb-height:3.8515%"><span>135V-450V⎓15A Max, 4000W Max</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:0.4689%;--hb-y:44.1542%;--hb-width:23.1796%;--hb-height:3.8218%"><span><strong>Interrupteur</strong> <strong>PV</strong> <strong>élevée</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:0.4689%;--hb-y:47.8622%;--hb-width:30.6686%;--hb-height:2.8195%"><span>Mettre l'interrupteur sur marche/arrêt pour</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:0.4689%;--hb-y:50.193%;--hb-width:32.4957%;--hb-height:2.8195%"><span>activer/désactiver la charge solaire PV élevé</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.4689%;--hb-y:55.1489%;--hb-width:10.5174%;--hb-height:3.8218%"><span><strong>Entrée</strong> <strong>CA</strong></span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:0.4689%;--hb-y:58.96%;--hb-width:10.0615%;--hb-height:2.8195%"><span>120V, 15A Max</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:0.4689%;--hb-y:67.62%;--hb-width:29.0927%;--hb-height:3.8218%"><span><strong>Port</strong> <strong>d’extension</strong> <strong>CC</strong> <strong>Borne</strong> <strong>A</strong></span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:0.4689%;--hb-y:71.0126%;--hb-width:22.5694%;--hb-height:2.8195%"><span>Connexion à l’unité de batterie</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:0.5152%;--hb-y:81.6726%;--hb-width:18.8685%;--hb-height:3.8218%"><span><strong>Poignée</strong> <strong>inférieure</strong></span></span></div></div></figure></div>

<span id="native-lcd"></span>

## ÉCRAN LCD

<div class="native-figure native-lcd-map native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-map" data-source-fragment-sha256="0b53ab70e9b932a0f805f70e0723e3ddea254a435406b8f79754836e488857d9" data-web-base-art-ref="lcd-map" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd-map.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd-map.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:19.6073%;--hb-y:3.5691%;--hb-width:1.4712%;--hb-height:5.4368%"><span>2</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:23.7861%;--hb-y:3.5691%;--hb-width:1.4822%;--hb-height:5.4368%"><span>3</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:27.5267%;--hb-y:3.5691%;--hb-width:1.5922%;--hb-height:5.4368%"><span>4</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:31.5714%;--hb-y:3.5691%;--hb-width:1.5042%;--hb-height:5.4368%"><span>5</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:35.5314%;--hb-y:3.5691%;--hb-width:1.4822%;--hb-height:5.4368%"><span>6</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:59.5039%;--hb-y:3.5691%;--hb-width:1.3942%;--hb-height:5.4368%"><span>7</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:15.6115%;--hb-y:3.5717%;--hb-width:1.0643%;--hb-height:5.4368%"><span>1</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:1.0001%;--hb-y:45.5627%;--hb-width:1.5218%;--hb-height:5.4368%"><span>8</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:96.2797%;--hb-y:45.8982%;--hb-width:2.648%;--hb-height:5.4368%"><span>22</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:96.2358%;--hb-y:57.064%;--hb-width:2.637%;--hb-height:5.4368%"><span>23</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:0.9099%;--hb-y:57.6012%;--hb-width:1.4822%;--hb-height:5.4368%"><span>9</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:15.2495%;--hb-y:92.2644%;--hb-width:2.516%;--hb-height:5.4368%"><span>10</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:19.9667%;--hb-y:92.2644%;--hb-width:1.8781%;--hb-height:5.4368%"><span>11</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:25.1465%;--hb-y:92.2644%;--hb-width:2.285%;--hb-height:5.4368%"><span>12</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:31.6944%;--hb-y:92.2644%;--hb-width:2.296%;--hb-height:5.4368%"><span>13</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:37.1421%;--hb-y:92.2644%;--hb-width:2.406%;--hb-height:5.4368%"><span>14</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:43.0068%;--hb-y:92.2644%;--hb-width:2.318%;--hb-height:5.4368%"><span>15</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:48.0861%;--hb-y:92.2644%;--hb-width:2.296%;--hb-height:5.4368%"><span>16</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:52.5054%;--hb-y:92.2644%;--hb-width:2.208%;--hb-height:5.4368%"><span>17</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:60.647%;--hb-y:92.2644%;--hb-width:2.3356%;--hb-height:5.4368%"><span>18</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:70.9378%;--hb-y:92.2644%;--hb-width:2.252%;--hb-height:5.4368%"><span>19</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:75.3072%;--hb-y:92.2644%;--hb-width:2.8569%;--hb-height:5.4368%"><span>20</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:80.8328%;--hb-y:92.2644%;--hb-width:2.241%;--hb-height:5.4368%"><span>21</span></span></div></div></figure></div>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><span class="native-lcd-number">1</span></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/lcd-native-01.svg"/></td><td class="hb-lcd-name">Wi-Fi</td><td class="hb-lcd-description"><strong>Activé</strong> : connexion Wi-Fi établie.<br/><strong>Clignotant</strong> : prêt à se connecter au Wi-Fi.<br/><strong>Désactivé</strong> : Wi-Fi non connecté.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">2</span></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/lcd-native-02.svg"/></td><td class="hb-lcd-name">Bluetooth</td><td class="hb-lcd-description"><strong>Activé</strong> : connexion Bluetooth établie.<br/><strong>Clignotant</strong> : prêt à se connecter au Bluetooth.<br/><strong>Désactivé</strong> : Bluetooth non connecté.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">3</span></td><td class="hb-lcd-icon"><img alt="Mode de charge silencieuse Peut être activé / désactivé via l’application Jackery." class="hb-lcd-icon-art" src="assets/lcd-native-03.svg"/></td><td class="hb-lcd-name">Mode de charge silencieuse<br/><span class="native-lcd-note">Peut être activé / désactivé via l’application Jackery.</span></td><td class="hb-lcd-description"><strong>Activé</strong> : le bruit pendant la charge est considérablement réduit, tandis que la puissance de charge diminue et la vitesse de charge ralentit.<br/><strong>Désactivé</strong> : mode de charge silencieuse désactivé.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">4</span></td><td class="hb-lcd-icon"><img alt="Mode économie de batterie Peut être activé / désactivé via l’application Jackery." class="hb-lcd-icon-art" src="assets/lcd-native-04.svg"/></td><td class="hb-lcd-name">Mode économie de batterie<br/><span class="native-lcd-note">Peut être activé / désactivé via l’application Jackery.</span></td><td class="hb-lcd-description"><strong>Activé</strong> : Aide à prolonger la durée de vie de la batterie en limitant sa capacité maximale utilisable.<br/><strong>Désactivé</strong> : mode économie de batterie désactivé.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">5</span></td><td class="hb-lcd-icon"><img alt="Indicateur du plan de charge/décharge Peut être configuré dans l’application Jackery via STS." class="hb-lcd-icon-art" src="assets/lcd-native-05.svg"/></td><td class="hb-lcd-name">Indicateur du plan de charge/décharge<br/><span class="native-lcd-note">Peut être configuré dans l’application Jackery via STS.</span></td><td class="hb-lcd-description">Indique que le produit fonctionne selon le plan de charge/décharge du commutateur de transfert intelligent (STS). Cela se produit uniquement lorsque le produit est connecté avec succès au STS et que le plan de charge/décharge est configuré dans l’application STS.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">6</span></td><td class="hb-lcd-icon"><img alt="Onduleur en ligne Peut être configuré dans l’application Jackery." class="hb-lcd-icon-art" src="assets/lcd-native-06.svg"/></td><td class="hb-lcd-name">Onduleur en ligne<br/><span class="native-lcd-note">Peut être configuré dans l’application Jackery.</span></td><td class="hb-lcd-description"><strong>Activé</strong> : le produit est en mode ASI en ligne (0 ms).<br/><strong>Désactivé</strong> : mode ASI de secours (par défaut).</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">7</span></td><td class="hb-lcd-icon"><img alt="Témoin de puissance CA" class="hb-lcd-icon-art" src="assets/lcd-native-07.svg"/></td><td class="hb-lcd-name">Témoin de puissance CA</td><td class="hb-lcd-description">La sortie CA (onde sinusoïdale pure) est activée.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">8</span></td><td class="hb-lcd-icon"><img alt="Puissance d’entrée" class="hb-lcd-icon-art" src="assets/lcd-native-08.svg"/></td><td class="hb-lcd-name">Puissance d’entrée</td><td class="hb-lcd-description">Affiche la puissance d’entrée en watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">9</span></td><td class="hb-lcd-icon"><img alt="Temps de charge restant" class="hb-lcd-icon-art" src="assets/lcd-native-09.svg"/></td><td class="hb-lcd-name">Temps de charge restant</td><td class="hb-lcd-description">Affiche le temps de charge restant.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">10</span></td><td class="hb-lcd-icon"><img alt="Témoin de charge murale CA" class="hb-lcd-icon-art" src="assets/lcd-native-10.svg"/></td><td class="hb-lcd-name">Témoin de charge murale CA</td><td class="hb-lcd-description">Le produit est chargé via l’entrée CA en utilisant le courant du réseau électrique.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">11</span></td><td class="hb-lcd-icon"><img alt="Témoin de charge de voiture" class="hb-lcd-icon-art" src="assets/lcd-native-11.svg"/></td><td class="hb-lcd-name">Témoin de charge de voiture</td><td class="hb-lcd-description">Le produit est chargé via l’entrée PV faible (8020) à l’aide de 12V DC (voiture).</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">12</span></td><td class="hb-lcd-icon"><img alt="Indicateur d'entrée PV élevée" class="hb-lcd-icon-art" src="assets/lcd-native-12.svg"/></td><td class="hb-lcd-name">Indicateur d'entrée PV élevée</td><td class="hb-lcd-description">Le produit est chargé via l’entrée PV élevée (MC4) à l’aide de panneau(x) solaire(s).</td></tr><tr><td class="hb-lcd-icon"><img alt="Indicateur d'entrée PV faible" class="hb-lcd-icon-art" src="assets/lcd-native-13.svg"/></td><td class="hb-lcd-name">Indicateur d'entrée PV faible</td><td class="hb-lcd-description">Le produit est chargé via l’entrée PV faible (8020) à l’aide de panneau(x) solaire(s).</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">13</span></td><td class="hb-lcd-icon"><img alt="Témoin d’expansion CA (En charge) Assurez-vous que le STS est connecté avec succès avant de continuer." class="hb-lcd-icon-art" src="assets/lcd-native-14.svg"/></td><td class="hb-lcd-name">Témoin d’expansion CA (En charge)<br/><span class="native-lcd-note">Assurez-vous que le STS est connecté avec succès avant de continuer.</span></td><td class="hb-lcd-description">Le produit se charge via le STS avec l’alimentation du réseau.</td></tr><tr><td class="hb-lcd-icon"><img alt="Témoin d’expansion CA (En décharge) Assurez-vous que le STS est connecté avec succès avant de continuer." class="hb-lcd-icon-art" src="assets/lcd-native-15.svg"/></td><td class="hb-lcd-name">Témoin d’expansion CA (En décharge)<br/><span class="native-lcd-note">Assurez-vous que le STS est connecté avec succès avant de continuer.</span></td><td class="hb-lcd-description">Le produit alimente les charges domestiques via le STS.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">14</span></td><td class="hb-lcd-icon"><img alt="Témoin de Smart Transfer Switch" class="hb-lcd-icon-art" src="assets/lcd-native-16.svg"/></td><td class="hb-lcd-name">Témoin de Smart Transfer Switch</td><td class="hb-lcd-description">Le produit est connecté avec succès au STS.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">15</span></td><td class="hb-lcd-icon"><img alt="Témoin d’alimentation de batterie" class="hb-lcd-icon-art" src="assets/lcd-native-17.svg"/></td><td class="hb-lcd-name">Témoin d’alimentation de batterie</td><td class="hb-lcd-description">Lorsque le produit est en cours de charge, le cercle orange autour du pourcentage de la batterie s'allume . Lors de la recharge d'autres appareils, le cercle orange restera allumé.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">16</span></td><td class="hb-lcd-icon"><img alt="Témoin de batterie faible" class="hb-lcd-icon-art" src="assets/lcd-native-18.svg"/></td><td class="hb-lcd-name">Témoin de batterie faible</td><td class="hb-lcd-description"><strong>Activé</strong> : le niveau de batterie est inférieur à 20 %.<br/><strong>Clignotant</strong> : le niveau de batterie est inférieur à 5 %.<br/><strong>Désactivé</strong> : le produit est en charge.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">17</span></td><td class="hb-lcd-icon"><img alt="Pourcentage de batterie restante" class="hb-lcd-icon-art" src="assets/lcd-native-19.svg"/></td><td class="hb-lcd-name">Pourcentage de batterie restante</td><td class="hb-lcd-description">Affiche le pourcentage de batterie restant.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">18</span></td><td class="hb-lcd-icon"><img alt="Témoin d’état de batterie et nombre de batteries connectées" class="hb-lcd-icon-art" src="assets/lcd-native-20.svg"/></td><td class="hb-lcd-name">Témoin d’état de batterie et nombre de batteries connectées</td><td class="hb-lcd-description">Indique que le produit est connecté au nombre spécifié de blocs-batterie 5000 Plus.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">19</span></td><td class="hb-lcd-icon"><img alt="Code d’erreur" class="hb-lcd-icon-art" src="assets/lcd-native-21.svg"/></td><td class="hb-lcd-name">Code d’erreur</td><td class="hb-lcd-description">Une erreur de fonctionnement est survenue. Veuillez consulter la section Dépannage pour plus de détails.</td></tr><tr><td class="hb-lcd-number" rowspan="2"><span class="native-lcd-number">20</span></td><td class="hb-lcd-icon"><img alt="Témoin de température élevée" class="hb-lcd-icon-art" src="assets/lcd-native-22.svg"/></td><td class="hb-lcd-name">Témoin de température élevée</td><td class="hb-lcd-description">La protection contre les hautes températures est activée. Le produit peut cesser de fonctionner jusqu’à ce que sa température revienne dans la plage de fonctionnement normale.</td></tr><tr><td class="hb-lcd-icon"><img alt="Témoin de température faible" class="hb-lcd-icon-art" src="assets/lcd-native-23.svg"/></td><td class="hb-lcd-name">Témoin de température faible</td><td class="hb-lcd-description">La protection contre les basses températures est activée. Le produit peut cesser de fonctionner jusqu’à ce que sa température revienne dans la plage de fonctionnement normale.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">21</span></td><td class="hb-lcd-icon"><img alt="Mode économie d’énergie" class="hb-lcd-icon-art" src="assets/lcd-native-24.svg"/></td><td class="hb-lcd-name">Mode économie d’énergie</td><td class="hb-lcd-description">Pour éviter une consommation inutile de batterie en cas d’oubli de désactivation de la sortie, le produit active le mode économie d’énergie par défaut. Si aucun appareil n’est connecté ou si la consommation est inférieure à un certain seuil (sortie CA ≤ 25 W ; sortie USB ≤ 2 W ; sortie voiture ≤ 2 W), l’appareil éteindra automatiquement toutes les sorties après 12 heures. <strong>Activé</strong>/<br/><strong>Désactivé</strong> : Appuyez et maintenez simultanément le bouton d’alimentation CA et le bouton principal.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">22</span></td><td class="hb-lcd-icon"><img alt="Puissance de sortie" class="hb-lcd-icon-art" src="assets/lcd-native-25.svg"/></td><td class="hb-lcd-name">Puissance de sortie</td><td class="hb-lcd-description">Affiche la puissance de sortie en watts.</td></tr><tr><td class="hb-lcd-number"><span class="native-lcd-number">23</span></td><td class="hb-lcd-icon"><img alt="Temps de décharge restant" class="hb-lcd-icon-art" src="assets/lcd-native-26.svg"/></td><td class="hb-lcd-name">Temps de décharge restant</td><td class="hb-lcd-description">Affiche le temps de décharge restant.</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## FONCTIONNEMENT

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Lorsque le mode économie d’énergie est activé, si le bouton d’alimentation de la sortie DC, AC ou USB est activé mais que la station d’énergie ne charge ni ne décharge, elle s’éteindra automatiquement après 12 heures.</p></td></tr></tbody></table>

### MISE SOUS/HORS TENSION

<div class="native-figure native-power native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="e9325fa6ddb75450e0393c25df7a9a4852d25aa1dc5b1c080d439db2f7610b80" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:76.1008%;--hb-y:7.7594%;--hb-width:11.5541%;--hb-height:8.8127%"><span><strong>marche</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.2059%;--hb-y:15.8738%;--hb-width:15.242%;--hb-height:5.5238%"><span>Appuyez une fois</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:76.0084%;--hb-y:24.3499%;--hb-width:7.6561%;--hb-height:8.8127%"><span><strong>arrêt</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:76.2059%;--hb-y:32.0681%;--hb-width:20.0038%;--hb-height:5.5238%"><span>Appuyez et maintenez</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:76.2059%;--hb-y:37.1462%;--hb-width:18.3586%;--hb-height:5.5238%"><span>pendant 3 secondes</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:80.4096%;--hb-y:44.7589%;--hb-width:11.9287%;--hb-height:6.2857%"><span>3 secondes</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="6" style="--hb-x:43.2899%;--hb-y:58.5045%;--hb-width:51.8618%;--hb-height:31.106%;--hb-fill:#f2f2f3"><span><strong>Temps</strong> <strong>de</strong> <strong>veille</strong> <strong>par</strong> <strong>défaut</strong> <strong>:</strong> 2 heures<br/>· Le produit s’éteindra automatiquement après 2 heures<br/>d’inactivité, sans charge ni décharge.<br/>· La durée de veille peut être définie dans l’application<br/>Jackery.</span></span></div></div></figure></div>

### MARCHE/ARRÊT SORTIE CA

<div class="native-figure native-ac-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-output" data-source-fragment-sha256="e49dd2fa27dba02dae0ac3d49c701112429da335423fee6de7bed6e7b3077a7c" data-web-base-art-ref="ac-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-output-fr.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.5175%;--hb-y:4.6091%;--hb-width:73.7538%;--hb-height:6.8057%;--hb-fill:#f2f2f3"><span><strong>Prérequis</strong> <strong>:</strong> Assurez-vous que le bouton d'alimentation principal est activé.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:79.9655%;--hb-y:16.1357%;--hb-width:11.5541%;--hb-height:6.8986%"><span><strong>marche</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:80.1403%;--hb-y:22.3008%;--hb-width:15.242%;--hb-height:4.3241%"><span>Appuyez une fois</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:79.8732%;--hb-y:28.1288%;--hb-width:7.6561%;--hb-height:6.8986%"><span><strong>arrêt</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:79.8766%;--hb-y:34.7988%;--hb-width:15.242%;--hb-height:4.3241%"><span>Appuyez une fois</span></span></div></div></figure></div>

### MARCHE/ARRÊT SORTIE USB

<div class="native-figure native-usb-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="usb-output" data-source-fragment-sha256="c1b6f98edbb729a788a9d31d86e80d94f47ac114e22c7ef8bf8d299cf84789bc" data-web-base-art-ref="usb-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="usb-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/usb-output-fr.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:1.2434%;--hb-y:3.4164%;--hb-width:67.0688%;--hb-height:11.1145%;--hb-fill:#f2f2f3"><span><strong>Prérequis</strong> <strong>:</strong> Assurez-vous que le bouton d'alimentation principal est activé.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:78.6921%;--hb-y:16.5169%;--hb-width:9.307%;--hb-height:10.2004%"><span><strong>marche</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:78.8677%;--hb-y:25.8658%;--hb-width:15.242%;--hb-height:7.7818%"><span>Appuyez une fois</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:78.5979%;--hb-y:33.9409%;--hb-width:6.1885%;--hb-height:10.2004%"><span><strong>arrêt</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:78.604%;--hb-y:42.6208%;--hb-width:15.242%;--hb-height:7.7818%"><span>Appuyez une fois</span></span></div></div></figure></div>

### MARCHE/ARRÊT SORTIE CC

<div class="native-figure native-dc-output native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dc-output" data-source-fragment-sha256="d3e091104bb0fa741b8e6b27b588f7dba5eabf8c894456b7b87a1c01e782c09b" data-web-base-art-ref="dc-output" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="dc-output.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/dc-output-fr.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:1.2434%;--hb-y:3.1095%;--hb-width:67.0688%;--hb-height:11.2148%;--hb-fill:#f2f2f3"><span><strong>Prérequis</strong> <strong>:</strong> Assurez-vous que le bouton d'alimentation principal est activé.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:78.6921%;--hb-y:14.7331%;--hb-width:9.307%;--hb-height:10.2924%"><span><strong>marche</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:78.8677%;--hb-y:24.1664%;--hb-width:15.242%;--hb-height:7.852%"><span>Appuyez une fois</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:78.5979%;--hb-y:32.3144%;--hb-width:6.1885%;--hb-height:10.2924%"><span><strong>arrêt</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:78.604%;--hb-y:41.0726%;--hb-width:15.242%;--hb-height:7.852%"><span>Appuyez une fois</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Le produit peut charger la batterie de votre voiture à l'aide du câble de charge de batterie automobile Jackery 12V, vendu séparément et disponible sur notre site web.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><ul><li>Le port allume-cigare est uniquement compatible avec les batteries de voiture 12V et ne convient pas aux systèmes 24V.</li><li>Ne démarrez pas la voiture pendant que le produit charge la batterie via le port de sortie CC 12V (port allume-cigare), car cela pourrait endommager le produit.</li><li>Cette fonctionnalité est destinée à un usage d'urgence uniquement et ne peut pas charger une batterie de voiture morte ou endommagée.</li></ul></td></tr></tbody></table>

### ÉCRAN LCD

<div class="native-lcd-panel"><figure aria-label="ÉCRAN LCD" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="ÉCRAN LCD" class="hb-lcd-mode-art" src="assets/lcd-button.svg"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">Écran LCD</td><td class="hb-lcd-mode-action">Allumer</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d’alimentation principal ou lorsque le produit est en cours de charge.</td></tr><tr><td class="hb-lcd-mode-action">Éteindre</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d’alimentation principal.</td></tr><tr><td class="hb-lcd-mode-action">Extinction automatique</td><td class="hb-lcd-mode-copy">L’écran LCD s’éteint automatiquement et passe en mode veille après 2 minutes d’inactivité.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Mode d’affichage permanent (en charge ou décharge)</td><td class="hb-lcd-mode-action">Allumer</td><td class="hb-lcd-mode-copy">Double-cliquez sur le bouton d’alimentation principal lorsque l’écran LCD est activé.</td></tr><tr><td class="hb-lcd-mode-action">Éteindre</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d’alimentation principal.</td></tr><tr><td class="hb-lcd-mode-action">Extinction automatique</td><td class="hb-lcd-mode-copy">Le mode d’affichage permanent s’éteindra automatiquement après 2 heures d’inactivité.</td></tr></tbody></table></div></figure></div>

### COMBINAISONS DE TOUCHES

<figure aria-label="Boutons / Utilisation / Fonction" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Boutons</th><th class="hb-key-operation" scope="col">Utilisation</th><th class="hb-key-function" scope="col">Fonction</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Bouton d’alimentation principal</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>Bouton d’alimentation USB</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3 secondes</span><p>Appuyer 3 secondes sur les deux</p></td><td class="hb-key-function">Réinitialiser Wi-Fi &amp; Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-power-bottom.svg"/><p>Bouton d’alimentation principal</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Bouton d’alimentation CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3 secondes</span><p>Appuyer 3 secondes sur les deux</p></td><td class="hb-key-function">Activer/désactiver le mode économie d’énergie</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-usb-bottom.svg"/><p>Bouton d’alimentation USB</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Bouton d’alimentation CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">1 secondes</span><p>Appuyer 1 secondes sur les deux</p></td><td class="hb-key-function">Activer/désactiver le Wi-Fi &amp; Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/button-dc-bottom.svg"/><p>Bouton d’alimentation CC</p></div><span class="hb-key-button-plus"></span><div class="hb-key-button"><img alt="" src="assets/button-ac-bottom.svg"/><p>Bouton d’alimentation CA</p></div></div></td><td class="hb-key-operation"><span class="hb-key-duration" data-duration-icon="clock">3 secondes</span><p>Appuyer 3 secondes sur les deux</p></td><td class="hb-key-function">Basculer entre ASI en ligne ou de secours</td></tr></tbody></table></figure>

<span id="native-troubleshooting"></span>

## DÉPANNAGE

<div class="table-wrapper docutils container"><table class="manual-table native-troubleshooting"><thead><tr><th>Code d'erreur</th><th>Nom</th><th>Description (à des fins d’entretien interne uniquement)</th></tr></thead><tbody><tr><td><strong>F0</strong></td><td><strong>Erreur de communication de données du BMS</strong></td><td>Défaut de communication entre le BMS et la carte mère</td></tr><tr><td><strong>F1</strong></td><td><strong>Erreur de communication de données de l’onduleur</strong></td><td>Défaut de communication entre l’onduleur et la carte mère</td></tr><tr><td><strong>F2</strong></td><td><strong>Erreur de communication de données d’entrée CC</strong></td><td>Défaut de communication entre le module de charge CC et le BMS</td></tr><tr><td><strong>F3</strong></td><td><strong>Défaillance du BMS ou de la batterie</strong></td><td>Défaillance du BMS ou de la batterie</td></tr><tr><td><strong>F4</strong></td><td><strong>Surtension de la batterie</strong></td><td>Surtension de la batterie</td></tr><tr><td><strong>F5</strong></td><td><strong>Sous-tension de la batterie</strong></td><td>Sous-tension de la batterie</td></tr><tr><td><strong>F6</strong></td><td><strong>Défaillance de l’onduleur</strong></td><td>Surcharge / surtension / court-circuit de la sortie CA ;<br/>Surtension / sous-tension / surfréquence / sous-fréquence de l’entrée réseau ;<br/>Protection contre la surchauffe de l’onduleur activée<br/>Défaut de détection d’isolation</td></tr><tr><td><strong>F7</strong></td><td><strong>Défaillance de l’entrée CC</strong></td><td>Surtension d’entrée PV ;<br/>Protection contre la surchauffe du module de charge CC activée/déclenchée ;<br/>Protection contre la surcharge de sortie du module de charge CC activée/déclenchée</td></tr><tr><td><strong>F8</strong></td><td><strong>Surcharge ou court-circuit lors de la charge/décharge de la batterie</strong></td><td>Protection contre surintensité ou court-circuit du BMS activée</td></tr><tr><td><strong>F9</strong></td><td><strong>Surcharge ou court-circuit de la sortie CC</strong></td><td>Protection contre court-circuit USB activée</td></tr><tr><td><strong>FA</strong></td><td><strong>Erreur de communication entre unités en parallèle</strong></td><td>Échec de communication entre deux unités 5000 Plus dû à une panne des deux unités.</td></tr><tr><td><strong>FC</strong></td><td><strong>Erreur de communication avec le bloc-batterie</strong></td><td>Échec de communication entre le 5000 Plus et le(s) bloc(s)-batterie</td></tr></tbody></table></div>

<span id="native-ups"></span>

## ALIMENTATION SANS INTERRUPTION (ASI)

<p>Un onduleur (ou ASI) est un type de système d’alimentation continue qui fournit une alimentation électrique de secours automatisée à une charge en cas de défaillance de l’alimentation principale.</p>

<p>Le HomePower 5000 Plus offre deux modes ASI : secours et en ligne.</p>

### ASI DE SECOURS

<p>Le mode de secours est activé par défaut. En cas de perte soudaine du courant électrique, l’HomePower 5000 Plus basculera automatiquement vers l’alimentation de secours stockée en moins de 20 ms pour maintenir vos appareils en marche.</p>

<p>En mode de secours, la puissance de crête atteint 1440 W avant les coupures. En mode dérivation (Bypass), la charge/décharge simultanée est activée, la puissance de sortie réelle est inférieure à la puissance nominale, mais elle revient à la normale pendant les coupures.</p>

<div class="native-figure native-ups native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups" data-source-fragment-sha256="cfed684eb7c06170ef9ca0d78188ac3eda7474164d72e157711dc924ea6c6bbc" data-web-base-art-ref="ups" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ups.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:37.9791%;--hb-y:69.5854%;--hb-width:56.7344%;--hb-height:22.0072%;--hb-fill:#f2f2f3"><span>Connectez le produit à une prise murale à l’aide du câble de<br/>charge CA, puis appuyez sur le bouton de sortie CA pour<br/>alimenter vos appareils en même temps.</span></span></div></div></figure></div>

### ASI EN LIGNE

<p>Le mode ASI en ligne, qui permet un basculement de 0 ms, peut être activé de deux façons :</p>

<ol><li>Activer le mode ASI en ligne dans l’application Jackery.</li><li>Appuyer simultanément sur les boutons CC et CA du HomePower 5000 Plus.</li></ol>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><ol><li>Les paramètres système reviennent en mode ASI de secours lorsque le produit redémarre en mode en ligne. En mode de secours, la puissance de sortie est limitée par la puissance de dérivation, avec une sortie maximale de 1440 W.</li><li>En mode ASI, les prises NEMA L14-30R et NEMA 14-50 fournissent une sortie 120V lorsqu’elles sont connectées au mur via le câble CA.</li><li>En mode ASI en ligne, il prend en charge un basculement de 0 ms avec une puissance de sortie maximale de 3600 W.</li></ol></td></tr></tbody></table>

<span id="native-connections"></span>

## CONNEXIONS

### <span class="hb-heading-title">CONNEXION À LA BATTERIE</span> <span class="hb-sold-separately">VENDUE SÉPARÉMENT</span>

<p>Ce dispositif peut prendre en charge jusqu’à 5 unités de batteries pour répondre aux besoins d’une grande capacité d’alimentation. Pour plus d’informations sur son utilisation, veuillez vous reporter au manuel d’utilisation du Jackery Battery Pack 5000 Plus.</p>

<div class="native-figure native-battery-packs native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-packs" data-source-fragment-sha256="10565abac666a6552d80850f15f9b9e4e9964ddb84facb746a29a0565519619d" data-web-base-art-ref="battery-packs" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-packs.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/battery-packs-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:24.3721%;--hb-y:91.5134%;--hb-width:20.2849%;--hb-height:5.7097%"><span>au moins 1 pi (300 mm)</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.3501%;--hb-y:91.5134%;--hb-width:20.2849%;--hb-height:5.7097%"><span>au moins 1 pi (300 mm)</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><ol><li>S’assurer que tous les produits sont éteints avant de connecter le HomePower 5000 Plus au(x) bloc(s)-batterie 5000 Plus.</li><li>Pour un bon fonctionnement, veillez à ce que les entrées/sorties d’air sur les côtés soient dégagées. Laissez au moins 1 pi d’espace entre les orifices de ventilation et les objets pour assurer une circulation d’air adéquate et une dissipation efficace de la chaleur.</li></ol></td></tr></tbody></table>

### <span class="hb-heading-title">CONNEXION AU COMMUTATEUR DE TRANSFERT INTELLIGENT</span> <span class="hb-sold-separately">VENDUE SÉPARÉMENT</span>

<div class="native-figure native-sts-connect native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-connect" data-source-fragment-sha256="8e2874e110e2cafc1da05c6d0228b8811b52e8888344a4160f7f5aa18a19ecf0" data-web-base-art-ref="sts-connect" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-connect.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-connect.svg"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:36.7944%;--hb-y:8.6219%;--hb-width:57.9211%;--hb-height:25.7035%;--hb-fill:#ffffff"><span>Le Jackery HomePower 5000 Plus peut alimenter votre<br/>maison via le STS. Pour plus de détails, consultez le manuel<br/>d’utilisation du STS.</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:55.2339%;--hb-y:38.6671%;--hb-width:36.6276%;--hb-height:5.2002%"><span>Lorsque le mode UPS est activé, la station</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:55.2339%;--hb-y:43.4477%;--hb-width:28.2584%;--hb-height:5.2002%"><span>d’alimentation portable reste en</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:55.2339%;--hb-y:48.2283%;--hb-width:39.7431%;--hb-height:5.2002%"><span>fonctionnement et consomme de l’énergie en</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:55.2339%;--hb-y:53.009%;--hb-width:34.907%;--hb-height:5.2002%"><span>continu. En cas de panne de courant, le</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:55.2339%;--hb-y:57.7896%;--hb-width:34.4%;--hb-height:5.2002%"><span>système bascule vers l’alimentation par</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:55.2339%;--hb-y:62.5702%;--hb-width:25.0722%;--hb-height:5.2002%"><span>batterie en 20 millisecondes.</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:55.2339%;--hb-y:67.3509%;--hb-width:33.2466%;--hb-height:5.2002%"><span>Lorsque le mode UPS est désactivé, la</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:55.2339%;--hb-y:72.1315%;--hb-width:34.2965%;--hb-height:5.2002%"><span>bascule vers l’alimentation par batterie</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:55.2339%;--hb-y:76.9121%;--hb-width:22.207%;--hb-height:5.2002%"><span>s’effectue en 5 secondes.</span></span></div></div></figure></div>

<span id="native-charging"></span>

## RECHARGE

<p>L'énergie verte d'abord : nous préconisons l'utilisation de l'énergie verte en premier. Ce produit prend en charge deux modes de recharge simultanés : la recharge solaire et la recharge par prise murale CA.</p>

<p>Quand la recharge par prise murale CA et la recharge solaire sont effectuées en même temps, le produit privilégie la recharge solaire. Les deux méthodes sont utilisées pour charger la batterie à la puissance maximalement autorisée.</p>

<p class="hb-prose-pill"><strong>CHARGEZ L'APPAREIL ENTIÈREMENT AVANT SA PREMIÈRE UTILISATION</strong></p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><ol><li>La température de charge recommandée pour le produit est de 0 °C à 45 °C (32 °F à 113 °F), et la température de décharge est de -15 °C à 45 °C (5 °F à 113 °F). L’utilisation du produit en dehors de cette plage de température peut limiter ses capacités de charge et de décharge, voire l’empêcher de fonctionner.</li><li>La puissance de charge et la capacité de la batterie peuvent varier en fonction des fluctuations de température. Lorsque la température ambiante est comprise entre -15 °C et -10 °C (5 °F à 14 °F), la puissance de sortie maximale diminue à 3600 W.</li></ol></td></tr></tbody></table>

### CHARGEMENT PAR PRISE MURALE CA

<div class="native-figure native-ac-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charge" data-source-fragment-sha256="d840bbf589dc41b35b31585589e47454e48fed8f3fce8bc2888e94d29907a708" data-web-base-art-ref="ac-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ac-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ac-charge-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:62.5038%;--hb-y:49.8601%;--hb-width:27.0338%;--hb-height:7.7059%"><span>Connecter le câble CA au port</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62.5038%;--hb-y:57.8317%;--hb-width:24.3335%;--hb-height:7.7059%"><span>d’entrée CA du HomePower</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.5038%;--hb-y:65.8034%;--hb-width:27.9941%;--hb-height:7.7059%"><span>5000 Plus et à une prise murale.</span></span></div></div></figure></div>

### RECHARGE AVEC LE STS

<div class="native-figure native-sts-charge native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="sts-charge" data-source-fragment-sha256="6d525b03a9f6a645283e931cb55bb334cdbddb65680ae04114ddf52e8c438d70" data-web-base-art-ref="sts-charge" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="sts-charge.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/sts-charge-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:41.8621%;--hb-y:3.8719%;--hb-width:54.803%;--hb-height:5.2065%"><span>Connecter votre STS Jackery au produit pour activer la charge</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:41.8621%;--hb-y:8.0622%;--hb-width:6.9258%;--hb-height:5.2065%"><span>via STS.</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:41.8621%;--hb-y:14.0981%;--hb-width:53.208%;--hb-height:5.2065%"><span>*Le paramètre de réserve fonctionne dans tous les modes du</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:41.8621%;--hb-y:18.8845%;--hb-width:53.5298%;--hb-height:5.2065%"><span>STS. Ainsi, le Jackery HomePower 5000 Plus cesse de charger</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:41.8621%;--hb-y:23.6708%;--hb-width:53.7247%;--hb-height:5.2065%"><span>lorsque sa capacité restante dépasse le seuil de réserve. Pour</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:41.8621%;--hb-y:28.4572%;--hb-width:54.8469%;--hb-height:5.2065%"><span>le recharger immédiatement, suivez les instructions ci-dessous.</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:41.9634%;--hb-y:35.2292%;--hb-width:6.9946%;--hb-height:5.3429%"><span><strong>ÉTAPE</strong> <strong>1</strong></span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:60.6434%;--hb-y:35.2292%;--hb-width:7.2697%;--hb-height:5.3429%"><span><strong>ÉTAPE</strong> <strong>2</strong></span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:64.3482%;--hb-y:80.872%;--hb-width:3.2482%;--hb-height:2.108%"><span>HP5000Plus</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:78.4848%;--hb-y:91.9473%;--hb-width:14.5321%;--hb-height:5.2065%"><span>*Application STS</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Lorsque le port d’extension CA est connecté avec succès au STS, le port d’entrée CA ne sera pas utilisé pour la charge. Dans ce cas, la centrale peut être rechargée via les ports suivants : port d’extension CA, PV élevée, PV faible.</p></td></tr></tbody></table>

### RECHARGE AVEC PANNEAUX SOLAIRES

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><p>Lorsque les panneaux solaires sont connectés en série, assurez-vous que la sortie de tension maximale est comprise entre 16 V - 60 V pour le port d'entrée PV faible, et entre 135 V - 450 V pour le port d'entrée PV élevé.</p></td></tr></tbody></table>

<ul><li><strong>Connecter au port d'entrée PV faible</strong></li></ul>

<p>Plage de tension d’entrée PV faible: 16 V à 60 V</p>

<p>Le Jackery HomePower 5000 Plus a deux ports d'entrée PV faibles, dont chacun prend en charge de la connexion directe à un panneau solaire de 500 W ou à trois panneaux solaires de 200 W. Si l'un port d'entrée PV faible nécessite de connecter simultanément deux panneaux solaires ou plus, référez-vous à la figure suivante pour charger à l'aide du connecteur du panneau solaire (vendu séparément, non inclus en standard).</p>

<div class="native-figure native-low-pv-500 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-500" data-source-fragment-sha256="c15fbfa8cf0f1dde0f0d3dbc98396dec1fbf186981f8a665885d7e1ed2bef6ff" data-web-base-art-ref="low-pv-500" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-500.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-500-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.8172%;--hb-y:9.8661%;--hb-width:5.7165%;--hb-height:5.1339%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.971%;--hb-y:88.1606%;--hb-width:15.2748%;--hb-height:5.6714%"><span>SolarSaga 500 X × 2</span></span></div></div></figure></div>

<div class="native-figure native-low-pv-200 native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="low-pv-200" data-source-fragment-sha256="fad18b7b2c402a027b5a4d822a86fc0b91020111738fc1bb20149f6038143401" data-web-base-art-ref="low-pv-200" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="low-pv-200.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/low-pv-200-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:38.1609%;--hb-y:12.3103%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:53.6889%;--hb-y:12.3107%;--hb-width:5.7165%;--hb-height:4.6247%"><span>DC8020</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:77.5703%;--hb-y:94.2461%;--hb-width:13.9104%;--hb-height:5.1089%"><span>SolarSaga 200 × 6</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><ol><li>Assurez-vous que la tension d'entrée pour les deux ports d'entrée CC est la même. Sinon, le produit pourrait être endommagé. Par exemple:</li></ol><ul><li>Il est recommandé d'utiliser le même modèle de panneaux solaires Jackery et le même nombre de panneaux lors de la connexion des panneaux solaires aux deux ports d'entrée DC8020.</li><li>Ne chargez pas le produit à la fois avec un chargeur de voiture et un panneau solaire simultanément. Cela pourrait faire sauter le fusible de la voiture ou entraîner un échec de la charge.</li></ul><ol start="2"><li>Il est recommandé d’utiliser le panneau solaire Jackery pour charger l’HomePower 5000 Plus. Jackery décline toute responsabilité en cas de dommages causés par l’utilisation de panneaux solaires d’autres marques.</li></ol></td></tr></tbody></table>

<ul><li><strong>Connecter au port d'entrée PV élevée</strong></li></ul>

<p>Plage de tension d’entrée PV élevée: 135 V à 450 V</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><ol><li>Mettez l’interrupteur PV élevé désactivé avant de connecter l’entrée PV élevée ou pendant la maintenance.</li><li>Avant d'utiliser les ports d'entrée PV élevée, assurez-vous que l'interrupteur PV est mis en marche.</li><li>Assurez-vous que l'interrupteur PV élevé est en position « OFF » ou « LOCK » avant d'utiliser la clé MC4 fournie pour démonter les connecteurs MC4.</li></ol></td></tr></tbody></table>

<div class="native-figure native-high-pv native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv" data-source-fragment-sha256="fd64ccc270a0a663193d42c6de350c02e119daa5469ce76102a4db774e4d8fd0" data-web-base-art-ref="high-pv" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.8316%;--hb-y:6.0332%;--hb-width:33.3562%;--hb-height:3.9716%"><span>Démontez les connecteurs MC4 avec</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.8316%;--hb-y:10.1978%;--hb-width:16.6362%;--hb-height:3.9716%"><span>la clé MC4 fournie.</span></span></div></div></figure></div>

<div class="native-figure native-high-pv-lock native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="high-pv-lock" data-source-fragment-sha256="467022dcb7d7bf2729a1ae8bdf448535e9a219c564e8921e7dffe8de3decfbca" data-web-base-art-ref="high-pv-lock" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="high-pv-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/high-pv-lock-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:7.1126%;--hb-y:14.2495%;--hb-width:14.6667%;--hb-height:8.3363%"><span><strong>Verrouillage</strong></span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:55.8164%;--hb-y:14.8955%;--hb-width:17.7377%;--hb-height:8.3363%"><span><strong>Déverrouillage</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:6.9177%;--hb-y:24.6047%;--hb-width:36.0055%;--hb-height:6.3597%"><span>Tournez l'interrupteur haute tension sur la</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:55.8097%;--hb-y:25.2508%;--hb-width:34.8746%;--hb-height:6.3597%"><span>Libérez le mécanisme de verrouillage et</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:6.9177%;--hb-y:30.4512%;--hb-width:41.5575%;--hb-height:6.3597%"><span>position « LOCK » et appuyez sur le mécanisme</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:55.8097%;--hb-y:31.0973%;--hb-width:35.0318%;--hb-height:6.3597%"><span>l'interrupteur revient en position « OFF ».</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:6.9177%;--hb-y:36.2977%;--hb-width:13.698%;--hb-height:6.3597%"><span>de verrouillage.</span></span></div></div></figure></div>

<ul><li><strong>Entrée PV élevée + PV faible</strong></li></ul>

<p>Plage de tension pour entrée PV faible: 16 V à 60 V</p>

<p>Plage de tension pour entrée PV élevée: 135 V à 450 V</p>

<div class="native-figure native-dual-pv native-dense"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dual-pv" data-source-fragment-sha256="0c66ccafa23616c19ca1e92a43b633566946a182d8ab4130ddfc6de832746e75"><div class="hb-reference-semantic" data-reference-id="dual-pv.semantic"><img alt="dual-pv" class="hb-reference-art hb-composite-art" src="assets/dual-pv-fr.svg"/></div></figure></div>

### RECHARGE VIA PRISE ALLUME-CIGARE

<p>Vous pouvez recharger ce produit à l'aide d'un chargeur de voiture de 12 V. Veillez à ce que la connexion entre le chargeur de voiture et l'allume-cigare de la voiture soit bonne.</p>

<div class="native-figure native-car native-dense"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="6eac90865fdf811ae983bf59156ce82574fcac016a3155d19fb46faf3e5252bb" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71.4472%;--hb-y:22.9934%;--hb-width:8.6479%;--hb-height:6.667%"><span>vehícule</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:51.3399%;--hb-y:84.2359%;--hb-width:45.6052%;--hb-height:9.2214%;--hb-fill:#ffffff"><span>*Le câble de charge pour voiture est vendu séparément.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><ol><li>Il convient de démarrer le véhicule avant de charger la station d'alimentation.</li><li>Si le véhicule circule sur une route cahoteuse, il est interdit d'utiliser le chargeur de voiture au cas où il brûlerait dans le cas d'une mauvaise connexion. L'entreprise ne peut pas être tenue responsable de toute perte provoquée par une opération inhabituelle.</li><li>Vous pouvez recharger les véhicules de 12 V seulement, pas ceux de 24 V. Veuillez ne pas recharger ce produit dans un véhicule 24V pour éviter les blessures et les pertes matérielles.</li></ol></td></tr></tbody></table>

<span id="native-storage"></span>

## STOCKAGE

<p>Conservez le produit dans un endroit propre et sec avec une ventilation adéquate.Température et humidité de stockage :</p>

<ul><li>1 mois : -20 à 45°C (0-60% HR)</li><li>3 mois : 0 à 45°C (0-60% HR)</li><li>12 mois : 0 à 25°C (0-60% HR)</li></ul>

<p>Si ce produit est stocké pendant une longue période (3 à 6 mois) avec la batterie déchargée, il peut devenir impossible de le recharger.Pour éviter cela et préserver la santé de la batterie, il est recommandé de vérifier et de recharger le produit tous les trois mois, et d'effectuer un cycle de charge et de décharge complet au moins une fois tous les 6 à 12 mois.</p>

<span id="native-app"></span>

## CONFIGURATION DE L’APPLICATION

### 1. Pour télécharger l’application et se connecter

<figure aria-label="App download" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Recherchez « Jackery » dans Google Play ou dans l’App Store pour installer l’application. Une fois que c’est fait, vous pouvez vous inscrire et vous connecter.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Vous pouvez également scanner le code QR ci-dessous pour télécharger et installer l'application.</p></div></div></div><div class="hb-app-download-semantic"><img alt="App download" class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

### 2. Pour ajouter un appareil

<p>2.1 Cliquez sur le bouton <span class="native-inline-plus">+</span> pour ajouter un appareil.</p>

<p>2.2 Maintenez enfoncé le bouton Power sur l’appareil pour l’allumer. Les icônes Wi-Fi et Bluetooth clignotent sur l’appareil afin d’indiquer qu’il est entré dans le mode Configuration réseau. Cliquez sur le bouton «icône qui clignotante» et autorisez l’application à se connecter aux appareils alentour, puis ouvrez les autorisations Bluetooth.</p>

<div class="native-figure native-app-add native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add" data-source-fragment-sha256="708b58634468539a0aee8bf378096f323c4e49e1dbbae5f6333fba125a633831" data-web-base-art-ref="app-add" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-add.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-add-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:19.3638%;--hb-y:94.9419%;--hb-width:4.0564%;--hb-height:4.954%"><span>2.1</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:76.3543%;--hb-y:94.9419%;--hb-width:4.6435%;--hb-height:4.954%"><span>2.2</span></span></div></div></figure></div>

<div class="native-figure native-app-control native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-control" data-source-fragment-sha256="c9a33cb3f2a142fa544f267fd4e31a418d7124dac2d8d788913fa04e4a3a026f" data-web-base-art-ref="app-control" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-control.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-control-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:72.357%;--hb-y:14.8093%;--hb-width:6.944%;--hb-height:11.3411%"><span>Bouton</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:14.257%;--hb-y:21.3046%;--hb-width:6.944%;--hb-height:11.3411%"><span>Bouton</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:72.357%;--hb-y:23.8558%;--hb-width:23.3232%;--hb-height:11.3411%"><span>d’alimentation principale</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:4.0489%;--hb-y:30.3511%;--hb-width:17.1521%;--hb-height:11.3411%"><span>d’alimentation CC</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:72.357%;--hb-y:43.2899%;--hb-width:6.944%;--hb-height:11.3411%"><span>Bouton</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:14.2582%;--hb-y:50.9643%;--hb-width:6.944%;--hb-height:11.3411%"><span>Bouton</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:72.357%;--hb-y:52.3364%;--hb-width:17.8939%;--hb-height:11.3411%"><span>d’alimentation USB</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:4.241%;--hb-y:60.0108%;--hb-width:16.9612%;--hb-height:11.3411%"><span>d’alimentation CA</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Si, une fois allumée, l’application n’est pas connectée à un appareil dans les 2 heures, le Wi-Fi et le Bluetooth de l’appareil seront automatiquement désactivés. Vous devrez maintenir les boutons USB et AC enfoncés pour réactiver le Wi-Fi et le Bluetooth.</p></td></tr></tbody></table>

<p>2.3 Une fois que vous avez appuyé sur l’icône de recherche d’appareils, l’appareil est automatiquement associé à l’application via le Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Si le message «l’appareil a été associé» s’affiche pendant l’appairage, vous pouvez suivre l’une de ces deux étapes pour procéder à la connexion.</p><ul><li>Le propriétaire de l’appareil peut partager ce dernier avec d’autres utilisateurs dans l’application.</li><li>Maintenez les boutons Power et USB enfoncés pendant 3 secondes pour réinitialiser l’appareil et l’associer de nouveau.</li></ul></td></tr></tbody></table>

<p>2.4 Une fois l’appairage réalisé avec succès, vous devrez saisir le nom et le mot de passe du Wi-Fi pour que l’appareil se connecte automatiquement au réseau Wi-Fi.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>Veuillez choisir un réseau Wi-Fi 2,4 GHz. L’appareil ne prend pas en charge le réseau Wi-Fi 5 GHz.</p></td></tr></tbody></table>

<p>2.5 Une fois l’appareil ajouté à la page d’accueil, l’icône Wi-Fi de l’appareil restera allumée.</p>

<div class="native-figure native-app-results native-regular"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-results" data-source-fragment-sha256="4b0abcf4f3dc9d0e8711acc7e64e70273219606452cc604306b7ad716a8b8825" data-web-base-art-ref="app-results" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="app-results.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/app-results-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:12.1857%;--hb-y:95.3279%;--hb-width:3.0179%;--hb-height:5.0903%"><span>2.3</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:48.4811%;--hb-y:95.3279%;--hb-width:3.1204%;--hb-height:5.0903%"><span>2.4</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:84.9837%;--hb-y:95.3279%;--hb-width:3.0384%;--hb-height:5.0903%"><span>2.5</span></span></div></div></figure></div>

<p>Les captures d’écran ci-dessus sont fournies à titre indicatif.</p>

### 3. Pour dissocier l’appareil

<p>Cliquez sur le bouton des paramètres en haut à droite de l’interface principale pour accéder à la page des paramètres. Cliquez sur le bouton de dissociation en bas de la page pour dissocier l’appareil.</p>

### 4. Remarques

<p><strong>4.1 Pour activer le Wi-Fi et le Bluetooth :</strong></p>

<ul><li>Le Wi-Fi et le Bluetooth sont automatiquement activés, une fois l’appareil allumé. Leurs icônes s’allument sur l’écran.</li><li>Appuyez simultanément sur les boutons d’alimentation des sorties USB et CA jusqu’à ce que les icônes Wi-Fi et Bluetooth s’allument sur l’écran.</li></ul>

<p><strong>4.2 Pour désactiver le Wi-Fi et le Bluetooth:</strong></p>

<ul><li>Appuyez simultanément sur les boutons d’alimentation des sorties USB et CA jusqu’à ce que les icônes Wi-Fi et Bluetooth s’éteignent de l’écran.</li><li>Le Wi-Fi et le Bluetooth sont automatiquement désactivés si aucun appareil n'est connecté dans les 2 heures.</li></ul>

<p><strong>4.3 Pour réinitialiser le Wi-Fi et le Bluetooth：</strong></p>

<ul><li>Maintenez les boutons Power et USB enfoncés simultanément pendant 3 secondes pour réinitialiser le Wi-Fi et le Bluetooth aux paramètres d’usine et redémarrer le système. Le compte connecté dans l’application sera dissocié.</li></ul>

<span id="native-warranty"></span>

## GARANTIE

<figure aria-label="GARANTIE" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>Nous ne fournissons notre garantie qu'aux clients qui achètent sur le site offciel de Jackery, sur des plateformes tierces portant la marque Jackery, ou auprès de revendeurs autorisés locaux.</strong></div><div class="hb-warranty-local-note">* La durée et les détails de la garantie peuvent varier en fonction des lois, réglementations et revendeurs autorisés locaux.</div></figure>

### Garantie limitée

<figure aria-label="Garantie limitée" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantit à l'acheteur et consommateur d'origine que le produit de Jackery sera exempt de tout défaut de fabrication et de matériaux dans le cadre d'une utilisation normale pendant toute la durée de la période de garantie applicable identifiée dans la section « Période de garantie » ci-dessous, sous réserve des exceptions énoncées ci-dessous.</p><p>Cette déclaration de garantie énonce les obligations totales et exclusives de garantie de Jackery. Nous n'assumerons pas et nous n'autorisons personne à assumer pour nous toute autre responsabilité en lien avec la vente de nos produits.</p></figure>

### Période de garantie

<figure aria-label="Période de garantie" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="5 ANS Garantie standard" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">5</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie standard</strong></div></div><div class="hb-warranty-period-copy">La période de garantie standard du Jackery HomePower 5000 Plus est de 60 mois. Dans tous les cas, la période de garantie commence à compter de la date d'achat par l'acheteur et consommateur d'origine. La facture du premier achat du consommateur ou toute autre preuve documentaire raisonnable est nécessaire afin d'établir la date de début de la période de garantie.</div></div><div aria-label="2 ANS Garantie prolongée" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie prolongée</strong></div></div><div class="hb-warranty-period-copy">Des frais supplémentaires sont exigés pour la garantie prolongée. Pour plus de détails sur la garantie prolongée, veuillez visiter le site Web de Jackery ou contacter le service client de Jackery.</div></div></div></figure>

### Réparation ou remplacement

<figure aria-label="Réparation ou remplacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3">Jackery réparera ou remplacera (aux frais de Jackery) tout produit Jackery qui ne fonctionnera pas pendant la période de garantie applicable en raison d'un défaut de fabrication ou de matériau. Le produit réparé/remplacé assume la garantie restante de la date d'achat originale.</figure>

### Limitée à l'acheteur et consommateur d'origine

<figure aria-label="Limitée à l'acheteur et consommateur d'origine" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4">La garantie d'un produit Jackery est limitée à l'acheteur et consommateur d'origine, elle ne peut pas être transférée à un autre propriétaire.</figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantie de Jackery ne s'applique pas à :</p><p>Une utilisation incorrecte, abusée, modifiée, aux dégâts provoqués par un accident ou toute autre utilisation qui n'est pas une utilisation normale de ce produit et autorisée par la documentation actuelle du produit de Jackery.</p><p>À une réparation tentée par quelqu'un d'autre qu'un établissement agréé.</p><p>Tout autre produit acheté par l'intermédiaire d'une vente aux enchères en ligne.</p><p>La garantie de Jackery ne s'applique pas aux cellules de la batterie, sauf si vous avez entièrement chargé les cellules de la batterie dans les sept jours suivant l'achat du produit et au moins une fois tous les 6 mois par la suite.</p></figure>

### Droits d'interprétation

<figure aria-label="Droits d'interprétation" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6">Jackery Inc. se réserve le droit d'interpréter de manière définitive la politique après-vente des clients ci-dessus.</figure>

<span id="native-specifications"></span>

## SPÉCIFICATIONS

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Numéro de modèle</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Chimie cellulaire</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 61 kg/134,5 lbs</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">41,8×39,5×63,5 cm/16,5×15,5×25 po</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 4 000 cycles à 70 % ou plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Onduleur</th><td class="manual-spec-value hb-spec-value">Onduleur de secours : ＜20ms Onduleur en ligne : 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topologie de l’onduleur</th><td class="manual-spec-value hb-spec-value">Non isolé</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Facteur de puissance</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unité complète</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS D’ENTRÉE</h2>

<figure aria-label="PORTS D’ENTRÉE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Mode de charge Entrée CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A max (Durée &lt; 3h lorsque le courant dépasse 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Mode bypass Entrée CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A max (Durée &lt; 3h lorsque le courant dépasse 12A)</td></tr><tr><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x Port d’extension CA (Entrée)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrée CC</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">PV élevée</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">PV faible</th><td class="manual-spec-value hb-spec-value">2 x ports 8mm CC ; 16V-60V⎓10,5A max, double à 21A/1200W max</td></tr><tr><td class="manual-spec-value hb-spec-value">11V-16V (tension de fonctionnement)⎓8A max, double à 8A max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS DE SORTIE</h2>

<figure aria-label="PORTS DE SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie CA (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie Mode bypass CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A max 240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × Sortie CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Total Sorties CA</th><td class="manual-spec-value hb-spec-value">7200W max, surtension 14400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties USB-C</th><td class="manual-spec-value hb-spec-value">100W max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties USB-A</th><td class="manual-spec-value hb-spec-value">18W max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1,5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port allume-cigare</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CA (Sortie)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><td class="manual-spec-value hb-spec-value">-15°C~-10°C (5°F~14°F) Puissance de sortie : 3600 W</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>RISQUE D’INGESTION :</strong> Ce dispositif contient une pile bouton.</p>

<p class="native-trademark">※ USB Type-C<sup>®</sup> et USB-C<sup>®</sup> sont des marques déposées de l’USB Implementers Forum.</p>

<span id="native-ess"></span>

## <span class="hb-heading-title">GUIDE D’INSTALLATION DU SYSTÈME DE SAUVEGARDE DOMESTIQUE INTELLIGENT (AC ESS)</span> <span class="hb-heading-model"><strong>Modèle du système</strong><br/>HB5000C-TS02A</span>

<p>Pour connecter l’Jackery HomePower 5000 Plus au Smart Transfer Switch (STS), utilisez le câble d’extension pour relier le port d’extension AC de l’Explorer 5000 Plus au port d’entrée/sortie AC du STS.</p>

<p>Pour connecter l’Jackery HomePower 5000 Plus au pack de batteries, utilisez le câble d’extension pour relier son port d’extension CC (A) au port d’extension CC (B) du pack de batteries.</p>

<div class="native-figure native-ess native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ess" data-source-fragment-sha256="d673db65b1378f190ffdc29fffa0b7730b7b6c10f7cbb24235ba214c67f2730c" data-web-base-art-ref="ess" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ess.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/ess-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4.4021%;--hb-y:89.0595%;--hb-width:75.6336%;--hb-height:3.2818%"><span>Pour des instructions détaillées sur l’installation et la connexion, consultez les manuels</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:4.4021%;--hb-y:92.8324%;--hb-width:38.7169%;--hb-height:3.2818%"><span>d’utilisation du STS et du pack de batteries.</span></span></div></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Mise en garde</td><td class="manual-callout-body"><p>Position d’installation du système de sauvegarde domestique intelligent (AC ESS) Installation en intérieur.</p><p>L’espace doit être complètement étanche.</p><p>Le mur doit être plat et nivelé.</p><p>Plage de température ambiante : -15°C~45°C.</p><p>La température et l’humidité doivent être maintenues à un niveau constant.</p><p>Installer dans un endroit bien ventilé.</p><p>Ne pas installer dans une zone accessible aux enfants ou aux animaux domestiques. L’emplacement d’installation doit éviter l’exposition directe au soleil.</p><p>Aucun matériau inflammable ou explosif ne doit se trouver à proximité de l’onduleur et de la batterie.</p></td></tr></tbody></table>

<span id="native-ess-host"></span>

### <span class="hb-heading-title">Jackery HomePower 5000 Plus</span> <span class="hb-heading-model">Modèle: JHP-5000C</span>

#### <span class="native-plain-title">SPÉCIFICATIONS</span>

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Numéro de modèle</th><td class="manual-spec-value hb-spec-value">JHP-5000C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Chimie cellulaire</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 61 kg/134,5 lbs</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">41,8×39,5×63,5 cm/16,5×15,5×25 po</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 4 000 cycles à 70 % ou plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Onduleur</th><td class="manual-spec-value hb-spec-value">Onduleur de secours : ＜20ms Onduleur en ligne : 0ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topologie de l’onduleur</th><td class="manual-spec-value hb-spec-value">Non isolé</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Facteur de puissance</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unité complète</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS D’ENTRÉE</h2>

<figure aria-label="PORTS D’ENTRÉE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Mode de charge Entrée CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 15A max (Durée &lt; 3h lorsque le courant dépasse 12A)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Mode bypass Entrée CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A max (Durée &lt; 3h lorsque le courant dépasse 12A)</td></tr><tr><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x Port d’extension CA (Entrée)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Entrée CC</th><td class="manual-spec-value hb-spec-value"></td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 x Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">PV élevée</th><td class="manual-spec-value hb-spec-value">135V-450V⎓15A max, 4000W Max</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">PV faible</th><td class="manual-spec-value hb-spec-value">2 x ports 8mm CC ; 16V-60V⎓10,5A max, double à 21A/1200W max</td></tr><tr><td class="manual-spec-value hb-spec-value">11V-16V (tension de fonctionnement)⎓8A max, double à 8A max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS DE SORTIE</h2>

<figure aria-label="PORTS DE SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie CA (NEMA L14-30R/14-50)</th><td class="manual-spec-value hb-spec-value">120V/240V~60Hz, 30A, 7200W max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie Mode bypass CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 12A max 240V~60Hz, 16,7A max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">4 × Sortie CA</th><td class="manual-spec-value hb-spec-value">120V~60Hz, 20A, 2400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Total Sorties CA</th><td class="manual-spec-value hb-spec-value">7200W max, surtension 14400W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties USB-C</th><td class="manual-spec-value hb-spec-value">100W max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties USB-A</th><td class="manual-spec-value hb-spec-value">18W max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1,5A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port allume-cigare</th><td class="manual-spec-value hb-spec-value">12V⎓10A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CA (Sortie)</th><td class="manual-spec-value hb-spec-value">240V~60Hz, 30A, 7200W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr><tr><td class="manual-spec-value hb-spec-value">-15°C~-10°C (5°F~14°F) Puissance de sortie : 3600 W</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>RISQUE D’INGESTION :</strong> Ce dispositif contient une pile bouton.</p>

<p class="native-trademark">※ USB Type-C<sup>®</sup> et USB-C<sup>®</sup> sont des marques déposées de l’USB Implementers Forum.</p>

<span id="native-ess-battery"></span>

### <span class="hb-heading-title">Jackery Battery Pack 5000 Plus</span> <span class="hb-heading-model">Modèle: JBP-5000A</span>

<h4 class="hb-heading-label-pair"><span class="hb-heading-title">SPÉCIFICATIONS</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span></h4>

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 5000 Plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Numéro de modèle</th><td class="manual-spec-value hb-spec-value">JBP-5000A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">45Ah/112Vdc (5040Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Chimie cellulaire</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 37 kg/81,57 lbs</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimension</th><td class="manual-spec-value hb-spec-value">41,8 × 34,4 × 33,6 cm / 16,5×13,5×13,2 po</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 4 000 cycles à 70 % ou plus</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">2600A/5ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Protection contre les intrusions</th><td class="manual-spec-value hb-spec-value">IP20</td></tr></tbody></table></figure>

<p>À utiliser uniquement avec le Jackery Explorer 5000 Plus et le Jackery HomePower 5000 Plus.</p>

<h2 class="hb-spec-group">PORTS D’ENTRÉE/SORTIE</h2>

<figure aria-label="PORTS D’ENTRÉE/SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓41A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">80,5V-126V⎓98A Max</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT AMBIANTE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">0°C~45°C (32°F~113°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-15°C~45°C (5°F~113°F)</td></tr></tbody></table></figure>

<p class="native-ingestion"><img alt="" src="assets/symbol_ingestion_hazard.svg"/><strong>RISQUE D’INGESTION :</strong> Ce dispositif contient une pile bouton.</p>

<span id="native-ess-sts"></span>

### <span class="hb-heading-title">Jackery Smart Transfer Switch</span> <span class="hb-heading-model">Modèle: JA-TS02A</span>

<h4 class="hb-heading-label-pair"><span class="hb-heading-title">SPÉCIFICATIONS</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span></h4>

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Smart Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Numéro de modèle</th><td class="manual-spec-value hb-spec-value">JA-TS02A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Voltage AC (Nominal)</th><td class="manual-spec-value hb-spec-value">120V/ 240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Feed-In Type</th><td class="manual-spec-value hb-spec-value">Phase de Division</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant maximal d'entrée</th><td class="manual-spec-value hb-spec-value">100A Grid/ 60A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant maximal de sortie</th><td class="manual-spec-value hb-spec-value">60A Home Load/ 33.4A Power Station</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant de court-circuit d'entrée maximal</th><td class="manual-spec-value hb-spec-value">10KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Catégorie de surtension</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">≤ 20 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Type d'annexe (Panel de distribution)</th><td class="manual-spec-value hb-spec-value">NEMA Type 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre de branches de charge</th><td class="manual-spec-value hb-spec-value">12</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuit principal</th><td class="manual-spec-value hb-spec-value">2 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuit de branchement</th><td class="manual-spec-value hb-spec-value">14 AWG 12 AWG 10 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Communication</th><td class="manual-spec-value hb-spec-value">Wi-Fi et Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température opérationnelle</th><td class="manual-spec-value hb-spec-value">-20°C~ 40°C(-4°F~ 104°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">22 x 14,7 x 7,87 in/ 56 x 37,4 x 20 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 25,57 lbs/11,6 kg</td></tr></tbody></table></figure>

<p>* Lorsque vous utilisez le produit, assurez-vous de vous connecter à une tension de secteur de 240 V en phase divisée.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarque</td><td class="manual-callout-body"><p>SYSTÈME DE SAUVEGARDE DOMESTIQUE INTELLIGENT (AC ESS) Environ 575.16 lbs/260.89 kg</p></td></tr></tbody></table>

<span id="native-ess-package"></span>

### LISTE DU COLIS

<div class="native-figure native-package-host native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-host" data-source-fragment-sha256="5c455f55573b494861ba82452edda0925714ef589c10a339a386be9a01556033" data-web-base-art-ref="package-host" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-host.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-host.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:88.3063%;--hb-y:40.9817%;--hb-width:1.8037%;--hb-height:1.9358%"><span>Model :JHP-5000C</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:82.8007%;--hb-y:67.0823%;--hb-width:5.5676%;--hb-height:4.1614%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:82.8123%;--hb-y:69.8627%;--hb-width:5.5441%;--hb-height:2.6155%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:81.0591%;--hb-y:74.0787%;--hb-width:1.9679%;--hb-height:2.2318%"><span><strong>CONTACT</strong> <strong>US</strong> <strong>:</strong></span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:82.0062%;--hb-y:75.5652%;--hb-width:4.9025%;--hb-height:3.224%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:87.9669%;--hb-y:75.7352%;--hb-width:1.7489%;--hb-height:1.9376%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:87.9669%;--hb-y:76.621%;--hb-width:1.6781%;--hb-height:1.9376%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:5.6426%;--hb-y:85.5466%;--hb-width:22.8663%;--hb-height:6.8182%"><span>Jackery HomePower 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:34.0827%;--hb-y:85.5466%;--hb-width:19.1414%;--hb-height:6.8182%"><span>Câble de chargement CA</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:62.2361%;--hb-y:85.5466%;--hb-width:6.5823%;--hb-height:6.8182%"><span>Clé MC4</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:78.3348%;--hb-y:85.5466%;--hb-width:14.4765%;--hb-height:6.8182%"><span>Manuel d’utilisation</span></span></div></div></figure></div>

<div class="native-figure native-package-battery native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-battery" data-source-fragment-sha256="5259dcfd6011e941f5e7d3792a0b474101585c1dd6f8df720efc058b3728f163" data-web-base-art-ref="package-battery" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-battery.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-battery.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:68.3587%;--hb-y:17.371%;--hb-width:1.7514%;--hb-height:2.5785%"><span>Model: JBP-5000A</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:77.4329%;--hb-y:28.568%;--hb-width:22.3546%;--hb-height:41.1083%;--hb-fill:#b5b5b6"><span><strong>Vendu</strong><br/><strong>séparément</strong></span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62.6267%;--hb-y:47.8592%;--hb-width:5.8832%;--hb-height:5.794%"><span><strong>USER</strong> <strong>MANUAL</strong></span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62.5785%;--hb-y:51.8103%;--hb-width:5.9802%;--hb-height:3.6064%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:61.0952%;--hb-y:60.9681%;--hb-width:1.8815%;--hb-height:2.9684%"><span><strong>CONTACT</strong> <strong>US:</strong></span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:62.0277%;--hb-y:62.9249%;--hb-width:4.8308%;--hb-height:4.2754%"><span><strong>1-888-502-2236</strong> (US)</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:67.8946%;--hb-y:63.1498%;--hb-width:1.7266%;--hb-height:2.5808%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:67.8946%;--hb-y:64.3165%;--hb-width:1.6569%;--hb-height:2.5808%"><span>www.jackery.com</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:5.3672%;--hb-y:77.8993%;--hb-width:23.4172%;--hb-height:9.1241%"><span>Jackery Battery Pack 5000 Plus</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:36.8967%;--hb-y:77.8993%;--hb-width:13.5138%;--hb-height:9.1241%"><span>Câble de rallonge</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:58.2884%;--hb-y:77.8993%;--hb-width:14.4765%;--hb-height:9.1241%"><span>Manuel d’utilisation</span></span></div></div></figure></div>

<div class="native-figure native-package-sts native-dense native-operation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-sts" data-source-fragment-sha256="3f6a1e8f40716ed776fed923118bd9ef5c83c83c8a903b1eadd0b25bc1774d6c" data-web-base-art-ref="package-sts" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="package-sts.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/package-sts-fr.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:36.2332%;--hb-y:11.9984%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:38.0496%;--hb-y:11.9984%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:36.2332%;--hb-y:12.6702%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:38.0496%;--hb-y:12.6702%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:33.6805%;--hb-y:13.1013%;--hb-width:1.2332%;--hb-height:1.8075%"><span>Upward</span></span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:33.2147%;--hb-y:14.2072%;--hb-width:1.4638%;--hb-height:1.6669%"><span>A scale of 1:1</span></span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:33.2147%;--hb-y:14.9153%;--hb-width:1.1306%;--hb-height:1.6669%"><span>Unit: mm</span></span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:74.8015%;--hb-y:18.1582%;--hb-width:1.8751%;--hb-height:1.6443%"><span>Model: JA-TS02A</span></span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:85.0004%;--hb-y:30.4717%;--hb-width:5.5775%;--hb-height:3.6757%"><span>Quick Guide</span></span><span class="hb-reference-live-label" data-source-line="9" style="--hb-x:84.1796%;--hb-y:33.0243%;--hb-width:7.4119%;--hb-height:2.6681%"><span>HomePower Energy System</span></span><span class="hb-reference-live-label" data-source-line="10" style="--hb-x:71.4968%;--hb-y:33.4395%;--hb-width:1.258%;--hb-height:1.367%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="11" style="--hb-x:71.0365%;--hb-y:35.019%;--hb-width:0.4048%;--hb-height:1.2415%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="12" style="--hb-x:71.4591%;--hb-y:35.019%;--hb-width:0.4368%;--hb-height:1.2415%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="13" style="--hb-x:71.919%;--hb-y:35.019%;--hb-width:0.3964%;--hb-height:1.2415%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="14" style="--hb-x:72.3228%;--hb-y:35.019%;--hb-width:0.4762%;--hb-height:1.2415%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="15" style="--hb-x:72.7936%;--hb-y:35.019%;--hb-width:0.4129%;--hb-height:1.2415%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="16" style="--hb-x:15.5296%;--hb-y:35.1312%;--hb-width:3.0898%;--hb-height:1.8832%"><span>Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="17" style="--hb-x:71.8922%;--hb-y:37.5254%;--hb-width:0.4928%;--hb-height:1.2415%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="18" style="--hb-x:71.7996%;--hb-y:37.6822%;--hb-width:0.6728%;--hb-height:1.2415%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="19" style="--hb-x:14.1585%;--hb-y:39.8788%;--hb-width:0.5703%;--hb-height:1.5108%"><span>AC1</span></span><span class="hb-reference-live-label" data-source-line="20" style="--hb-x:15.4242%;--hb-y:39.8788%;--hb-width:0.6642%;--hb-height:1.5108%"><span>GRID</span></span><span class="hb-reference-live-label" data-source-line="21" style="--hb-x:16.8019%;--hb-y:39.8788%;--hb-width:0.5455%;--hb-height:1.5108%"><span>IOT</span></span><span class="hb-reference-live-label" data-source-line="22" style="--hb-x:18.0119%;--hb-y:39.8788%;--hb-width:0.781%;--hb-height:1.5108%"><span>ERROR</span></span><span class="hb-reference-live-label" data-source-line="23" style="--hb-x:19.4227%;--hb-y:39.8788%;--hb-width:0.5936%;--hb-height:1.5108%"><span>AC2</span></span><span class="hb-reference-live-label" data-source-line="24" style="--hb-x:69.0447%;--hb-y:40.1335%;--hb-width:6.1448%;--hb-height:3.577%"><span>USER MANUAL</span></span><span class="hb-reference-live-label" data-source-line="25" style="--hb-x:69.0447%;--hb-y:42.6209%;--hb-width:6.145%;--hb-height:2.26%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="26" style="--hb-x:67.5802%;--hb-y:46.4988%;--hb-width:1.3788%;--hb-height:1.6614%"><span><strong>Contact</strong> <strong>us:</strong></span></span><span class="hb-reference-live-label" data-source-line="27" style="--hb-x:67.5802%;--hb-y:47.0453%;--hb-width:1.9922%;--hb-height:1.6443%"><span>hello@jackery.com</span></span><span class="hb-reference-live-label" data-source-line="28" style="--hb-x:16.7214%;--hb-y:47.4191%;--hb-width:0.8302%;--hb-height:1.5108%"><span>POWER</span></span><span class="hb-reference-live-label" data-source-line="29" style="--hb-x:74.4355%;--hb-y:47.5636%;--hb-width:2.2612%;--hb-height:1.6443%"><span>Version: JAK-UM-V1.0</span></span><span class="hb-reference-live-label" data-source-line="30" style="--hb-x:67.5802%;--hb-y:47.585%;--hb-width:2.111%;--hb-height:1.6443%"><span>1-888-502-2236(US)</span></span><span class="hb-reference-live-label" data-source-line="31" style="--hb-x:36.2329%;--hb-y:47.6176%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="32" style="--hb-x:38.0496%;--hb-y:47.6176%;--hb-width:1.2737%;--hb-height:1.5544%"><span>Marking hole</span></span><span class="hb-reference-live-label" data-source-line="33" style="--hb-x:16.4443%;--hb-y:47.8903%;--hb-width:1.362%;--hb-height:1.5108%"><span>PAUSE/RESUME</span></span><span class="hb-reference-live-label" data-source-line="34" style="--hb-x:36.2332%;--hb-y:48.4227%;--hb-width:1.5036%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="35" style="--hb-x:38.0496%;--hb-y:48.4227%;--hb-width:1.5037%;--hb-height:1.5544%"><span>M6 tapped hole</span></span><span class="hb-reference-live-label" data-source-line="36" style="--hb-x:5.9686%;--hb-y:56.5243%;--hb-width:22.2194%;--hb-height:5.5228%"><span>Jackery Smart Transfer Switch</span></span><span class="hb-reference-live-label" data-source-line="37" style="--hb-x:29.7643%;--hb-y:56.5243%;--hb-width:16.262%;--hb-height:5.5228%"><span>Modèle de marquage</span></span><span class="hb-reference-live-label" data-source-line="38" style="--hb-x:51.0952%;--hb-y:56.5243%;--hb-width:9.8962%;--hb-height:5.5228%"><span>Entrée/sortie</span></span><span class="hb-reference-live-label" data-source-line="39" style="--hb-x:64.8844%;--hb-y:56.5243%;--hb-width:14.4765%;--hb-height:5.5228%"><span>Manuel d’utilisation</span></span><span class="hb-reference-live-label" data-source-line="40" style="--hb-x:82.9962%;--hb-y:56.5243%;--hb-width:9.9454%;--hb-height:5.5228%"><span>Guide rapide</span></span><span class="hb-reference-live-label" data-source-line="41" style="--hb-x:48.403%;--hb-y:60.9426%;--hb-width:15.6827%;--hb-height:5.5228%"><span>d'alimentation Câble</span></span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="42" style="--hb-x:77.4329%;--hb-y:67.1211%;--hb-width:22.3546%;--hb-height:24.8829%;--hb-fill:#b5b5b6"><span><strong>Vendu</strong><br/><strong>séparément</strong></span></span><span class="hb-reference-live-label" data-source-line="43" style="--hb-x:49.5961%;--hb-y:84.6502%;--hb-width:20.6566%;--hb-height:5.5228%"><span>4*M4 Phillips plate Vis à tête</span></span><span class="hb-reference-live-label" data-source-line="44" style="--hb-x:48.2941%;--hb-y:89.3152%;--hb-width:23.2623%;--hb-height:5.5228%"><span>(fixer des supports muraux pour</span></span><span class="hb-reference-live-label" data-source-line="45" style="--hb-x:10.1855%;--hb-y:89.2047%;--hb-width:14.1574%;--hb-height:5.5228%"><span>étiquette de circuit</span></span><span class="hb-reference-live-label" data-source-line="46" style="--hb-x:32.3235%;--hb-y:89.2047%;--hb-width:12.1393%;--hb-height:5.5228%"><span>2*Support mural</span></span><span class="hb-reference-live-label" data-source-line="47" style="--hb-x:51.4843%;--hb-y:93.9801%;--hb-width:16.8834%;--hb-height:5.5228%"><span>Smart Transfer Switch )</span></span></div></div></figure></div>

<div class="native-contact-card" id="native-contact"><p class="native-contact-company"><strong>JACKERY INC.</strong></p><p class="native-contact-address">5310 Bunche Dr., Fremont, CA 94538-8301</p><div class="native-contact-row"><div class="native-contact-panel"><p class="native-contact-phone"><img alt="" class="native-contact-glyph" src="assets/contact-phone.svg"/><strong>1-888-502-2236</strong> <span class="native-contact-region">(US)</span></p><div class="native-contact-links"><p class="native-contact-email"><img alt="" class="native-contact-glyph" src="assets/contact-mail.svg"/>hello@jackery.com</p><p class="native-contact-web"><img alt="" class="native-contact-glyph" src="assets/contact-web.svg"/>www.jackery.com</p></div></div><div class="native-contact-qr"><img alt="" src="assets/contact-qr.svg"/></div></div></div>
