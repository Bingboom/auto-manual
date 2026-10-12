<style>
/* Native exceptions only. Chapter H1 / dot-led H2 use shared web_manual.css. */
#furo-main-content #jackery-homepower-3600-pro-max-manual-de-usuario > h1,
#furo-main-content section#fcc > h1,
#furo-main-content section#contacto > h1,
#furo-main-content h2.hb-source-hidden-heading,
#furo-main-content section#contenido-de-la-caja section > h3 {
  display: none;
}
#furo-main-content section#importante > h2 {
  display: block;
  padding: 0;
  background: transparent !important;
  color: var(--hb-text);
  border-radius: 0;
  font-size: 1.12rem;
}
#furo-main-content section#importante > h2::before {
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
#furo-main-content section#configuracion-de-la-aplicacion h2::before,
#furo-main-content section#configuracion-de-la-aplicacion h3::before {
  display: none;
}
#furo-main-content section#configuracion-de-la-aplicacion h2,
#furo-main-content section#configuracion-de-la-aplicacion h3 {
  display: block;
  padding: 0;
  text-transform: none;
}
#furo-main-content section[id^="jackery-battery-pack-3600-sold-separately"] > h1,
#furo-main-content section#jackery-automatic-transfer-switch-se-vende-por-separado > h1 {
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
#furo-main-content #especificaciones > p.manual-spec-footnote,
#furo-main-content #specifications-model-jhp-3600c > p.manual-spec-footnote {
  margin: 0;
}

/* Native main-power art has no external copy or independent caption frames. */
#furo-main-content #encendido-apagado .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #encendido-apagado .hb-operation-supporting-copy > .line:first-child { font-weight: 400; }
#furo-main-content #encendido-apagado .hb-operation-supporting-copy > .line:last-child {
  padding: 1.2cqw 1.8cqw;
  border-radius: 2.4cqw;
  background: var(--hb-surface);
}
@media (min-width: 761px) {
  #furo-main-content #encendido-apagado .hb-operation-step-label { font-size: 3.1546cqw; }
  #furo-main-content #encendido-apagado .hb-operation-step-instruction { font-size: 1.8927cqw; }
  #furo-main-content #encendido-apagado .hb-operation-duration { font-size: 2.2082cqw; }
  #furo-main-content #encendido-apagado .hb-operation-supporting-copy:has(> .line:nth-child(4):last-child) {
    margin-top: -12.5cqw;
    grid-template-columns: 43% minmax(0, 1fr);
    padding-inline: 4.4cqw;
    font-size: 1.8927cqw;
  }
  #furo-main-content #encendido-apagado .hb-operation-supporting-copy:has(> .line:nth-child(4):last-child) > .line:last-child { margin-top: 1.2cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #encendido-apagado .hb-operation-supporting-copy > .line:last-child { padding: 0.7rem; border-radius: 0.8rem; }
  #furo-main-content #encendido-apagado .hb-operation-art-box > .hb-operation-duration { display: block; font-size: max(.5rem, 2.2082cqw); }
}

/* USB native artwork retains only product markings and connection geometry. */
#furo-main-content #encender-apagar-salida-usb .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #encender-apagar-salida-usb .hb-operation-prerequisite { background: var(--hb-fill); font-weight: 400; }
@media (min-width: 761px) {
  #furo-main-content #encender-apagar-salida-usb .hb-operation-step-label { font-size: 3.1546cqw; }
  #furo-main-content #encender-apagar-salida-usb .hb-operation-step-instruction { font-size: 1.8927cqw; }
  #furo-main-content #encender-apagar-salida-usb .hb-operation-prerequisite { font-size: 2.082cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #encender-apagar-salida-usb .hb-operation-art-box { display: flex; flex-direction: column; }
  #furo-main-content #encender-apagar-salida-usb .hb-operation-prerequisite {
    position: static; order: -1; width: auto; max-width: none; min-width: 0;
    margin: 0.65rem 0.65rem 0; padding: 0.5rem 0.75rem; border-radius: 0.8rem;
  }
}

/* AC native artwork retains only product markings and connection geometry. */
#furo-main-content #encender-apagar-salida-ca .hb-operation-stage { border-color: #e6e7e8; }
#furo-main-content #encender-apagar-salida-ca .hb-operation-prerequisite { background: var(--hb-fill); font-weight: 400; }
@media (min-width: 761px) {
  #furo-main-content #encender-apagar-salida-ca .hb-operation-step-label { font-size: 3.1646cqw; }
  #furo-main-content #encender-apagar-salida-ca .hb-operation-step-instruction { font-size: 1.8987cqw; }
  #furo-main-content #encender-apagar-salida-ca .hb-operation-prerequisite { font-size: 2.0886cqw; }
}
@media (max-width: 760px) {
  #furo-main-content #encender-apagar-salida-ca .hb-operation-art-box { display: flex; flex-direction: column; }
  #furo-main-content #encender-apagar-salida-ca .hb-operation-prerequisite {
    position: static; order: -1; width: auto; max-width: none; min-width: 0;
    margin: 0.65rem 0.65rem 0; padding: 0.5rem 0.75rem; border-radius: 0.8rem;
  }
}

/* Native energy-saving copy flows above the lower artwork; anchors use artwork only. */
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-stage { display: flex; flex-direction: column; border-color: #e6e7e8; }
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-supporting-copy {
  order: -1; position: static; width: auto; margin: 1rem 1rem 0.8rem; padding: 1rem 1.2rem;
  background: #ebebec; border: 0; border-radius: 1.2rem; font-size: 1rem; line-height: 1.5;
}
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-supporting-copy > .line { margin: 0; }
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-canvas > .hb-operation-steps {
  position: absolute; display: block; inset: 0; padding: 0; border: 0;
}
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-step {
  position: absolute; top: var(--hb-step-y); left: var(--hb-step-x); width: var(--hb-step-width);
}
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-step-instruction { font-size: max(.5rem, 1.735cqw); line-height: 1.1; white-space: nowrap; }
#furo-main-content #modo-de-ahorro-de-energia [data-step-id="toggle"] .hb-operation-step-label { font-size: max(.5rem, 3.1546cqw); line-height: 1.1; }
#furo-main-content #modo-de-ahorro-de-energia [data-step-id="toggle"] .hb-operation-step-instruction { font-size: max(.5rem, 1.8927cqw); }
#furo-main-content #modo-de-ahorro-de-energia .hb-operation-art-box > .hb-operation-duration { display: block; font-size: max(.5rem, 2.2082cqw); }
@media (max-width: 760px) {
  #furo-main-content #modo-de-ahorro-de-energia .hb-operation-supporting-copy { margin: .65rem .65rem .6rem; padding: .75rem; }
}

#furo-main-content #modo-de-ahorro-de-energia .hb-operation-step[data-step-id="toggle"] { width: 32%; }

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

# Jackery HomePower 3600 Pro Max — Manual de usuario

<span id="important"></span>

## IMPORTANTE

<p>Felicitaciones por su nuevo Jackery HomePower 3600 Pro Max. Antes de utilizar el producto, lea cuidadosamente este manual, especialmente las precauciones relevantes para asegurar un uso adecuado. Mantenga este manual en un lugar accesible para futuras consultas.</p>

<p>De acuerdo con las leyes y regulaciones, el derecho de interpretación final de este documento y todos los documentos relacionados con este producto corresponde a la Empresa. Aunque se ha hecho todo lo posible para garantizar la exactitud de este manual, Jackery Inc. no asume ninguna responsabilidad por los errores que puedan aparecer.</p>

<p>Tenga en cuenta que no se emitirán notificaciones adicionales en caso de actualizaciones, revisiones o terminación. Para obtener la última versión de los manuales del producto, visite support.jackery.com.</p>

<p>* Las cifras son sólo de referencia. Consulte el producto real.</p>

<span id="safety"></span>

# INFORMACIÓN IMPORTANTE DE SEGURIDAD

<figure class="hb-symbol-signal-composition hb-safety-instruction"><table class="manual-callout-table manual-callout-table hb-symbol-signal-table"><tbody><tr><td class="manual-callout-label hb-symbol-signal-label-cell"><span class="hb-source-risk-label"><img alt="" src="assets/e1746d6937db_warning_triangle_dark.svg"/><strong>ADVERTENCIA</strong></span></td><td class="manual-callout-body hb-symbol-signal-meaning-cell"><p>INSTRUCCIONES RELATIVAS AL RIESGO DE INCENDIO, DESCARGA ELÉCTRICA O LESIONES PERSONALES</p></td></tr></tbody></table></figure>

<table class="manual-two-col-table"><tbody><tr><td><p>Sigue siempre estas precauciones básicas al usar este producto.</p><ul><li>Lee todas las instrucciones antes de usar el producto.</li><li>No permitas que los niños jueguen sobre del producto. Se requiere la supervisión cercana de adultos cuando se use cerca de niños.</li><li>Evita colocar las manos o los dedos dentro del producto.</li><li>Deja de usar el producto de inmediato si ha sufrido daños físicos o modificaciones. El uso inadecuado puede causar un comportamiento impredecible, provocando incendio, explosión o lesiones.</li><li>Si se observan los siguientes condiciones, incluidas, entre otras, sobrecalentamiento, olores inusuales, humo, fugas o quemaduras, deja de usar el producto de inmediato y contacta al distribuidor o a nuestro servicio al cliente.</li><li>Nunca intentes abrir, reparar o modificar el producto. Cualquier manipulación, reensamblaje o modificación puede resultar en descarga eléctrica, incendio o daños a la batería.</li></ul></td><td><ul><li>Ten en cuenta que el líquido expulsado del producto puede causar irritación o quemaduras. El uso inapropiado o abusivo puede causar fugas en la batería. Evita el contacto directo con líquidos que se filtren. Si el líquido entra en contacto con los ojos, busca atención médica de inmediato. Si entra en contacto con otras partes del cuerpo, enjuaga con agua corriente y consulta a un médico de inmediato.</li><li>No expongas el producto al fuego o a temperaturas extremas. Hacerlo puede provocar una explosión si la temperatura supera los 130 °C (265 °F).</li><li>El uso de materiales o piezas no recomendadas o no suministradas puede implicar riesgo de incendio, descarga eléctrica o lesiones personales.</li><li>No dejes la batería cargando sin supervisión durante periodos prolongados. Supervisa siempre el proceso de carga para garantizar un funcionamiento seguro.</li><li>Para reducir el riesgo de descarga eléctrica, desconecta el producto de cualquier fuente de energía antes de realizar servicio técnico o resolución de problemas.</li></ul></td></tr></tbody></table>

## INSTRUCCIONES DE USO

<table class="manual-two-col-table"><tbody><tr><td><p>GUARDA ESTAS INSTRUCCIONES</p><ul><li>Deja de usar el producto de inmediato si muestra signos de daño. Suspende el uso y contacta al servicio al cliente para recibir asistencia.</li><li>No cargues la batería en ambientes extremadamente calientes o fríos y cumple estrictamente con los rangos de temperatura especificados por el producto:<ul><li>Temperatura de carga: -4 °F a 113 °F (-20 °C a 45 °C);</li><li>Temperatura de descarga: -4 °F a 113 °F (-20 °C a 45 °C).</li></ul></li><li>Para garantizar una circulación de aire adecuada, no cubras las rejillas de ventilación del producto. El área donde se use el producto debe tener un flujo de aire adecuado en un entorno fresco y seco para evitar el sobrecalentamiento.<ul><li>Cargar en espacios húmedos o mal ventilados puede representar riesgos para la seguridad.</li><li>El agua puede provocar cortocircuitos o dañar el cargador, generando riesgos de seguridad.</li></ul></li><li>Desconecta el cable de alimentación de la toma de corriente durante tormentas eléctricas.</li><li>Apaga el producto de inmediato presionando el botón de encendido si se ha caído, golpeado o expuesto a vibraciones.</li></ul></td><td><ul><li>Asegúrate de que los dispositivos estén apagados antes de conectarlos al producto.</li><li>No cargues el producto con un cable o enchufe dañado o roto.</li><li>No uses el producto para cargar dispositivos con cable o enchufe dañado o roto.</li><li>Siempre desconecta el cable de carga tirando del enchufe, no del cable, para evitar daños.</li><li>Asegúrate de que el producto esté bien asegurado al transportarlo en un vehículo en movimiento.</li><li>NO coloques la unidad boca abajo ni de lado durante el uso o almacenamiento.</li><li>NO coloques el producto en el suelo o a una altura menor de 18 pulgadas (457 mm) sobre el suelo durante el funcionamiento en un taller o centro de reparación.</li><li>NO uses los accesorios del producto con otros dispositivos o equipos.</li><li>El tiempo de carga solar depende de las condiciones meteorológicas. Coloque su panel solar donde reciba la mayor cantidad posible de luz solar directa.</li></ul></td></tr></tbody></table>

## INSTRUCCIONES PARA LA CONEXIÓN A TIERRA

<p>Este producto debe estar conectado a tierra. Si presenta mal funcionamiento o fallas, la conexión a tierra proporciona una ruta de menor resistencia para la corriente eléctrica y reduce el riesgo de shock eléctrico. Este producto está equipado con un cable que tiene un conductor de conexión a tierra y un enchufe con polo a tierra. El enchufe debe conectarse a un tomacorriente que esté instalado y conectado a tierra correctamente, de acuerdo con todos los códigos y ordenanzas locales.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ADVERTENCIA</td><td class="manual-callout-body"><p>Una conexión incorrecta del conductor de conexión a tierra del equipo puede provocar riesgo de shock eléctrico. Consulte con un electricista cualificado si tiene dudas sobre si el producto está conectado a tierra correctamente. No modifique el enchufe proporcionado con el producto; si no se ajusta al tomacorriente, haga que un electricista cualificado instale un tomacorriente adecuado.</p></td></tr></tbody></table>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PELIGRO</td><td class="manual-callout-body"><p>Este dispositivo está diseñado únicamente para uso en interiores (coloque este dispositivo en un ambiente similar a interiores cuando lo use en exteriores, ej. autocaravanas, tiendas de campaña, cabañas, etc.). ※ Este dispositivo no es resistente al agua ni al polvo.Manténgalo alejado de la lluvia y ambientes húmedos durante su uso.</p></td></tr></tbody></table>

## INSTRUCCIONES DE MANTENIMIENTO PARA EL USUARIO

<p>Durante el ciclo de vida de los productos de almacenamiento de energía, se producirá cierto grado de degradación de capacidad y energía. A medida que aumenta el número de ciclos de uso y se extiende el tiempo de almacenamiento, esta degradación se intensificará gradualmente, lo cual es un fenómeno normal acorde con el patrón de envejecimiento natural de las celdas de la batería.</p>

<span id="symbols"></span>

# SIGNIFICADO DE LOS SÍMBOLOS

<figure aria-label="SIGNIFICADO DE LOS SÍMBOLOS" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col"><p>Símbolo</p></th><th class="hb-symbol-signal-meaning-heading" scope="col"><p>Significado</p></th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ADVERTENCIA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ADVERTENCIA</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Prácticas peligrosas que pueden resultar en lesiones graves, muerte y/o daños a la propiedad.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="PRECAUCIÓN" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">PRECAUCIÓN</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Prácticas peligrosas que pueden resultar en lesiones personales y/o daños a la propiedad.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTA" class="hb-signal-badge"><span class="hb-signal-label">NOTA</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Prácticas peligrosas que pueden resultar en daño al equipo, pérdida de datos, deterioro del rendimiento o resultados inesperados.</p></td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEJOS" class="hb-signal-badge"><span class="hb-signal-label">CONSEJOS</span></span></td><td class="hb-symbol-signal-meaning-cell"><p>Complementa la información importante o consejos de operación en el texto.</p></td></tr></tbody></table></figure>

<figure aria-label="Símbolos de seguridad" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significado</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="¡Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">¡Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lea el manual del operador" class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Lea el manual del operador</td></tr><tr><td class="hb-symbol-icon"><img alt="Riesgo de descarga eléctrica" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Riesgo de descarga eléctrica</td></tr><tr><td class="hb-symbol-icon"><img alt="Carga de batería" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Carga de batería</td></tr><tr><td class="hb-symbol-icon"><img alt="Material explosivo" class="hb-symbol-art" src="assets/symbol_explosive_material.svg"/></td><td class="hb-symbol-meaning">Material explosivo</td></tr><tr><td class="hb-symbol-icon"><img alt="Objeto pesado" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Objeto pesado</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significado</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="No desarmes el producto." class="hb-symbol-art" src="assets/symbol_do_not_dismantle.svg"/></td><td class="hb-symbol-meaning">No desarmes el producto.</td></tr><tr><td class="hb-symbol-icon"><img alt="No fumar ni hacer llamas abiertas" class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">No fumar ni hacer llamas abiertas</td></tr><tr><td class="hb-symbol-icon"><img alt="No se permiten niños" class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">No se permiten niños</td></tr><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada." class="hb-symbol-art" src="assets/symbol_li_ion.svg"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada.</td></tr><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje. El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje. El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<div class="hb-fcc-balanced-flow"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/45f309ed8b3f_fcc_mark.png"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">Este dispositivo cumple con la parte 15 de las Reglas de la FCC. El funcionamiento está sujeto a las siguientes dos condiciones : (1) Este dispositivo no debe causar interferencias dañinas, y (2) Este dispositivo debe aceptar cualquier interferencia recibida, incluidas las interferencias que puedan causar un funcionamiento no deseado.</div></div></div></div><p><strong>NOTA :</strong> Este equipo ha sido probado y cumple con los límites para un dispositivo digital de Clase B, según la parte 15 de las Reglas de la FCC. Estos límites están diseñados para proporcionar una protección razonable contra las interferencias perjudiciales en una instalación residencial. Este equipo genera, utiliza y puede emitir energía de radiofrecuencia y, si no se instala y utiliza de acuerdo con las instrucciones, puede causar interferencias perjudiciales en las comunicaciones. Sin embargo, no hay garantía de que no se produzcan interferencias en una instalación particular. Si este equipo causa interferencias perjudiciales en la recepción de radio o televisión, lo que puede determinarse encendiendo y apagando el equipo, se recomienda al usuario intentar corregir las interferencias mediante una o más de las siguientes medidas :</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Reorientar o reubicar la antena de recepción.</p></li><li><p>Aumentar la separación entre el equipo y el receptor.</p></li><li><p>Conectar el equipo a una toma de corriente en un circuito diferente al que está conectado el receptor.</p></li><li><p>Consultar al distribuidor o a un técnico experimentado en radio/TV para obtener ayuda.</p></li></ul><p><strong>MODIFICACIÓN :</strong> Cualquier cambio o modificación no expresamente aprobada por la parte responsable de la conformidad podría anular la autorización del usuario para operar el dispositivo.</p></div></div></figure></div>

<span id="inbox"></span>

# CONTENIDO DE LA CAJA

<figure aria-label="CONTENIDO DE LA CAJA" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery HomePower 3600 Pro Max" class="hb-inbox-art" src="assets/inbox_unit.png"/><div class="hb-inbox-label"><p>Jackery HomePower 3600 Pro Max</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Cable de carga de CA" class="hb-inbox-art" src="assets/inbox_ac.png"/><div class="hb-inbox-label"><p>Cable de carga de CA</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Bornera de tornillo" class="hb-inbox-art" src="assets/inbox_terminal.png"/><div class="hb-inbox-label"><p>Bornera de tornillo</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Documentos" class="hb-inbox-art" src="assets/87ac44e52863_manual_icon1.png"/><div class="hb-inbox-label"><p>Documentos</p></div></li></ol><div class="hb-inbox-tip" role="note"><div class="hb-inbox-tip-label">CONSEJOS</div><div class="hb-inbox-tip-body">El cable de carga para automóvil no está incluido, pero está disponible para su compra por separado en nuestro sitio web. Para obtener asistencia, comunícate con el servicio al cliente de Jackery.</div></div></figure>

<span id="overview"></span>

# DESCRIPCIÓN GENERAL DEL PRODUCTO

## VISTA FRONTAL

<img alt="LCD Salidas de CA (NEMA 14-50R) 240V~ 60Hz, 16.7A máx., 4000 W máx. Botón de encendido principal Salida USB-C 100W Max, 5V⎓3A, 9V⎓3A, 12V⎓3A, 15V⎓3A, 20V⎓5A Salidas de CA (NEMA 5-20R) 120 V~ 60 Hz, 16,7 A máx., 2000 W por puerto, 4000 W en total L1 y L2 respectivamente de izquierda a derecha Salida USB-A 18W Max, 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A Botón de energía CA Botón de energía USB" src="assets/overview_front.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## VISTA LATERAL DERECHA

<img alt="EPO (apagado de emergencia) Comunicación en paralelo Para conectar a un botón externo de paro de emergencia Entrada de CA 100 V-120 V~60 Hz, 15 A máx. Entrada de CC (2 x Puertos DC8020) 12-16 V⎓8 A máx., Doble a 8 A máx. 16–60 V⎓12 A máx., Doble a 24 A/1200 W máx. Para conexión de comunicación en operación en paralelo en cascada Puerto de expansión CC Conectar al paquete de baterías Para conexión ATS o conexión en paralelo en cascada Entrada/Salida: 240 V~60 Hz, 16,7A máx., 4000 W Puerto de expansión CA" src="assets/overview_side.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<span id="lcd"></span>

# AFFICHAGE LCD

<img alt="Mapa numerado de la pantalla LCD, 1–31." src="assets/lcd_map.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<figure aria-label="AFFICHAGE LCD" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number"><p>1</p></td><td class="hb-lcd-icon"><img alt="Wi-Fi" class="hb-lcd-icon-art" src="assets/fc4cc02b42ef_fc4cc02b42ef_fc4cc02b42ef_1_Wi-Fi_KCcAbdDk7o4RjKx82micuKJ5nyf.png"/></td><td class="hb-lcd-name"><p>Wi-Fi</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> Wi-Fi conectado.<br/><strong>Parpadeo:</strong> listo para conectarse al Wi-Fi.<br/><strong>Apagado:</strong> Wi-Fi desconectado.</p></td></tr><tr><td class="hb-lcd-number"><p>2</p></td><td class="hb-lcd-icon"><img alt="Bluetooth" class="hb-lcd-icon-art" src="assets/7e1392ba6a45_7e1392ba6a45_7e1392ba6a45_2_Bluetooth_HVgvbJhq5o4EDKxhm7McCF4FnjB.png"/></td><td class="hb-lcd-name"><p>Bluetooth</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> Bluetooth conectado.<br/><strong>Parpadeo:</strong> listo para conectarse al Bluetooth.<br/><strong>Apagado:</strong> Bluetooth desconectado.</p></td></tr><tr><td class="hb-lcd-number"><p>3</p></td><td class="hb-lcd-icon"><img alt="Modo de Carga Silenciosa" class="hb-lcd-icon-art" src="assets/7f743182c050_7f743182c050_7f743182c050_3_Quiet_Charging_Mode_WLkMbiHS1oGsOtxUCp7cRhFAn1g.png"/></td><td class="hb-lcd-name"><p>Modo de Carga Silenciosa</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> el ruido durante la carga se minimiza significativamente, mientras que la potencia de carga se reduce y la velocidad de carga disminuye.<br/><strong>Apagado:</strong> El modo de carga silenciosa está desactivado. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>4</p></td><td class="hb-lcd-icon"><img alt="Modo de Ahorro de Batería" class="hb-lcd-icon-art" src="assets/e32e6ae96321_e32e6ae96321_e32e6ae96321_15_Battery_Saving_Mode_ClYfbtOGSoK5q2xySXCcgehVn8f.png"/></td><td class="hb-lcd-name"><p>Modo de Ahorro de Batería</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> limita la capacidad máxima utilizable de la batería para prolongar su vida útil.<br/><strong>Apagado:</strong> el modo de ahorro de batería está desactivado. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, se retiene la configuración.<br/><strong>Nota 1:</strong> Esta función no está disponible cuando el producto está conectado a paquetes de baterías.<br/><strong>Nota 2:</strong> Cuando esta función está habilitada, el producto ocasionalmente realiza un ciclo completo de carga-descarga para calibrar el SOC.</p></td></tr><tr><td class="hb-lcd-number"><p>5</p></td><td class="hb-lcd-icon"><img alt="Plan de Carga" class="hb-lcd-icon-art" src="assets/71017f43bab4_71017f43bab4_71017f43bab4_4_Charging_Plan_M96RbyZQxoGjRRxQHsuczeIln1b.png"/></td><td class="hb-lcd-name"><p>Plan de Carga</p></td><td class="hb-lcd-description"><p>Personaliza el tiempo de carga del producto. Adecuado para situaciones con tarifas eléctricas variables, permite establecer planes de carga según las horas pico y valle, reduciendo así los costos de electricidad. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>6</p></td><td class="hb-lcd-icon"><img alt="Límite de potencia de carga" class="hb-lcd-icon-art" src="assets/21b5f19ca9a6_21b5f19ca9a6_21b5f19ca9a6_16_Charging_Power_Limit_VLf2bJfrkoCL0CxJoMNcL5ZxnCt.png"/></td><td class="hb-lcd-name"><p>Límite de potencia de carga</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> El límite de potencia de carga está activado en la aplicación Jackery.<br/><strong>Apagado:</strong> El límite de potencia de carga está desactivado en la aplicación Jackery. Cuando el dispositivo se apaga, se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>7</p></td><td class="hb-lcd-icon"><img alt="Mode Autonome" class="hb-lcd-icon-art" src="assets/73225cf9faa8_73225cf9faa8_73225cf9faa8_5_Self-powered_Mode_FYTnb9vttoexjbxVMchcJaobnCg.png"/></td><td class="hb-lcd-name"><p>Mode Autonome</p></td><td class="hb-lcd-description"><p>Maximiza el uso de la energía solar y reduce la dependencia de la electricidad de la red al priorizar la energía solar almacenada, reduciendo los costos eléctricos. La estación de energía debe estar conectada simultáneamente a los paneles solares y a la red, con la potencia de carga limitada por la potencia de derivación. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>8</p></td><td class="hb-lcd-icon"><img alt="Modo TOU" class="hb-lcd-icon-art" src="assets/f4cdcb551105_f4cdcb551105_f4cdcb551105_6_TOU_Mode_BjEkbz0rFo6Bw4xiwNpcod9qnnc.png"/></td><td class="hb-lcd-name"><p>Modo TOU</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong>el modo TOU está habilitado (SOC de respaldo predeterminado: 60 %). Durante las horas pico, el producto prioriza la descarga de la batería para reducir los costos de la electricidad en momentos de alta demanda, cuando la energía almacenada supera el SOC de respaldo. Durante las horas valle, el sistema carga la batería desde la red para lograr recortar los picos y llenar los valles.<br/><strong>Apagado:</strong> el modo TOU está deshabilitado. El dispositivo no sigue la estrategia TOU (tarifa por periodo de uso) y opera según la lógica predeterminada de suministro de energía y carga. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>9</p></td><td class="hb-lcd-icon"><img alt="Paralelo" class="hb-lcd-icon-art" src="assets/lcd_parallel.png"/></td><td class="hb-lcd-name"><p>Paralelo</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> La conexión en paralelo se ha configurado correctamente.<br/><strong>Parpadeo:</strong> La conexión en paralelo se está configurando.<br/><strong>Apagado:</strong> La conexión en paralelo no está configurada.</p></td></tr><tr><td class="hb-lcd-number"><p>10</p></td><td class="hb-lcd-icon"><img alt="UPS" class="hb-lcd-icon-art" src="assets/e422a56922eb_e422a56922eb_e422a56922eb_7_UPS_Lgdgb8pvvoGwaLxSf8ec2QeHn3c.png"/></td><td class="hb-lcd-name"><p>UPS</p></td><td class="hb-lcd-description"><p>El indicador del SAI permanece encendido cuando hay energía de la red eléctrica disponible y se apaga cuando se pierde la energía de la red eléctrica.</p></td></tr><tr><td class="hb-lcd-number"><p>11</p></td><td class="hb-lcd-icon"><img alt="Indicador de Energía de CA" class="hb-lcd-icon-art" src="assets/8be87c5a0849_8be87c5a0849_8be87c5a0849_8_AC_Power_Indicator_HFPSbvWBgosvCux69jMcuWe6nnh.png"/></td><td class="hb-lcd-name"><p>Indicador de Energía de CA</p></td><td class="hb-lcd-description"><p>La salida CA (onda sinusoidal pura) está activada.</p></td></tr><tr><td class="hb-lcd-number"><p>12</p></td><td class="hb-lcd-icon"><img alt="Voltaje y frecuencia de salida" class="hb-lcd-icon-art" src="assets/7623ef10e229_7623ef10e229_7623ef10e229_9_Output_Voltage_and_Frequency_Jh3JbmBDBoKlmOxaRJDcIMJAn6b.png"/></td><td class="hb-lcd-name"><p>Voltaje y frecuencia de salida</p></td><td class="hb-lcd-description"><p>Muestra el voltaje y la frecuencia de salida cuando la salida de CA está habilitada mediante el botón de alimentación de CA o cuando el puerto de expansión de CA está suministrando energía. • 120 V : Se muestra cuando el producto se está cargando desde la entrada de CA de 120 V mientras simultáneamente suministra energía a través de los puertos de salida de CA. • 120/240 V : Se muestra cuando la salida de CA de 240 V está activa o cuando el producto está conectado a un interruptor de transferencia y funciona en modo bypass.</p></td></tr><tr><td class="hb-lcd-number"><p>13</p></td><td class="hb-lcd-icon"><img alt="Potencia de Entrada" class="hb-lcd-icon-art" src="assets/d5100a538e96_d5100a538e96_d5100a538e96_10_Input_Power_LOAZbnxfqoHFwIxx2Myc532jnzb.png"/></td><td class="hb-lcd-name"><p>Potencia de Entrada</p></td><td class="hb-lcd-description"><p>Muestra la potencia de entrada de CA utilizada para la carga de la batería en vatios.</p></td></tr><tr><td class="hb-lcd-number"><p>14</p></td><td class="hb-lcd-icon"><img alt="Tiempo de Carga Restante" class="hb-lcd-icon-art" src="assets/cfb69b1ffc0b_cfb69b1ffc0b_cfb69b1ffc0b_11_Remaining_Charge_Time_KIWHbHFOvotGuBxJsxlcunSDnPf.png"/></td><td class="hb-lcd-name"><p>Tiempo de Carga Restante</p></td><td class="hb-lcd-description"><p>Muestra el tiempo de carga restante.</p></td></tr><tr><td class="hb-lcd-number"><p>15</p></td><td class="hb-lcd-icon"><img alt="Indicador de Carga desde Toma de Corriente CA" class="hb-lcd-icon-art" src="assets/28f3cad42ae3_28f3cad42ae3_28f3cad42ae3_12_AC_Wall_Charging_Indicator_ZpOmbCjx8oYUTVxyl4JcvcTanPe.png"/></td><td class="hb-lcd-name"><p>Indicador de Carga desde Toma de Corriente CA</p></td><td class="hb-lcd-description"><p>El producto se carga a través de la entrada CA utilizando energía de la red eléctrica.</p></td></tr><tr><td class="hb-lcd-number"><p>16</p></td><td class="hb-lcd-icon"><img alt="Indicador de Carga desde Coche" class="hb-lcd-icon-art" src="assets/eed3299c3f6a_eed3299c3f6a_eed3299c3f6a_13_Car_Charging_Indicator_DLkibYaP1ot6d5x1S0jcUr1knlb.png"/></td><td class="hb-lcd-name"><p>Indicador de Carga desde Coche</p></td><td class="hb-lcd-description"><p>El producto se carga a través de la entrada CC (DC8020) utilizando CC 12 V (carga desde el coche).</p></td></tr><tr><td class="hb-lcd-number"><p>17</p></td><td class="hb-lcd-icon"><img alt="Indicador de Carga Solar" class="hb-lcd-icon-art" src="assets/91cec82eeaa5_91cec82eeaa5_91cec82eeaa5_14_Solar_Charging_Indicator_RgAUbPXNWoRxiHxKNgkc2gqDnEb.png"/></td><td class="hb-lcd-name"><p>Indicador de Carga Solar</p></td><td class="hb-lcd-description"><p>El producto se carga a través de la entrada CC (DC8020) utilizando paneles solares.</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>18</p></td><td class="hb-lcd-icon"><img alt="Indicador de expansión de CA (Carga)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-in.png"/></td><td class="hb-lcd-name"><p>Indicador de expansión de CA (Carga)</p></td><td class="hb-lcd-description"><p>El producto puede cargarse desde la red a través de un Jackery Automatic Transfer Switch (ATS).</p></td></tr><tr><td class="hb-lcd-icon"><img alt="Indicador de expansión de CA (Descarga)" class="hb-lcd-icon-art" src="assets/lcd_ac-expansion-out.png"/></td><td class="hb-lcd-name"><p>Indicador de expansión de CA (Descarga)</p></td><td class="hb-lcd-description"><p>El producto suministra energía a las cargas de su hogar a través del interruptor de transferencia conectado (ATS).</p></td></tr><tr><td class="hb-lcd-number"><p>19</p></td><td class="hb-lcd-icon"><img alt="Indicador del interruptor de transferencia" class="hb-lcd-icon-art" src="assets/lcd_transfer-switch.png"/></td><td class="hb-lcd-name"><p>Indicador del interruptor de transferencia</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> El producto está conectado correctamente a un interruptor de transferencia (ATS).<br/><strong>Apagado:</strong> El producto no está conectado a un interruptor de transferencia (ATS).</p></td></tr><tr><td class="hb-lcd-number"><p>20</p></td><td class="hb-lcd-icon"><img alt="Carga de vehículos eléctricos (EV)" class="hb-lcd-icon-art" src="assets/lcd_ev-charging.png"/></td><td class="hb-lcd-name"><p>Carga de vehículos eléctricos (EV)</p></td><td class="hb-lcd-description"><p>El adaptador de tierra (se vende por separado) está conectado correctamente al producto.</p></td></tr><tr><td class="hb-lcd-number"><p>21</p></td><td class="hb-lcd-icon"><img alt="Indicador de Potencia de la BateríaBatterie" class="hb-lcd-icon-art" src="assets/85921a9ad7fb_85921a9ad7fb_85921a9ad7fb_17_Battery_Power_Indicator_VLufb9exvoVLfgxz47pcfnRGnaf.png"/></td><td class="hb-lcd-name"><p>Indicador de Potencia de la BateríaBatterie</p></td><td class="hb-lcd-description"><p>Cuando el producto se está cargando, el círculo naranja alrededor del porcentaje de batería se ilumina secuencialmente. Cuando está cargando otros dispositivos, el círculo naranja permanece encendido.allumé.</p></td></tr><tr><td class="hb-lcd-number"><p>22</p></td><td class="hb-lcd-icon"><img alt="Indicador de Batería Baja" class="hb-lcd-icon-art" src="assets/c7862a87e742_c7862a87e742_c7862a87e742_19_Low_Battery_Indicator_KDk9bhs8poHUBdx96PLckPganhd.png"/></td><td class="hb-lcd-name"><p>Indicador de Batería Baja</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> el nivel de la batería está por debajo del 20 %.<br/><strong>Parpadeo:</strong> el nivel de la batería está por debajo del 5 %.<br/><strong>Apagado:</strong> el nivel de la batería no está por debajo del 20 % o el producto se está cargando.</p></td></tr><tr><td class="hb-lcd-number"><p>23</p></td><td class="hb-lcd-icon"><img alt="Porcentaje de Batería Restante" class="hb-lcd-icon-art" src="assets/747147be99d7_747147be99d7_747147be99d7_18_Remaining_Battery_Percentage_VkJcbUDbUoYC1hxrU6rc168OnJe.png"/></td><td class="hb-lcd-name"><p>Porcentaje de Batería Restante</p></td><td class="hb-lcd-description"><p>Muestra el porcentaje de batería restante.</p></td></tr><tr><td class="hb-lcd-number"><p>24</p></td><td class="hb-lcd-icon"><img alt="Indicador del medidor inteligente" class="hb-lcd-icon-art" src="assets/lcd_smart-meter.png"/></td><td class="hb-lcd-name"><p>Indicador del medidor inteligente</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> Un medidor inteligente está en línea.<br/><strong>Apagado:</strong> No se ha agregado ningún medidor inteligente al sistema o el medidor inteligente está fuera de línea.</p></td></tr><tr><td class="hb-lcd-number"><p>25</p></td><td class="hb-lcd-icon"><img alt="Temporizador de descarga" class="hb-lcd-icon-art" src="assets/6aab9a14900a_6aab9a14900a_6aab9a14900a_20_Discharge_Timer_DHPMbkjSWoiuALxJyJ8cWyQOn0e.png"/></td><td class="hb-lcd-name"><p>Temporizador de descarga</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> se ha configurado un temporizador de descarga.<br/><strong>Apagado:</strong> no se ha configurado un temporizador de descarga. Activar/desactivar esta función en la App Jackery. Cuando el dispositivo se apaga, no se retiene la configuración.</p></td></tr><tr><td class="hb-lcd-number"><p>26</p></td><td class="hb-lcd-icon"><img alt="Baterías conectadas" class="hb-lcd-icon-art" src="assets/lcd_connected-batteries.png"/></td><td class="hb-lcd-name"><p>Baterías conectadas</p></td><td class="hb-lcd-description"><p>Indica que el producto está conectado al número especificado de baterías adicionales 3600.</p></td></tr><tr><td class="hb-lcd-number"><p>27</p></td><td class="hb-lcd-icon"><img alt="Mode d’Économie d’Énergie" class="hb-lcd-icon-art" src="assets/c4b830c769a3_c4b830c769a3_c4b830c769a3_22_Energy_Saving_Mode_O4Jdb5pUQoCBAqx0sfQcm9Nbntd.png"/></td><td class="hb-lcd-name"><p>Mode d’Économie d’Énergie</p></td><td class="hb-lcd-description"><p><strong>Encendido:</strong> Mode d’économie d’énergie activé.<br/><strong>Éteint :</strong> Mode d’économie d’énergie désactivé.</p></td></tr><tr><td class="hb-lcd-number" rowspan="2"><p>28</p></td><td class="hb-lcd-icon"><img alt="Indicador de Alta Temperatura" class="hb-lcd-icon-art" src="assets/f548c6504f49_f548c6504f49_f548c6504f49_23_High_Temperature_Indicator_UmkEbOgCKoKyxoxDSINcfO6LnQd.png"/></td><td class="hb-lcd-name"><p>Indicador de Alta Temperatura</p></td><td class="hb-lcd-description"><p>Se activó la protección por alta temperatura. El producto puede dejar de funcionar hasta que su temperatura vuelva al rango normal de operación.</p></td></tr><tr><td class="hb-lcd-icon"><img alt="Indicador de Baja Temperatura" class="hb-lcd-icon-art" src="assets/bdbf602db74a_bdbf602db74a_bdbf602db74a_24_Low_Temperature_Indicator_JDMEbD96noSbyWxbOnVcgip1nab.png"/></td><td class="hb-lcd-name"><p>Indicador de Baja Temperatura</p></td><td class="hb-lcd-description"><p>Se activó la protección por baja temperatura. El producto puede dejar de funcionar hasta que su temperatura vuelva al rango normal de operación.</p></td></tr><tr><td class="hb-lcd-number"><p>29</p></td><td class="hb-lcd-icon"><img alt="Código de fallo" class="hb-lcd-icon-art" src="assets/lcd_fault-code.png"/></td><td class="hb-lcd-name"><p>Código de fallo</p></td><td class="hb-lcd-description"><p>Se ha producido un error en el producto. Por favor, consulte la sección de solución de problemas para más detalles.</p></td></tr><tr><td class="hb-lcd-number"><p>30</p></td><td class="hb-lcd-icon"><img alt="Potencia de Salida" class="hb-lcd-icon-art" src="assets/58c1d3604ca7_58c1d3604ca7_58c1d3604ca7_26_Output_Power_PviebR618oofvKxcKVRcHLlInqd.png"/></td><td class="hb-lcd-name"><p>Potencia de Salida</p></td><td class="hb-lcd-description"><p>Muestra la potencia de salida total (CA + USB) en vatios. Muestra OFF durante 1 segundo antes de que el producto se apague.</p></td></tr><tr><td class="hb-lcd-number"><p>31</p></td><td class="hb-lcd-icon"><img alt="Tiempo de Descarga Restante" class="hb-lcd-icon-art" src="assets/9b148ea95d3a_9b148ea95d3a_9b148ea95d3a_27_Remaining_Discharge_Time_JEpobf59DoBV4dxWlnxcNtIinke.png"/></td><td class="hb-lcd-name"><p>Tiempo de Descarga Restante</p></td><td class="hb-lcd-description"><p>Muestra el tiempo de descarga restante.</p></td></tr></tbody></table></figure>

<span id="operations"></span>

# OPERACIONES

## ENCENDIDO/APAGADO

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="main-power" data-source-fragment-sha256="41d83ece012764e640b02f70ccd29f534c3d337a3e98114a4420e1bd1d084eaf" data-web-base-art-ref="assets/power_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/power_framefree.png"/><div aria-hidden="true" class="hb-operation-duration" data-duration-icon="none" style="--hb-x:79.06%;--hb-y:51.9%">3s</div></div><div class="line-block hb-operation-steps" data-callout-id="operation.main-power.steps"><div class="hb-operation-step" data-callout-id="operation.main-power.on" data-step-id="on" style="--hb-step-x:74.5%;--hb-step-y:16.963%;--hb-step-width:23%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Encendido</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Presione una vez</div></div><div class="hb-operation-step" data-callout-id="operation.main-power.off" data-step-id="off" style="--hb-step-x:74.5%;--hb-step-y:37.378%;--hb-step-width:23%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Apagado</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Appuyez et maintenez pendant 3 secondes</div></div></div></div><div class="hb-operation-supporting-copy" data-callout-id="operation.main-power.supporting-copy"><div class="line"><strong>Tiempo de espera predeterminado: 2 horas</strong></div><div class="line">El producto se apagará automáticamente después de 2 horas de inactividad, sin carga ni descarga. </div><div class="line">*El tiempo en espera puede configurarse en la App de Jackery.</div><div class="line">Cuando el modo de ahorro de energía está activado, el producto se apagará automáticamente después de 12 horas si el botón de energía CA o USB está encendido, pero el producto no está cargando ni descargando.</div></div></div></figure>

## ENCENDER/APAGAR SALIDA USB

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="dc-usb-output" data-source-fragment-sha256="24f4220d3e48a76f8e183a6a10b5e93cbe478a22f10ab3cc8f0e6354e4c87ee7" data-web-base-art-ref="assets/usb_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/usb_framefree.png"/><div class="hb-operation-prerequisite" data-callout-id="operation.dc-usb-output.prerequisite" style="--hb-x:4.21%;--hb-y:8.66%;--hb-width:41.5%;--hb-height:8.67%;--hb-max-width:45.5%;--hb-fill:#ebebec"><p>Requisito previo: el producto está encendido.</p></div></div><div class="line-block hb-operation-steps" data-callout-id="operation.dc-usb-output.steps"><div class="hb-operation-step" data-callout-id="operation.dc-usb-output.on" data-step-id="on" style="--hb-step-x:83.1%;--hb-step-y:14.9037%;--hb-step-width:15%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Encendido</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Presione una vez</div></div><div class="hb-operation-step" data-callout-id="operation.dc-usb-output.off" data-step-id="off" style="--hb-step-x:83.1%;--hb-step-y:31.0853%;--hb-step-width:15%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Apagado</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Presione una vez</div></div></div></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>El puerto USB-C de 100 W es una salida de alta potencia de tipo Fuente de Alimentación 3 (PS3) según USB-PD. Si el dispositivo del usuario o accesorio conectado no cumple con los requisitos de seguridad, puede existir riesgo de incendio. Antes de usar estos puertos, asegúrese de que el dispositivo o accesorio conectado tenga protección contra incendios.</li><li>Solo conecte el Jackery HomePower 3600 Pro Max a dispositivos o accesorios que cumplan con las cláusulas 6.3, 6.4 y 6.5 de IEC/EN/UL 62368-1 (u otros estándares equivalentes).</li><li>Para obtener la potencia máxima de salida, utilice el cable USB-C a USB-C de 5 A (20 V CC/5 A, 100W).</li></ul></td></tr></tbody></table>

## ENCENDER/APAGAR SALIDA CA

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="ac-output" data-source-fragment-sha256="bdaa805e6f8d8756b1d9da46698a3add05aa95d453f6e3c7933b1cb17bcd337b" data-web-base-art-ref="assets/ac_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/ac_framefree.png"/><div class="hb-operation-prerequisite" data-callout-id="operation.ac-output.prerequisite" style="--hb-x:4.3707%;--hb-y:6.36197%;--hb-width:41.3244%;--hb-height:8.1506%;--hb-max-width:45.5%;--hb-fill:#ebebec"><p>Requisito previo: el producto está encendido.</p></div></div><div class="line-block hb-operation-steps" data-callout-id="operation.ac-output.steps"><div class="hb-operation-step" data-callout-id="operation.ac-output.on" data-step-id="on" style="--hb-step-x:80.1653%;--hb-step-y:25.3536%;--hb-step-width:18%"><div class="line hb-operation-step-label" data-step-id="on" data-step-part="label"><strong>Encendido</strong></div><div class="line hb-operation-step-instruction" data-step-id="on" data-step-part="instruction">Presione una vez</div></div><div class="hb-operation-step" data-callout-id="operation.ac-output.off" data-step-id="off" style="--hb-step-x:80.1653%;--hb-step-y:40.8387%;--hb-step-width:18%"><div class="line hb-operation-step-label" data-step-id="off" data-step-part="label"><strong>Apagado</strong></div><div class="line hb-operation-step-instruction" data-step-id="off" data-step-part="instruction">Presione una vez</div></div></div></div></div></figure>

## MODO DE AHORRO DE ENERGÍA

<figure class="hb-operation-figure hb-operation-layout-status-right hb-base-art-live-copy" data-component-id="HB-SPECIAL-OPERATION" data-operation-id="energy-saving" data-source-fragment-sha256="2b7eb4a8f64094ee0c922fe569300f478da82ac3ac4e781934c8b78b8dcbb78d" data-web-base-art-ref="assets/energy_framefree.png" data-web-presentation-mode="base-art-live-copy"><div class="hb-operation-stage"><div class="hb-operation-canvas"><div class="hb-operation-art-box"><img alt="" class="hb-operation-art" src="assets/energy_framefree.png"/><div aria-hidden="true" class="hb-operation-duration" data-duration-icon="none" style="--hb-x:56.8897%;--hb-y:82.7556%">3s</div></div><div class="line-block hb-operation-steps" data-callout-id="operation.energy-saving.steps"><div class="hb-operation-step" data-callout-id="operation.energy-saving.main-button" data-step-id="main-button" style="--hb-step-x:46.2162%;--hb-step-y:46.2497%;--hb-step-width:26%"><div class="line" data-step-id="main-button" data-step-part="summary"><span class="hb-operation-step-instruction">Botón de encendido principal</span></div></div><div class="hb-operation-step" data-callout-id="operation.energy-saving.ac-button" data-step-id="ac-button" style="--hb-step-x:73.5028%;--hb-step-y:46.2497%;--hb-step-width:26%"><div class="line" data-step-id="ac-button" data-step-part="summary"><span class="hb-operation-step-instruction">Botón de energía CA</span></div></div><div class="hb-operation-step" data-callout-id="operation.energy-saving.toggle" data-step-id="toggle" style="--hb-step-x:61.3479%;--hb-step-y:73.5854%;--hb-step-width:26%"><div class="line" data-step-id="toggle" data-step-part="summary"><span class="hb-operation-step-instruction"><strong>Encendido/Apagado</strong><br/>3s Mantén presionado durante 3 segundos</span></div></div></div></div><div class="hb-operation-supporting-copy" data-callout-id="operation.energy-saving.supporting-copy"><div class="line">Para evitar el consumo innecesario de batería al olvidar apagar la salida, el producto activa por defecto el Modo de Ahorro de Energía. Cuando la salida de CA o USB está encendida, el ícono del modo de Ahorro de Energía se mostrará en la pantalla LCD. Si no hay ningún dispositivo conectado o si el consumo del dispositivo conectado está por debajo de un cierto umbral (salida de CA de 25 W o salida USB de 2 W) durante 12 horas, el dispositivo apagará automáticamente todas las salidas. Configure la duración del modo de Ahorro de Energía en la aplicación Jackery.</div><div class="line">Para desactivar el modo de ahorro de energía, presione y mantenga presionados el botón de energía CA y el botón de energía principal durante más de 3 segundos. Una vez desactivado el modo de ahorro de energía, el icono dejará de mostrarse en la pantalla LCD y el producto no apagará automáticamente la salida CA o CC.</div><div class="line">Cuando alimente dispositivos de baja potencia (CA ≤ 25 W o USB ≤ 2 W), desactive el modo de ahorro de energía para evitar que la salida se apague automáticamente durante el funcionamiento.</div></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>El modo de ahorro de energía reanuda el estado anterior después de encender. Se requiere un cambio manual para modificar el modo.</p></td></tr></tbody></table>

## PANTALLA LCD

<figure aria-label="PANTALLA LCD" class="hb-lcd-mode-composition" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="PANTALLA LCD" class="hb-lcd-mode-art" src="assets/lcd_device.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3"><p>En breve</p></td><td class="hb-lcd-mode-action"><p>Encender</p></td><td class="hb-lcd-mode-copy"><p>Presione el botón de encendido principal o cuando el producto se esté cargando.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Apagar</p></td><td class="hb-lcd-mode-copy"><p>Presione el botón de encendido principal.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Apagado automático</p></td><td class="hb-lcd-mode-copy"><p>La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad.</p></td></tr><tr><td class="hb-lcd-mode-state" rowspan="3"><p>Estable en (durante el estado de carga o descarga)</p></td><td class="hb-lcd-mode-action"><p>Encender</p></td><td class="hb-lcd-mode-copy"><p>Presione dos veces el botón de encendido principal cuando el producto esté encendida.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Apagar</p></td><td class="hb-lcd-mode-copy"><p>Presione el botón de energía principal.</p></td></tr><tr><td class="hb-lcd-mode-action"><p>Apagado automático</p></td><td class="hb-lcd-mode-copy"><p>La pantalla LCD se apaga automáticamente después de 2 horas de inactividad.</p></td></tr></tbody></table></div></figure>

<p>También puedes configurar el modo de visualización de la pantalla en la aplicación Jackery.</p>

## COMBINACIONES DE TECLAS

<figure aria-label="Botones / Operación / Función" class="hb-key-combination-composition" data-component-id="HB-TABLE-KEY-COMBINATIONS" tabindex="0"><table class="hb-key-combination-table"><colgroup><col class="hb-key-col-buttons"/><col class="hb-key-col-operation"/><col class="hb-key-col-function"/></colgroup><thead><tr><th class="hb-key-buttons" scope="col">Botones</th><th class="hb-key-operation" scope="col">Operación</th><th class="hb-key-function" scope="col">Función</th></tr></thead><tbody><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Botón principal de encendido</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p>Botón de energía USB</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Mantenga pulsados ambos botones durante 3 segundos</p></td><td class="hb-key-function">Restablecer Wi-Fi y Bluetooth</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/7b5fa9057ca9_power-bottom.svg"/><p>Botón principal de encendido</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p>Botón de energía CA</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">3s</p><p>Mantenga pulsados ambos botones durante 3 segundos</p></td><td class="hb-key-function">Encender/apagar el modo de ahorro de energía</td></tr><tr><td class="hb-key-buttons"><div class="hb-key-button-pair"><div class="hb-key-button"><img alt="" src="assets/4025f864c192_usb-bottom.svg"/><p>Botón de energía USB</p></div><span class="hb-key-button-plus">+</span><div class="hb-key-button"><img alt="" src="assets/ad437a82a4fe_ac-bottom.svg"/><p>Botón de energía CA</p></div></div></td><td class="hb-key-operation"><p class="hb-key-duration" data-duration-icon="clock">1s</p><p>Mantenga pulsados ambos botones durante 1 segundo</p></td><td class="hb-key-function">Encender/apagar Wi-Fi y Bluetooth</td></tr></tbody></table></figure>

## FUNCIÓN DE REANUDACIÓN DE SALIDA DE CA Y CC

<p>Esta función memoriza el estado de la salida y reanuda automáticamente las salidas de CA y CC bajo condiciones definidas.</p>

<figure aria-label="Condiciones de reanudación automática / Condiciones sin reanudación automática" class="hb-auto-resume-composition" data-component-id="HB-TABLE-AUTO-RESUME" tabindex="0"><table class="hb-auto-resume-table"><colgroup><col class="hb-auto-resume-col"/><col class="hb-auto-resume-col"/></colgroup><thead><tr><th class="hb-auto-resume-left" scope="col">Condiciones de reanudación automática</th><th class="hb-auto-resume-right" scope="col">Condiciones sin reanudación automática</th></tr></thead><tbody><tr><td class="hb-auto-resume-left">Encendido/Reiniciar después de apagado o reinicio</td><td class="hb-auto-resume-right">Apagado manual de la salida (botón/App)</td></tr><tr><td class="hb-auto-resume-left" rowspan="2">SOC de la batería ≥ límite de descarga +10 % después de alcanzar el límite</td><td class="hb-auto-resume-right">Apagado de salida en modo de ahorro de energía</td></tr><tr><td class="hb-auto-resume-right">Apagado de salida activado por protección</td></tr><tr><td class="hb-auto-resume-left">Actualización OTA completada</td><td class="hb-auto-resume-right">Apagado de salida activado por temporizador de descarga</td></tr></tbody></table></figure>

<span id="ups"></span>

# FUENTE DE ALIMENTACIÓN ININTERRUMPIDA (UPS)

<p>Un sistema de alimentación ininterrumpida (UPS) es un tipo de sistema de energía continua que proporciona energía eléctrica de respaldo automática a una carga cuando falla la energía de la red principal. En caso de una pérdida repentina de energía de la red, el HomePower 3600 Pro Max cambiará automáticamente a la energía almacenada en menos de 10 ms para mantener sus electrodomésticos en funcionamiento. En modo SAI, la potencia de pico de salida de la unidad varía según los voltajes de entrada de la energía de la red eléctrica antes de un apagón. La potencia de salida real vuelve a la potencia de salida nominal durante los apagones.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>Este producto no admite conmutación de 0 ms. No lo conecte a equipos que requieran una fuente de alimentación con conmutación de 0 ms, como servidores de datos o estaciones de trabajo.</li><li>Antes de usar, pruebe la compatibilidad con su dispositivo varias veces.</li><li>No conectes cargas que excedan la potencia máxima de salida del producto. De lo contrario, se activará la protección contra sobrecarga.</li></ul></td></tr></tbody></table>

## CON ENTRADA DE CA DE 120 V

<p>Conecte el producto a una toma de corriente de pared de 120 V usando el cable de carga de CA. Presione el botón de alimentación de CA para habilitar la salida de CA.</p>

<p class="hb-prose-pill">Carga total ≤1440 W:</p>

<p>El producto funciona en modo bypass de CA. Se pueden usar los tres puertos de CA (dos NEMA 5-20R y uno NEMA 14-50R). En esta condición, el producto admite entrada de 120 V con salidas de 120 V y 240 V y cambia a energía de batería en 10 ms cuando falla la energía de la red eléctrica.</p>

<p>Si solo se requiere un puerto de 120 V, use el puerto izquierdo NEMA 5-20R (L1) como conexión principal.</p>

<p class="hb-prose-pill">Carga total &gt;1440 W:</p>

<p>Cada puerto NEMA 5-20R admite hasta 1440 W, con un máximo combinado de 2880 W entre ambos puertos. El puerto NEMA 14-50R admite hasta 2880 W. Los tres puertos de salida CA juntos admiten una salida total de hasta 2880 W. Cuando se opera por encima de 1440 W con entrada de CA de 120V, el producto aún admite salidas de 120 V/240 V. En esta condición, las salidas de CA consumen energía de batería. Si la batería se descarga completamente, la carga conectada puede experimentar un apagado por sobrecarga y una interrupción de energía.</p>

<img alt="CON ENTRADA DE CA DE 120 V" src="assets/ups120.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

## CON ENTRADA DE CA DE 240 V

<p>Conecte el producto a una fuente de alimentación de CA de 240 V usando un cable de carga Jackery de 40 A (se vende por separado). Presione el botón de alimentación de CA para habilitar la salida de CA.</p>

<p>Todos los puertos de salida CA admiten el funcionamiento del SAI con entrada de 240 V: </p>

<ul><li>NEMA 14-50R (240 V~60 Hz): Hasta 9600 W de salida en bypass </li><li>NEMA 5-20R ×2 (120 V~60 Hz): Hasta 2400 W por puerto y 4800 W de salida total en bypass </li></ul>

<p>La carga total máxima permitida es de 4000 W para una sola unidad y 8000 W para dos unidades (conexión en paralelo). </p>

<p>Cuando falla la energía de la red eléctrica de 240 V, el sistema cambia automáticamente a energía de batería con un tiempo de transferencia &lt;10 ms. Cuando la batería se agota, todas las salidas de CA se apagan.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ups240" data-source-fragment-sha256="5c2ae4d282f3501276fd26c68670cbcc828e152e3f372a314801043cad435727" data-web-base-art-ref="assets/ups240.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ups240"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ups240.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ups240", "web_replace_key": "reference.ups240", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "ed1d46eb529548addc353a34055753b2854d7989835fc3deccad422b11d75fa4", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [66.0, 62.8, 31.5, 11.5]}]}}' src="assets/ups240.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:66%;--hb-y:62.8%;--hb-width:31.5%;--hb-height:11.5%">Câble de charge Jackery 40 A (vendu séparément)</span></div></div></figure>

<span id="connections"></span>

# CONEXIONES

## <span class="hb-heading-title">CONECTAR AL/LOS PAQUETE(S) DE BATERÍAS</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<p>Este producto puede soportar hasta 5 paquetes de baterías para satisfacer la necesidad de una gran capacidad de energía. Para detalles sobre su uso, consulte el manual de usuario del Jackery Battery Pack 3600.</p>

<img alt="≥0,66 pied (≈200 mm) ≥0,66 pied (≈200 mm)" src="assets/battery_packs.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Si está utilizando solo un paquete de batería, puede colocarlo en cualquiera de las siguientes configuraciones:</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="battery-placement" data-source-fragment-sha256="b575494b2ce7cf794d47875b17fc68bbeb74dfcb20adfab1b3f9ccaf3ea63cdf" data-web-base-art-ref="assets/placement_framefree.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.battery-placement"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="battery-placement.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "battery-placement", "image_key": "assets/placement_framefree.png", "web_replace_key": "reference.battery-placement", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "2dc586aea7e86b79daa7f0b0219cdf963ccef0668212657ae0357aaa7a6427a4", "panel_top": 0, "panel_fill": "#ffffff", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [2.427848101265822, 6.870068027210877, 26.524050632911393, 9.314965986394547], "fill": "#ebebec"}, {"line": 1, "rect": [52.7246835443038, 6.870068027210877, 21.934493670886074, 9.314965986394547], "fill": "#ebebec"}, {"line": 2, "rect": [27.491455696202536, 83.38027210884354, 17.60348101265823, 5.735374149659853], "color": "#555555"}]}}' src="assets/placement_framefree.png"/><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="0" style="--hb-x:2.4278%;--hb-y:6.8701%;--hb-width:26.5241%;--hb-height:9.315%;--hb-fill:#ebebec">Colocación lado a lado</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:52.7247%;--hb-y:6.8701%;--hb-width:21.9345%;--hb-height:9.315%;--hb-fill:#ebebec">Colocación apilada</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:27.4915%;--hb-y:83.3803%;--hb-width:17.6035%;--hb-height:5.7354%;--hb-label-color:#555555">≥0,66 pied (≈200 mm)</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>Asegúrese de que todos los productos estén apagados antes de conectar el HomePower 3600 Pro Max al paquete de Jackery Battery Pack 3600.</li><li>Para asegurar el funcionamiento adecuado del producto, asegúrese de que las rejillas de entrada y salida de aire en ambos lados estén despejadas. Deje al menos 0,66 pies (200 mm) de espacio entre las rejillas y cualquier objeto para permitir una disipación de calor adecuada.</li></ul></td></tr></tbody></table>

## CONEXIÓN EN PARALELO EN CASCADA

<p>La conexión en cascada permite que 2 unidades HomePower 3600 Pro Max funcionen como un sistema combinado, aumentando la potencia de salida total.</p>

<h3 class="hb-source-pill-heading" id="required-accessories">Accesorios requeridos</h3>

<p>Cable de carga Jackery de 40 A Cable de comunicación en paralelo de JackeryJackery se vende por separado</p>

<h3 class="hb-source-pill-heading" id="connection-steps">PASOS PARA LA CONEXIÓN</h3>

<p>1. Asegúrese de que ambas unidades estén APAGADAS y completamente desconectadas de las fuentes de energía. 2. Conecte los puertos de comunicación en paralelo en ambas unidades</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>No omita este paso. Sin comunicación, las unidades no pueden sincronizar datos y pueden dañarse.</p></td></tr></tbody></table>

<p>3. Conecte el puerto de salida de 240 V (NEMA 14-50R) de la primera unidad al puerto de expansión CA de la segunda unidad.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cascade" data-source-fragment-sha256="c33e21dca7799d77895a8b7db62a666b8c60889a42a8a27c0e0d87cef9961ddd" data-web-base-art-ref="assets/cascade.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.cascade"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="cascade.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "cascade", "web_replace_key": "reference.cascade", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "c73793a80a50ef9eb0e2f3ac4b7d28478110bad1b05999bce390bf86a93a67fb", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [70, 12.5, 28, 10.5]}, {"line": 1, "rect": [75.5, 52.5, 22.5, 17]}]}}' src="assets/cascade.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:70%;--hb-y:12.5%;--hb-width:28%;--hb-height:10.5%">Câble de charge Jackery 40 A (vendu séparément)</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75.5%;--hb-y:52.5%;--hb-width:22.5%;--hb-height:17%">Cable de comunicación en paralelo de Jackery (se vende por separado)</span></div></div></figure>

<p>La información del sistema se sincronizará en ambas pantallas.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Después de la conexión en cascada, la potencia de salida total del sistema a través del puerto NEMA 14-50R del segundo dispositivo es de 8000 W. La carga total NO DEBE exceder la potencia total.</p></td></tr></tbody></table>

## CONECTAR AL INTERRUPTOR EPO

<p>La interfaz EPO (Apagado de Emergencia) se utiliza para conectar un interruptor externo de parada de emergencia (preparado por el usuario). Cuando ocurre una emergencia, al presionar el botón EPO se apagan inmediatamente todas las entradas y salidas de CA y CC. Se proporciona un bloque de terminales con tornillos con el producto para instalar el interruptor externo de parada de emergencia.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="epo" data-source-fragment-sha256="e8eb0b3ecfbceab4da39b4e32aaea3fe06831e465c668a3bd469b3ae5efaa36e" data-web-base-art-ref="assets/epo.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.epo"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="epo.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "epo", "web_replace_key": "reference.epo", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "73538543ce16f0a0fbce0da4f719b4c69163a881ba9f66e3376603b1047bc068", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [73.5, 24, 7.5, 10]}]}}' src="assets/epo.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:73.5%;--hb-y:24%;--hb-width:7.5%;--hb-height:10%">EPO</span></div></div></figure>

## CONNEXION D’ALIMENTATION DE SECOURS

<h3 class="hb-heading-label-pair" id="connect-to-ats-sold-separately"><span class="hb-heading-title">CONECTAR A ATS</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span></h3>

<p>El HomePower 3600 Pro Max puede suministrar energía de respaldo a los circuitos del hogar a través de un interruptor de transferencia automática Jackery (ATS). Para la instalación y operación detalladas, consulte el manual del usuario de ATS de Jackery.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ats-lock" data-source-fragment-sha256="637b5f8805f40325c8805ee43dd3d178486da304a4f38e5e6a06042b9c3f72ae" data-web-base-art-ref="assets/ats_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ats-lock"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ats-lock.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ats-lock", "image_key": "assets/ats_live.png", "web_replace_key": "reference.ats-lock", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "3a501abecb4e24bf96a40a4314d9dab8273cd3bdff9a345905c90bb6fb2652cb", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [8.577460317460316, 9.62055555555556, 10.152698412698413, 4.8238888888888845], "color": "#555555"}, {"line": 1, "rect": [61.75174603174603, 9.62055555555556, 10.311746031746031, 4.8238888888888845], "color": "#555555"}, {"line": 2, "rect": [63.492063492063494, 50.39388888888889, 29.206349206349206, 8.444444444444438], "color": "#555555"}]}}' src="assets/ats_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:8.5775%;--hb-y:9.6206%;--hb-width:10.1527%;--hb-height:4.8239%;--hb-label-color:#555555"><strong>Lock</strong></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:61.7517%;--hb-y:9.6206%;--hb-width:10.3117%;--hb-height:4.8239%;--hb-label-color:#555555"><strong>Unlock</strong></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:63.4921%;--hb-y:50.3939%;--hb-width:29.2063%;--hb-height:8.4444%;--hb-label-color:#555555">Cable de entrada/salida de alimentación en el paquete del ATS</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Cuando el modo SAI está habilitado en el ATS, la estación de energía permanece activa y consume energía continuamente. Durante un apagón de la red eléctrica, el sistema cambia a energía de batería en 20 milisegundos.</p></td></tr></tbody></table>

## <span class="hb-heading-title">CONECTAR A MTS</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<p>El HomePower 3600 Pro Max puede conectarse a un Manual Transfer Switch (MTS) para alimentar circuitos seleccionados del hogar. Elija el método adecuado según su modo de instalación.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Tous les câbles utilisés dans cette section sont vendus séparément ou inclus avec le MTS vendu séparément.</p></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="mts-installation-notice">Aviso de instalación de un interruptor de transferencia manual (MTS)</h3>

<p>Para un rendimiento óptimo al usar el HP3600 Pro Max con un interruptor MTS, se recomienda conectar la entrada de CA a un circuito sin protección GFCI (interruptor de circuito por fallo a tierra). Si se requiere protección GFCI, se recomienda instalar los dispositivos GFCI en el lado de la carga. Esta configuración ayuda a mejorar la compatibilidad del sistema y garantiza un funcionamiento de derivación de CA confiable.</p>

## CONEXIÓN DE UNA SOLA UNIDAD CON MTS

<p>En modo automático, el HomePower 3600 Pro Max recibe entrada de CA y proporciona energía de respaldo tipo SAI a través del MTS.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mts-single" data-source-fragment-sha256="e9d3d14cf00973b7c734f6c628ab6c0c9d0d112e2c906ffcb91c993166f9598c" data-web-base-art-ref="assets/mts_single_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.mts-single"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="mts-single.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "mts-single", "image_key": "assets/mts_single_live.png", "web_replace_key": "reference.mts-single", "capture_following_lines": 7, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "6351b0b395ed043bb9f3a66f98605ad951645065688dc1eff8125f6d4870625c", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [5.063291139240507, 3.5238197424892688, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 1, "rect": [5.063291139240507, 14.098326180257509, 30.696202531645568, 9.442060085836921], "color": "#555555"}, {"line": 2, "rect": [5.063291139240507, 26.66583690987124, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 3, "rect": [5.063291139240507, 39.82802575107297, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 4, "rect": [5.063291139240507, 50.12467811158799, 30.696202531645568, 9.44206008583691], "color": "#555555"}, {"line": 5, "rect": [48.65632911392405, 12.902145922746787, 19.69810126582279, 6.953218884120156], "color": "#555555"}, {"line": 6, "rect": [70.88607594936708, 77.88326180257512, 27.531645569620252, 6.523175965665217], "color": "#555555"}]}}' src="assets/mts_single_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:5.0633%;--hb-y:3.5238%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">1.</strong><span class="hb-mts-step-body">Apague el HomePower 3600 Pro Max.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:5.0633%;--hb-y:14.0983%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">2.</strong><span class="hb-mts-step-body">Conecte el HomePower 3600 Pro Max a una fuente de alimentación de CA de 240 V.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:5.0633%;--hb-y:26.6658%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">3.</strong><span class="hb-mts-step-body">Conecte el puerto de salida de 240 V (NEMA 14-50R) a la entrada del MTS.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="3" style="--hb-x:5.0633%;--hb-y:39.828%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">4.</strong><span class="hb-mts-step-body">Coloque el interruptor de carga del MTS en respaldo.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="4" style="--hb-x:5.0633%;--hb-y:50.1247%;--hb-width:30.6962%;--hb-height:9.4421%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">5.</strong><span class="hb-mts-step-body">Encienda la unidad y habilite la salida de CA.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="5" style="--hb-x:48.6563%;--hb-y:12.9021%;--hb-width:19.6981%;--hb-height:6.9532%;--hb-label-color:#555555">Cable de carga en el paquete del MTS</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="6" style="--hb-x:70.8861%;--hb-y:77.8833%;--hb-width:27.5316%;--hb-height:6.5232%;--hb-label-color:#555555">Cable de carga Jackery de 40 A (se vende por separado)</span></div></div></figure>

<p>Cuando hay energía de la red eléctrica, la energía de CA pasa hacia el MTS. Durante un apagón, el sistema cambia automáticamente a energía de batería en 10 milisegundos.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>La conmutación automática requiere que la entrada de CA permanezca conectada en todo momento.</p></td></tr></tbody></table>

## CONEXIÓN EN PARALELO EN CASCADA CON MTS

<p>Cuando dos unidades están conectadas en modo paralelo en cascada, el sistema puede entregar mayor potencia de salida al MTS.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mts-cascade" data-source-fragment-sha256="869112471cccfa92addd2b6cdc7dcf75c898f836849703b902c4a74a00344f91" data-web-base-art-ref="assets/mts_cascade_live.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.mts-cascade"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="mts-cascade.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#e6e7e8"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "mts-cascade", "image_key": "assets/mts_cascade_live.png", "web_replace_key": "reference.mts-cascade", "capture_following_lines": 6, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "a143c40b3d9936f2a5aa9d48b9a459952760a9b518ad9194e59113e2eb805477", "panel_top": 0, "panel_fill": "#e6e7e8", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [56.782334384858046, 5.276270718232044, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 1, "rect": [56.782334384858046, 12.082265193370162, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 2, "rect": [56.782334384858046, 20.171408839779005, 36.59305993690852, 6.629834254143646], "color": "#555555"}, {"line": 3, "rect": [8.517350157728707, 26.382292817679556, 24.9211356466877, 4.833176795580114], "color": "#555555"}, {"line": 4, "rect": [43.217665615141954, 36.6271546961326, 31.861198738170348, 5.085552486187842], "color": "#555555"}, {"line": 5, "rect": [69.08517350157729, 76.8868232044199, 22.397476340694006, 6.81483425414364], "color": "#555555"}]}}' src="assets/mts_cascade_live.png"/><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="0" style="--hb-x:56.7823%;--hb-y:5.2763%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">1.</strong><span class="hb-mts-step-body">Complete los pasos de conexión en paralelo en cascada descritos anteriormente.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="1" style="--hb-x:56.7823%;--hb-y:12.0823%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">2.</strong><span class="hb-mts-step-body">Conecte el puerto de salida de 240 V (NEMA 14-50R) del segundo dispositivo a la entrada del MTS.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="2" style="--hb-x:56.7823%;--hb-y:20.1714%;--hb-width:36.5931%;--hb-height:6.6298%;--hb-label-color:#555555"><span class="hb-mts-step"><strong class="hb-mts-step-number">3.</strong><span class="hb-mts-step-body">Encienda ambas unidades y habilite la salida de CA.</span></span></span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="3" style="--hb-x:8.5174%;--hb-y:26.3823%;--hb-width:24.9211%;--hb-height:4.8332%;--hb-label-color:#555555">Cable de carga en el paquete del MTS</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="4" style="--hb-x:43.2177%;--hb-y:36.6272%;--hb-width:31.8612%;--hb-height:5.0856%;--hb-label-color:#555555">Cable de carga Jackery de 40 A (se vende por separado)</span><span class="hb-reference-live-label hb-reference-source-badge" data-source-line="5" style="--hb-x:69.0852%;--hb-y:76.8868%;--hb-width:22.3975%;--hb-height:6.8148%;--hb-label-color:#555555">Cable de comunicación paralela Jackery (se vende por separado)</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Después de la conexión en cascada, la salida máxima al MTS es de 8000 W. La carga total NO DEBE exceder la potencia total.</p></td></tr></tbody></table>

<span id="charging"></span>

# CARGANDO

<p><strong>Energía renovable primero:</strong>Abogamos por utilizar primero energía renovable. Este producto admite dos modos de carga al mismo tiempo: carga solar y carga de pared de CA. Cuando la carga en la pared de CA y la carga solar están activadas al mismo tiempo, el producto dará prioridad a la carga solar y se utilizarán ambos métodos para cargar la batería a la máxima potencia permitida.</p>

<p class="hb-prose-pill">Carga completamente el producto antes de usarlo por primera vez.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><ul><li>La temperatura de carga recomendada para el producto está entre -4 °F y 113 °F (-20 °C a 45 °C), y la temperatura de descarga está entre -4 °F y 113 °F (-20 °C a 45 °C). Operar el producto fuera de este rango de temperatura puede limitar sus capacidades de carga y descarga, e incluso impedir la carga o descarga.</li><li>La potencia de carga y la capacidad de la batería del producto pueden variar debido a fluctuaciones de temperatura.</li></ul></td></tr></tbody></table>

## CARGA MEDIANTE TOMA DE CORRIENTE DE PARED DE CA DE 120 V

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charge120" data-source-fragment-sha256="484f4e7d5cd67891ce8d3420c9456b0f87d70dc6e1c42fde243326bee8a6d1c2" data-web-base-art-ref="assets/charge120.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.charge120"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charge120.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "charge120", "web_replace_key": "reference.charge120", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "378983dcedd288cc23b4752b949ca53ddf98dcf5a1334ce6b0319c59a0e3ecbb", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "labels": [{"line": 0, "rect": [57.65, 79.53, 38.3, 14.3]}], "mobile_labels": "overlay"}}' src="assets/charge120.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:57.65%;--hb-y:79.53%;--hb-width:38.3%;--hb-height:14.3%">Conecte el cable de carga de CA al puerto de entrada de CA del producto y a una toma de corriente.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>Asegúrese de que el cable de carga de CA esté completamente y firmemente insertado en el puerto de entrada de CA.</li><li>Una conexión incompleta puede provocar corriente inestable, sobrecalentamiento, mal contacto o fallos en el funcionamiento del producto.</li></ul></td></tr></tbody></table>

## CARGA MEDIANTE ENTRADA DE CA DE 240 V

<p>El HomePower 3600 Pro Max admite carga a través de su puerto de expansión CA de 240 V. Según su instalación, la entrada de CA de 240 V puede provenir de una toma de CA de 240 V o de un Automatic Transfer Switch (ATS) de Jackery.</p>

<h3 class="hb-source-pill-heading" id="v-ac-outlet">Toma de CA de 240 V</h3>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="charge240" data-source-fragment-sha256="9fbdce0cceb7c5cfc7d57647b27466d7b643b7b6eb3ed4e40055dadaaa6cf355" data-web-base-art-ref="assets/charge240.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.charge240"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="charge240.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#eaebec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "charge240", "web_replace_key": "reference.charge240", "capture_following_lines": 1, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "78421e939d39ded94f7ec9c48de298d160fb082d1302f8aef16d395679252632", "panel_top": 0, "panel_fill": "#eaebec", "preserve_frame": true, "labels": [{"line": 0, "rect": [43.82, 75.04, 52, 16]}], "mobile_labels": "overlay"}}' src="assets/charge240.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:43.82%;--hb-y:75.04%;--hb-width:52%;--hb-height:16%">Conecte el producto a una fuente de alimentación de CA de 240 V usando un cable de carga Jackery de 40 A (se vende por separado).</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>Asegúrese de que el cable de carga Jackery de 40 A esté completamente y firmemente conectado tanto a la toma de 240 V como al puerto de expansión de CA.</li><li>Una conexión incompleta puede provocar corriente inestable, sobrecalentamiento, mal contacto o fallos en el funcionamiento del producto.</li></ul></td></tr></tbody></table>

<h3 class="hb-source-pill-heading" id="transfer-switch-ats">INTERRUPTOR DE TRANSFERENCIA (ATS)</h3>

<p>Conecte su ATS de Jackery al producto para habilitar la carga mediante el interruptor de transferencia.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>La configuración de reserva de respaldo se aplica en todos los modos de operación del ATS. Cuando la capacidad restante del HomePower 3600 Pro Max supere la reserva de respaldo configurada, la carga se detendrá automáticamente.</p></td></tr></tbody></table>

<p>Para cargarlo inmediatamente, sigue las instrucciones a continuación: 1. Toca Estación de energía en el flujo de energía del panel de control del ATS. 2. En la página de la Estación de energía, toca Cargar ahora.</p>

<img alt="INTERRUPTOR DE TRANSFERENCIA (ATS)" src="assets/ats_app.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Cuando el puerto de expansión de CA está conectado al ATS, la entrada de CA no se utilizará para cargar. En ese caso, la estación de energía se puede cargar mediante los siguientes puertos: puerto de expansión de CA, puertos DC8020.</p></td></tr></tbody></table>

## <span class="hb-heading-title">CARGA MEDIANTE PANELES SOLARES</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<p>El Jackery HomePower 3600 Pro Max cuenta con dos puertos de entrada DC8020, y cada uno admite la conexión directa a un panel solar de 500 W o a tres paneles solares de 200 W. Si desea conectar dos o más paneles solares a un solo puerto de entrada DC8020 simultáneamente, consulte la figura a continuación para la conexión mediante el conector de panel solar (se vende por separado, no incluido de serie).</p>

<img alt="SolarSaga 500 X × 2" src="assets/solar500.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="SolarSaga 200 × 6" src="assets/solar200.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Asegúrese de que el voltaje de entrada para ambos puertos de entrada CC sea el mismo. De lo contrario, podría dañar el producto. Por ejemplo: Utilizar paneles solares Jackery del mismo modelo y la misma cantidad de paneles al conectar paneles solares a ambos puertos de entrada DC8020. No cargue el producto utilizando simultáneamente un cargador de automóvil y un panel solar. Hacerlo podría quemar el fusible del automóvil o resultar en un fallo de carga.</p></td></tr></tbody></table>

<p>Se recomienda utilizar paneles solares Jackery para cargar el HomePower 3600 Pro Max. Asegúrate de que la tensión de funcionamiento (Vmp) del panel solar esté dentro del rango de entrada de CC (16 V-60 V) del HomePower 3600 Pro Max. Jackery no se hace responsable de pérdidas causadas por el uso de paneles solares de otras marcas.</p>

## <span class="hb-heading-title">CARGA MEDIANTE UN CARGADOR PARA VEHÍCULO</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<p>Este producto puede cargarse con un cargador para vehículo de 12 V. Asegúrate de que el cargador para vehículo y la toma de alimentación de 12 V del vehículo estén bien conectados.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car_charging" data-source-fragment-sha256="111f246c1ca9ec451326e4a94db0ad00a58983c5955c082180746bc224a72528" data-web-base-art-ref="assets/car_charging_framefree.svg" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.car-charging"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car_charging.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "car_charging", "web_replace_key": "reference.car-charging", "capture_following_lines": 2, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "c5bf094d9b0f2cd27cd5f6ac9e82e6ad413ac0c4f36441d76dcb7de7d7cfdfd4", "panel_top": 0, "panel_fill": "#ebecec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [67, 10.4, 15, 9]}, {"line": 1, "rect": [49.37, 75.12, 47.65, 10.07], "fill": "#ffffff"}]}}' src="assets/car_charging_framefree.svg"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:67%;--hb-y:10.4%;--hb-width:15%;--hb-height:9%">Vehículo</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="1" style="--hb-x:49.37%;--hb-y:75.12%;--hb-width:47.65%;--hb-height:10.07%;--hb-fill:#ffffff">* El cable de carga para auto se vende por separado.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>Por favor, encienda el vehículo antes de cargar su estación de energía.</li><li>Si el vehículo circula por caminos accidentados, está prohibido usar el cargador de coche para evitar que se queme debido a una mala conexión. La empresa no se responsabiliza por pérdidas causadas por un uso incorrecto.</li><li>La carga en vehículo solo es aplicable a vehículos con 12 V CC, no a 24 V CC. Por favor, no cargue este producto en vehículos de 24 V para evitar lesiones personales y daños materiales.</li></ul></td></tr></tbody></table>

<span id="troubleshooting"></span>

# RESOLUCIÓN DE PROBLEMAS

<p>Si aparece alguno de los siguientes códigos de falla, siga las acciones correctivas listadas para resolver el problema. Si la falla persiste, por favor contacte con atención al cliente de Jackery.</p>

<figure aria-label="Código de Error / Medidas correctivas" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Código de Error</th><th class="hb-troubleshooting-measures" scope="col">Medidas correctivas</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0/F1 F2/F3</td><td class="hb-troubleshooting-measures">Reiniciar el producto.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Conecte el producto a cargas para descargar su batería hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Cargue el producto mediante paneles solares o toma de corriente CA hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">F6</td><td class="hb-troubleshooting-measures">1. Espere a que la red eléctrica se normalice antes de cargar el producto a través de una toma de corriente CA.<br/>2. Verifique si las rejillas de entrada y salida de aire están obstruidas; asegure un espacio libre de 0,66 pies (20 cm) a ambos lados del producto.<br/>3. Coloque el producto en un lugar que no esté expuesto a la luz solar directa o a altas temperaturas ambientales.<br/>4. Desconecte todas las cargas del producto. Mantenga el producto inactivo y espere hasta que la falla desaparezca.<br/>5. Reiniciar el producto.</td></tr><tr><td class="hb-troubleshooting-code">F7</td><td class="hb-troubleshooting-measures">1. Retire todas las entradas de CC del producto.<br/>2. Verifique la tensión de funcionamiento (Vmp) de los paneles solares conectados. El producto permite un voltaje máximo de entrada de CC de 60 V.<br/>3. Reinicie el producto y déjelo en reposo. Espere hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">F8</td><td class="hb-troubleshooting-measures">Contacter le service à la clientèle de Jackery.</td></tr><tr><td class="hb-troubleshooting-code">F9</td><td class="hb-troubleshooting-measures">Retire la carga conectada a los puertos USB del producto. Espere hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">FA</td><td class="hb-troubleshooting-measures">1. Apague las salidas de CA y apague ambas unidades.<br/>2. Desconecte los cables entre las unidades y vuelva a conectar las dos unidades.<br/>3. Reinicie ambas unidades y habilite sus salidas de CA.</td></tr><tr><td class="hb-troubleshooting-code">FC</td><td class="hb-troubleshooting-measures">1. Reinicie los paquetes de baterías y el HomePower 3600 Pro Max respectivamente.<br/>2. Si la falla persiste, desconecte el paquete de baterías del HomePower 3600 Pro Max y reconéctelos.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures">1. Después de que la condición de emergencia se haya despejado, presione el botón EPO nuevamente.<br/>2. Si necesita alimentar cargas de CA o CC, presione el botón de alimentación de CA o el botón de alimentación de CC para volver a habilitar la salida.</td></tr></tbody></table></figure>

<span id="storage"></span>

# ALMACENAMIENTO

<p>Almacene el producto en un lugar seco y limpio con ventilación adecuada.Temperatura y humedad de almacenamiento:</p>

<ul><li>1 mes: -4°F a 113°F / -20 a 45 °C (0-60 % HR)</li><li>3 meses: 32°F a 113°F / 0 a 45 °C (0-60 % HR)</li><li>12 meses: 32°F a 77°F / 0 a 25 °C (0-60 % HR)</li></ul>

<p>Si este producto se almacena durante un período prolongado (de 3 a 6 meses) con la batería descargada, podría volverse imposible recargarlo. Para evitar esto y mantener la salud de la batería, se recomienda revisar y recargar el producto cada tres meses, y realizar un ciclo completo de carga y descarga al menos una vez cada 6 a 12 meses.</p>

<span id="specifications"></span>

# ESPECIFICACIONES

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química Celular</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">73,85 libras/33,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">14,76 × 10,83 × 17,72 pulgadas / 37,5×27,5×45,0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">6000 ciclos de carga hasta 70 % + de capacidad</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">&lt;10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topología de inversor</th><td class="manual-spec-value hb-spec-value">Aislada</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Factor de potencia</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unidad entera</th><td class="manual-spec-value hb-spec-value">Tipo 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE ENTRADA</h2>

<figure aria-label="PUERTOS DE ENTRADA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">1 × Entrada CA</th><td class="manual-spec-value hb-spec-value">Modo de carga: 100 V-120 V~ 60 Hz, 15 A máx., 1800 W</td></tr><tr><td class="manual-spec-value hb-spec-value">Modo de derivación<sup class="hb-spec-reference">①</sup>: 100 V-120 V~ 60 Hz, 12 A máx., 1440 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Puertos DC8020</th><td class="manual-spec-value hb-spec-value">12–16 V⎓8 A máx., Doble a 8 A máx. 16-60 V<sup class="hb-spec-reference">②</sup>⎓12A máx., Doble a 24 A / 1200 W máx.</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE SALIDA</h2>

<figure aria-label="PUERTOS DE SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salidas CA (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120 V~ 60 Hz, 16,7A máx., 2000 W por puerto, 4000W en total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salidas CA (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240 V~60 Hz, 16,7A máx., 4000 W nominales, 8000W pico de sobretensión</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida total de CA<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000 W nominales, 8000 W pico de sobretensión</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Salida de CA en Modo de derivación<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value"><strong>Entrada de CA de 120 V:</strong><br/>NEMA 5-20R: 100 V-120 V~ 60 Hz, 12 A máx., 1440 W por puerto, 1440W<sup class="hb-spec-reference">④</sup> en total<br/>NEMA 14-50R: 240 V~ 60 Hz, 1440W<sup class="hb-spec-reference">④</sup> máx.</td></tr><tr><td class="manual-spec-value hb-spec-value"><strong>Entrada de CA de 240 V:</strong><br/>NEMA 5-20R: 100 V-120 V~ 60 Hz, 20 A máx., 2400 W por puerto, 4800W en total<br/>NEMA 14-50R: 240 V~ 60 Hz, 40 A máx., 9600 W máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salida USB-C</th><td class="manual-spec-value hb-spec-value">100 W máx., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salida USB-A</th><td class="manual-spec-value hb-spec-value">18 W máx., 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE EXPANSIÓN</h2>

<figure aria-label="PUERTOS DE EXPANSIÓN" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de expansión CA</th><td class="manual-spec-value hb-spec-value">240 V~60 Hz, 16,7 máx., 4000 W máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de expansión CC</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓126 A máx. (Entrada)<br/>36,4 V-50,4 V⎓60 A máx. (Salida)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">ESPECIFICACIONES AMBIENTALES</h2>

<figure aria-label="ESPECIFICACIONES AMBIENTALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F (-20 °C a 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F (-20 °C a 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitud</th><td class="manual-spec-value hb-spec-value">≤ 3000 m</td></tr></tbody></table></figure>

<p>※ USB Type-C® y USB-C® son marcas registradas de USB Implementers Forum.</p>

<p class="manual-spec-footnote">① El producto puede cargar la batería desde una toma de corriente CA o a través del ATS mientras suministra energía a través de los puertos de salida CA.</p>

<p class="manual-spec-footnote">② Indica la tensión de funcionamiento (Vmp) permitida del panel solar.</p>

<p class="manual-spec-footnote">③ Indica que dos o más puertos de salida CA trabajan en conjunto.</p>

<p class="manual-spec-footnote">④ Cuando está conectado a cargas superiores a 1440 W bajo entrada de CA de 120 V, el producto toma energía de la batería para cumplir con el requerimiento de carga total de hasta 2880 W.</p>

<span id="warranty"></span>

# GARANTÍA

<figure aria-label="GARANTÍA" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><p>Solo ofrecemos nuestra garantía a clientes que compren en el sitio web oficial de Jackery, plataformas de terceros con la marca Jackery o distribuidores autorizados locales.</p></div><div class="hb-warranty-local-note"><p>*El periodo de garantía y los detalles pueden variar según las leyes, regulaciones y distribuidores autorizados locales.</p></div></figure>

## Garantía limitada

<figure aria-label="Garantía limitada" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantiza al consumidor original que el producto Jackery estará libre de defectos relativos al acabado y a los materiales en condiciones normales de uso por parte del consumidor durante el período de garantía aplicable identificado en la sección "Período de garantía" que figura a continuación, sujeto a las exclusiones que se establecen a continuación. Esta declaración de garantía establece la obligación de garantía total y exclusiva de Jackery. No asumiremos ni autorizaremos que ninguna persona asuma por nosotros ninguna otra responsabilidad en relación con la venta de nuestros productos.</p></figure>

## Período de garantía

<figure aria-label="Período de garantía" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 AÑOS Garantía Estándar" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía Estándar</strong></div></div><div class="hb-warranty-period-copy"><p>El periodo de garantía estándar de Jackery HomePower 3600 Pro Max es de 36 meses. En cada caso, el período de garantía se mide a partir de la fecha de compra por parte del comprador consumidor original. Para establecer la fecha de inicio del período de garantía, se necesita el recibo de venta de la primera compra del consumidor u otra prueba documental razonable.</p></div></div><div aria-label="2 AÑOS Garantía extendida" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía extendida</strong></div></div><div class="hb-warranty-period-copy"><p>Para activar la extensión de garantía, debe registrar su producto en línea o ponerse en contacto con nuestro equipo de atención al cliente en hello@jackery.com para ampliar la duración de la garantía estándar.</p></div></div></div></figure>

## Reparación o reemplazo

<figure aria-label="Reparación o reemplazo" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>Jackery reparará o reemplazará (a cargo de Jackery) cualquier producto Jackery que no funcione durante el periodo de garantía aplicable debido a defectos en la mano de obra o el material. El producto reparado o reemplazado asumirá el periodo restante de la garantía desde la fecha original de compra.</p></figure>

## Limitado al comprador consumidor original

<figure aria-label="Limitado al comprador consumidor original" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>La garantía del producto de Jackery se limita al consumidor original y no es transferible a ningún propietario posterior.</p></figure>

## Exclusiones

<figure aria-label="Exclusiones" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantía de Jackery no se aplica a:</p>Mal uso, abuso, modificación, daño por accidente, o uso para cualquier cosa que no sea el uso normal del consumidor según lo autorizado en los folletos actuales del producto de Jackery. Intento de reparación por cualquier persona que no sea un centro autorizado. Cualquier producto adquirido a través de una casa de subastas en línea. La garantía de Jackery no se aplica a la célula de la batería a menos que usted la cargue completamente en los siete días siguientes a la compra del producto y, a partir de entonces, al menos una vez cada 6 meses.</figure>

## Derechos de interpretación

<figure aria-label="Derechos de interpretación" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>Jackery se reserva el derecho a la interpretación final de la política posventa de los clientes anterior.</p></figure>

<span id="app"></span>

# CONFIGURACIÓN DE LA APLICACIÓN

## 1. Descargar la aplicación e iniciar sesión

<figure aria-label="1. Descargar la aplicación e iniciar sesión" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app_store_badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Buscar "Jackery" en Google Play o en la App Store para instalar la aplicación. Después, podrá registrarte e iniciar sesión.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/app_download_qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternativamente, escanee el código QR a continuación para descargar e instalar la app.</p></div></div></div><div class="hb-app-download-semantic"><img alt="1. Descargar la aplicación e iniciar sesión" class="hb-app-download-semantic-art" src="assets/app_store_badges.png"/></div></figure>

## 2. Añadir un dispositivo

<p>2.1 Haga clic en el botón <span aria-label="+" class="hb-inline-add-device-icon" data-component-id="HB-SPECIAL-APP" role="img">+</span> Añadir dispositivo ;</p>

<p>2.2 Presione una vez el botón de encendido principal del dispositivo para encenderlo. Los iconos del wifi y del Bluetooth del dispositivo parpadearán para indicar que el dispositivo ha entrado en el modo de configuración de red. A continuación, pulse el botón "icono parpadeante" y permita que la aplicación se conecte a los dispositivos cercanos y abra los permisos de Bluetooth;</p>

<img alt="2.2 2.1" class="hb-app-add-device-phone-art hb-app-phone-pair" src="assets/app_add.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<img alt="Botón de encendido principal" src="assets/app_control.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">REMARQUE</td><td class="manual-callout-body"><p>Después de estar encendido, si la APP no se conecta en 2 horas, el dispositivo desactivará automáticamente el Wi-Fi y el Bluetooth. Ahora se requiere mantener presionados el botón de alimentación SAI y el botón de alimentación de CA para activar nuevamente el Wi-Fi y Bluetooth.</p></td></tr></tbody></table>

<p>2.3. Tras hacer clic en el icono del dispositivo buscado, la aplicación conecta automáticamente el dispositivo a través de Bluetooth.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Si durante el proceso de vinculación se indica que "el dispositivo ha sido vinculado", se pueden utilizar las dos formas siguientes para la conexión.</p><ul><li>El propietario del dispositivo lo compartirá con otros usuarios a través de la App.</li><li>Mantenga pulsados el botón de encendido principal y el botón de energía USB durante 3 segundos para reiniciar el Wi-Fi y el Bluetooth del dispositivo y, a continuación, vuelva a vincularlo.</li></ul></td></tr></tbody></table>

<p>2.4 Una vez que el dispositivo se haya conectado correctamente, es necesario introducir el nombre y la contraseña de la red Wi-Fi a la que se conectará el dispositivo.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Selecciona una red Wi-Fi en la banda de 2,4 GHz. El dispositivo no admite una red Wi-Fi en la banda de 5 GHz.</p></td></tr></tbody></table>

<p>2.5. Después de agregar exitosamente el dispositivo en la App, el icono del Wi-Fi en el dispositivo permanecerá siempre encendido.</p>

<img alt="CONFIGURACIÓN DE LA APLICACIÓN" class="hb-app-add-device-phone-art hb-app-phone-trio" src="assets/app_connect_result_steps.png" style="display:block;max-width:100%;height:auto;margin:1rem auto;"/>

<p>Las capturas de pantalla anteriores sirven solo de referencia.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>La aplicación Jackery solo puede conectarse a una estación de energía a la vez mediante Bluetooth. Regresar a la lista de dispositivos desconecta automáticamente Bluetooth. Toque la estación de energía en la lista nuevamente para reconectarse automáticamente.</p></td></tr></tbody></table>

## 3. Desvincular el dispositivo

<p>Haga clic en el botón «Configuración» situado en la esquina superior derecha de la interfaz principal del dispositivo para entrar en la página de configuración. Después, haga clic en el botón «Desvincular» situado en la parte inferior de la página para desvincular el dispositivo.</p>

## 4. Notas

### 4.1 Para activar Wi-Fi y Bluetooth:

<ul><li>El wifi y el Bluetooth se encienden automáticamente al encender el dispositivo y se iluminan los iconos de wifi y Bluetooth de la pantalla;</li><li>Pulse el botón de energía USB y el botón de energía CA al mismo tiempo hasta que se enciendan los iconos de wifi y Bluetooth en la pantalla;</li></ul>

### 4.2 Para desactivar Wi-Fi y Bluetooth:

<ul><li>Pulse el botón de energía USB y el botón de energía CA al mismo tiempo hasta que se apaguen los iconos de wifi y Bluetooth en la pantalla;</li><li>El Wi-Fi y el Bluetooth se apagarán automáticamente si se conecta ningún dispositivo en 2 horas;</li></ul>

### 4.3 Para restablecer Wi-Fi y Bluetooth:

<p>Pulsa el botón de encendido principal y el botón de energía USB al mismo tiempo durante 3 segundos para restablecer los ajustes de fábrica de Wi-Fi y Bluetooth y reiniciar el sistema. Se desvinculará la cuenta de la aplicación conectada.</p>

<span id="ess"></span>

# <span class="hb-heading-title">SISTEMA DE RESPALDO INTELIGENTE PARA EL HOGAR (AC ESS)</span> <span class="hb-heading-model">N° de modelo: HB3600C-TS05A</span>

<table class="manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/e1746d6937db_warning_triangle_dark.svg"/><strong>ADVERTENCIA</strong></span></td><td class="manual-callout-body"><p>RIESGO DE DESCARGA ELÉCTRICA. ASEGÚRESE SIEMPRE DE QUE TODOS LOS EQUIPOS ELÉCTRICOS ESTÉN DESCONECTADOS DE FORMA SEGURA ANTES DE EMPEZAR A TRABAJAR.</p></td></tr></tbody></table>

<p>Para conectar el Jackery HomePower 3600 Pro Max al ATS, use el cable de entrada/salida de alimentación para conectarlo al puerto de expansión CA del HomePower 3600 Pro Max al puerto de entrada/salida CA del ATS. Para conectar el Jackery HomePower 3600 Pro Max al paquete de baterías, use el cable de expansión para conectar su puerto de expansión CC (A) al puerto de expansión CC (B) del paquete de baterías.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ess_connection" data-source-fragment-sha256="a738982bea2a6e3a2a366e7ccc39b2ab4c8c5e253d3642256a74e6afbbacb2f4" data-web-base-art-ref="assets/ess_connection.png" data-web-presentation-mode="base-art-live-copy" data-web-replace-key="reference.ess-connection"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="ess_connection.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ebecec"><img alt="" class="hb-source-reference hb-reference-art hb-composite-art" data-reference='{"id": "ess_connection", "image_key": "assets/ess_connection.png", "web_replace_key": "reference.ess-connection", "capture_following_lines": 3, "presentation_mode": "base-art-live-copy", "base_art_layout": {"art_sha256": "4039388533950249061954f24e6866b64c0641c146e277ada6e96c4892c52616", "panel_top": 0, "panel_fill": "#ebecec", "preserve_frame": true, "mobile_labels": "overlay", "labels": [{"line": 0, "rect": [69.52, 36.26, 26.35, 8.4]}, {"line": 1, "rect": [72.38, 53.05, 23.5, 8.78]}, {"line": 2, "rect": [3.49, 89.31, 55.87, 8.02]}]}}' src="assets/ess_connection.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:69.52%;--hb-y:36.26%;--hb-width:26.35%;--hb-height:8.4%">Cable de entrada/salida de alimentación</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:72.38%;--hb-y:53.05%;--hb-width:23.5%;--hb-height:8.78%">Cable de expansión</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:3.49%;--hb-y:89.31%;--hb-width:55.87%;--hb-height:8.02%">Para obtener instrucciones detalladas sobre la instalación y conexión, consulte los manuales de usuario del ATS y del paquete de baterías.</span></div></div></figure>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Posición de instalación del sistema de respaldo inteligente para el hogar (AC ESS)</p><ul><li>Instalación en interiores.</li><li>El área debe ser completamente impermeable.</li><li>La pared debe ser plana y nivelada.</li><li>Rango de temperatura ambiente: -4 °F a 113 °F (-20 °C a 45 °C);</li><li>La temperatura y la humedad deben mantenerse en un nivel constante.</li><li>Instale en un lugar bien ventilado.</li><li>No instale en un área accesible para niños o mascotas.</li><li>El área de instalación debe evitar la luz solar directa.</li><li>No debe haber materiales inflamables o explosivos cerca del inversor y la batería.</li></ul></td></tr></tbody></table>

<span id="ess-specifications"></span>

# <span class="hb-heading-title">ESPECIFICACIONES</span> <span class="hb-heading-model">N° de modelo: JHP-3600C</span>

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery HomePower 3600 Pro Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JHP-3600C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 V DC (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química Celular</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">73,85 libras/33,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">14,76 × 10,83 × 17,72 pulgadas / 37,5×27,5×45,0 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">6000 ciclos de carga hasta 70 % + de capacidad</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1520A, 2.56ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">&lt;10 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Topología de inversor</th><td class="manual-spec-value hb-spec-value">Aislada</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Factor de potencia</th><td class="manual-spec-value hb-spec-value">≥0,98</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Unidad entera</th><td class="manual-spec-value hb-spec-value">Tipo 1</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE ENTRADA</h2>

<figure aria-label="PUERTOS DE ENTRADA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">1 × Entrada CA</th><td class="manual-spec-value hb-spec-value">Modo de carga: 100 V-120 V~ 60 Hz, 15 A máx., 1800 W</td></tr><tr><td class="manual-spec-value hb-spec-value">Modo de derivación<sup class="hb-spec-reference">①</sup>: 100 V-120 V~ 60 Hz, 12 A máx., 1440 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Puertos DC8020</th><td class="manual-spec-value hb-spec-value">12–16 V⎓8 A máx., Doble a 8 A máx. 16-60 V<sup class="hb-spec-reference">②</sup>⎓12A máx., Doble a 24 A / 1200 W máx.</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE SALIDA</h2>

<figure aria-label="PUERTOS DE SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">2 × Salidas CA (NEMA 5-20R)</th><td class="manual-spec-value hb-spec-value">120 V~ 60 Hz, 16,7A máx., 2000 W por puerto, 4000W en total</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salidas CA (NEMA 14-50R)</th><td class="manual-spec-value hb-spec-value">240 V~60 Hz, 16,7A máx., 4000 W nominales, 8000W pico de sobretensión</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Salida total de CA<sup class="hb-spec-reference">③</sup></th><td class="manual-spec-value hb-spec-value">4000 W nominales, 8000 W pico de sobretensión</td></tr><tr><th class="manual-spec-label hb-spec-label" rowspan="2" scope="row">Salida de CA en Modo de derivación<sup class="hb-spec-reference">①</sup></th><td class="manual-spec-value hb-spec-value"><strong>Entrada de CA de 120 V:</strong><br/>NEMA 5-20R: 100 V-120 V~ 60 Hz, 12 A máx., 1440 W por puerto, 1440W<sup class="hb-spec-reference">④</sup> en total<br/>NEMA 14-50R: 240 V~ 60 Hz, 1440W<sup class="hb-spec-reference">④</sup> máx.</td></tr><tr><td class="manual-spec-value hb-spec-value"><strong>Entrada de CA de 240 V:</strong><br/>NEMA 5-20R: 100 V-120 V~ 60 Hz, 20 A máx., 2400 W por puerto, 4800W en total<br/>NEMA 14-50R: 240 V~ 60 Hz, 40 A máx., 9600 W máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salida USB-C</th><td class="manual-spec-value hb-spec-value">100 W máx., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Salida USB-A</th><td class="manual-spec-value hb-spec-value">18 W máx., 5-6V⎓3A, 6-9V⎓2A, 9-12V⎓1.5A</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE EXPANSIÓN</h2>

<figure aria-label="PUERTOS DE EXPANSIÓN" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de expansión CA</th><td class="manual-spec-value hb-spec-value">240 V~60 Hz, 16,7 máx., 4000 W máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">1 × Puerto de expansión CC</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓126 A máx. (Entrada)<br/>36,4 V-50,4 V⎓60 A máx. (Salida)</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">ESPECIFICACIONES AMBIENTALES</h2>

<figure aria-label="ESPECIFICACIONES AMBIENTALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F (-20 °C a 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F (-20 °C a 45 °C)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Altitud</th><td class="manual-spec-value hb-spec-value">≤ 3000 m</td></tr></tbody></table></figure>

<p>※ USB Type-C® y USB-C® son marcas registradas de USB Implementers Forum.</p>

<p class="manual-spec-footnote">① El producto puede cargar la batería desde una toma de corriente CA o a través del ATS mientras suministra energía a través de los puertos de salida CA.</p>

<p class="manual-spec-footnote">② Indica la tensión de funcionamiento (Vmp) permitida del panel solar.</p>

<p class="manual-spec-footnote">③ Indica que dos o más puertos de salida CA trabajan en conjunto.</p>

<p class="manual-spec-footnote">④ Cuando está conectado a cargas superiores a 1440 W bajo entrada de CA de 120 V, el producto toma energía de la batería para cumplir con el requerimiento de carga total de hasta 2880 W.</p>

# <span class="hb-heading-title">Jackery Battery Pack 3600</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<h2 aria-level="2" class="hb-spec-group" role="heading">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 3600</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JBP-3600 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">80 Ah / 44,8 Vdc (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química Celular</th><td class="manual-spec-value hb-spec-value">LiFePO4</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 55,1 libras/25 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">14,8 × 12,5 × 9,0 pulgadas / 37,5 × 31,7 × 22,9 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">6000 ciclos de carga hasta 70 %+ de capacidad</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">PUERTOS DE ENTRADA/SALIDA</h2>

<figure aria-label="PUERTOS DE ENTRADA/SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓60 A máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">36,4 V-50,4 V⎓100 A máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Maximum Short Circuit Current and Duration</th><td class="manual-spec-value hb-spec-value">1160A/860μs</td></tr></tbody></table></figure>

<h2 aria-level="2" class="hb-spec-group" role="heading">TEMPERATURA DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F / -20 °C a 45 °C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-4 °F a 113 °F / -20 °C a 45 °C</td></tr></tbody></table></figure>

# <span class="hb-heading-title">Jackery Automatic Transfer Switch</span> <span class="hb-sold-separately">SE VENDE POR SEPARADO</span>

<h2 aria-hidden="true" aria-level="2" class="hb-spec-group hb-source-hidden-heading" role="heading">Jackery Automatic Transfer Switch</h2>

<figure aria-label="Jackery Automatic Transfer Switch" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery Automatic Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JA-TS05 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tensión CA (Nominal)</th><td class="manual-spec-value hb-spec-value">120 V/240 V~60 Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tipo de Alimentación</th><td class="manual-spec-value hb-spec-value">Split-Phase</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Entrada Máxima</th><td class="manual-spec-value hb-spec-value">Red de 100 A / Estación de Energía de 84 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Salida Máxima</th><td class="manual-spec-value hb-spec-value">Carga Doméstica de 100 A / Estación de Energía de 33,4 A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente Máxima de Cortocircuito de Entrada</th><td class="manual-spec-value hb-spec-value">10KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Consumo en modo de espera</th><td class="manual-spec-value hb-spec-value">Cerca de 5 W</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Categoría de Sobretensión</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS (SAI)</th><td class="manual-spec-value hb-spec-value">≤20 ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">CONSEJOS</th><td class="manual-spec-value hb-spec-value">Caja de distribución: NEMA Tipo 3R<br/>Caja de enchufes: NEMA Tipo 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Grado de contaminación</th><td class="manual-spec-value hb-spec-value">III</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito Principal</th><td class="manual-spec-value hb-spec-value">2 AWG (100 A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito de carga</th><td class="manual-spec-value hb-spec-value">2 AWG (100 A)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Comunicación</th><td class="manual-spec-value hb-spec-value">Wi-Fi y Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">27 × 14,4 × 5,7 pulgadas/ 68,5 × 36,5 × 14,4 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 23,1 libras/10,5 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de Funcionamiento</th><td class="manual-spec-value hb-spec-value">-4 °F a 122 °F / -20 °C a 50 °C</td></tr></tbody></table></figure>

<span id="ess-package"></span>

## CONTENIDO DE LA CAJA

### Jackery HomePower 3600 Pro Max

<div class="hb-package-panel"><ul class="hb-package-grid"><li class="hb-package-item"><div class="hb-package-art hb-package-art--unit"><img alt="" src="assets/inbox_unit.png"/></div><p>Jackery HomePower 3600 Pro Max</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--ac"><img alt="" src="assets/inbox_ac.png"/></div><p>Cable de carga de CA</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--terminal"><img alt="" src="assets/inbox_terminal.png"/></div><p>Bornera de tornillo</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Documentos</p></li></ul></div>

### Jackery Battery Pack 3600 — Se vende por separado

<div class="hb-package-panel hb-package-panel--optional"><ul class="hb-package-grid"><li class="hb-package-item"><div class="hb-package-art hb-package-art--battery"><img alt="" src="assets/package_battery.png"/></div><p>Jackery Battery Pack 3600</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--expansion"><img alt="" src="assets/package_expansion.png"/></div><p>Cable de expansión</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manual de usuario</p></li><li class="hb-package-availability"><div class="hb-package-sold">Se vende por separado</div></li></ul></div>

### Jackery Automatic Transfer Switch — Se vende por separado

<div class="hb-package-panel hb-package-panel--optional"><ul class="hb-package-grid hb-package-grid--five"><li class="hb-package-item"><div class="hb-package-art hb-package-art--ats"><img alt="" src="assets/package_ats.png"/></div><p>Jackery Automatic Transfer Switch</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--template"><img alt="" src="assets/package_template.png"/></div><p>Plantilla de Marcado</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--power_cable"><img alt="" src="assets/package_power_cable.png"/></div><p>Cable de entrada/salida de alimentación</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--neutral_wire"><img alt="" src="assets/package_neutral_wire.png"/></div><p>Cable neutro</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--gland"><img alt="" src="assets/package_gland.png"/></div><p>Prensaestopa</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--jumper"><img alt="" src="assets/package_jumper.png"/></div><p>Puente de conexión neutro-tierra (con tornillos)</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manual del usuario</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Manual de instalación</p></li><li class="hb-package-item"><div class="hb-package-art hb-package-art--document"><img alt="" src="assets/87ac44e52863_manual_icon1.png"/></div><p>Guía de inicio rápido</p></li><li class="hb-package-availability"><div class="hb-package-sold">Se vende por separado</div></li></ul></div>

<span id="contact"></span>

# CONTACTO

<p>JACKERY INC.</p>

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>1-888-502-2236 (US)</p>

<p>hello@jackery.com</p>

<p>www.jackery.com</p>
