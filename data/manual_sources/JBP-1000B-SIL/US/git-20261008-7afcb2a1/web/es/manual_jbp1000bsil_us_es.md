<style>
/* Shared Manual IR owns typography and components. Native geometry only. */
.hb-reference-figure { max-width: 720px; margin: 1rem auto; }
.native-step-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 1rem; margin: 1rem 0; }
.native-step-card { border: 1px solid var(--hb-border-color,#dedede); border-radius: 12px; padding: 1rem; min-width: 0; }
.native-step-card p { margin: 0 0 .75rem; }
.native-step-card .hb-reference-figure { margin: 0; }
.native-step-card .hb-reference-live-label { font-size: max(10px, 2.8cqw) !important; }
[data-reference-id="wood-prep"] .hb-reference-art-panel::before,
[data-reference-id="concrete-prep"] .hb-reference-art-panel::before { content: ""; position:absolute; border:1px dashed #858585; border-radius:12px; left:31%; top:10%; width:47%; height:82%; }
[data-reference-id="wood-prep"] .hb-reference-live-label,
[data-reference-id="concrete-prep"] .hb-reference-live-label { font-weight:700; }
[data-reference-id="overview"] .hb-reference-live-label { font-size:max(10px,2.2cqw) !important; }
[data-reference-id="power"] .hb-reference-live-label:nth-of-type(odd) { font-weight:700; }
.hb-inbox-card-art { max-height:180px; object-fit:contain; }
@media(max-width:760px) {
 .native-step-grid { grid-template-columns: minmax(0,1fr); }
}

.native-step-card:has(img[src*="-result"]) .hb-reference-figure { max-width:120px; margin-inline:auto; }
[data-reference-id="wood-prep"] .hb-reference-art-panel::before { top:23%; height:69%; }
[data-reference-id="concrete-prep"] .hb-reference-art-panel::before { left:28%; top:23%; width:49%; height:69%; }
.native-step-card [data-reference-id="wood-prep"] .hb-reference-live-label,
.native-step-card [data-reference-id="concrete-prep"] .hb-reference-live-label { font-size:9px !important; }
[data-reference-id="overview"] [data-source-line="1"] { font-size:max(8px,1.65cqw) !important; }
[data-reference-id="overview"] [data-source-line="0"],
[data-reference-id="overview"] [data-source-line="2"],
[data-reference-id="overview"] [data-source-line="3"] { font-weight:700; }

@media(max-width:760px) { .hb-reference-figure:not([data-reference-id="lcd"]) .hb-reference-live-label { font-size:10px; } }

[data-reference-id="overview"] [data-source-line="2"] { font-size:max(8px,1.65cqw) !important; font-weight:400; }
[data-reference-id="overview"] [data-source-line="4"] { font-weight:700; }

.native-inline-pack { display:inline-block; width:11px; height:15px; vertical-align:middle; margin:0 3px; }

/* Native FCC geometry: compact mark above the left copy; shared panel/breakpoints. */
#furo-main-content .hb-fcc-opening { display:block; }
#furo-main-content .hb-fcc-mark { width:2.6rem !important; margin:0 0 .4rem !important; }

/* Native LCD glyphs need a larger cell footprint, including stacked readouts. */
#furo-main-content .hb-lcd-col-icon { width:14%; }
#furo-main-content .hb-lcd-col-name { width:26%; }
#furo-main-content .hb-lcd-col-description { width:54%; }
#furo-main-content table.hb-lcd-icon-table td.hb-lcd-icon { padding-inline:.35rem !important; }
#furo-main-content .hb-lcd-icon-art { width:4.5rem !important; height:auto !important; }

/* CSS owns the native power panel and its inset live Note, never the base art. */
.native-power-panel { position:relative; border:2px solid var(--hb-line-soft); border-radius:var(--hb-panel-radius); padding:.6rem; margin:.6rem 0 1.35rem; }
.native-power-panel .hb-reference-figure { max-width:none; margin:0; }
#furo-main-content .native-power-panel table.manual-callout-table { position:absolute; right:3%; bottom:5%; width:60% !important; margin:0 !important; font-size:.85rem; line-height:1.3; }
#furo-main-content .native-power-panel .manual-callout-label { width:18% !important; padding:.7rem .5rem !important; background:var(--hb-surface) !important; }
#furo-main-content .native-power-panel .manual-callout-body { padding:.7rem !important; background:var(--hb-paper) !important; }
#furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="0"],
#furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="2"] { font-size:max(10px,3.2cqw) !important; }
@media(max-width:760px) {
 #furo-main-content .native-power-panel table.manual-callout-table { position:static; width:100% !important; margin:.4rem 0 0 !important; }
}

@media(max-width:760px) {
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label { font-size:.88rem !important; }
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="0"],
 #furo-main-content [data-reference-id="power"] .hb-reference-live-label[data-source-line="2"] { font-size:1rem !important; margin-top:.7rem; }
}

/* Native portrait and the shared state table fill the same desktop row. */
.hb-lcd-mode-composition.hb-lcd-mode-portrait { grid-template-columns:minmax(0,1.4fr) minmax(0,3fr); align-items:stretch; }
.hb-lcd-mode-portrait .hb-lcd-mode-art-panel { position:relative; aspect-ratio:246/477; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-art { position:absolute; left:0; top:0; width:auto !important; height:100% !important; max-width:none; max-height:none; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-state { font-weight:400; }
#furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-action { font-weight:600; }
@media(max-width:760px) {
 .hb-lcd-mode-composition.hb-lcd-mode-portrait { grid-template-columns:minmax(0,1fr); }
 .hb-lcd-mode-portrait .hb-lcd-mode-art-panel { aspect-ratio:auto; }
 #furo-main-content .hb-lcd-mode-portrait .hb-lcd-mode-art { position:static; width:9rem !important; height:auto !important; max-width:100%; }
}

/* Native vertical-stand opening: plain heading, live inset caption, unframed result. */
#furo-main-content :is(#vertical-stand,#support-vertical,#soporte-vertical,#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 { background:transparent; color:var(--hb-brand-dark); border:0; border-radius:0; padding:0; font-size:1.15rem; line-height:1.3; margin-bottom:.35rem; }
.native-vertical-opening { display:grid; grid-template-columns:minmax(0,2.7fr) minmax(0,1fr); gap:2.6rem; align-items:end; margin-bottom:1rem; }
.native-vertical-preparation { min-width:0; }
#furo-main-content .native-vertical-preparation > p { margin:0 0 .35rem; }
.native-vertical-opening .hb-reference-figure { margin:0; max-width:none; }
.native-vertical-result .hb-reference-figure { position:static; }
.native-vertical-result { position:relative; align-self:stretch; margin-top:-2.2rem; }
#furo-main-content .native-vertical-result img { position:absolute; right:0; top:0; height:100% !important; width:auto !important; max-width:none !important; }
#furo-main-content [data-reference-id="vertical-prep"] .hb-reference-live-label { font-size:.95rem !important; line-height:1.25; }
@media(max-width:760px) {
 .native-vertical-opening { grid-template-columns:minmax(0,1fr); gap:1rem; }
 .native-vertical-result { width:7.5rem; margin:0 auto; }
 #furo-main-content .native-vertical-result img { position:static; width:100% !important; height:auto !important; max-width:100%; }
 #furo-main-content [data-reference-id="vertical-prep"] .hb-reference-live-label { font-size:.85rem !important; }
}

/* Native vertical-stand installation: each step occupies a full-width row. */
#furo-main-content :is(#vertical-stand,#support-vertical,#soporte-vertical) .native-step-grid { grid-template-columns:minmax(0,1fr); }

/* Native wall-mount title and compact introduction/subsection spacing. */
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 .headerlink { color:inherit; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > p { margin:0; line-height:1.5; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section { margin-top:.65rem; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section > h2 { margin:0 0 .65rem; }
#furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section > h2::before { display:none; }

/* Native wooden-wall opening reuses the admitted base art with live inset copy. */
.native-wood-opening .hb-reference-figure { margin:0; max-width:none; }
#furo-main-content .native-wood-preparation .hb-reference-art-panel { background:#f7f7f7; border-radius:var(--hb-panel-radius); overflow:hidden; }
#furo-main-content .native-wood-preparation .hb-reference-art { mix-blend-mode:multiply; }
#furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="0"] { font-size:.9rem !important; font-weight:400; line-height:1.2; }
#furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="1"] { font-size:max(10px,3cqw) !important; }
#furo-main-content .native-wood-result .hb-reference-figure { max-width:none; }
#furo-main-content .native-wood-result img { width:100% !important; height:auto !important; max-width:100% !important; }
@media(min-width:761px) {
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) { display:grid; grid-template-columns:minmax(0,2.05fr) minmax(0,1fr); column-gap:2rem; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > h1 { grid-column:1; grid-row:1; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > p { grid-column:1; grid-row:2; }
 #furo-main-content :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera), .native-wood-opening { display:contents; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera) > h2 { grid-column:1; grid-row:3; margin:.65rem 0; }
 .native-wood-preparation { grid-column:1; grid-row:4; min-width:0; }
 .native-wood-result { grid-column:2; grid-row:1 / span 4; align-self:start; min-width:0; }
 #furo-main-content :is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera) > .native-step-grid { grid-column:1 / -1; grid-row:5; }
 #furo-main-content :is(#jackery-wall-mounted-bracket-sold-separately,#jackery-wall-mounted-bracket-vendus-separement,#jackery-wall-mounted-bracket-se-vende-por-separado) > section:not(:is(#on-wooden-walls,#sur-les-murs-en-bois,#en-paredes-de-madera)) { grid-column:1 / -1; }
}
@media(max-width:760px) {
 .native-wood-opening { display:grid; grid-template-columns:minmax(0,1fr); gap:1rem; }
 .native-wood-result { width:8.5rem; margin-inline:auto; }
 #furo-main-content [data-reference-id="wood-prep"] .hb-reference-live-label[data-source-line="0"] { font-size:.85rem !important; }
}

</style>

<h1 class="hb-preface-heading" id="preface"><span class="hb-preface-region">ES</span> <span>IMPORTANTE</span></h1>

<div class="hb-preface-prose"><p>Felicitaciones por su nuevo Jackery Battery Pack. Antes de utilizar el producto, lea cuidadosamente este manual, especialmente las precauciones relevantes para asegurar un uso adecuado. Mantenga este manual en un lugar accesible para futuras consultas.</p><p>De acuerdo con las leyes y regulaciones, el derecho de interpretación final de este documento y todos los documentos relacionados con este producto corresponde a la Empresa. Aunque se ha hecho todo lo posible para garantizar la exactitud de este manual, Jackery Inc. no asume ninguna responsabilidad por los errores que puedan aparecer.</p><p>Tenga en cuenta que no se emitirán notificaciones adicionales en caso de actualizaciones, revisiones o terminación. Para obtener la última versión de los manuales del producto, visite support.jackery.com.</p><p>* Las cifras son sólo de referencia. Consulte el producto real.</p></div>

<span id="safety"></span>

# INFORMACIÓN IMPORTANTE DE SEGURIDAD

<p>Se deben seguir las precauciones básicas de seguridad al utilizar este producto, incluyendo:</p>

<ul><li>Leer todas las instrucciones antes de utilizar este producto.</li><li>Se requiere una atenta supervisión cuando se utiliza este producto cerca de los niños para reducir el riesgo.</li><li>Puede haber riesgo de descarga eléctrica si se utilizan accesorios no recomendados o vendidos por fabricantes de productos no profesionales.</li><li>Cuando el producto no esté en uso, desconecte el enchufe del producto.</li><li>No desmonte el producto, ya que puede provocar riesgos imprevisibles como incendios, explosiones o descargas eléctricas.</li><li>No utilice el producto con cables o enchufes dañados, o con cables de salida dañados, ya que pueden provocar una descarga eléctrica.</li><li>Cargue el producto en un área bien ventilada y no restrinja la ventilación de ninguna manera.</li><li>Por favor, coloque el producto en un lugar ventilado y seco para evitar que la lluvia y el agua provoquen una descarga eléctrica.</li><li>No exponga el producto al fuego o a altas temperaturas (bajo la luz directa del sol o en un vehículo con mucho calor), ya que puede provocar accidentes como incendios y explosiones.</li><li>Si este producto se almacena durante un largo periodo de tiempo (3 a 6 meses) con la batería descargada, podría volverse imposible de recargar.</li></ul>

<span id="symbols"></span>

# SIGNIFICADO DE LOS SÍMBOLOS

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Símbolo</th><th class="hb-symbol-signal-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ADVERTENCIA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ADVERTENCIA</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en lesiones graves, muerte y/o daños a la propiedad.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="PRECAUCIÓN" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">PRECAUCIÓN</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en lesiones personales y/o daños a la propiedad.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">NOTA</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en daño al equipo, pérdida de datos, deterioro del rendimiento o resultados inesperados.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEJOS" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CONSEJOS</span></span></td><td class="hb-symbol-signal-meaning-cell">Complementa la información importante o consejos de operación en el texto.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones." class="hb-symbol-art" src="assets/symbol-1.svg"/></td><td class="hb-symbol-meaning">Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lea el manual del operador" class="hb-symbol-art" src="assets/symbol-2.svg"/></td><td class="hb-symbol-meaning">Lea el manual del operador</td></tr><tr><td class="hb-symbol-icon"><img alt="No desarme el producto." class="hb-symbol-art" src="assets/symbol-3.svg"/></td><td class="hb-symbol-meaning">No desarme el producto.</td></tr><tr><td class="hb-symbol-icon"><img alt="No fumar ni hacer llamas abiertas" class="hb-symbol-art" src="assets/symbol-4.svg"/></td><td class="hb-symbol-meaning">No fumar ni hacer llamas abiertas</td></tr><tr><td class="hb-symbol-icon"><img alt="No se permiten niños" class="hb-symbol-art" src="assets/symbol-5.svg"/></td><td class="hb-symbol-meaning">No se permiten niños</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada." class="hb-symbol-art" src="assets/symbol-6.svg"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada.</td></tr><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje. El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto." class="hb-symbol-art" src="assets/symbol-7.png"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje. El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">Este dispositivo cumple con la parte 15 de la normativa FCC. Su operación está sujeta a las siguientes dos condiciones:</div><div class="line">(1) este dispositivo no debe causar interferencias dañinas, y</div><div class="line">(2) este dispositivo debe aceptar cualquier interferencia recibida, incluyendo interferencias que puedan causar un funcionamiento no deseado.</div></div></div></div><p><strong>NOTA:</strong> Este aparato ha sido probado y cumple con los límites para un dispositivo digital de Clase B, de acuerdo con el Apartado 15 de las Reglas de la FCC. Estos límites están diseñados para proporcionar una protección razonable contra interferencias perjudiciales en una instalación residencial. Este aparato genera, usa y puede irradiar energía de radiofrecuencia y, si no se instala y utiliza de acuerdo con las instrucciones, puede causar interferencias perjudiciales en las comunicaciones por radio.</p></div><div class="hb-fcc-column hb-fcc-column-right"><p>Sin embargo, no hay garantía de que no se produzcan interferencias en una instalación concreta. Si este aparato causa interferencias dañinas en la recepción de radio o televisión, lo cual puede determinarse encendiendo y apagando el equipo, se recomienda al usuario que intente corregir la interferencia mediante una o varias de las siguientes medidas:</p><ul class="simple"><li><p>Reorientar o reubicar la antena receptora.</p></li><li><p>Aumentar la separación entre el equipo y el receptor.</p></li><li><p>Conecte el aparato a una toma de corriente en un circuito diferente al que está conectado el receptor.</p></li><li><p>Consulte con el distribuidor o con un técnico de radio o TV experimentado para recibir ayuda.</p></li></ul><p><strong>MODIFICACIÓN:</strong> Cualquier cambio o modificación no aprobado expresamente por el cesionario de este dispositivo podría anular la autoridad del usuario para utilizar el dispositivo.</p></div></div></figure>

<span id="inbox"></span>

# CONTENIDO DE LA CAJA

<figure aria-label="What's in the box" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Battery Pack" class="hb-inbox-art" src="assets/inbox-1.png"/><div class="hb-inbox-label"><p>Jackery Battery Pack</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Cable de expansión" class="hb-inbox-art" src="assets/inbox-2.png"/><div class="hb-inbox-label"><p>Cable de expansión</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Documentos" class="hb-inbox-art" src="assets/inbox-3.png"/><div class="hb-inbox-label"><p>Documentos</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Soporte Vertical" class="hb-inbox-art" src="assets/inbox-4.png"/><div class="hb-inbox-label"><p>Soporte Vertical</p></div></li></ol></figure>

<span id="overview"></span>

# DESCRIPCIÓN GENERAL DEL PRODUCTO

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview" data-source-fragment-sha256="59c7d420b244dd8f8744e9165289687e628294511ef50ff74c45be3e17753b98" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:63%;--hb-y:2%;--hb-width:34%;--hb-height:5%">Puerto de expansión</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62%;--hb-y:7%;--hb-width:36%;--hb-height:3%">Entrada:40V-57,6V⎓24A Máx</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62%;--hb-y:10%;--hb-width:36%;--hb-height:3%">Salida:40V-57,6V⎓50A Máx</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62%;--hb-y:34%;--hb-width:36%;--hb-height:5%">Botón de encendido principal</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:65%;--hb-y:49%;--hb-width:33%;--hb-height:5%">Pantalla LCD</span></div></div></figure>

<span id="lcd"></span>

# PANTALLA LCD

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd" data-source-fragment-sha256="03e21106852d242795966b24aa9810919ea195cada895b83a1562d154766433f" data-web-base-art-ref="lcd" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:8.7534%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:22.8417%;--hb-y:4.22%;--hb-width:2.1667%;--hb-height:5.3299%">2</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:39.3679%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:39.4125%;--hb-y:94.2347%;--hb-width:2.0889%;--hb-height:5.3299%">7</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:10.8057%;--hb-y:95.0695%;--hb-width:2.2%;--hb-height:5.3299%">5</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:3.1402%;--hb-y:95.0695%;--hb-width:2.2889%;--hb-height:5.3299%">4</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:24.0513%;--hb-y:95.0695%;--hb-width:2.1778%;--hb-height:5.3299%">6</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:58.7708%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:89.3849%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span></div></div></figure>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Potencia de Entrada / Tiempo de Carga Restante" class="hb-lcd-icon-art" src="assets/lcd-icon-1.svg"/></td><td class="hb-lcd-name">Potencia de Entrada / Tiempo de Carga Restante</td><td class="hb-lcd-description">Muestra alternativamente la potencia de entrada y el tiempo de carga restante.</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Porcentaje de Batería Restante" class="hb-lcd-icon-art" src="assets/lcd-icon-2.svg"/></td><td class="hb-lcd-name">Porcentaje de Batería Restante</td><td class="hb-lcd-description">Muestra el porcentaje de batería restante.</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="Potencia de Salida / Tiempo de Descarga Restante" class="hb-lcd-icon-art" src="assets/lcd-icon-3.svg"/></td><td class="hb-lcd-name">Potencia de Salida / Tiempo de Descarga Restante</td><td class="hb-lcd-description">Muestra alternativamente la potencia de salida y el tiempo de descarga restante.</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="Indicador de carga" class="hb-lcd-icon-art" src="assets/lcd-icon-4.svg"/></td><td class="hb-lcd-name">Indicador de carga</td><td class="hb-lcd-description"><strong>Encendido :</strong> el Jackery Battery Pack está en estado de carga. <strong>Apagado :</strong> el Jackery Battery Pack no está en estado de carga.</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="Indicador de Potencia de la Batería" class="hb-lcd-icon-art" src="assets/lcd-icon-5.svg"/></td><td class="hb-lcd-name">Indicador de Potencia de la Batería</td><td class="hb-lcd-description">El círculo naranja indica el nivel de batería restante.</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="Entrada de CC" class="hb-lcd-icon-art" src="assets/lcd-icon-6.svg"/></td><td class="hb-lcd-name">Entrada de CC</td><td class="hb-lcd-description"><strong>Encendido :</strong> El Módulo de Entrada CC de Jackery está conectado. <strong>Apagado :</strong> El Módulo de Entrada CC de Jackery está desconectado.</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="Código de fallo" class="hb-lcd-icon-art" src="assets/lcd-icon-7.svg"/></td><td class="hb-lcd-name">Código de fallo</td><td class="hb-lcd-description">Se ha producido un error en el producto. Por favor, consulte la sección de solución de problemas para más detalles.</td></tr></tbody></table></figure>

<span id="operations"></span>

# OPERACIONES

## ENCENDIDO/APAGADO

<div class="native-power-panel"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="8c9a89327f12aa442ae5001db31f6153b0a4a71961c3cdd9fbd624d2feaf8f8f" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71%;--hb-y:10%;--hb-width:27%;--hb-height:9%">Encendido</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:71%;--hb-y:18%;--hb-width:27%;--hb-height:7%">Presione una vez</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:71%;--hb-y:29%;--hb-width:27%;--hb-height:9%">Apagado</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:71%;--hb-y:36%;--hb-width:27%;--hb-height:7%">Mantén presionado durante 3 segundos</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:77%;--hb-y:46%;--hb-width:12%;--hb-height:8%">3s</span></div></div></figure><table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>El producto se apagará automáticamente si no se carga o no se conectan cargos durante 2 horas.</p></td></tr></tbody></table></div>

## ENCENDER/APAGAR PANTALLA LCD

<figure aria-label="ENCENDER/APAGAR PANTALLA LCD" class="hb-lcd-mode-composition hb-lcd-mode-portrait" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="ENCENDER/APAGAR PANTALLA LCD" class="hb-lcd-mode-art" src="assets/lcd-button.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">En breve</td><td class="hb-lcd-mode-action">Encender</td><td class="hb-lcd-mode-copy">Presione el botón de encendido principal o cuando el producto se esté cargando.</td></tr><tr><td class="hb-lcd-mode-action">Apagar</td><td class="hb-lcd-mode-copy">Presione el botón de encendido principal.</td></tr><tr><td class="hb-lcd-mode-action">Apagado automático</td><td class="hb-lcd-mode-copy">La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Estable en (durante el estado de carga o descarga)</td><td class="hb-lcd-mode-action">Encender</td><td class="hb-lcd-mode-copy">Presione dos veces el botón de encendido principal cuando el producto está encendido.</td></tr><tr><td class="hb-lcd-mode-action">Apagar</td><td class="hb-lcd-mode-copy">Presione el botón de energía principal.</td></tr><tr><td class="hb-lcd-mode-action">Apagado automático</td><td class="hb-lcd-mode-copy">El modo de estable se apaga automáticamente después de 2 horas de inactividad.</td></tr></tbody></table></div></figure>

<span id="troubleshooting"></span>

# RESOLUCIÓN DE PROBLEMAS

<p>Si aparece alguno de los siguientes códigos de falla, siga las acciones correctivas listadas para resolver el problema.Si la falla persiste, por favor contacte con atención al cliente de Jackery.</p>

<figure aria-label="Código de error / Medidas correctivas" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Código de error</th><th class="hb-troubleshooting-measures" scope="col">Medidas correctivas</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0 / F2 / F3</td><td class="hb-troubleshooting-measures">Reiniciar el producto.</td></tr><tr><td class="hb-troubleshooting-code">F1 / F6 / F7 / F8</td><td class="hb-troubleshooting-measures">Contacte con atención al cliente de Jackery.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Conecte el producto a cargas para descargar su batería hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Cargue el producto mediante paneles solares o toma de corriente CA hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures"><p><strong>En condiciones de alta temperatura:</strong></p><ol><li>Desconecte todos los cables de carga y descarga del producto (incluyendo cargador de pared, paneles solares, cargador de coche y dispositivos de carga).</li><li>Coloque el producto en un área sombreada y bien ventilada donde la temperatura ambiente sea inferior a 113°F (45 °C).</li><li>Mantenga el producto en reposo y espere a que la falla desaparezca.</li><li>Si la falla persiste después de varios intentos, contacte al distribuidor o al Servicio de Atención al Cliente de Jackery.</li></ol><p><strong>En condiciones de baja temperatura:</strong></p><ol><li>Traslade el producto a un ambiente más cálido por encima de 32°F (0 °C).</li><li>No utilice ni cargue el producto al aire libre en condiciones extremadamente frías. Si es necesario, précaliéntelo en interiores.</li><li>Si el dispositivo se traslada al interior desde un ambiente frío, déjelo reposar un tiempo antes de usarlo.</li><li>Cuando aparezca el indicador de Baja Temperatura, mantenga el producto en reposo y espere a que el sistema se recupere automáticamente.</li><li>Si la falla persiste después de varios intentos, contacte al distribuidor o al Servicio de Atención al Cliente de Jackery.</li></ol></td></tr></tbody></table></figure>

<span id="positioning"></span>

# COLOCACIÓN CON EL JACKERY FRIDGEGUARD

## DISPOSICIÓN EN PARALELO

<p>Coloca el paquete de baterías Jackery FridgeGuard y el Jackery FridgeGuard en una disposición en paralelo.</p>

<div class="hb-reference-figure"><img alt="parallel" class="hb-reference-art" src="assets/parallel.png"/></div>

## APILADOS

<p>Coloca el paquete de baterías Jackery FridgeGuard y el Jackery FridgeGuard apilados uno sobre otro.</p>

<div class="hb-reference-figure"><img alt="stacked" class="hb-reference-art" src="assets/stacked.png"/></div>

## CON SOPORTES

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><ul><li>No instale el producto en estructuras no portantes, como placas de yeso, muros aislantes o ladrillos huecos, ya que podría caerse.</li><li>Evite los cables eléctricos, tuberías de agua, tuberías de gas y otras instalaciones dentro de las paredes.</li></ul></td></tr></tbody></table>

<span id="vertical"></span>

# SOPORTE VERTICAL

<div class="native-vertical-opening"><div class="native-vertical-preparation"><p>El Jackery Battery Pack instalado con el soporte vertical se puede colocar en el suelo. Siga los pasos de instalación a continuación:</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="vertical-prep" data-source-fragment-sha256="40cde0db33ca2d5a799bcfcd09b0eca736b960b1cb1102dafb1d2dfd2a9c7437" data-web-base-art-ref="vertical-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="vertical-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#f7f7f7"><img alt="" class="hb-reference-art hb-reference-art hb-composite-art" src="assets/vertical-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:4%;--hb-y:3%;--hb-width:92%;--hb-height:14%">Preparación antes de la instalación:</span></div></div></figure></div><div class="native-vertical-result"><div class="hb-reference-figure"><img alt="Vertical stand installation result" class="hb-reference-art" src="assets/vertical-result.png"/></div></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Remove two screws from the bottom of the product.</p><div class="hb-reference-figure"><img alt="vertical-1" class="hb-reference-art" src="assets/vertical-1.png"/></div></div><div class="native-step-card"><p>2. Alinee los orificios de montaje en la parte inferior del producto con los orificios en el soporte vertical.</p><div class="hb-reference-figure"><img alt="vertical-2" class="hb-reference-art" src="assets/vertical-2.png"/></div></div><div class="native-step-card"><p>3. Apriete los tornillos.</p><div class="hb-reference-figure"><img alt="vertical-3" class="hb-reference-art" src="assets/vertical-3.png"/></div></div></div>

<span id="wall-mount"></span>

# JACKERY WALL-MOUNTED BRACKET (SE VENDE POR SEPARADO)

<p>El Jackery Battery Pack instalado con el soporte de montaje se puede colocar en la pared. Siga los pasos de instalación a continuación:</p>

## EN PAREDES DE MADERA

<div class="native-wood-opening"><div class="native-wood-preparation"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-prep" data-source-fragment-sha256="c84865c0e16ec2767e8bf0bb44e629ca104cacf161d0fcc71e421a95ada41cbb" data-web-base-art-ref="wood-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:5%;--hb-y:3%;--hb-width:68%;--hb-height:13%">Preparación antes de la instalación:</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:57%;--hb-y:24%;--hb-width:21%;--hb-height:18%">SE VENDE POR SEPARADO</span></div></div></figure></div><div class="native-wood-result"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-result" data-source-fragment-sha256="7dee94a85283863c17dcb4100a220778599b1d71c99fff5d163026c2ed00b33f" data-web-base-art-ref="wood-result" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-result.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-result.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:10%;--hb-y:0%;--hb-width:80%;--hb-height:10%">Estructura de madera</span></div></div></figure></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Instala el Jackery FridgeGuard de acuerdo con el manual del usuario. 2. Retire los dos tornillos de la parte inferior del producto.</p><div class="hb-reference-figure"><img alt="wood-1-2" class="hb-reference-art" src="assets/wood-1-2.png"/></div></div><div class="native-step-card"><p>3. Fije firmemente los soportes de montaje superior e inferior en la parte posterior del producto.</p><div class="hb-reference-figure"><img alt="wood-3" class="hb-reference-art" src="assets/wood-3.png"/></div></div><div class="native-step-card"><p>4. Utilice un buscador de montantes para identificar los montantes de madera detrás de la pared.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-4" data-source-fragment-sha256="70c83f32f5139c05004f2dba0482542c929a42591235148c283e44a78c2451d9" data-web-base-art-ref="wood-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65%;--hb-y:32%;--hb-width:32%;--hb-height:11%">Estructura de madera</span></div></div></figure></div><div class="native-step-card"><p>5. Mide una distancia horizontal de 406 mm (16 in) desde la posición del perno en el Jackery FridgeGuard y marca el punto de montaje en el montante de madera de la pared.</p><p>* 406 mm (16 in) es la distancia recomendada. La distancia real depende de las condiciones de la pared.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-5" data-source-fragment-sha256="0b30b5c66d0e668f09fbee45b757599b7125311ac30378fd6b6bc834187abe72" data-web-base-art-ref="wood-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:33.5914%;--hb-y:21.1809%;--hb-width:16.2108%;--hb-height:7.557%">Estructura de madera</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:58.5429%;--hb-y:20.5752%;--hb-width:16.2108%;--hb-height:7.557%">Estructura de madera</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:44.8879%;--hb-y:40.1803%;--hb-width:19.0607%;--hb-height:7.557%">406 mm (16 in)</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:4.6084%;--hb-y:67.2917%;--hb-width:25.3171%;--hb-height:7.557%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>6. Atornille el tornillo para madera en la pared en el punto de montaje, dejando un espacio de 2-4mm entre el tornillo y la pared.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-6" data-source-fragment-sha256="70647904b18f86a9869ebe490b0b473ca340cc9d0d79f2bdd6328b356e3e9ee3" data-web-base-art-ref="wood-6" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-6.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-6.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:66.3707%;--hb-y:31.4483%;--hb-width:13.4462%;--hb-height:9.2069%">2~4mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:44.5016%;--hb-y:21.3514%;--hb-width:16.2108%;--hb-height:9.2069%">Estructura de madera</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:1.9525%;--hb-y:39.2574%;--hb-width:22.2641%;--hb-height:8.1724%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>7. Cuelgue el producto verticalmente sobre el tornillo. Atornille el tornillo autorroscante a través del orificio de montaje en el soporte inferior hacia la pared y apriételo. Luego, apriete completamente el tornillo para madera.</p><div class="hb-reference-figure"><img alt="wood-7" class="hb-reference-art" src="assets/wood-7.png"/></div></div></div>

## EN PAREDES DE CONCRETO

<p>Preparación antes de la instalación:</p>

<div class="native-step-grid"><div class="native-step-card"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-prep" data-source-fragment-sha256="200de0359b67f09315424b70e56d7443f276d29275aa17da0d89fc00c63ac623" data-web-base-art-ref="concrete-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:54%;--hb-y:27%;--hb-width:25%;--hb-height:18%">SE VENDE POR SEPARADO</span></div></div></figure></div><div class="native-step-card"><div class="hb-reference-figure"><img alt="concrete-result" class="hb-reference-art" src="assets/concrete-result.png"/></div></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Instala el Jackery FridgeGuard de acuerdo con el manual del usuario. 2. Retire los dos tornillos de la parte inferior del producto.</p><div class="hb-reference-figure"><img alt="concrete-1-2" class="hb-reference-art" src="assets/concrete-1-2.png"/></div></div><div class="native-step-card"><p>3. Fije firmemente los soportes de montaje superior e inferior en la parte posterior del producto.</p><div class="hb-reference-figure"><img alt="concrete-3" class="hb-reference-art" src="assets/concrete-3.png"/></div></div><div class="native-step-card"><p>4. Mide una distancia horizontal de 406 mm (16 in) desde la posición del perno en el Jackery FridgeGuard y marca el punto de montaje en el montante de madera de la pared.</p><p>* 406 mm (16 in) es la distancia recomendada. La distancia real depende de las condiciones de la pared.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-4" data-source-fragment-sha256="f9356f888d233301588fe9f250d1a94c8db922094523551e30351c802c54765b" data-web-base-art-ref="concrete-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:24%;--hb-y:30%;--hb-width:31%;--hb-height:7%">406 mm (16 in)</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:41%;--hb-y:78%;--hb-width:55%;--hb-height:7%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>5. Perfore un agujero en el punto de montaje utilizando un taladro de impacto para mampostería de 8mm hasta una profundidad de aproximadamente 70mm. Inserta un perno de expansión y afloja su tuerca de 2 a 4 mm.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-5" data-source-fragment-sha256="c0c60625d2ef6a1ea7b4fa5a4a61d36e0fd0ab71e593053c9907f6fc16b1bf98" data-web-base-art-ref="concrete-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:52%;--hb-y:41%;--hb-width:21%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:45%;--hb-y:73%;--hb-width:24%;--hb-height:7%">2~4mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:72%;--hb-y:52%;--hb-width:23%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-step-card"><p>6. Cuelga el producto verticalmente en el perno de expansión y marca el punto de montaje en la pared.</p><div class="hb-reference-figure"><img alt="concrete-6" class="hb-reference-art" src="assets/concrete-6.png"/></div></div><div class="native-step-card"><p>7. Retira el producto. Perfora un orificio en el punto de montaje e inserta un perno de expansión sin la tuerca y la arandela en el agujero.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-7" data-source-fragment-sha256="e9b8f2a12516dd6c38815f9d180d037acc45d3b1908a69418abd6f0103020a04" data-web-base-art-ref="concrete-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:61%;--hb-y:39%;--hb-width:24%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75%;--hb-y:50%;--hb-width:20%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-step-card"><p>8. Cuelga el producto en el perno de expansión superior.</p><div class="hb-reference-figure"><img alt="concrete-8" class="hb-reference-art" src="assets/concrete-8.png"/></div></div><div class="native-step-card"><p>9. Levanta el producto para alinear el perno preinstalado y bájalo hasta su posición. Aprieta la tuerca.</p><div class="hb-reference-figure"><img alt="concrete-9" class="hb-reference-art" src="assets/concrete-9.png"/></div></div></div>

<span id="connections"></span>

# CONEXIONES

<p>El Paquete de Baterías Jackery FridgeGuard puede usarse junto con el Jackery FridgeGuard para satisfacer las necesidades de mayor capacidad.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Asegúrese de que todos los productos estén apagados antes de conectar el Jackery FridgeGuard al paquete de Jackery Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="connections" class="hb-reference-art" src="assets/connections.png"/></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Observaciones</td><td class="manual-callout-body"><p>La aparición del icono <img alt="" class="native-inline-pack" src="assets/connection-icon.svg"/> en la pantalla LCD (Jackery FridgeGuard) indica que la conexión entre la batería y el Jackery FridgeGuard se ha realizado correctamente.</p></td></tr></tbody></table>

<span id="charging"></span>

# CARGANDO

## CARGA MEDIANTE UNA TOMA DE CORRIENTE DE PARED ALTERNA

<p>Cuando se carga desde la red, este producto debe utilizarse con Jackery FridgeGuard.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Advertencia</td><td class="manual-callout-body"><p>Asegúrese de que todos los productos estén apagados antes de conectar el Jackery FridgeGuard al paquete de Jackery Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="ac" class="hb-reference-art" src="assets/ac.png"/></div>

## CARGA MEDIANTE PANELES SOLARES (SE VENDE POR SEPARADO)

<p>Cargue su producto con paneles solares y el Jackery DC Input Module(SE VENDE POR SEPARADO) como se muestra en la siguiente figura. Consulte el manual de usuario de Jackery DC Input Module para obtener más información.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar" data-source-fragment-sha256="f22437451b71c691729af99ef4443af2145b0d02b6d23ae7128a0012024e57d7" data-web-base-art-ref="solar" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:23.2139%;--hb-y:51.0353%;--hb-width:14.2673%;--hb-height:5.1953%">SolarSaga 500 X</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:57.8558%;--hb-y:76.2323%;--hb-width:8.3319%;--hb-height:5.1953%">DC8020</span></div></div></figure>

## CARGA CON UN CARGADOR DE EN EL VEHÍCULO(SE VENDE POR SEPARADO)

<p>Carga tu producto con el cargador de coche y el módulo de entrada de CC Jackery(SE VENDE POR SEPARADO) como se muestra en la figura a continuación. Consulta el manual del usuario del módulo de entrada de CC Jackery para obtener más información.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="59512e005378bb2d04b9a472fd444dc1072e760633103eab6d5e33d9f8fd1f15" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65%;--hb-y:14%;--hb-width:25%;--hb-height:9%">Vehículo</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:30%;--hb-y:63%;--hb-width:20%;--hb-height:9%">DC8020</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="2" style="--hb-x:53%;--hb-y:65%;--hb-width:43%;--hb-height:18%;--hb-fill:#f2f2f2">※ El cable de carga para auto se vende por separado.</span></div></div></figure>

<span id="storage"></span>

# ALMACENAMIENTO

<p>Almacene el producto en un lugar seco y limpio con ventilación adecuada.Temperatura y humedad de almacenamiento:</p>

<ul><li>1 mes: -4°F a 113°F / -20 a 45 °C (0-60 % HR)</li><li>3 meses: 32°F a 113°F / 0 a 45 °C (0-60 % HR)</li><li>12 meses: 32°F a 77°F / 0 a 25 °C (0-60 % HR)</li></ul>

<p>Si este producto se almacena durante un período prolongado (de 3 a 6 meses) con la batería descargada, podría volverse imposible recargarlo. Para evitar esto y mantener la salud de la batería, se recomienda revisar y recargar el producto cada tres meses, y realizar un ciclo completo de carga y descarga al menos una vez cada 6 a 12 meses.</p>

<span id="specifications"></span>

# ESPECIFICACIONES

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Nº de modelo</th><td class="manual-spec-value hb-spec-value">JBP-1000B-SIL</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">20Ah / 51,2Vdc (1024 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química Celular</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 19,8 libras/9 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">23,6 × 12,8 × 2,4 pulgadas/60 × 32,5 × 6 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">6000 ciclos de carga hasta 70 % + de capacidad</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE ENTRADA/SALIDA</h2>

<figure aria-label="PUERTOS DE ENTRADA/SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">40V-57,6V⎓24A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">40V-57,6V⎓50A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente máxima de cortocircuito y duración</th><td class="manual-spec-value hb-spec-value">1250A/1.55ms</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPERATURA DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">-4°F a 113°F / -20°C a 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-4°F a 113°F / -20°C a 45°C</td></tr></tbody></table></figure>

<span id="warranty"></span>

# GARANTÍA

<figure aria-label="Warranty" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel">Solo ofrecemos nuestra garantía a clientes que compren en el sitio web oficial de Jackery, plataformas de terceros con la marca Jackery o distribuidores autorizados locales.</div><div class="hb-warranty-local-note">* El periodo de garantía y los detalles pueden variar según las leyes, regulaciones y distribuidores autorizados locales.</div></figure>

## GARANTÍA LIMITADA

<figure aria-label="GARANTÍA LIMITADA" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantiza al consumidor original que el producto Jackery estará libre de defectos relativos al acabado y a los materiales en condiciones normales de uso por parte del consumidor durante el período de garantía aplicable identificado en la sección "Período de garantía" que figura a continuación, sujeto a las exclusiones que se establecen a continuación.</p><p>Esta declaración de garantía establece la obligación de garantía total y exclusiva de Jackery. No asumiremos ni autorizaremos que ninguna persona asuma por nosotros ninguna otra responsabilidad en relación con la venta de nuestros productos.</p></figure>

## PERÍODO DE GARANTÍA

<figure aria-label="PERÍODO DE GARANTÍA" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 AÑOS Garantía estándar" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía estándar</strong></div></div><div class="hb-warranty-period-copy">El periodo de garantía estándar de Jackery Battery Pack es de 36 meses. En cada caso, el período de garantía se mide a partir de la fecha de compra por parte del comprador consumidor original. Para establecer la fecha de inicio del período de garantía, se necesita el recibo de venta de la primera compra del consumidor u otra prueba documental razonable.</div></div><div aria-label="2 AÑOS Garantía extendida" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía extendida</strong></div></div><div class="hb-warranty-period-copy">Para activar la extensión de garantia,debe registrar su producto en línea oponerse en contacto con nuestro equipo de atención al cliente en hello@jackery.com para ampliar laduración de la garantia estándar.</div></div></div></figure>

## REPARACIÓN O REEMPLAZO

<figure aria-label="REPARACIÓN O REEMPLAZO" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery reparará o reemplazará (a cargo de Jackery) cualquier producto Jackery que no funcione durante el periodo de garantía aplicable debido a defectos en la mano de obra o el material. El producto reparado o reemplazado asumirá el periodo restante de la garantía desde la fecha original de compra.</p></figure>

## LIMITADO AL COMPRADOR CONSUMIDOR ORIGINAL

<figure aria-label="LIMITADO AL COMPRADOR CONSUMIDOR ORIGINAL" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantía del producto de Jackery se limita al consumidor original y no es transferible a ningún propietario posterior.</p></figure>

## EXCLUSIONES

<figure aria-label="EXCLUSIONES" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantía de Jackery no se aplica a:</p><ul><li>Mal uso, abuso, modificación, daño por accidente, o uso para cualquier cosa que no sea el uso normal del consumidor según lo autorizado en los folletos actuales del producto de Jackery.</li><li>Intento de reparación por cualquier persona que no sea un centro autorizado.</li><li>Cualquier producto adquirido a través de una casa de subastas en línea.</li><li>La garantía de Jackery no se aplica a la célula de la batería a menos que usted la cargue completamente en los siete días siguientes a la compra del producto y, a partir de entonces, al menos una vez cada 6 meses.</li></ul></figure>

## DERECHOS DE INTERPRETACIÓN

<figure aria-label="DERECHOS DE INTERPRETACIÓN" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>La garantía del producto de Jackery se limita al consumidor original y no es transferible a ningún propietario posterior.</p></figure>

<span id="contact"></span>

# JACKERY INC.

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>hello@jackery.com www.jackery.com 1-888-502-2236 (US)</p>
