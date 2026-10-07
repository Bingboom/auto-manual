<style>
/* Native exceptions only. Chapter H1 / dot-led H2 use shared web_manual.css. */
#furo-main-content #jackery-homepower-3600-pro-max-manuel-dutilisation > h1,
#furo-main-content section#fcc > h1,
#furo-main-content section#contactez-nous > h1,
#furo-main-content h2.hb-source-hidden-heading,
#furo-main-content section#liste-du-colis section > h3 {
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
#furo-main-content section#configuration-de-lapplication h2::before,
#furo-main-content section#configuration-de-lapplication h3::before {
  display: none;
}
#furo-main-content section#configuration-de-lapplication h2,
#furo-main-content section#configuration-de-lapplication h3 {
  display: block;
  padding: 0;
  text-transform: none;
}
#furo-main-content section[id^="jackery-battery-pack-3600-sold-separately"] > h1,
#furo-main-content section#jackery-automatic-transfer-switch-vendu-separement > h1 {
  text-transform: none;
}

/* Source geometry at the shared 8px mobile floor: keep labels above leaders/inside the panel. */
@media (max-width: 40rem) {
  #furo-main-content [data-reference-id="ess_connection"] [data-source-line="0"] { top: 32%; }
  #furo-main-content [data-reference-id="ess_connection"] [data-source-line="2"] { top: 87%; }
  #furo-main-content [data-reference-id="ess_connection"] .hb-reference-live-label br { display: none; }
}

/* Keep the native outlet label close to its introduction and diagram. */
#furo-main-content p:has(+ #v-ac-outlet) { margin-bottom: 0.4rem; }
#furo-main-content #v-ac-outlet { margin: 0.4rem 0 0.2rem; }
#furo-main-content #v-ac-outlet + [data-reference-id="charge240"] { margin-top: 0.3rem !important; }

/* Source labels stay above their original horizontal leaders at the mobile floor. */
@media (max-width: 40rem) {
  #furo-main-content [data-reference-id="cascade"] [data-source-line="0"] { top: 4%; }
  #furo-main-content [data-reference-id="cascade"] [data-source-line="1"] { top: 41.5%; }
}

/* Preserve the source 6pt/316pt caption ratio with the shared mobile 8px floor. */
#furo-main-content [data-reference-id="charge120"] [data-source-line="0"] {
  font-size: max(.5rem, 1.9cqw);
}
/* On small phones the native blank lower region admits a wider two-line caption. */
@media (max-width: 400px) {
  #furo-main-content [data-reference-id="charge120"] [data-source-line="0"] {
    left: 40%;
    top: 78%;
    width: 57%;
  }
}

/* 240V caption follows the native 6pt/316pt ratio; phones use the shared 8px floor. */
#furo-main-content [data-reference-id="charge240"] [data-source-line="0"] {
  font-size: max(.5rem, 1.9cqw);
}
@media (max-width: 400px) {
  #furo-main-content [data-reference-id="charge240"] [data-source-line="0"] {
    left: 40%;
    top: 69%;
    width: 57%;
  }
}

/* Native specification footnotes form four continuous lines, without body paragraph gaps. */
#furo-main-content #specifications > p.manual-spec-footnote,
#furo-main-content #specifications-model-jhp-3600c > p.manual-spec-footnote {
  margin: 0;
}

/* Native main-power art has no external copy or independent caption frames. */
#furo-main-content #marche-arret .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #marche-arret .hb-operation-supporting-copy > .line:first-child { font-weight: 400; }
#furo-main-content #marche-arret .hb-operation-supporting-copy > .line:last-child {
  padding: 1.2cqw 1.8cqw;
  border-radius: 2.4cqw;
  background: var(--hb-surface);
}
@media (min-width: 761px) {
  #furo-main-content #marche-arret .hb-operation-step-label { font-size: 3.1546cqw; }
  #furo-main-content #marche-arret .hb-operation-step-instruction { font-size: 1.8927cqw; }
  #furo-main-content #marche-arret .hb-operation-duration { font-size: 2.2082cqw; }
  #furo-main-content #marche-arret .hb-operation-supporting-copy:has(> .line:nth-child(4):last-child) {
    margin-top: -12.5cqw;
    grid-template-columns: 43% minmax(0, 1fr);
    padding-inline: 4.4cqw;
    font-size: 1.8927cqw;
  }
  #furo-main-content #marche-arret .hb-operation-supporting-copy:has(> .line:nth-child(4):last-child) > .line:last-child { margin-top: 1.2cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #marche-arret .hb-operation-supporting-copy > .line:last-child { padding: 0.7rem; border-radius: 0.8rem; }
  #furo-main-content #marche-arret .hb-operation-art-box > .hb-operation-duration { display: block; font-size: max(.5rem, 2.2082cqw); }
}

/* USB native artwork retains only product markings and connection geometry. */
#furo-main-content #sortie-usb-marche-arret .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #sortie-usb-marche-arret .hb-operation-prerequisite { background: var(--hb-fill); font-weight: 400; }
@media (min-width: 761px) {
  #furo-main-content #sortie-usb-marche-arret .hb-operation-step-label { font-size: 3.1546cqw; }
  #furo-main-content #sortie-usb-marche-arret .hb-operation-step-instruction { font-size: 1.8927cqw; }
  #furo-main-content #sortie-usb-marche-arret .hb-operation-prerequisite { font-size: 2.082cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #sortie-usb-marche-arret .hb-operation-art-box { display: flex; flex-direction: column; }
  #furo-main-content #sortie-usb-marche-arret .hb-operation-prerequisite {
    position: static; order: -1; width: auto; max-width: none; min-width: 0;
    margin: 0.65rem 0.65rem 0; padding: 0.5rem 0.75rem; border-radius: 0.8rem;
  }
}

/* AC native artwork retains only product markings and connection geometry. */
#furo-main-content #sortie-ca-marche-arret .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #sortie-ca-marche-arret .hb-operation-prerequisite { background: var(--hb-fill); font-weight: 400; }
@media (min-width: 761px) {
  #furo-main-content #sortie-ca-marche-arret .hb-operation-step-label { font-size: 3.1646cqw; }
  #furo-main-content #sortie-ca-marche-arret .hb-operation-step-instruction { font-size: 1.8987cqw; }
  #furo-main-content #sortie-ca-marche-arret .hb-operation-prerequisite { font-size: 2.0886cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #sortie-ca-marche-arret .hb-operation-art-box { display: flex; flex-direction: column; }
  #furo-main-content #sortie-ca-marche-arret .hb-operation-prerequisite {
    position: static; order: -1; width: auto; max-width: none; min-width: 0;
    margin: 0.65rem 0.65rem 0; padding: 0.5rem 0.75rem; border-radius: 0.8rem;
  }
}

/* Native energy-saving copy flows above the lower artwork; anchors use artwork only. */
#furo-main-content #mode-deconomie-denergie .hb-operation-stage { display: flex; flex-direction: column; border-color: #e6e7e8; }
#furo-main-content #mode-deconomie-denergie .hb-operation-supporting-copy {
  order: -1; position: static; width: auto; margin: 1rem 1rem 0.8rem; padding: 1rem 1.2rem;
  background: #ebebec; border: 0; border-radius: 1.2rem; font-size: 1rem; line-height: 1.5;
}
#furo-main-content #mode-deconomie-denergie .hb-operation-supporting-copy > .line { margin: 0; }
#furo-main-content #mode-deconomie-denergie .hb-operation-canvas > .hb-operation-steps {
  position: absolute; display: block; inset: 0; padding: 0; border: 0;
}
#furo-main-content #mode-deconomie-denergie .hb-operation-step {
  position: absolute; top: var(--hb-step-y); left: var(--hb-step-x); width: var(--hb-step-width);
}
#furo-main-content #mode-deconomie-denergie .hb-operation-step-instruction { font-size: max(.5rem, 1.735cqw); line-height: 1.1; white-space: nowrap; }
#furo-main-content #mode-deconomie-denergie [data-step-id="toggle"] .hb-operation-step-label { font-size: max(.5rem, 3.1546cqw); line-height: 1.1; }
#furo-main-content #mode-deconomie-denergie [data-step-id="toggle"] .hb-operation-step-instruction { font-size: max(.5rem, 1.8927cqw); }
#furo-main-content #mode-deconomie-denergie .hb-operation-art-box > .hb-operation-duration { display: block; font-size: max(.5rem, 2.2082cqw); }
@media (max-width: 760px) {
  #furo-main-content #mode-deconomie-denergie .hb-operation-supporting-copy { margin: .65rem .65rem .6rem; padding: .75rem; }
}

#furo-main-content #mode-deconomie-denergie .hb-operation-step[data-step-id="toggle"] { width: 32%; }

/* Native two-placement geometry; shared ReferenceFigure draws live caption pills. */
#furo-main-content [data-reference-id="battery-placement"] .hb-reference-art-panel::before,
#furo-main-content [data-reference-id="battery-placement"] .hb-reference-art-panel::after {
  content: ""; position: absolute; box-sizing: border-box; pointer-events: none; z-index: 1;
  border: max(1px, .25cqw) solid #e6e7e8; border-radius: 1.6cqw;
}
#furo-main-content [data-reference-id="battery-placement"] .hb-reference-art-panel::before { left: 0.6092%; top: 0.9403%; width: 48.8035%; height: 97.7456%; }
#furo-main-content [data-reference-id="battery-placement"] .hb-reference-art-panel::after { left: 50.6754%; top: 0.9403%; width: 48.5256%; height: 97.7456%; }
#furo-main-content [data-reference-id="battery-placement"] .hb-reference-live-label { z-index: 2; font-size: max(.5rem, 2.09cqw); }
#furo-main-content [data-reference-id="battery-placement"] [data-source-line="2"] { font-size: max(.5rem, 1.92cqw); white-space: nowrap; width: 21%; }
@media (max-width: 480px) {
  #furo-main-content [data-reference-id="battery-placement"] [data-source-line="2"] { left: 4%; width: 43%; justify-content: center; }
}

/* Native ATS labels retain source alignment above the operation views and cable leader. */
#furo-main-content [data-reference-id="ats-lock"] .hb-reference-live-label { font-size: max(.5rem, 2.1073cqw); }
#furo-main-content [data-reference-id="ats-lock"] [data-source-line="2"] { font-size: max(.5rem, 1.9048cqw); justify-content: center; text-align: center; }
@media (max-width: 480px) {
  #furo-main-content [data-reference-id="ats-lock"] [data-source-line="2"] { top: 41.5%; }
}

/* Native MTS steps/cable captions use shared ReferenceFigure with source geometry. */
#furo-main-content [data-reference-id="mts-single"] .hb-reference-live-label { font-size: max(.5rem, 1.8987cqw); align-items: flex-start; }
#furo-main-content [data-reference-id="mts-single"] .hb-mts-step { display: grid; grid-template-columns: 4.3cqw minmax(0,1fr); width: 100%; }
#furo-main-content [data-reference-id="mts-single"] .hb-mts-step-number { font-size: 3.1646cqw; line-height: 1.16; padding: .34cqw 0 0 .63cqw; }
#furo-main-content [data-reference-id="mts-single"] .hb-mts-step-body { display: block; line-height: 1.18; }
#furo-main-content [data-reference-id="mts-single"] [data-source-line="0"] .hb-mts-step-body { line-height: 1.5; }
#furo-main-content [data-reference-id="mts-single"] [data-source-line="6"] { text-align: center; }
@media (max-width: 760px) {
  #furo-main-content [data-reference-id="mts-single"] .hb-reference-art-panel { display: grid; grid-template-columns: minmax(0,1fr); }
  #furo-main-content [data-reference-id="mts-single"] .hb-reference-art { grid-column: 1; grid-row: 6; align-self: start; }
  #furo-main-content [data-reference-id="mts-single"] .hb-reference-live-label:has(.hb-mts-step) { position: static; display: block; grid-column: 1; width: auto; min-height: 0; margin: 0; padding: .55rem .9rem; background: #e6e7e8; font-size: 1rem; }
  #furo-main-content [data-reference-id="mts-single"] .hb-mts-step { grid-template-columns: 1.6rem minmax(0,1fr); }
  #furo-main-content [data-reference-id="mts-single"] .hb-mts-step-number { font-size: 1rem; line-height: 1.5; padding: 0; }
  #furo-main-content [data-reference-id="mts-single"] .hb-mts-step-body { line-height: 1.5; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="0"] { border-radius: 1rem 1rem 0 0; padding-top: .9rem; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="4"] { border-radius: 0 0 1rem 1rem; padding-bottom: .9rem; margin-bottom: .75rem; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="5"],
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="6"] { position: static; display: block; grid-column: 1; grid-row: 6; align-self: start; min-height: 0; margin-bottom: 0; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="5"] { margin-left: 32%; margin-top: 6.5cqw; width: 35%; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="6"] { margin-left: 66%; margin-top: 57.4266cqw; width: 32%; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="0"] { grid-row: 1; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="1"] { grid-row: 2; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="2"] { grid-row: 3; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="3"] { grid-row: 4; }
  #furo-main-content [data-reference-id="mts-single"] [data-source-line="4"] { grid-row: 5; }
}

/* Native cascade MTS geometry; shared ReferenceFigure holds all external copy. */
#furo-main-content [data-reference-id="mts-cascade"] .hb-reference-live-label { font-size: max(.5rem,1.8927cqw); align-items: flex-start; }
#furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step { display: grid; grid-template-columns: 4.3cqw minmax(0,1fr); width: 100%; }
#furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step-number { font-size: 3.1546cqw; line-height: 1.16; padding: .34cqw 0 0 .63cqw; }
#furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step-body { display: block; line-height: 1.18; }
#furo-main-content [data-reference-id="mts-cascade"] [data-source-line="0"] .hb-mts-step-body { line-height: 1.5; }
#furo-main-content [data-reference-id="mts-cascade"] [data-source-line="4"],
#furo-main-content [data-reference-id="mts-cascade"] [data-source-line="5"] { text-align: center; }
@media (max-width: 760px) {
 #furo-main-content [data-reference-id="mts-cascade"] .hb-reference-art-panel { display: grid; grid-template-columns: minmax(0,1fr); }
 #furo-main-content [data-reference-id="mts-cascade"] .hb-reference-art { grid-column: 1; grid-row: 4; align-self: start; }
 #furo-main-content [data-reference-id="mts-cascade"] .hb-reference-live-label:has(.hb-mts-step) { position: static; display: block; grid-column: 1; width: auto; min-height: 0; margin: 0; padding: .55rem .9rem; background: #e6e7e8; font-size: 1rem; }
 #furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step { grid-template-columns: 1.6rem minmax(0,1fr); }
 #furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step-number { font-size: 1rem; line-height: 1.5; padding: 0; }
 #furo-main-content [data-reference-id="mts-cascade"] .hb-mts-step-body { line-height: 1.5; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="0"] { grid-row: 1; border-radius: 1rem 1rem 0 0; padding-top: .9rem; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="1"] { grid-row: 2; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="2"] { grid-row: 3; border-radius: 0 0 1rem 1rem; padding-bottom: .9rem; margin-bottom: .75rem; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="3"],
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="4"],
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="5"] { position: static; display: block; grid-column: 1; grid-row: 4; align-self: start; min-height: 0; margin-bottom: 0; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="3"] { margin-left: 8.5174%; margin-top: 28.2cqw; width: 25%; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="4"] { margin-left: 40%; margin-top: 40cqw; width: 38%; }
 #furo-main-content [data-reference-id="mts-cascade"] [data-source-line="5"] { margin-left: 68%; margin-top: 87.7cqw; width: 30%; }
}

/* Native longer button copy wraps inside the shared operation geometry. */
#furo-main-content .hb-operation-step-label,
#furo-main-content .hb-operation-step-label strong,
#furo-main-content .hb-operation-step-instruction { white-space: normal !important; overflow-wrap: anywhere !important; }

</style>

# Jackery HomePower 3600 Pro Max — Manuel d’utilisation

<span id="important"></span>

## IMPORTANT

<p>Félicitations pour votre nouveau Jackery HomePower 3600 Pro Max. Veuillez lire attentivement ce manuel avant d'utiliser le produit, en particulier les précautions à prendre pour garantir une utilisation correcte du produit. Conservez ce manuel dans un endroit accessible pour pouvoir vous y référer ultérieurement.</p>

<p>Conformément aux lois et réglementations en vigueur, le droit d'interprétation final de ce document et de tous les documents associés à ce produit appartient à l'entreprise. Bien que tous les efforts aient été déployés pour garantir l'exactitude de ce manuel, Jackery Inc. n'assume aucune responsabilité pour les erreurs qui pourraient y figurer.</p>

<p>Veuillez noter qu'aucune autre notification ne sera faite en cas de mise à jour, de révision ou de résiliation. Pour la dernière version des manuels du produit, consultez support.jackery.com.</p>

<p>* Les chiffres sont donnés à titre indicatif uniquement. Veuillez vous référer au produit réel.</p>

<span id="safety"></span>

# INFORMATIONS DE SÉCURITÉ IMPORTANTES

<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="manual-callout-table manual-callout-table hb-symbol-signal-table"><tbody><tr><td class="manual-callout-label hb-symbol-signal-label-cell"><span class="hb-source-risk-label"><img alt="" src="assets/e1746d6937db_warning_triangle_dark.svg"/><strong>AVERTISSEMENT</strong></span></td><td class="manual-callout-body hb-symbol-signal-meaning-cell"><p>INSTRUCTIONS CONCERNANT LES RISQUES D’INCENDIE, DE CHOC ÉLECTRIQUE OU DE BLESSURES</p></td></tr></tbody></table></figure>

<table class="manual-two-col-table"><tbody><tr><td><p>Respectez toujours les précautions de base lors de l’utilisation de ce produit.</p><ul><li>Lisez toutes les instructions avant d’utiliser le produit.</li><li>Ne laissez pas les enfants jouer avec du produit. Une surveillance étroite est nécessaire lorsque le produit est utilisé à proximité d’enfants.</li><li>Évitez de placer les mains ou les doigts à l’intérieur du produit.</li><li>Arrêtez immédiatement d’utiliser le produit s’il a été endommagé physiquement ou modifié. Une mauvaise utilisation peut entraîner un comportement imprévisible, un incendie, une explosion ou des blessures.</li><li>Si vous constatez une surchauffe, une odeur inhabituelle, de la fumée, des fuites ou des brûlures, cessez immédiatement l’utilisation et contactez le revendeur ou notre service client.</li><li>Ne tentez jamais d’ouvrir, de réparer ou de modifier le produit. Toute altération ou réassemblage peut entraîner un choc électrique, un incendie ou des dommages à la batterie.</li></ul></td><td><ul><li>Soyez conscient que le liquide éjecté peut causer une irritation ou des brûlures. Une mauvaise utilisation peut provoquer des fuites. Évitez tout contact direct. En cas de contact avec les yeux, consultez immédiatement un médecin. En cas de contact avec la peau, rincez abondamment à l’eau claire et consultez un professionnel de santé sans tarder.</li><li>N’exposez pas le produit au feu ni à des températures excessives. Une température supérieure à 130 °C peut entraîner une explosion.</li><li>L’utilisation de pièces non recommandées ou non fournies peut entraîner un risque d’incendie, de choc électrique ou de blessures.</li><li>Ne laissez jamais la batterie en charge sans surveillance pendant de longues périodes. Surveillez toujours la charge pour assurer une utilisation sûre.</li><li>Pour réduire le risque de choc électrique, débranchez le produit de toute source d’alimentation avant d’effectuer un entretien technique ou un dépannage.</li></ul></td></tr></tbody></table>

## INSTRUCTIONS D’UTILISATION

<table class="manual-two-col-table"><tbody><tr><td><p>CONSERVEZ CES INSTRUCTIONS</p><ul><li>Cessez immédiatement d’utiliser le produit s’il présente des signes de dommage. Arrêtez l’utilisation et contactez l’assistance clientèle pour obtenir de l’aide.</li><li>Ne rechargez pas la batterie dans un environnement extrêmement chaud ou froid, et respectez strictement les plages de températures d’utilisation spécifiées du produit :<ul><li>Température de charge : -4°F à 113°F (-20 °C à 45 °C)</li><li>Température de décharge : -4°F à 113°F (-20 °C à 45 °C)</li></ul></li><li>Pour garantir une bonne circulation de l’air, gardez les orifices de ventilation du produit dégagés. Utilisez-le dans un endroit bien aéré, frais et sec pour éviter toute surchauffe.<ul><li>La charge dans un environnement humide ou mal ventilé peut présenter des risques pour la sécurité.</li><li>L’eau peut provoquer des courts-circuits ou endommager le chargeur, entraînant des risques.</li></ul></li><li>Débranchez le cordon d’alimentation de la prise secteur pendant un orage.</li><li>Éteignez immédiatement le produit à l’aide du bouton d’alimentation s’il est tombé, a subi un choc ou des vibrations.</li></ul></td><td><ul><li>Assurez-vous que les appareils sont éteints avant de les connecter au produit.</li><li>Ne rechargez pas le produit avec un câble ou une fiche endommagé(e).</li><li>N’utilisez pas le produit pour charger un appareil équipé d’un câble ou d’une fiche endommagé(e).</li><li>Débranchez toujours le cordon de charge en tirant sur la fiche, jamais sur le câble, afin d’éviter tout dommage.</li><li>Veillez à ce que le produit soit correctement fixé lors du transport dans un véhicule en mouvement.</li><li>NE placez PAS l’appareil à l’envers ou sur le côté pendant l’utilisation ou le stockage.</li><li>NE placez PAS le produit sur le sol ou à une hauteur inférieure à 457 mm (18 pouces) lors de son utilisation dans un atelier ou un centre de réparation.</li><li>N’utilisez PAS les accessoires du produit avec d’autres appareils ou équipements.</li><li>Le temps de charge solaire dépend des conditions météorologiques. Placez le panneau solaire dans un endroit exposé au soleil direct autant que possible.</li></ul></td></tr></tbody></table>

## INSTRUCTION DE MISE À LA TERRE

<p>Ce produit doit être mis à la terre. En cas de dysfonctionnement ou de panne, la mise à la terre fournit un chemin de moindre résistance au courant électrique afin de réduire le risque de choc électrique. Ce produit est équipé d'un cordon avec un conducteur de mise à la terre et d'une fiche de mise à la terre. La fiche doit être branchée dans une prise correctement installée et mise à la terre conformément à tous les codes et règlements locaux.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">AVERTISSEMENT</td><td class="manual-callout-body"><p>Une connexion incorrecte du conducteur de mise à la terre peut entraîner un risque de choc électrique. Consultez un électricien qualifié si vous avez des doutes quant à la mise à la terre correcte du produit. Ne modifiez pas la fiche fournie avec le produit – si elle ne correspond pas à la prise, faites installer une prise appropriée par un électricien qualifié.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">AVERTISSEMENT</td><td class="manual-callout-body"><p>Cet appareil est destiné à un usage intérieur uniquement (veuillez placer cet appareil dans un environnement intérieur similaire lors de son utilisation à l'extérieur, par exemple dans des VR résidentiels, des tentes, des chalets, etc.). ※ Cet appareil n'est pas étanche ni résistant à la poussière. Éloignez-le de la pluie et des environnements humides pendant son utilisation.</p></td></tr></tbody></table>

## INSTRUCTIONS D’ENTRETIEN PAR L’UTILISATEUR

<p>Au cours du cycle des produits de stockage d'énergie, une certaine dégradation de la capacité et de l'énergie se produira. À mesure que le nombre de cycles d'utilisation augmente et que la durée de stockage s'allonge, cette dégradation s'intensifiera progressivement, ce qui est un phénomène normal conforme au modèle de vieillissement naturel des cellules de batterie.</p>

<span id="symbols"></span>

# SIGNIFICATION DES SYMBOLES

<figure aria-label="SIGNIFICATION DES SYMBOLES" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col"><p>Symbole</p></th><th class="hb-symbol-signal-meaning-heading" scope="col"><p>Signification</p></th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="AVERTISSEMENT" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">AVERTISSEMENT</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ATTENTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ATTENTION</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Pratiques dangereuses pouvant entraîner des blessures corporelles et/ou des dommages matériels.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="REMARQUE" class="hb-signal-badge"><span class="hb-signal-label">REMARQUE</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Pratiques dangereuses pouvant entraîner des dommages à l'équipement, une perte de données, une détérioration des performances ou des résultats inattendus.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEILS" class="hb-signal-badge"><span class="hb-signal-label">CONSEILS</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Complémente les informations importantes ou les conseils d'utilisation dans le texte.</p></td></tr></tbody></table></figure>

<figure aria-label="Symboles de sécurité" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Mlise en garde! Le non-respect des messages d'avertissement peut entraîner des blessures." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Mlise en garde! Le non-respect des messages d'avertissement peut entraîner des blessures.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lire le manuel de l'opérateur" class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Lire le manuel de l'opérateur</td></tr><tr><td class="hb-symbol-icon"><img alt="Risque de choc électrique" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Risque de choc électrique</td></tr><tr><td class="hb-symbol-icon"><img alt="Chargement de la batterie" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Chargement de la batterie</td></tr><tr><td class="hb-symbol-icon"><img alt="Matière explosive" class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Matière explosive</td></tr><tr><td class="hb-symbol-icon"><img alt="Objet lourd" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Objet lourd</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Ne démontez pas le produit." class="hb-symbol-art" src="assets/symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">Ne démontez pas le produit.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ne pas fumer ni utiliser de ﬂamme nue" class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Ne pas fumer ni utiliser de ﬂamme nue</td></tr><tr><td class="hb-symbol-icon"><img alt="Les enfants ne sont pas admis" class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Les enfants ne sont pas admis</td></tr><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée." class="hb-symbol-art" src="assets/symbol_li_ion.svg"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères. Il doit être apporté à un point de collecte désigné pour un recyclage approprié. Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères. Il doit être apporté à un point de collecte désigné pour un recyclage approprié. Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<div class="hb-fcc-balanced-flow"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/45f309ed8b3f_fcc_mark.png"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">Cet appareil est conforme à la partie 15 du règlement de la FCC. Le fonctionnement dépend des deux conditions suivantes : (1) Cet appareil ne doit pas provoquer d'interférences dangereuses, et (2) Cet appareil doit accepter toute interférence reçue, y compris les interférences pouvant provoquer un fonctionnement non désiré.</div></div></div></div><p><strong>REMARQUE :</strong> Cet équipement a été testé et déclaré conforme aux limites concernant les appareils numériques de classe B, conformément à la partie 15 du règlement de la FCC. Ces limites sont conçues pour offrir une protection raisonnable contre les interférences dangereuses dans le cadre d'une installation résidentielle. Cet équipement génère, utilise et émet des ondes radios qui peuvent, si cet équipement n'est pas installé et utilisé conformément aux instructions, perturber les communications radios. Toutefois, il n'y a aucune garantie qu'aucune interférence ne se produise lors d'une installation particulière. Si cet équipement trouble la réception de la radio ou de la télévision, ce qui peut être déterminé en éteignant et en allumant cet équipement, l'utilisateur est encouragé à tenter de corriger ces interférences en essayant une ou plusieurs des mesures suivantes :</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Réorientez ou déplacez l'antenne de réception.</p></li><li><p>Éloignez l'équipement du récepteur.</p></li><li><p>Connectez l'équipement à une prise d'un autre circuit que celui auquel le récepteur est connecté.</p></li><li><p>Consultez le revendeur ou bien demandez de l'aide à un technicien de radio/télévision expérimenté.</p></li></ul><p><strong>MODIFICATION :</strong> Tout changement ou modification non expressément approuvé par le titulaire de cet appareil pourrait annuler l'autorisation de l'utilisateur à utiliser l'appareil.</p></div></div></figure></div>

<span id="inbox"></span>

# CONTENU DE LA BOÎTE

<figure aria-label="CONTENU DE LA BOÎTE" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 3600 Pro Max" class="hb-inbox-art" src="assets/inbox_unit.png"/><div class="hb-inbox-label"><p>Jackery HomePower 3600 Pro Max</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Câble de charge CA" class="hb-inbox-art" src="assets/inbox_ac.png"/><div class="hb-inbox-label"><p>Câble de charge CA</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Bornier à vis" class="hb-inbox-art" src="assets/inbox_terminal.png"/><div class="hb-inbox-label"><p>Bornier à vis</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Documents" class="hb-inbox-art" src="assets/87ac44e52863_manual_icon1.png"/><div class="hb-inbox-label"><p>Documents</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">CONSEILS</div><div class="hb-inbox-tip-body">Le câble de chargement pour voiture n’est pas inclus, mais peut être acheté séparément sur notre site Web. Pour obtenir de l’aide, veuillez contacter le service à la clientèle de Jackery.</div></div></figure>

<span id="overview"></span>

# APERÇU DU PRODUIT

## VUE DE FACE

<img alt="LCD Sortie CA (NEMA 14-50R) 240V~ 60Hz, 16.7A Max, 4000W Max Bouton d’alimentation principale Sortie USB-C 100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A Sortie CA (NEMA 5-20R) 120V~ 60Hz, 16.7A Max, 2000W per port, 4000W in Total L1 et L2 respectivement de gauche à droite Sortie USB-A 18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A Bouton d’alimentation CA Bouton d'alimentation USB" src="assets/overview_front.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## VUE LATÉRALE DROITE

<img alt="EPO (Arrêt d’urgence de l’alimentation) Communication parallèle Pour connexion à un bouton d’arrêt d’urgence externe Entrée CA 100 V-120 V~60 Hz, 15 A max. Entrée CC (2×Ports DC8020) 12-16 V⎓8 A max., double à 8 A max. 16–60 V⎓12 A max., double à 24 A/1200 W max. Pour la connexion de communication en fonctionnement parallèle en cascade Port d’extension CC Connexion au bloc-batterie Pour connexion ATS ou connexion parallèle en cascade Entrée/Sortie : 240 V~60 Hz, 16,7 A max., 4000 W Port d’extension CA" src="assets/overview_side.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<span id="lcd"></span>

# AFFICHAGE LCD

<img alt="Repères numérotés de l’écran LCD, 1–31." src="assets/lcd_map.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<figure aria-label="AFFICHAGE LCD" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><p>1</p></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/fc4cc02b42ef_fc4cc02b42ef_fc4cc02b42ef_1_Wi-Fi_KCcAbdDk7o4RjKx82micuKJ5nyf.png"/></td><td class="hb-lcd-name"><p>Wi-Fi</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Wi-Fi connecté.<br/><strong>Clignotant :</strong> Prêt à se connecter au Wi-Fi.<br/><strong>Éteint :</strong> Wi-Fi déconnecté.</p></td></tr><tr><td class="hb-lcd-number"><p>2</p></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/7e1392ba6a45_7e1392ba6a45_7e1392ba6a45_2_Bluetooth_HVgvbJhq5o4EDKxhm7McCF4FnjB.png"/></td><td class="hb-lcd-name"><p>Bluetooth</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Bluetooth connecté.<br/><strong>Clignotant :</strong> Prêt à se connecter au Bluetooth.<br/><strong>Éteint :</strong> Bluetooth déconnecté.</p></td></tr><tr><td class="hb-lcd-number"><p>3</p></td><td class="hb-lcd-icon"><img alt="Mode de Charge Silencieuse" class="hb-lcd-icon-art" src="assets/7f743182c050_7f743182c050_7f743182c050_3_Quiet_Charging_Mode_WLkMbiHS1oGsOtxUCp7cRhFAn1g.png"/></td><td class="hb-lcd-name"><p>Mode de Charge Silencieuse</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Le bruit pendant la charge est considérablement réduit, tandis que la puissance de charge est diminuée et la vitesse de charge ralentit.<br/><strong>Éteint :</strong> Le mode de charge silencieuse est désactivé. Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>4</p></td><td class="hb-lcd-icon"><img alt="Mode d’Économie de Batterie" class="hb-lcd-icon-art" src="assets/e32e6ae96321_e32e6ae96321_e32e6ae96321_15_Battery_Saving_Mode_ClYfbtOGSoK5q2xySXCcgehVn8f.png"/></td><td class="hb-lcd-name"><p>Mode d’Économie de Batterie</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Limite la capacité maximale utilisable de la batterie pour prolonger sa durée de vie.<br/><strong>Éteint :</strong> Le mode d'économie de batterie est désactivé. Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.<br/><strong>Note 1:</strong> Cette fonction n'est pas disponible lorsque le produit est connecté à des blocs-batteries.<br/><strong>Note 2 :</strong> Lorsque cette fonction est activée, le produit effectue occasionnellement un cycle de charge-décharge complet pour calibrer le SOC.</p></td></tr><tr><td class="hb-lcd-number"><p>5</p></td><td class="hb-lcd-icon"><img alt="Plan de Charge" class="hb-lcd-icon-art" src="assets/71017f43bab4_71017f43bab4_71017f43bab4_4_Charging_Plan_M96RbyZQxoGjRRxQHsuczeIln1b.png"/></td><td class="hb-lcd-name"><p>Plan de Charge</p></td><td class="hb-lcd-description"><p>Personnalisez le temps de charge du Jackery HomePower 3600 Plus. Adapté aux situations avec des tarifs d’électricité variables, il permet d’établir des plans de charge en fonction des heures pleines et creuses, afin de réduire les coûts d’électricité. Veuillez configurer cette fonction dans l’application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>6</p></td><td class="hb-lcd-icon"><img alt="Limite de puissance de charge" class="hb-lcd-icon-art" src="assets/21b5f19ca9a6_21b5f19ca9a6_21b5f19ca9a6_16_Charging_Power_Limit_VLf2bJfrkoCL0CxJoMNcL5ZxnCt.png"/></td><td class="hb-lcd-name"><p>Limite de puissance de charge</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> La limite de puissance de charge est activée dans l’application Jackery.<br/><strong>Éteint :</strong> La limite de puissance de charge est désactivée dans l’application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>7</p></td><td class="hb-lcd-icon"><img alt="Mode Autonome" class="hb-lcd-icon-art" src="assets/73225cf9faa8_73225cf9faa8_73225cf9faa8_5_Self-powered_Mode_FYTnb9vttoexjbxVMchcJaobnCg.png"/></td><td class="hb-lcd-name"><p>Mode Autonome</p></td><td class="hb-lcd-description"><p>Maximise l’utilisation de l’énergie solaire et réduit la dépendance à l’électricité du réseau en donnant la priorité à l’énergie solaire stockée, ce qui diminue les coûts d’électricité. La station d’énergie doit être connectée simultanément aux panneaux solaires et au réseau, la puissance de charge étant limitée par la puissance de dérivation. Activez/désactivez cette fonction dans l’application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>8</p></td><td class="hb-lcd-icon"><img alt="Mode TOU" class="hb-lcd-icon-art" src="assets/f4cdcb551105_f4cdcb551105_f4cdcb551105_6_TOU_Mode_BjEkbz0rFo6Bw4xiwNpcod9qnnc.png"/></td><td class="hb-lcd-name"><p>Mode TOU</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Le mode TOU est activé (SOC de secours par défaut : 60 %). Pendant les heures de pointe, le produit privilégie la décharge de la batterie afin de réduire les coûts liés à la consommation en période de pointe, lorsque l’énergie stockée dépasse le SOC de réserve. Pendant les heures creuses, le système recharge la batterie à partir du réseau afin de réaliser l’écrêtage des pics et le remplissage des creux.<br/><strong>Éteint :</strong> Le mode TOU est désactivé. L’appareil ne suit pas la stratégie TOU (heures pleines / heures creuses) et fonctionne selon la logique d’alimentation et de charge par défaut. Activez/désactivez cette fonction dans l’application Jackery. Le réglage est conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>9</p></td><td class="hb-lcd-icon"><img alt="Parallèle" class="hb-lcd-icon-art" src="assets/lcd_parallel.png"/></td><td class="hb-lcd-name"><p>Parallèle</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> La connexion parallèle est établie avec succès.<br/><strong>Clignotant :</strong> La connexion parallèle est en cours de configuration.<br/><strong>Éteint :</strong> La connexion parallèle n’est pas établie.</p></td></tr><tr><td class="hb-lcd-number"><p>10</p></td><td class="hb-lcd-icon"><img alt="UPS (ASI)" class="hb-lcd-icon-art" src="assets/e422a56922eb_e422a56922eb_e422a56922eb_7_UPS_Lgdgb8pvvoGwaLxSf8ec2QeHn3c.png"/></td><td class="hb-lcd-name"><p>UPS (ASI)</p></td><td class="hb-lcd-description"><p>L’indicateur UPS reste allumé lorsque l’alimentation du réseau est disponible et s’éteint en cas de coupure du réseau.</p></td></tr><tr><td class="hb-lcd-number"><p>11</p></td><td class="hb-lcd-icon"><img alt="Indicateur d’alimentation CA" class="hb-lcd-icon-art" src="assets/8be87c5a0849_8be87c5a0849_8be87c5a0849_8_AC_Power_Indicator_HFPSbvWBgosvCux69jMcuWe6nnh.png"/></td><td class="hb-lcd-name"><p>Indicateur d’alimentation CA</p></td><td class="hb-lcd-description"><p>La sortie CA (onde sinusoïdale pure) est activée.</p></td></tr><tr><td class="hb-lcd-number"><p>12</p></td><td class="hb-lcd-icon"><img alt="Tension et fréquence de sortie" class="hb-lcd-icon-art" src="assets/7623ef10e229_7623ef10e229_7623ef10e229_9_Output_Voltage_and_Frequency_Jh3JbmBDBoKlmOxaRJDcIMJAn6b.png"/></td><td class="hb-lcd-name"><p>Tension et fréquence de sortie</p></td><td class="hb-lcd-description"><p>Affiche la tension et la fréquence de sortie lorsque la sortie CA est activée via le bouton d’alimentation CA ou lorsque le port d’extension CA fournit de l’énergie. • 120 V : Affiché lorsque le produit se recharge à partir de l’entrée CA 120 V tout en fournissant simultanément de l’énergie via les ports de sortie CA. • 120/240 V : Affiché lorsque la sortie CA 240 V est active, ou lorsque le produit est connecté à un commutateur de transfert et fonctionne en mode bypass.</p></td></tr><tr><td class="hb-lcd-number"><p>13</p></td><td class="hb-lcd-icon"><img alt="Puissance d’Entrée" class="hb-lcd-icon-art" src="assets/d5100a538e96_d5100a538e96_d5100a538e96_10_Input_Power_LOAZbnxfqoHFwIxx2Myc532jnzb.png"/></td><td class="hb-lcd-name"><p>Puissance d’Entrée</p></td><td class="hb-lcd-description"><p>Affiche la puissance d’entrée CA utilisée pour la charge de la batterie en watts.</p></td></tr><tr><td class="hb-lcd-number"><p>14</p></td><td class="hb-lcd-icon"><img alt="Temps de Charge Restant" class="hb-lcd-icon-art" src="assets/cfb69b1ffc0b_cfb69b1ffc0b_cfb69b1ffc0b_11_Remaining_Charge_Time_KIWHbHFOvotGuBxJsxlcunSDnPf.png"/></td><td class="hb-lcd-name"><p>Temps de Charge Restant</p></td><td class="hb-lcd-description"><p>Affiche le temps de charge restant.</p></td></tr><tr><td class="hb-lcd-number"><p>15</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Charge sur Prise Murale CA" class="hb-lcd-icon-art" src="assets/28f3cad42ae3_28f3cad42ae3_28f3cad42ae3_12_AC_Wall_Charging_Indicator_ZpOmbCjx8oYUTVxyl4JcvcTanPe.png"/></td><td class="hb-lcd-name"><p>Indicateur de Charge sur Prise Murale CA</p></td><td class="hb-lcd-description"><p>Le produit est chargé via l’entrée CA en utilisant l’énergie du réseau.</p></td></tr><tr><td class="hb-lcd-number"><p>16</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Charge Voiture" class="hb-lcd-icon-art" src="assets/eed3299c3f6a_eed3299c3f6a_eed3299c3f6a_13_Car_Charging_Indicator_DLkibYaP1ot6d5x1S0jcUr1knlb.png"/></td><td class="hb-lcd-name"><p>Indicateur de Charge Voiture</p></td><td class="hb-lcd-description"><p>Le produit est chargé via l’entrée CC (DC8020) en utilisant du CC 12 V (charge via voiture).</p></td></tr><tr><td class="hb-lcd-number"><p>17</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Charge Solaire" class="hb-lcd-icon-art" src="assets/91cec82eeaa5_91cec82eeaa5_91cec82eeaa5_14_Solar_Charging_Indicator_RgAUbPXNWoRxiHxKNgkc2gqDnEb.png"/></td><td class="hb-lcd-name"><p>Indicateur de Charge Solaire</p></td><td class="hb-lcd-description"><p>Le produit est chargé via l’entrée CC (DC8020) à l’aide de panneaux solaires.</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>18</p></td><td class="hb-lcd-icon"><img alt="Témoin d’expansion CA (En charge)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-in.png"/></td><td class="hb-lcd-name"><p>Témoin d’expansion CA (En charge)</p></td><td class="hb-lcd-description"><p>Le produit peut être chargé à partir du réseau via un commutateur de transfert automatique Jackery (ATS).</p></td></tr><tr><td class="hb-lcd-icon"><img alt="Témoin d’expansion CA (En décharge)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-out.png"/></td><td class="hb-lcd-name"><p>Témoin d’expansion CA (En décharge)</p></td><td class="hb-lcd-description"><p>Le produit alimente les charges de votre maison via le commutateur de transfert connecté (ATS).</p></td></tr><tr><td class="hb-lcd-number"><p>19</p></td><td class="hb-lcd-icon"><img alt="Indicateur de commutateur de transfert" class="hb-lcd-icon-art" src="assets/lcd_transfer-switch.png"/></td><td class="hb-lcd-name"><p>Indicateur de commutateur de transfert</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Le produit est correctement connecté à un commutateur de transfert (ATS).<br/><strong>Éteint :</strong> Le produit n’est pas connecté à un commutateur de transfert (ATS).</p></td></tr><tr><td class="hb-lcd-number"><p>20</p></td><td class="hb-lcd-icon"><img alt="Recharge de VE" class="hb-lcd-icon-art" src="assets/lcd_ev-charging.png"/></td><td class="hb-lcd-name"><p>Recharge de VE</p></td><td class="hb-lcd-description"><p>L’adaptateur de mise à la terre est connecté avec succès au produit.</p></td></tr><tr><td class="hb-lcd-number"><p>21</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Puissance de la Batterie" class="hb-lcd-icon-art" src="assets/85921a9ad7fb_85921a9ad7fb_85921a9ad7fb_17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"/></td><td class="hb-lcd-name"><p>Indicateur de Puissance de la Batterie</p></td><td class="hb-lcd-description"><p>Lorsque le produit est en charge, le cercle orange autour du pourcentage de batterie s’allume en séquence. Lorsqu’il charge d’autres appareils, le cercle orange reste allumé.</p></td></tr><tr><td class="hb-lcd-number"><p>22</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Batterie Faible" class="hb-lcd-icon-art" src="assets/c7862a87e742_c7862a87e742_c7862a87e742_19_Low_Battery_Indicator_KDk9bhs8poHUBdx96PLckPganhd.png"/></td><td class="hb-lcd-name"><p>Indicateur de Batterie Faible</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Le niveau de la batterie est inférieur à 20 %.<br/><strong>Clignotant :</strong> Le niveau de la batterie est inférieur à 5 %.<br/><strong>Éteint :</strong> Le niveau de la batterie n’est pas inférieur à 20 % ou le produit est en charge.</p></td></tr><tr><td class="hb-lcd-number"><p>23</p></td><td class="hb-lcd-icon"><img alt="Pourcentage de Batterie Restant" class="hb-lcd-icon-art" src="assets/747147be99d7_747147be99d7_747147be99d7_18_Remaining_Battery_Percentage_VkJcbUDbUoYC1hxrU6rc168OnJe.png"/></td><td class="hb-lcd-name"><p>Pourcentage de Batterie Restant</p></td><td class="hb-lcd-description"><p>Affiche le pourcentage de batterie restant.</p></td></tr><tr><td class="hb-lcd-number"><p>24</p></td><td class="hb-lcd-icon"><img alt="Indicateur de compteur intelligent" class="hb-lcd-icon-art" src="assets/lcd_smart-meter.png"/></td><td class="hb-lcd-name"><p>Indicateur de compteur intelligent</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Un compteur intelligent est en ligne.<br/><strong>Éteint :</strong> Aucun compteur intelligent n’est ajouté au système, ou le compteur intelligent est hors ligne.</p></td></tr><tr><td class="hb-lcd-number"><p>25</p></td><td class="hb-lcd-icon"><img alt="Minuterie de décharge" class="hb-lcd-icon-art" src="assets/6aab9a14900a_6aab9a14900a_6aab9a14900a_20_Discharge_Timer_DHPMbkjSWoiuALxJyJ8cWyQOn0e.png"/></td><td class="hb-lcd-name"><p>Minuterie de décharge</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> une minuterie de décharge est définie.<br/><strong>Éteint :</strong> aucune minuterie de décharge n’est définie. Activez/désactivez cette fonction dans l’application Jackery. Le réglage n’est pas conservé lorsque l’appareil est mis hors tension.</p></td></tr><tr><td class="hb-lcd-number"><p>26</p></td><td class="hb-lcd-icon"><img alt="Batteries connectées" class="hb-lcd-icon-art" src="assets/lcd_connected-batteries.png"/></td><td class="hb-lcd-name"><p>Batteries connectées</p></td><td class="hb-lcd-description"><p>Indique que le produit est connecté au nombre spécifié de blocs-batterie 3600.</p></td></tr><tr><td class="hb-lcd-number"><p>27</p></td><td class="hb-lcd-icon"><img alt="Mode d’Économie d’Énergie" class="hb-lcd-icon-art" src="assets/c4b830c769a3_c4b830c769a3_c4b830c769a3_22_Energy_Saving_Mode_O4Jdb5pUQoCBAqx0sfQcm9Nbntd.png"/></td><td class="hb-lcd-name"><p>Mode d’Économie d’Énergie</p></td><td class="hb-lcd-description"><p><strong>Allumé :</strong> Mode d’économie d’énergie activé.<br/><strong>Éteint :</strong> Mode d’économie d’énergie désactivé.</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>28</p></td><td class="hb-lcd-icon"><img alt="Indicateur de Température Élevée" class="hb-lcd-icon-art" src="assets/f548c6504f49_f548c6504f49_f548c6504f49_23_High_Temperature_Indicator_UmkEbOgCKoKyxoxDSINcfO6LnQd.png"/></td><td class="hb-lcd-name"><p>Indicateur de Température Élevée</p></td><td class="hb-lcd-description"><p>La protection contre les températures élevées est déclenchée. Le produit peut cesser de fonctionner jusqu’à ce que sa température revienne dans la plage de fonctionnement normale.</p></td></tr><tr><td class="hb-lcd-icon"><img alt="Indicateur de Basse Température" class="hb-lcd-icon-art" src="assets/bdbf602db74a_bdbf602db74a_bdbf602db74a_24_Low_Temperature_Indicator_JDMEbD96noSbyWxbOnVcgip1nab.png"/></td><td class="hb-lcd-name"><p>Indicateur de Basse Température</p></td><td class="hb-lcd-description"><p>La protection contre les basses températures est déclenchée. Le produit peut cesser de fonctionner jusqu’à ce que sa température revienne dans la plage de fonctionnement normale.</p></td></tr><tr><td class="hb-lcd-number"><p>29</p></td><td class="hb-lcd-icon"><img alt="Code d’erreur" class="hb-lcd-icon-art" src="assets/lcd_fault-code.png"/></td><td class="hb-lcd-name"><p>Code d’erreur</p></td><td class="hb-lcd-description"><p>Une erreur produit s’est produite. Veuillez consulter la section « Dépannage » pour plus de détails.</p></td></tr><tr><td class="hb-lcd-number"><p>30</p></td><td class="hb-lcd-icon"><img alt="Puissance de Sortie" class="hb-lcd-icon-art" src="assets/58c1d3604ca7_58c1d3604ca7_58c1d3604ca7_26_Output_Power_PviebR618oofvKxcKVRcHLlInqd.png"/></td><td class="hb-lcd-name"><p>Puissance de Sortie</p></td><td class="hb-lcd-description"><p>Affiche la puissance de sortie totale (CA + USB) en watts. Affiche OFF pendant 1 seconde avant l’arrêt du produit.</p></td></tr><tr><td class="hb-lcd-number"><p>31</p></td><td class="hb-lcd-icon"><img alt="Temps de Décharge Restant" class="hb-lcd-icon-art" src="assets/9b148ea95d3a_9b148ea95d3a_9b148ea95d3a_27_Remaining_Discharge_Time_JEpobf59DoBV4dxWlnxcNtIinke.png"/></td><td class="hb-lcd-name"><p>Temps de Décharge Restant</p></td><td class="hb-lcd-description"><p>Affiche le temps de décharge restant.</p></td></tr></tbody></table></figure>

<span id="operations"></span>

# FONCTIONNEMENT

## MARCHE/ARRÊT

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="main-power" data-source-fragment-sha256="a6327185830d6d31f89c2de32daa5f2714831b29e39072186bb32f5ca99ed55a" data-web-base-art-ref="assets/power_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/power_framefree.png"/><div aria-hidden="true" class="hb-operation-duration" data-duration-icon="none" style="--hb-x:79.06%;--hb-y:51.9%">3s</div></div><div class="line-block hb-operation-steps" data-callout-id="operation.main-power.steps"><div class="hb-operation-step" data-callout-id="operation.main-power.on" data-step-id="on" style="--hb-step-x:74.5%;--hb-step-y:16.963%;--hb-step-width:23%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Allumé</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Appuyez une fois</div></div><div class="hb-operation-step" data-callout-id="operation.main-power.off" data-step-id="off" style="--hb-step-x:74.5%;--hb-step-y:37.378%;--hb-step-width:23%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Éteint</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Appuyez et maintenez pendant 3 secondes</div></div></div></div><div class="hb-operation-supporting-copy" data-callout-id="operation.main-power.supporting-copy"><div class="line"><strong>Temps de veille par défaut : 2 heures</strong></div><div class="line">Le produit s’éteindra automatiquement après 2 heures d’inactivité, sans charge ni décharge. </div><div class="line">*Le temps de veille peut être réglé dans l'application Jackery.</div><div class="line">Lorsque le mode Économie d’énergie est active, le produit s’éteint automatiquement après 12 heures si le bouton d’alimentation CA ou USB est active, mais que le produit n’est ni en charge ni en décharge.</div></div></div></figure>

## SORTIE USB MARCHE/ARRÊT

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="dc-usb-output" data-source-fragment-sha256="a34467708aeb2e85b24563fe40b8a47c3651ce8830d40010556e589ac9adaf2d" data-web-base-art-ref="assets/usb_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/usb_framefree.png"/><div class="hb-operation-prerequisite" data-callout-id="operation.dc-usb-output.prerequisite" style="--hb-x:4.21%;--hb-y:8.66%;--hb-width:41.5%;--hb-height:8.67%;--hb-max-width:45.5%;--hb-fill:#ebebec"><p>Prérequis : Le produit est allumé.</p></div></div><div class="line-block hb-operation-steps" data-callout-id="operation.dc-usb-output.steps"><div class="hb-operation-step" data-callout-id="operation.dc-usb-output.on" data-step-id="on" style="--hb-step-x:83.1%;--hb-step-y:14.9037%;--hb-step-width:15%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Allumé</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Appuyez une fois</div></div><div class="hb-operation-step" data-callout-id="operation.dc-usb-output.off" data-step-id="off" style="--hb-step-x:83.1%;--hb-step-y:31.0853%;--hb-step-width:15%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Éteint</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Appuyez une fois</div></div></div></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Le port USB-C 100 W MAX est un port de sortie haute puissance conforme à la norme USB-PD Power Source 3 (PS3). Si l’appareil ou l’accessoire connecté ne répond pas aux exigences de sécurité, il peut exister un risque d’incendie. Avant d’utiliser ces ports, assurez-vous que l’appareil ou l’accessoire connecté est doté d’une protection contre les incendies.</li><li>Connectez uniquement le Jackery HomePower 3600 Pro Max à des appareils ou accessoires conformes aux clauses 6.3, 6.4 et 6.5 de la norme IEC/EN/UL 62368-1 (ou à d’autres normes équivalentes).</li><li>Pour obtenir la puissance de sortie maximale, utilisez le câble USB-C vers USB-C 5 A (20 V CC/5 A, 100 W).</li></ul></td></tr></tbody></table>

## SORTIE CA MARCHE/ARRÊT

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="ac-output" data-source-fragment-sha256="b1a1e858d82036320762bc940b97aa611078bc86c1e4d8e755dd6648c984b00a" data-web-base-art-ref="assets/ac_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/ac_framefree.png"/><div class="hb-operation-prerequisite" data-callout-id="operation.ac-output.prerequisite" style="--hb-x:4.3707%;--hb-y:6.36197%;--hb-width:41.3244%;--hb-height:8.1506%;--hb-max-width:45.5%;--hb-fill:#ebebec"><p>Prérequis : Le produit est allumé.</p></div></div><div class="line-block hb-operation-steps" data-callout-id="operation.ac-output.steps"><div class="hb-operation-step" data-callout-id="operation.ac-output.on" data-step-id="on" style="--hb-step-x:80.1653%;--hb-step-y:25.3536%;--hb-step-width:18%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Allumé</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Appuyez une fois</div></div><div class="hb-operation-step" data-callout-id="operation.ac-output.off" data-step-id="off" style="--hb-step-x:80.1653%;--hb-step-y:40.8387%;--hb-step-width:18%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Éteint</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Appuyez une fois</div></div></div></div></div></figure>

## MODE D’ÉCONOMIE D’ÉNERGIE

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="energy-saving" data-source-fragment-sha256="200c2d508051e5c5a80f16495472205b377a31c73a2178a657292ddbb8143e0b" data-web-base-art-ref="assets/energy_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/energy_framefree.png"/><div aria-hidden="true" class="hb-operation-duration" data-duration-icon="none" style="--hb-x:56.8897%;--hb-y:82.7556%">3s</div></div><div class="line-block hb-operation-steps" data-callout-id="operation.energy-saving.steps"><div class="hb-operation-step" data-callout-id="operation.energy-saving.main-button" data-step-id="main-button" style="--hb-step-x:46.2162%;--hb-step-y:46.2497%;--hb-step-width:26%"><div class="line" data-step-id="main-button" data-step-part="summary"><span class="hb-operation-step-instruction">Bouton d’alimentation principal</span></div></div><div class="hb-operation-step" data-callout-id="operation.energy-saving.ac-button" data-step-id="ac-button" style="--hb-step-x:73.5028%;--hb-step-y:46.2497%;--hb-step-width:26%"><div class="line" data-step-id="ac-button" data-step-part="summary"><span class="hb-operation-step-instruction">Bouton d’alimentation CA</span></div></div><div class="hb-operation-step" data-callout-id="operation.energy-saving.toggle" data-step-id="toggle" style="--hb-step-x:61.3479%;--hb-step-y:73.5854%;--hb-step-width:26%"><div class="line" data-step-id="toggle" data-step-part="summary"><span class="hb-operation-step-instruction"><strong>Allumé/Éteint</strong><br/>3s Appuyez et maintenez pendant 3 secondes</span></div></div></div></div><div class="hb-operation-supporting-copy" data-callout-id="operation.energy-saving.supporting-copy"><div class="line">Pour éviter une consommation inutile de la batterie due à l’oubli de désactiver la sortie, le produit active par défaut le Mode d’Économie d’Énergie. Lorsque la sortie CA ou USB est activée, l’icône du mode Économie d’énergie s’affichera sur l’écran LCD. Si aucun appareil n’est connecté ou si la consommation de l’appareil connecté est inférieure à un certain seuil (Sortie CA de 25 W ou sortie USB de 2 W) pendant 12 heures, l’appareil désactivera automatiquement toutes les sorties. Veuillez configurer la durée du mode Économie d’énergie dans l’application Jackery.</div><div class="line">Pour désactiver le mode d’économie d’énergie, appuyez et maintenez enfoncé à la fois le bouton d’alimentation CA et le bouton d’alimentation principal pendant plus de 3 secondes. Le produit n’éteindra pas automatiquement la sortie CA ou USB.</div></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Le mode d’économie d’énergie reprend l’état précédent après l’allumage. Un changement de mode nécessite un commutateur manuel.</p></td></tr></tbody></table>

## AFFICHAGE LCD

<figure aria-label="AFFICHAGE LCD" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="AFFICHAGE LCD" class="hb-lcd-mode-art" src="assets/lcd_device.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3"><p>Allumer en discontinu</p></td><td class="hb-lcd-mode-action"><p>Allumer</p></td><td class="hb-lcd-mode-copy"><p>Appuyez sur le bouton d'alimentation principal ou lorsque le produit est en charge.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Éteindre</p></td><td class="hb-lcd-mode-copy"><p>Appuyez sur le bouton d'alimentation principal.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Arrêt automatique</p></td><td class="hb-lcd-mode-copy"><p>L'écran LCD s'éteint automatiquement et entre en mode veille après 2 minutes d'inactivité.</p></td></tr><tr><td class="hb-lcd-mode-state" rowspan="3"><p>Allumer en continu (en cours de charge ou de décharge)</p></td><td class="hb-lcd-mode-action"><p>Allumer</p></td><td class="hb-lcd-mode-copy"><p>Appuyez deux fois sur le bouton d'alimentation principal lorsque le produit est allumé.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Éteindre</p></td><td class="hb-lcd-mode-copy"><p>Appuyez sur le bouton d'alimentation principal.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Arrêt automatique</p></td><td class="hb-lcd-mode-copy"><p>L'écran LCD s'éteint automatiquement après 2 heures d'inactivité.</p></td></tr></tbody></table></div></figure>

<p>Vous pouvez également définir le mode d'affichage de l'écran dans l'application Jackery.</p>

## FONCTIONNEMENT DES BOUTONS

<figure aria-label="Boutons / Utilisation / Fonction" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Boutons</th><th class="hb-key-operation" scope="col">Utilisation</th><th class="hb-key-function" scope="col">Fonction</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Bouton d’alimentation principal</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p>Bouton d’alimentation USB</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Appuyer 3 secondes sur les deux</p></td><td class="hb-key-function">Réinitialiser le Wi-Fi et le Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Bouton d’alimentation principal</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p>Bouton d’alimentation CA</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Appuyer 3 secondes sur les deux</p></td><td class="hb-key-function">Activer/désactiver le mode économie d’énergie</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p>Bouton d’alimentation USB</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p>Bouton d’alimentation CA</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">1s</p><p>Appuyer 1 seconde sur les deux</p></td><td class="hb-key-function">Activer le Wi-Fi et le Bluetooth</td></tr></tbody></table></figure>

## FONCTION DE REPRISE DE SORTIE CA ET CC

<p>Cette fonction mémorise l’état de la sortie et reprend automatiquement les sorties CA et CC sous certaines conditions définies.</p>

<figure aria-label="Conditions de reprise automatique / Conditions sans reprise automatique" class="hb-auto-resume-composition" data-component-id="HB-TABLE-AUTO-RESUME" tabindex="0"><table class="hb-auto-resume-table"><colgroup><col class="hb-auto-resume-col"/><col class="hb-auto-resume-col"/></colgroup><thead><tr><th class="hb-auto-resume-left" scope="col">Conditions de reprise automatique</th><th class="hb-auto-resume-right" scope="col">Conditions sans reprise automatique</th></tr></thead><tbody><tr><td class="hb-auto-resume-left">Mise sous tension/redémarrage après arrêt ou redémarrage</td><td class="hb-auto-resume-right">Sortie désactivée manuellement (bouton/App)</td></tr><tr><td class="hb-auto-resume-left" rowspan="2">SOC de la batterie ≥ limite de décharge +10% après avoir atteint la limite</td><td class="hb-auto-resume-right">Sortie désactivée en mode économie d’énergie</td></tr><tr><td class="hb-auto-resume-right">Sortie désactivée suite à un déclenchement de protection</td></tr><tr><td class="hb-auto-resume-left">Mise à niveau OTA terminée</td><td class="hb-auto-resume-right">Sortie désactivée par le minuteur de décharge</td></tr></tbody></table></figure>

<span id="ups"></span>

# ALIMENTATION SANS INTERRUPTION (ASI)

<p>Une alimentation sans coupure (UPS) est un système d’alimentation continue qui fournit automatiquement une alimentation électrique de secours à une charge lorsque l’alimentation du réseau principal est interrompue. In the event of a sudden loss of grid power, the HomePower 3600 Pro Max will automatically switch to stored power within 10 ms to keep your appliances running. En mode UPS, la puissance de sortie maximale de l’unité varie en fonction de la tension d’entrée du réseau avant une coupure de courant. La puissance de sortie réelle revient à la puissance nominale pendant les coupures.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Ce produit ne prend pas en charge un basculement instantané (0 ms). Ne le connectez pas à des équipements nécessitant une alimentation vec commutation en 0 ms, tels que des serveurs de données ou des stations de travail.</li><li>Avant toute utilisation, testez plusieurs fois la compatibilité avec votre appareil.</li><li>Ne connectez pas de charges dépassant la puissance de sortie maximale du produit. Sinon, la protection contre les surcharges sera déclenchée.</li></ul></td></tr></tbody></table>

## AVEC ENTRÉE CA 120 V

<p>Connectez le produit à une prise murale 120 V à l’aide du câble de charge CA. Appuyez sur le bouton d’alimentation CA pour activer la sortie CA.</p>

<p class="hb-prose-pill">Charges totales ≤1440 W :</p>

<p>Le produit fonctionne en mode bypass CA. Les trois ports CA (deux NEMA 5-20R et un NEMA 14-50R) peuvent être utilisés. Dans cette condition, le produit prend en charge une entrée 120 V avec des sorties 120 V et 240 V, et bascule sur l’alimentation par batterie en moins de 10 ms en cas de coupure du réseau.</p>

<p>Si un seul port 120 V est requis, utilisez le port NEMA 5-20R gauche (L1) comme connexion principale.</p>

<p class="hb-prose-pill">Charges totales &gt;1440 W :</p>

<p>Chaque port NEMA 5-20R prend en charge jusqu’à 1440 W, avec un maximum combiné de 2880 W sur les deux ports. Le port NEMA 14-50R prend en charge jusqu’à 2880 W. Les trois ports CA ensemble prennent en charge une sortie totale maximale de 2880 W. Lors d’un fonctionnement au-delà de 1440 W avec une entrée CA 120 V, le produit prend toujours en charge des sorties 120 V/240 V. Dans cette condition, les sorties CA consomment l’énergie de la batterie. Si la batterie est complètement déchargée, la charge connectée peut subir un arrêt pour surcharge et une interruption d’alimentation.</p>

<img alt="AVEC ENTRÉE CA 120 V" src="assets/ups120.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## AVEC ENTRÉE CA 240 V

<p>Connectez le produit à une alimentation CA 240 V à l’aide d’un câble de charge Jackery 40 A (vendu séparément). Appuyez sur le bouton d’alimentation CA pour activer la sortie CA.</p>

<p>Tous les ports de sortie CA prennent en charge le fonctionnement UPS sous une entrée 240 V : </p>

<ul><li>NEMA 14-50R (240 V~60 Hz) : Jusqu’à 9600 W de sortie en dérivation </li><li>NEMA 5-20R ×2 (120 V~60 Hz) : Jusqu’à 2400 W par port, 4800 W de sortie totale en dérivation </li></ul>

<p>La charge totale maximale autorisée est de 4000 W pour une unité et de 8000 W pour deux unités (connexion en parallèle). </p>

<p>En cas de coupure du réseau 240 V, le système bascule automatiquement sur l’alimentation par batterie avec un temps de transfert de &lt;10 ms. Lorsque la batterie est épuisée, toutes les sorties CA s’éteignent.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups240" data-source-fragment-sha256="1e00c9f4093204cc3bea201da1d3425080c47000df856e2a9dc5434815a85ab5" data-web-base-art-ref="assets/ups240.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ups240"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups240.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ups240", "web_replace_key": "reference.ups240", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "ed1d46eb529548addc353a34055753b2854d7989835fc3deccad422b11d75fa4", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [66.0, 62.8, 31.5, 11.5]}]}}' src="assets/ups240.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:66%;--hb-y:62.8%;--hb-width:31.5%;--hb-height:11.5%">Câble de charge Jackery 40 A (vendu séparément)</span></div></div></figure>

<span id="connections"></span>

# CONNEXIONS

## <span class="hb-heading-title">CONNECTER AU(X) PACK(S) BATTERIE</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<p>Ce produit peut prendre en charge jusqu’à 5 packs batterie pour répondre aux besoins d’une grande capacité énergétique. Pour les détails sur son utilisation, veuillez vous référer au manuel d’utilisation du Jackery Battery Pack 3600.</p>

<img alt="≥0,66 pied (≈200 mm) ≥0,66 pied (≈200 mm)" src="assets/battery_packs.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Si vous utilisez un seul bloc-piles, vous pouvez le placer dans l’une des configurations suivantes :</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-placement" data-source-fragment-sha256="28bd217e68ad521af91b174f42992ec18e3eea39dccd2e9783ad5d35adc696a1" data-web-base-art-ref="assets/placement_framefree.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.battery-placement"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-placement.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "battery-placement", "image_key": "assets/placement_framefree.png", "web_replace_key": "reference.battery-placement", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "2dc586aea7e86b79daa7f0b0219cdf963ccef0668212657ae0357aaa7a6427a4", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [2.427848101265822, 6.870068027210877, 26.524050632911393, 9.314965986394547], "fill": "#ebebec"}, {"line": 1, "rect": [52.7246835443038, 6.870068027210877, 21.934493670886074, 9.314965986394547], "fill": "#ebebec"}, {"line": 2, "rect": [27.491455696202536, 83.38027210884354, 17.60348101265823, 5.735374149659853], "color": "#555555"}]}}' src="assets/placement_framefree.png"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.4278%;--hb-y:6.8701%;--hb-width:26.5241%;--hb-height:9.315%;--hb-fill:#ebebec">Disposition côte à côte</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:52.7247%;--hb-y:6.8701%;--hb-width:21.9345%;--hb-height:9.315%;--hb-fill:#ebebec">Disposition empilée</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:27.4915%;--hb-y:83.3803%;--hb-width:17.6035%;--hb-height:5.7354%;--hb-label-color:#555555">≥0,66 pied (≈200 mm)</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Assurez-vous que tous les produits sont éteints avant de connecter le HomePower 3600 Pro Max au Jackery Battery Pack 3600.</li><li>Pour assurer le bon fonctionnement du produit, assurez-vous que les entrées et sorties d’air sur les deux côtés ne sont pas obstruées. Laissez un espace d’au moins 0,66 pied (200 mm) entre les ouvertures et tout objet pour permettre une dissipation thermique adéquate.</li></ul></td></tr></tbody></table>

## CONNEXION EN PARALLÈLE EN CASCADE

<p>La connexion en cascade permet à 2 unités HomePower 3600 Pro Max de fonctionner comme un système combiné, augmentant la puissance de sortie totale.</p>

<h3 class="hb-source-pill-heading" id="required-accessories">Accessoires requis</h3>

<p>Câble de charge Jackery 40 A Câble de communication parallèle Jackery Vendu séparément</p>

<h3 class="hb-source-pill-heading" id="connection-steps">ÉTAPES DE CONNEXION</h3>

<p>1. Assurez-vous que les deux unités sont éteintes et complètement déconnectées de toute source d’alimentation. 2. Connectez les ports de communication parallèle des deux unités</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>Ne sautez pas cette étape. Sans communication, les unités ne peuvent pas synchroniser les données et peuvent être endommagées.</p></td></tr></tbody></table>

<p>3. Connectez le port de sortie 240 V de la première unité (NEMA 14-50R) au port d’extension CA de la deuxième unité.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cascade" data-source-fragment-sha256="5146e605b78f157dd2957ab00ee56a19ea8a5d5aff81bac03597e5da38cbc57a" data-web-base-art-ref="assets/cascade.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.cascade"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="cascade.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "cascade", "web_replace_key": "reference.cascade", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "c73793a80a50ef9eb0e2f3ac4b7d28478110bad1b05999bce390bf86a93a67fb", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [70, 12.5, 28, 10.5]}, {"line": 1, "rect": [75.5, 52.5, 22.5, 17]}]}}' src="assets/cascade.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:70%;--hb-y:12.5%;--hb-width:28%;--hb-height:10.5%">Câble de charge Jackery 40 A (vendu séparément)</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.5%;--hb-y:52.5%;--hb-width:22.5%;--hb-height:17%">Câble de communication parallèle Jackery (vendu séparément)</span></div></div></figure>

<p>Les informations du système se synchroniseront sur les deux écrans</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>Après la mise en cascade, la puissance de sortie totale du système via le port NEMA 14-50R du deuxième appareil est de 8000 W. La charge totale NE DOIT PAS dépasser la puissance totale.</p></td></tr></tbody></table>

## CONNEXION AU COMMUTATEUR EPO

<p>The EPO (Emergency Power Off) interface is used to connect an external emergency-stop switch (prepared by the user). When an emergency occurs, pressing the EPO button immediately shuts down all AC and DC inputs and outputs. A screw terminal block is provided with the product for installing the external emergency-stop switch.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="epo" data-source-fragment-sha256="531b8790ab76682a36582a048ce57994077e024ad7fe8fb4cf401ef067db7fd4" data-web-base-art-ref="assets/epo.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.epo"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="epo.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "epo", "web_replace_key": "reference.epo", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "73538543ce16f0a0fbce0da4f719b4c69163a881ba9f66e3376603b1047bc068", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [73.5, 24, 7.5, 10]}]}}' src="assets/epo.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.5%;--hb-y:24%;--hb-width:7.5%;--hb-height:10%">EPO</span></div></div></figure>

## CONNEXION D’ALIMENTATION DE SECOURS

<h3 class="hb-heading-label-pair" id="connect-to-ats-sold-separately"><span class="hb-heading-title">CONNECTER AU ATS</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span></h3>

<p>Le HomePower 3600 Pro Max peut fournir une alimentation de secours aux circuits domestiques via un Automatic Transfer Switch (ATS) Jackery. Pour des instructions détaillées d’installation et d’utilisation, reportez-vous au manuel utilisateur ATS Jackery.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ats-lock" data-source-fragment-sha256="775e1cd76ca5ed9a7231753ee3ced20c07ba55f5ff651acf897cb9154d03acc9" data-web-base-art-ref="assets/ats_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ats-lock"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ats-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ats-lock", "image_key": "assets/ats_live.png", "web_replace_key": "reference.ats-lock", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "3a501abecb4e24bf96a40a4314d9dab8273cd3bdff9a345905c90bb6fb2652cb", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [8.577460317460316, 9.62055555555556, 10.152698412698413, 4.8238888888888845], "color": "#555555"}, {"line": 1, "rect": [61.75174603174603, 9.62055555555556, 10.311746031746031, 4.8238888888888845], "color": "#555555"}, {"line": 2, "rect": [63.492063492063494, 50.39388888888889, 29.206349206349206, 8.444444444444438], "color": "#555555"}]}}' src="assets/ats_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:8.5775%;--hb-y:9.6206%;--hb-width:10.1527%;--hb-height:4.8239%;--hb-label-color:#555555"><strong>Lock</strong></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:61.7517%;--hb-y:9.6206%;--hb-width:10.3117%;--hb-height:4.8239%;--hb-label-color:#555555"><strong>Unlock</strong></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:63.4921%;--hb-y:50.3939%;--hb-width:29.2063%;--hb-height:8.4444%;--hb-label-color:#555555">Câble d’alimentation entrée/sortie dans le paquet ATS</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Lorsque le mode UPS est activé sur le ATS, la station d’énergie reste active et consomme en continu de l’énergie. En cas de coupure du réseau, le système bascule sur l’alimentation par batterie en 20 millisecondes.</p></td></tr></tbody></table>

## <span class="hb-heading-title">CONNECTER AU MTS</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<p>Le HomePower 3600 Pro Max peut être connecté à un Manual Transfer Switch (MTS) pour alimenter certains circuits domestiques. Choisissez la méthode appropriée en fonction de votre mode d’installation.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Tous les câbles utilisés dans cette section sont vendus séparément ou inclus avec le MTS vendu séparément.</p></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="mts-installation-notice">Avis d’installation du MTS</h3>

<p>Pour des performances optimales lors de l’utilisation du HP3600 Pro Max avec un commutateur de transfert manuel (MTS), il est recommandé de raccorder l’entrée CA à un circuit non protégé par un GFCI. Si une protection GFCI est requise, il est recommandé d’installer les dispositifs GFCI en aval, du côté de la charge. Cette configuration améliore la compatibilité du système et favorise un fonctionnement fiable du mode de dérivation CA (bypass).</p>

## CONNEXION D’UNE SEULE UNITÉ AVEC MTS

<p>En mode automatique, le HomePower 3600 Pro Max reçoit une entrée CA et fournit une alimentation de secours de type UPS via le MTS.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mts-single" data-source-fragment-sha256="ddedb4a4eb07e1091b4d2ebd1190ed7734871fad21da9bfeb054f575a5b5589c" data-web-base-art-ref="assets/mts_single_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.mts-single"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="mts-single.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "mts-single", "image_key": "assets/mts_single_live.png", "web_replace_key": "reference.mts-single", "capture_following_lines": 7, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "6351b0b395ed043bb9f3a66f98605ad951645065688dc1eff8125f6d4870625c", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [5.063291139240507, 3.5238197424892688, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 1, "rect": [5.063291139240507, 14.098326180257509, 30.696202531645568, 9.442060085836921], "color": "#555555"}, {"line": 2, "rect": [5.063291139240507, 26.66583690987124, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 3, "rect": [5.063291139240507, 39.82802575107297, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 4, "rect": [5.063291139240507, 50.12467811158799, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 5, "rect": [48.65632911392405, 12.902145922746787, 19.69810126582279, 6.953218884120156], "color": "#555555"}, {"line": 6, "rect": [70.88607594936708, 77.88326180257512, 27.531645569620252, 6.523175965665217], "color": "#555555"}]}}' src="assets/mts_single_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:5.0633%;--hb-y:3.5238%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">1.</strong><span class="hb-mts-step-body">Éteignez le HomePower 3600 Pro Max.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:5.0633%;--hb-y:14.0983%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">2.</strong><span class="hb-mts-step-body">Connectez le HomePower 3600 Pro Max à une alimentation CA 240 V.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:5.0633%;--hb-y:26.6658%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">3.</strong><span class="hb-mts-step-body">Connectez le port de sortie 240 V (NEMA 14-50R) à l’entrée du MTS.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="3" style="--hb-x:5.0633%;--hb-y:39.828%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">4.</strong><span class="hb-mts-step-body">Réglez l’interrupteur de charge du MTS sur secours.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="4" style="--hb-x:5.0633%;--hb-y:50.1247%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">5.</strong><span class="hb-mts-step-body">Allumez l’unité et activez la sortie CA.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="5" style="--hb-x:48.6563%;--hb-y:12.9021%;--hb-width:19.6981%;--hb-height:6.9532%;--hb-label-color:#555555">Câble de charge dans le paquet MTS</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="6" style="--hb-x:70.8861%;--hb-y:77.8833%;--hb-width:27.5316%;--hb-height:6.5232%;--hb-label-color:#555555">Câble de charge Jackery de 40 A (vendu séparément)</span></div></div></figure>

<p>Lorsque le réseau est présent, l’alimentation CA est transmise au MTS. En cas de coupure de courant, le système bascule automatiquement sur l’alimentation par batterie en 10 millisecondes.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>La commutation automatique nécessite que l’entrée CA reste connectée en permanence.</p></td></tr></tbody></table>

## CONNEXION PARALLÈLE EN CASCADE AVEC MTS

<p>Lorsque deux unités sont connectées en mode parallèle en cascade, le système peut fournir une puissance de sortie plus élevée au MTS.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mts-cascade" data-source-fragment-sha256="a344303c64ae00e09c77a7423b3454647b14f185504a92e0225ddde6200d5905" data-web-base-art-ref="assets/mts_cascade_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.mts-cascade"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="mts-cascade.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "mts-cascade", "image_key": "assets/mts_cascade_live.png", "web_replace_key": "reference.mts-cascade", "capture_following_lines": 6, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "a143c40b3d9936f2a5aa9d48b9a459952760a9b518ad9194e59113e2eb805477", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [56.782334384858046, 5.276270718232044, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 1, "rect": [56.782334384858046, 12.082265193370162, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 2, "rect": [56.782334384858046, 20.171408839779005, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 3, "rect": [8.517350157728707, 26.382292817679556, 24.9211356466877, 4.833176795580114], "color": "#555555"}, {"line": 4, "rect": [43.217665615141954, 36.6271546961326, 31.861198738170348, 5.085552486187842], "color": "#555555"}, {"line": 5, "rect": [69.08517350157729, 76.8868232044199, 22.397476340694006, 6.81483425414364], "color": "#555555"}]}}' src="assets/mts_cascade_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:56.7823%;--hb-y:5.2763%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">1.</strong><span class="hb-mts-step-body">Suivez les étapes de connexion parallèle en cascade décrites précédemment.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:56.7823%;--hb-y:12.0823%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">2.</strong><span class="hb-mts-step-body">Connectez le port de sortie 240 V (NEMA 14-50R) du deuxième appareil à l’entrée du MTS.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:56.7823%;--hb-y:20.1714%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">3.</strong><span class="hb-mts-step-body">Allumez les deux unités et activez la sortie CA.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="3" style="--hb-x:8.5174%;--hb-y:26.3823%;--hb-width:24.9211%;--hb-height:4.8332%;--hb-label-color:#555555">Câble de recharge inclus dans le kit MTS</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="4" style="--hb-x:43.2177%;--hb-y:36.6272%;--hb-width:31.8612%;--hb-height:5.0856%;--hb-label-color:#555555">Câble de charge Jackery de 40 A (vendu séparément)</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="5" style="--hb-x:69.0852%;--hb-y:76.8868%;--hb-width:22.3975%;--hb-height:6.8148%;--hb-label-color:#555555">Câble de communication parallèle Jackery (vendu séparément)</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>Après la mise en cascade, la puissance de sortie maximale vers le MTS est de 8000 W. La charge totale NE DOIT PAS dépasser la puissance totale.</p></td></tr></tbody></table>

<span id="charging"></span>

# CHARGE

<p><strong>L’énergie verte d’abord :</strong>nous préconisons l’utilisation de l’énergie verte en premier. Ce produit prend en charge deux modes de recharge simultanés : la recharge solaire et la recharge par prise murale CA. Quand la recharge par prise murale CA et la recharge solaire sont effectuées en même temps, le produit privilégie la recharge solaire. Les deux méthodes sont utilisées pour charger la batterie à la puissance maximalement autorisée.</p>

<p class="hb-prose-pill">Chargez complètement le produit avant sa première utilisation.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><ul><li>La température de charge recommandée pour le produit est comprise entre -4 °F et 113 °F (-20 °C à 45 °C), et la température de décharge est comprise entre -4 °F et 113 °F (-20 °C à 45 °C). Utiliser le produit en dehors de cette plage de températures peut limiter ses capacités de charge et de décharge, voire empêcher la charge ou la décharge.</li><li>La puissance de charge et la capacité de la batterie du produit peuvent varier en raison des fluctuations de température.</li></ul></td></tr></tbody></table>

## CHARGEMENT VIA PRISE MURALE CA 120 V

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charge120" data-source-fragment-sha256="6b1b1e35fa9bae6b1a44f0b98adb59679e18abd95fb2a23cb58a4ed39c299265" data-web-base-art-ref="assets/charge120.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.charge120"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charge120.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "charge120", "web_replace_key": "reference.charge120", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "378983dcedd288cc23b4752b949ca53ddf98dcf5a1334ce6b0319c59a0e3ecbb", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "labels": [{"line": 0, "rect": [57.65, 79.53, 38.3, 14.3]}], "mobile_labels": "overlay"}}' src="assets/charge120.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:57.65%;--hb-y:79.53%;--hb-width:38.3%;--hb-height:14.3%">Connectez le câble de charge CA au port d’entrée CA de l’appareil et à une prise murale.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Assurez-vous que le câble de charge CA est entièrement et solidement inséré dans le port d’entrée CA.</li><li>Une connexion incomplète peut entraîner un courant instable, une surchauffe, un mauvais contact ou un dysfonctionnement de l’appareil.</li></ul></td></tr></tbody></table>

## CHARGEMENT VIA ENTRÉE CA 240 V

<p>Le HomePower 3600 Pro Max prend en charge la charge via son port d’extension CA 240 V. Selon votre installation, l’entrée CA 240 V peut provenir d’une prise CA 240 V ou d’un Jackery Automatic Transfer Switch (ATS).</p>

<h3 class="hb-source-pill-heading" id="v-ac-outlet">Prise CA 240 V</h3>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charge240" data-source-fragment-sha256="8c7a15c1f81e033f61af4e0d39262a7e87c3737f56f8a3d84c5c9dc44fc8fbd6" data-web-base-art-ref="assets/charge240.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.charge240"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charge240.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "charge240", "web_replace_key": "reference.charge240", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "78421e939d39ded94f7ec9c48de298d160fb082d1302f8aef16d395679252632", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "labels": [{"line": 0, "rect": [43.82, 75.04, 52, 16]}], "mobile_labels": "overlay"}}' src="assets/charge240.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:43.82%;--hb-y:75.04%;--hb-width:52%;--hb-height:16%">Connectez le produit à une alimentation CA 240 V à l’aide d’un câble de charge Jackery 40 A (Vendu séparément).</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Assurez-vous que le câble de charge Jackery 40 A est entièrement et solidement branché à la fois sur la prise 240 V et sur le port d’extension CA.</li><li>Une connexion incomplète peut entraîner un courant instable, une surchauffe, un mauvais contact ou un dysfonctionnement de l’appareil.</li></ul></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="transfer-switch-ats">COMMUTATEUR DE TRANSFERT (ATS)</h3>

<p>Connectez votre Jackery ATS au produit pour permettre la charge via le commutateur de transfert.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Le réglage de réserve de secours s’applique dans tous les modes de fonctionnement du ATS. Lorsque la capacité restante du HomePower 3600 Pro Max dépasse la réserve de secours configurée, la charge s’arrête automatiquement.</p></td></tr></tbody></table>

<p>Pour le charger immédiatement, suivez les instructions ci-dessous : 1. Touchez Station d’énergie dans le flux d’énergie du tableau de bord du ATS. 2. Sur la page Station d’énergie, touchez Charger maintenant.</p>

<img alt="COMMUTATEUR DE TRANSFERT (ATS)" src="assets/ats_app.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Lorsque le port d’extension CA est connecté avec succès au ATS, le port d’entrée CA ne sera plus utilisé pour la charge. Dans cette configuration, le HomePower 3600 Pro Max peut être chargé via les ports suivants : port d’extension CA, ports DC8020</p></td></tr></tbody></table>

## <span class="hb-heading-title">CHARGING VIA SOLAR PANELS</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<p>Le Jackery HomePower 3600 Max dispose de deux ports d’entrée DC8020 et dont chacun prend en charge la connexion directe à un panneau solaire de 500 W ou à trois panneaux solaires de 200 W. Si vous souhaitez connecter un seul port d’entrée DC8020 à deux panneaux solaires ou plus simultanément, veuillez vous référer au schéma ci-dessous pour le branchement via le connecteur de panneau solaire (vendu séparément, non inclus en standard).</p>

<img alt="SolarSaga 500 X × 2" src="assets/solar500.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="SolarSaga 200 × 6" src="assets/solar200.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>Assurez-vous que la tension d’entrée pour les deux ports d’entrée CC est la même. Sinon, le produit pourrait être endommagé. Par exemple : Utiliser le même modèle de panneaux solaires Jackery et le même nombre de panneaux lors de la connexion des panneaux solaires aux deux ports d’entrée DC8020. Ne chargez pas le produit à la fois avec un chargeur de voiture et un panneau solaire simultanément. Cela pourrait faire sauter le fusible de la voiture ou entraîner un échec de la charge.</p></td></tr></tbody></table>

<p>Il est recommandé d’utiliser le panneau solaire Jackery pour charger le HomePower 3600 Pro Max. Si vous choisissez des panneaux solaires d’autres marques, assurez-vous que leur tension de fonctionnement (Vmp) est comprise dans la plage d’entrée CC (16V-60V) du HomePower 3600 Pro Max. Jackery décline toute responsabilité en cas de pertes causées par l’utilisation de panneaux solaires d’autres marques.</p>

## <span class="hb-heading-title">CHARGEMENT PAR PRISE DE VOITURE</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<p>Ce produit peut être chargé à l’aide d’un chargeur de voiture 12 V. Assurez-vous que le chargeur allume-cigare et l’allume-cigare de la voiture sont bien branchés.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car_charging" data-source-fragment-sha256="ddeadf9b8ed18522bfb4864b1e00ac0bfdae136adb25892f4a95f6b6e5ac8814" data-web-base-art-ref="assets/car_charging_framefree.svg" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.car-charging"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car_charging.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "car_charging", "web_replace_key": "reference.car-charging", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "c5bf094d9b0f2cd27cd5f6ac9e82e6ad413ac0c4f36441d76dcb7de7d7cfdfd4", "panel_top": 0, "panel_fill": "#ebecec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [67, 10.4, 15, 9]}, {"line": 1, "rect": [49.37, 75.12, 47.65, 10.07], "fill": "#ffffff"}]}}' src="assets/car_charging_framefree.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:67%;--hb-y:10.4%;--hb-width:15%;--hb-height:9%">Véhicule</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:49.37%;--hb-y:75.12%;--hb-width:47.65%;--hb-height:10.07%;--hb-fill:#ffffff">*Le câble de chargement de voiture est vendu séparément.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Veuillez démarrer le véhicule avant de charger votre station d’alimentation.</li><li>Si le véhicule roule sur des routes accidentées, il est interdit d’utiliser le chargeur de voiture afin d’éviter tout risque de surchauffe dû à une mauvaise connexion. La société ne sera pas responsable des pertes causées par une utilisation non conforme.</li><li>La charge par véhicule est uniquement applicable aux véhicules en 12 V CC, pas en 24 V CC. Veuillez ne pas charger ce produit dans un véhicule 24 V afin d’éviter tout risque de blessure ou de dommage matériel.</li></ul></td></tr></tbody></table>

<span id="troubleshooting"></span>

# DÉPANNAGE

<p>Si l’un des codes d’erreur suivants apparaît, suivez les actions correctives indiquées pour résoudre le problème. Si l’erreur persiste, veuillez contacter le service à la clientèle de Jackery.</p>

<figure aria-label="Code d’erreur / Mesures correctives" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Code d’erreur</th><th class="hb-troubleshooting-measures" scope="col">Mesures correctives</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0/F1 F2/F3</td><td class="hb-troubleshooting-measures">Redémarrez le produit.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Connectez le produit à des charges pour décharger sa batterie jusqu’à ce que l’erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Chargez le produit via des panneaux solaires ou une prise murale CA jusqu’à ce que l’erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures">1. Attendez que le réseau se normalise avant de charger le produit via une prise murale CA.<br/>2. Vérifiez si les entrées et sorties d’air sont obstruées; assurez un espace de 0,66 pied (20 cm) de chaque côté du produit.<br/>3. Placez le produit dans un endroit qui n’est pas exposé à la lumière directe du soleil ou à des températures ambiantes élevées.<br/>4. Déconnectez toutes les charges du produit. Laissez le produit inactif et attendez que l’erreur disparaisse.<br/>5. Redémarrez le produit.</td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures">1. Retirez toutes les entrées CC du produit.<br/>2. Vérifiez la tension de fonctionnement (Vmp) des panneaux solaires connectés. Le produit autorise une tension d’entrée CC maximale de 60 V.<br/>3. Redémarrez le produit et laissez-le inactif. Attendez que l’erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">Contacter le service à la clientèle de Jackery.</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">Retirez la charge connectée aux ports USB du produit. Attendez que l’erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">FA</td><td class="hb-troubleshooting-measures">1. Désactivez les sorties CA et éteignez les deux unités.<br/>2. Déconnectez les câbles entre les unités et reconnectez les deux unités.<br/>3. Redémarrez les deux unités et activez leurs sorties CA.</td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures">1. Redémarrez respectivement les blocs-batteries et le HP3600 Pro Max.<br/>2. Si le défaut persiste, déconnectez le bloc-batterie du HP3600 Pro Max puis reconnectez-les.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures">1. Après que la situation d'urgence est résolue, appuyez de nouveau sur le bouton EPO.<br/>2. Si vous devez alimenter des charges CA ou CC, appuyez sur le bouton d'alimentation CA ou CC pour réactiver la sortie.</td></tr></tbody></table></figure>

<span id="storage"></span>

# STOCKAGE

<p>Conservez le produit dans un endroit propre et sec avec une ventilation adéquate.Température et humidité de stockage :</p>

<ul><li>1 mois : -4°F à 113°F / -20°C à 45°C (0-60% HR)</li><li>3 mois : 32°F à 113°F / 0°C à 45°C (0-60% HR)</li><li>12 mois : 32°F à 77°F / 0°C à 25°C (0-60% HR)</li></ul>

<p>Si ce produit est stocké pendant une longue période (3 à 6 mois) avec la batterie déchargée, il peut devenir impossible de le recharger. Pour éviter cela et préserver la santé de la batterie, il est recommandé de vérifier et de recharger le produit tous les trois mois, et d'effectuer un cycle de charge et de décharge complet au moins une fois tous les 6 à 12 mois.</p>

<span id="specifications"></span>

# SPÉCIFICATIONS

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cellule Chimique</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 73,85 lb / 33,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14,76 × 10,83 × 17,72 po / 37,5 × 27,5 × 45,0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">6000 cycles (capacité conservée ≥ 70 % SOH)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS (ASI)</th><td class="manual-spec-value hb-spec-value">&lt;10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topologie de l’onduleur</th><td class="manual-spec-value hb-spec-value">Isolée</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Facteur de puissance</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unité complète</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS D’ENTRÉE</h2>

<figure aria-label="PORTS D’ENTRÉE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">1 × Entrée CA</th><td class="manual-spec-value hb-spec-value">Mode charge : 100 V-120 V~ 60 Hz, 15 A max., 1800 W</td></tr><tr><td class="manual-spec-value hb-spec-value">Mode dérivation<sup class="hb-spec-reference">①</sup> : 100 V-120 V~ 60 Hz, 12 A max., 1440 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Ports DC8020</th><td class="manual-spec-value hb-spec-value">12–16 V⎓8 A max., double à 8 A max. 16-60 V<sup class="hb-spec-reference">②</sup>⎓12 A max., double jusqu’a 24 A, 1200 W max.</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS DE SORTIE</h2>

<figure aria-label="PORTS DE SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties CA (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120 V~ 60 Hz, 16,7 A max., 2000 W par port, 4000 W au total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie CA (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240 V~ 60 Hz, 16,7 A max., 4000 W nominal, 8000 W crête</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie totale CA<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000 W nominal, 8000 W crête</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">AC Output in Bypass Mode<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value"><strong>Entrée CA 120 V :</strong><br/>NEMA 5-20R: 100V-120V~ 60Hz, 12A Max, 1440W Max per port, 1440W<sup class="hb-spec-reference">④</sup> in Total<br/>NEMA 14-50R: 240V~ 60Hz, 1440W<sup class="hb-spec-reference">④</sup> Max</td></tr><tr><td class="manual-spec-value hb-spec-value"><strong>Entrée CA 240 V :</strong><br/>NEMA 5-20R : 100 V-120 V~ 60 Hz, 20 A max., 2400 W par port, 4800 W au total<br/>NEMA 14-50R : 240 V~ 60 Hz, 40 A max., 9600 W max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie USB-C</th><td class="manual-spec-value hb-spec-value">100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie USB-A</th><td class="manual-spec-value hb-spec-value">18 W max., 5–6 V⎓3 A, 6–9 V⎓2 A, 9–12 V⎓1,5 A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS D’EXTENSION</h2>

<figure aria-label="PORTS D’EXTENSION" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CA</th><td class="manual-spec-value hb-spec-value">240 V~ 60 Hz, 16,7 A max., 4000 W max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CC</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓126 A max. (Entrée)<br/>36,4 V-50,4 V⎓60 A max. (Sortie)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">SPÉCIFICATIONS ENVIRONNEMENTALES</h2>

<figure aria-label="SPÉCIFICATIONS ENVIRONNEMENTALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">-4 °F à 113 °F (-20 °C à 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-4 °F à 113 °F (-20 °C à 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitude</th><td class="manual-spec-value hb-spec-value">≤3000m</td></tr></tbody></table></figure>

<p>※ USB Type-C® et USB-C® sont des marques déposées de USB Implementers Forum.</p>

<p class="manual-spec-footnote">① Le produit peut charger la batterie à partir d’une prise murale CA ou via du ATS tout en fournissant de l’énergie via les ports de sortie CA.</p>

<p class="manual-spec-footnote">② Indique la tension de fonctionnement (Vmp) admissible du panneau solaire.</p>

<p class="manual-spec-footnote">③ Indique que deux ports de sortie CA ou plus fonctionnent ensemble.</p>

<p class="manual-spec-footnote">④ Lorsqu’il est connecté à des charges supérieures à 1440 W sous une entrée CA 120 V, le produit prélève de l’énergie de la batterie pour répondre à une demande de charge totale allant jusqu’à 2880 W.</p>

<span id="warranty"></span>

# GARANTIE

<figure aria-label="GARANTIE" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p>Nous ne fournissons notre garantie qu'aux clients qui achètent sur le site officiel de Jackery, sur des plateformes tierces portant la marque Jackery, ou auprès de revendeurs autorisés locaux.</p></div><div class="hb-warranty-local-note"><p>*La durée et les détails de la garantie peuvent varier en fonction des lois, réglementations et revendeurs autorisés locaux.</p></div></figure>

## Garantie limitée

<figure aria-label="Garantie limitée" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantit à l'acheteur et consommateur d'origine que le produit de Jackery sera exempt de tout défaut de fabrication et de matériaux dans le cadre d'une utilisation normale pendant toute la durée de la période de garantie applicable identifiée dans la section « Période de garantie » ci-dessous, sous réserve des exceptions énoncées ci-dessous. Cette déclaration de garantie énonce les obligations totales et exclusives de garantie de Jackery. Nous n'assumerons pas et nous n'autorisons personne à assumer pour nous toute autre responsabilité en lien avec la vente de nos produits.</p></figure>

## Période de garantie

<figure aria-label="Période de garantie" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 ANS Garantie standard" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie standard</strong></div></div><div class="hb-warranty-period-copy"><p>La période de garantie standard du Jackery HomePower 3600 Pro Max est de 36 mois. Dans tous les cas, la période de garantie commence à compter de la date d’achat par l’acheteur et consommateur d’origine. La facture du premier achat du consommateur ou toute autre preuve documentaire raisonnable est nécessaire afin d’établir la date de début de la période de garantie.</p></div></div><div aria-label="2 ANS Garantie prolongée" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie prolongée</strong></div></div><div class="hb-warranty-period-copy"><p>Pour activer l’extension de garantie, vous devez enregistrer votre produit en ligne ou bien contacter notre service client à hello@jackery.com afin de prolonger la durée de la garantie standard.</p></div></div></div></figure>

## Réparation ou remplacement

<figure aria-label="Réparation ou remplacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>Jackery réparera ou remplacera (aux frais de Jackery) tout produit Jackery qui cesse de fonctionner pendant la période de garantie applicable en raison d’un défaut de fabrication ou de matériau. Le produit réparé ou remplacé bénéficie de la garantie restante de la date d’achat d’origine.</p></figure>

## Limitée à l’acheteur et consommateur d’origine

<figure aria-label="Limitée à l’acheteur et consommateur d’origine" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>La garantie d’un produit Jackery est limitée à l’acheteur et consommateur d’origine, elle ne peut pas être transférée à un autre propriétaire.</p></figure>

## Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantie de Jackery ne s'applique pas à :</p>Une utilisation incorrecte, abusée, modifiée, aux dégâts provoqués par un accident ou toute autre utilisation qui n'est pas une utilisation normale de ce produit et autorisée par la documentation actuelle du produit de Jackery. À une réparation tentée par quelqu'un d'autre qu'un établissement agréé. Tout autre produit acheté par l'intermédiaire d'une vente aux enchères en ligne. La garantie de Jackery ne s'applique pas aux cellules de la batterie, sauf si vous avez entièrement chargé les cellules de la batterie dans les sept jours suivant l'achat du produit et au moins une fois tous les 6 mois par la suite.</figure>

## Droits d'interprétation

<figure aria-label="Droits d'interprétation" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery Inc. se réserve le droit d’interpréter de manière définitive la politique après-vente des clients ci-dessus.</p></figure>

<span id="app"></span>

# CONFIGURATION DE L’APPLICATION

## 1. Télécharger l’application et se connecter

<figure aria-label="1. Télécharger l’application et se connecter" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Recherchez « Jackery » dans Google Play ou dans l’App Store pour installer l’application. Une fois que c’est fait, vous pouvez vous inscrire et vous connecter.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Vous pouvez également scanner le code QR ci-dessous pour télécharger et installer l'application.</p></div></div></div><div class="hb-app-download-semantic"><img alt="1. Télécharger l’application et se connecter" class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

## 2. Ajouter un appareil

<p>2.1 Cliquez sur le bouton <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> pour ajouter un appareil.</p>

<p>2.2 Maintenez enfoncé le bouton d'alimentation principal sur l’appareil pour l’allumer. Les icônes Wi-Fi et Bluetooth clignotent sur l’appareil afin d’indiquer qu’il est entré dans le mode Configuration réseau. Cliquez sur le bouton «icône qui clignotante» et autorisez l’application à se connecter aux appareils alentour, puis ouvrez les autorisations Bluetooth.</p>

<img alt="2.2 2.1" class="hb-app-add-device-phone-art hb-app-phone-pair" src="assets/app_add.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="Bouton d’alimentation principal" src="assets/app_control.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Une fois allumé, si l’application n’est pas connectée dans un délai de 2 heures, l’appareil éteindra automatiquement le Wi-Fi et le Bluetooth. Il est maintenant nécessaire d’appuyer et de maintenir enfoncés le bouton d’alimentation USB et le bouton d’alimentation CA pour réactiver le Wi-Fi et le Bluetooth.</p></td></tr></tbody></table>

<p>2.3. Une fois que vous avez appuyé sur l’icône de recherche d’appareils, l’appareil est automatiquement associé à l’application via le Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Si le message «l’appareil a été associé» s’affiche pendant l’appairage, vous pouvez suivre l’une de ces deux étapes pour procéder à la connexion.</p><ul><li>Le propriétaire de l’appareil peut partager ce dernier avec d’autres utilisateurs dans l’application.</li><li>Maintenez le bouton d’alimentation principal et le bouton d’alimentation USB enfoncés pendant 3 secondes pour réinitialiser l’appareil et l’associer de nouveau.</li></ul></td></tr></tbody></table>

<p>2.4 Une fois l’appairage réalisé avec succès, vous devrez saisir le nom et le mot de passe du Wi-Fi pour que l’appareil se connecte automatiquement au réseau Wi-Fi.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Veuillez choisir un réseau Wi-Fi 2,4 GHz. L’appareil ne prend pas en charge le réseau Wi-Fi 5 GHz.</p></td></tr></tbody></table>

<p>2.5. Une fois l’appareil ajouté à la page d’accueil, l’icône Wi-Fi de l’appareil restera allumée.</p>

<img alt="CONFIGURATION DE L’APPLICATION" class="hb-app-add-device-phone-art hb-app-phone-trio" src="assets/app_connect_result_steps.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Les captures d’écran ci-dessus sont fournies à titre indicatif.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>L’application Jackery ne peut se connecter qu’à une seule station d’énergie à la fois via Bluetooth. Revenir à la liste des appareils déconnecte automatiquement le Bluetooth. Touchez à nouveau la station d’énergie dans la liste pour vous reconnecter automatiquement.</p></td></tr></tbody></table>

## 3. Dissocier l’appareil

<p>Cliquez sur le bouton des paramètres en haut à droite de l’interface principale pour accéder à la page des paramètres. Cliquez sur le bouton de dissociation en bas de la page pour dissocier l’appareil.</p>

## 4. Remarques

### 4.1. Pour activer le Wi-Fi et le Bluetooth :

<ul><li>Le Wi-Fi et le Bluetooth sont automatiquement activés, une fois l’appareil allumé. Leurs icônes s’allument sur l’écran.</li><li>Appuyez simultanément sur le bouton d’alimentation USB et le bouton d’alimentation CA jusqu’à ce que les icônes Wi-Fi et Bluetooth s’allument sur l’écran.</li></ul>

### 4.2. Pour désactiver le Wi-Fi et le Bluetooth :

<ul><li>Appuyez simultanément sur le bouton d’alimentation USB et le bouton d’alimentation CA jusqu’à ce que les icônes Wi-Fi et Bluetooth s’éteignent de l’écran.</li><li>Le Wi-Fi et le Bluetooth sont automatiquement désactivés si aucun appareil n'est connecté dans les 2 heures.</li></ul>

### 4.3. Pour réinitialiser le Wi-Fi et le Bluetooth :

<p>Maintenez le bouton d’alimentation principal et le bouton d’alimentation USB enfoncés simultanément pendant 3 secondes pour réinitialiser le Wi-Fi et le Bluetooth aux paramètres d’usine et redémarrer le système. Le compte connecté dans l’application sera dissocié.</p>

<span id="ess"></span>

# <span class="hb-heading-title">SYSTÈME DE SAUVEGARDE DOMESTIQUE INTELLIGENT (AC ESS)</span> <span class="hb-heading-model">Model: HB3600C-TS05A</span>

<table class="manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/e1746d6937db_warning_triangle_dark.svg"/><strong>AVERTISSEMENT</strong></span></td><td class="manual-callout-body"><p>RISQUE DE CHOC ÉLECTRIQUE. VEILLEZ TOUJOURS À CE QUE TOUS LES ÉQUIPEMENTS ÉLECTRIQUES SOIENT MIS HORS TENSION EN TOUTE SÉCURITÉ AVANT DE COMMENCER LE TRAVAIL.</p></td></tr></tbody></table>

<p>Utilisez le câble d’entrée/sortie d’alimentation inclus dans l’emballage du ATS pour connecter le port d’extension CA du HomePower 3600 Pro Max au port d’entrée/sortie CA du ATS. Utilisez le câble d’extension inclus dans l’emballage du bloc-batterie pour connecter le HomePower 3600 Pro Max au bloc-batterie, c’est-à-dire pour relier son port d’extension CC (A) au port d’extension CC (B) du bloc-batterie.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ess_connection" data-source-fragment-sha256="b0270152fb7b06f614fe4ec18729a2e9a7846f7e4215e19ebdb6f6196ac26016" data-web-base-art-ref="assets/ess_connection.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ess-connection"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ess_connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ess_connection", "image_key": "assets/ess_connection.png", "web_replace_key": "reference.ess-connection", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "4039388533950249061954f24e6866b64c0641c146e277ada6e96c4892c52616", "panel_top": 0, "panel_fill": "#ebecec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [69.52, 36.26, 26.35, 8.4]}, {"line": 1, "rect": [72.38, 53.05, 23.5, 8.78]}, {"line": 2, "rect": [3.49, 89.31, 55.87, 8.02]}]}}' src="assets/ess_connection.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:69.52%;--hb-y:36.26%;--hb-width:26.35%;--hb-height:8.4%">Câble d’entrée/sortie d’alimentation dans l’emballage du ATS</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:72.38%;--hb-y:53.05%;--hb-width:23.5%;--hb-height:8.78%">Câble d’extension dans l’emballage du bloc-batterie</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:3.49%;--hb-y:89.31%;--hb-width:55.87%;--hb-height:8.02%">Pour des instructions détaillées sur l’installation et le raccordement, consultez les manuels d’utilisation du ATS et du bloc-batterie.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><p>Position d’installation du système de sauvegarde domestique intelligent (AC ESS)</p><ul><li>Installation en intérieur.</li><li>L’espace doit être complètement étanche.</li><li>Le mur doit être plat et nivelé.</li><li>Plage de température ambiante : -4 °F à 113 °F (-20 °C à 45 °C);</li><li>La température et l’humidité doivent être maintenues à un niveau constant.</li><li>Installer dans un endroit bien ventilé.</li><li>Ne pas installer dans une zone accessible aux enfants ou aux animaux domestiques.</li><li>L’emplacement d’installation doit éviter l’exposition directe au soleil.</li><li>Aucun matériau inflammable ou explosif ne doit se trouver à proximité de l’onduleur et de la batterie.</li></ul></td></tr></tbody></table>

<span id="ess-specifications"></span>

# <span class="hb-heading-title">SPÉCIFICATIONS</span> <span class="hb-heading-model">Model: JHP-3600C</span>

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cellule Chimique</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 73,85 lb / 33,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14,76 × 10,83 × 17,72 po / 37,5 × 27,5 × 45,0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">6000 cycles (capacité conservée ≥ 70 % SOH)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS (ASI)</th><td class="manual-spec-value hb-spec-value">&lt;10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topologie de l’onduleur</th><td class="manual-spec-value hb-spec-value">Isolée</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Facteur de puissance</th><td class="manual-spec-value hb-spec-value">≥0.98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unité complète</th><td class="manual-spec-value hb-spec-value">Type 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS D’ENTRÉE</h2>

<figure aria-label="PORTS D’ENTRÉE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">1 × Entrée CA</th><td class="manual-spec-value hb-spec-value">Mode charge : 100 V-120 V~ 60 Hz, 15 A max., 1800 W</td></tr><tr><td class="manual-spec-value hb-spec-value">Mode dérivation<sup class="hb-spec-reference">①</sup> : 100 V-120 V~ 60 Hz, 12 A max., 1440 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Ports DC8020</th><td class="manual-spec-value hb-spec-value">12–16 V⎓8 A max., double à 8 A max. 16-60 V<sup class="hb-spec-reference">②</sup>⎓12 A max., double jusqu’a 24 A, 1200 W max.</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS DE SORTIE</h2>

<figure aria-label="PORTS DE SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Sorties CA (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120 V~ 60 Hz, 16,7 A max., 2000 W par port, 4000 W au total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie CA (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240 V~ 60 Hz, 16,7 A max., 4000 W nominal, 8000 W crête</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Sortie totale CA<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000 W nominal, 8000 W crête</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">AC Output in Bypass Mode<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value"><strong>Entrée CA 120 V :</strong><br/>NEMA 5-20R: 100V-120V~ 60Hz, 12A Max, 1440W Max per port, 1440W<sup class="hb-spec-reference">④</sup> in Total<br/>NEMA 14-50R: 240V~ 60Hz, 1440W<sup class="hb-spec-reference">④</sup> Max</td></tr><tr><td class="manual-spec-value hb-spec-value"><strong>Entrée CA 240 V :</strong><br/>NEMA 5-20R : 100 V-120 V~ 60 Hz, 20 A max., 2400 W par port, 4800 W au total<br/>NEMA 14-50R : 240 V~ 60 Hz, 40 A max., 9600 W max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie USB-C</th><td class="manual-spec-value hb-spec-value">100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Sortie USB-A</th><td class="manual-spec-value hb-spec-value">18 W max., 5–6 V⎓3 A, 6–9 V⎓2 A, 9–12 V⎓1,5 A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS D’EXTENSION</h2>

<figure aria-label="PORTS D’EXTENSION" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CA</th><td class="manual-spec-value hb-spec-value">240 V~ 60 Hz, 16,7 A max., 4000 W max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Port d’extension CC</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓126 A max. (Entrée)<br/>36,4 V-50,4 V⎓60 A max. (Sortie)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">SPÉCIFICATIONS ENVIRONNEMENTALES</h2>

<figure aria-label="SPÉCIFICATIONS ENVIRONNEMENTALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">-4 °F à 113 °F (-20 °C à 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-4 °F à 113 °F (-20 °C à 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitude</th><td class="manual-spec-value hb-spec-value">≤3000m</td></tr></tbody></table></figure>

<p>※ USB Type-C® et USB-C® sont des marques déposées de USB Implementers Forum.</p>

<p class="manual-spec-footnote">① Le produit peut charger la batterie à partir d’une prise murale CA ou via du ATS tout en fournissant de l’énergie via les ports de sortie CA.</p>

<p class="manual-spec-footnote">② Indique la tension de fonctionnement (Vmp) admissible du panneau solaire.</p>

<p class="manual-spec-footnote">③ Indique que deux ports de sortie CA ou plus fonctionnent ensemble.</p>

<p class="manual-spec-footnote">④ Lorsqu’il est connecté à des charges supérieures à 1440 W sous une entrée CA 120 V, le produit prélève de l’énergie de la batterie pour répondre à une demande de charge totale allant jusqu’à 2880 W.</p>

# <span class="hb-heading-title">Jackery Battery Pack 3600</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 3600</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JBP-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cellule Chimique</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 55,1 lbs / 25 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14,8 x 12,5 x 9,0 po/37,5 x 31,7x 22,9 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 6000 cycles à 70 % ou plus</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PORTS D’ENTRÉE/SORTIE</h2>

<figure aria-label="PORTS D’ENTRÉE/SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓60 A max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓100 A max.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1160A/860μs</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">TEMPÉRATURE DE FONCTIONNEMENT</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-4°F to 113°F / -20°C to 45°C</td></tr></tbody></table></figure>

# <span class="hb-heading-title">Jackery Automatic Transfer Switch</span> <span class="hb-sold-separately">VENDU SÉPARÉMENT</span>

<h2 aria-hidden="true" aria-level="2" class="hb-spec-group hb-source-hidden-heading" role="heading">Jackery Automatic Transfer Switch</h2>

<figure aria-label="Jackery Automatic Transfer Switch" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Automatic Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JA-TS05A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tension CA (nominale)</th><td class="manual-spec-value hb-spec-value">120V/240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Type d’alimentation</th><td class="manual-spec-value hb-spec-value">Réseau monophasé à point milieu</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant d’entrée maximal</th><td class="manual-spec-value hb-spec-value">100 A Réseau / 84 A Station d’énergie</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant de sortie maximal</th><td class="manual-spec-value hb-spec-value">100 A Charge domestique/ 33,4 A Station d’énergie</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant de court-circuit d’entrée maximal</th><td class="manual-spec-value hb-spec-value">10 KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Consommation électrique en mode veille</th><td class="manual-spec-value hb-spec-value">Environ 5 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Catégorie de surtension</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS (ASI)</th><td class="manual-spec-value hb-spec-value">≤20 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Type d’enveloppe</th><td class="manual-spec-value hb-spec-value">Boîtier de distribution : NEMA type 3R<br/>Boîtier de prise : NEMA type 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Degré de pollution</th><td class="manual-spec-value hb-spec-value">III</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuit principal</th><td class="manual-spec-value hb-spec-value">2 AWG (100 A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuit de charge</th><td class="manual-spec-value hb-spec-value">2 AWG (100 A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Communication</th><td class="manual-spec-value hb-spec-value">Wi-Fi et Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">27 × 14,4 × 5,7 in/ 68,5 × 36,5 × 14,4 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 23,1 lbs/10,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de fonctionnement</th><td class="manual-spec-value hb-spec-value">-4 °F à 122 °F / -20 °C à 50 °C</td></tr></tbody></table></figure>

<span id="ess-package"></span>

## LISTE DU COLIS

### Jackery HomePower 3600 Pro Max

<div class="hb-package-panel"><ul class="hb-package-grid"><li class="hb-package-item"><div class="hb-package-art hb-package-art--unit"><img alt="" src="assets/inbox_unit.png"/></div><p>Jackery HomePower 3600 Pro Max</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--ac"><img alt="" src="assets/inbox_ac.png"/></div><p>Câble de charge CA</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--terminal"><img alt="" src="assets/inbox_terminal.png"/></div><p>Bornier à vis</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Documents</p></li></ul></div>

### Jackery Battery Pack 3600 — Vendu séparément

<div class="hb-package-panel hb-package-panel--optional"><ul class="hb-package-grid"><li class="hb-package-item"><div class="hb-package-art hb-package-art--battery"><img alt="" src="assets/package_battery.png"/></div><p>Jackery Battery Pack 3600</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--expansion"><img alt="" src="assets/package_expansion.png"/></div><p>Câble de rallonge</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manuel d’utilisation</p></li><li class="hb-package-availability"><div class="hb-package-sold">Vendu séparément</div></li></ul></div>

### Jackery Automatic Transfer Switch — Vendu séparément

<div class="hb-package-panel hb-package-panel--optional"><ul class="hb-package-grid hb-package-grid--five"><li class="hb-package-item"><div class="hb-package-art hb-package-art--ats"><img alt="" src="assets/package_ats.png"/></div><p>Jackery Automatic Transfer Switch</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--template"><img alt="" src="assets/package_template.png"/></div><p>Modèle de marquage</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--power_cable"><img alt="" src="assets/package_power_cable.png"/></div><p>Modèle de marquage Entrée/ sortie d’alimentation Câble</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--neutral_wire"><img alt="" src="assets/package_neutral_wire.png"/></div><p>Fil neutre</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--gland"><img alt="" src="assets/package_gland.png"/></div><p>Presse-étoupe</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--jumper"><img alt="" src="assets/package_jumper.png"/></div><p>Cavalier de liaison neutre-terre (avec vis)</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manuel du propriétaire</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manuel d’installation</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Guide de démarrage rapide</p></li><li class="hb-package-availability"><div class="hb-package-sold">Vendu séparément</div></li></ul></div>

<span id="contact"></span>

# CONTACTEZ-NOUS

<p>JACKERY INC.</p>

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>1-888-502-2236 (US)</p>

<p>hello@jackery.com</p>

<p>www.jackery.com</p>
