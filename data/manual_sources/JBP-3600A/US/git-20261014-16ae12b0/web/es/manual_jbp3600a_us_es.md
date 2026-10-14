<style>
/* JBP-3600A US source geometry only. Shared Web theme owns headings, callouts, tables and figures;
   layout follows the JBP-2000B and JBP-3600A EU Web manuals. */

/* Figures: the print's own art width; no visible caption (the art carries its labels). */
.native-figure { max-width: 680px; margin: 1rem auto; min-width: 0; }
.native-figure .hb-reference-figure { margin: 0; max-width: none; }
#furo-main-content .native-figure img { width: 100% !important; height: auto !important; max-height: none; }

/* p5 FCC measures: printed as indented lines without marks. */
#furo-main-content .native-fcc .hb-fcc-column ul { list-style: none; padding-left: 0.6em; }
#furo-main-content .native-fcc .hb-fcc-column ul > li { margin: 0; }
#furo-main-content .native-fcc .hb-fcc-column ul > li > p { margin: 0; }

/* Two-column tables fit the phone (the print's troubleshooting table has two columns). */
@media (max-width: 760px) {
  #furo-main-content .native-fit-phone table { min-width: 0 !important; }
  #furo-main-content .native-fit-phone col.hb-troubleshooting-col-code { width: 5.4rem !important; }
}

/* p9 SOLD SEPARATELY tag beside its subheading. */
#furo-main-content .native-sold-separately {
  display: inline-block; margin-left: 0.4em; padding: 0.1em 0.55em; border-radius: 0.3em;
  background: var(--hb-text); color: var(--hb-paper); font-size: 0.72em; vertical-align: 0.12em; white-space: nowrap;
}

/* p8 inline LCD connection icon at text size. */
#furo-main-content img.native-inline-control {
  display: inline-block; width: auto !important; height: 1.15em !important;
  margin: 0 0.3em !important; vertical-align: -0.2em;
}

/* Print case for subheadings (the print sets them in bold capitals or title case); shared markers stay. */
#furo-main-content h2:not(.hb-spec-section), #furo-main-content :is(h3, h4) { text-transform: none; }

</style>

<span id="native-safety"></span>

## INFORMACIÓN IMPORTANTE DE SEGURIDAD

<p><strong>Se deben seguir las precauciones básicas de seguridad al utilizar este producto, incluyendo:</strong></p>

<p>Leer todas las instrucciones antes de utilizar este producto.<br/>Se requiere una atenta supervisión cuando se utiliza este producto cerca de los niños para reducir el riesgo.<br/>Puede haber riesgo de descarga eléctrica si se utilizan accesorios no recomendados o vendidos por fabricantes de productos no profesionales.<br/>Cuando el producto no esté en uso, desconecte el enchufe del producto.<br/>No desmonte el producto, ya que puede provocar riesgos imprevisibles como incendios, explosiones o descargas eléctricas.<br/>No utilice el producto con cables o enchufes dañados, o con cables de salida dañados, ya que pueden provocar una descarga eléctrica.<br/>Cargue el producto en un área bien ventilada y no restrinja la ventilación de ninguna manera.<br/>Por favor, coloque el producto en un lugar ventilado y seco para evitar que la lluvia y el agua provoquen una descarga eléctrica.<br/>No exponga el producto al fuego o a altas temperaturas (bajo la luz directa del sol o en un vehículo con mucho calor), ya que puede provocar accidentes como incendios y explosiones.</p>

<span id="native-symbols"></span>

## SIGNIFICADO DE LOS SÍMBOLOS

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Símbolo</th><th class="hb-symbol-signal-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ADVERTENCIA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ADVERTENCIA</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en lesiones graves, muerte y/o daños a la propiedad.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="PRECAUCIÓN" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">PRECAUCIÓN</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en lesiones personales y/o daños a la propiedad.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="NOTA" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">NOTA</span></span></td><td class="hb-symbol-signal-meaning-cell">Prácticas peligrosas que pueden resultar en daño al equipo, pérdida de datos, deterioro del rendimiento o resultados inesperados.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEJOS" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CONSEJOS</span></span></td><td class="hb-symbol-signal-meaning-cell">Complementa la información importante o consejos de operación en el texto.</td></tr></tbody></table></figure>

<figure aria-label="Meaning of symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Precaución! El incumplimiento de los mensajes de advertencia puede provocar lesiones.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lea el manual del operador" class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Lea el manual del operador</td></tr><tr><td class="hb-symbol-icon"><img alt="Riesgo de descarga eléctrica" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Riesgo de descarga eléctrica</td></tr><tr><td class="hb-symbol-icon"><img alt="Carga de batería" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Carga de batería</td></tr><tr><td class="hb-symbol-icon"><img alt="Material explosivo" class="hb-symbol-art" src="assets/symbol_explosive_material_native_v2_3e3a39.svg"/></td><td class="hb-symbol-meaning">Material explosivo</td></tr><tr><td class="hb-symbol-icon"><img alt="Objeto pesado" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Objeto pesado</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Símbolo</th><th class="hb-symbol-meaning-heading" scope="col">Significados</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="No desarme el producto." class="hb-symbol-art" src="assets/screwdriver-prohibited-tw-477dfbd7.svg"/></td><td class="hb-symbol-meaning">No desarme el producto.</td></tr><tr><td class="hb-symbol-icon"><img alt="No fumar ni hacer llamas abiertas" class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">No fumar ni hacer llamas abiertas</td></tr><tr><td class="hb-symbol-icon"><img alt="No se permiten niños" class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">No se permiten niños</td></tr><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada." class="hb-symbol-art" src="assets/symbol_li_ion_htp017.svg"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto contiene una batería de iones de litio (Li-ion), la cual debe desecharse o reciclarse de forma adecuada.</td></tr><tr><td class="hb-symbol-icon"><img alt="Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje. El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">Este símbolo indica que el producto no debe desecharse con los residuos domésticos. En su lugar, debe llevarse a un punto de recogida designado para su correcto reciclaje.<br/>El desecho y reciclaje adecuados ayudan a proteger el medioambiente. Para más información, póngase en contacto con su autoridad local, el servicio de gestión de residuos o el distribuidor del producto.</td></tr></tbody></table></div></div></figure>

<div class="native-fcc"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc_mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"></div></div></div><p><strong>NOTA:</strong> Este aparato ha sido probado y cumple con los límites para un dispositivo digital de Clase B, de acuerdo con el Apartado 15 de las Reglas de la FCC. Estos límites están diseñados para proporcionar una protección razonable contra interferencias perjudiciales en una instalación residencial. Este aparato genera, usa y puede irradiar energía de radiofrecuencia y, si no se instala y utiliza de acuerdo con las instrucciones, puede causar interferencias perjudiciales en las comunicaciones por radio. Sin embargo, no hay garantía de que no se produzcan interferencias en una instalación concreta. Si este aparato causa interferencias dañinas en la recepción de radio o televisión, lo cual puede determinarse encendiendo y apagando el equipo, se recomienda al usuario que intente corregir la interferencia mediante una o varias de las siguientes medidas:</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Reorientar o reubicar la antena receptora.</p></li><li><p>Aumentar la separación entre el equipo y el receptor.</p></li><li><p>Conecte el aparato a una toma de corriente en un circuito diferente al que está conectado el receptor.</p></li><li><p>Consulte con el distribuidor o con un técnico de radio o TV experimentado para recibir ayuda.</p></li></ul><p><strong>MODIFICACIÓN:</strong> Cualquier cambio o modificación no aprobado expresamente por el cesionario de este dispositivo podría anular la autoridad del usuario para utilizar el dispositivo.</p></div></div></figure></div>

<span id="native-in-the-box"></span>

## CONTENIDO DE LA CAJA

<figure aria-label="CONTENIDO DE LA CAJA" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Battery Pack 3600" class="hb-inbox-art" src="assets/es-inbox-unit.png"/><div class="hb-inbox-label"><p>Jackery Battery Pack 3600</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Cable de expansión" class="hb-inbox-art" src="assets/es-inbox-cable.png"/><div class="hb-inbox-label"><p>Cable de expansión</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Manual de usuario" class="hb-inbox-art" src="assets/es-inbox-manual.png"/><div class="hb-inbox-label"><p>Manual de usuario</p></div></li></ol></figure>

<span id="native-product-overview"></span>

## DESCRIPCIÓN GENERAL DEL PRODUCTO

### VISTA FRONTAL

<div class="native-figure native-overview-front native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="3b8a386afe760754d905aeaf227db833f579ca615ea7ea8563a1e4fe907eeb37" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-front.semantic"><img alt="Front view: LCD display and POWER button" class="hb-reference-art hb-composite-art" src="assets/es-overview-front.png"/></div></figure></div>

### VISTA LATERAL IZQUIERDA

<div class="native-figure native-overview-left native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="bfcc1c09df1ca41e5f77386db0c28da3ea8d4833398e80e819d1989aefe1fa5f" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-left.semantic"><img alt="Left side view: handle, DC Expansion Port A (connect to Expansion Cable Terminal A) and DC Expansion Port B (connect to Expansion Cable Terminal B)" class="hb-reference-art hb-composite-art" src="assets/es-overview-left.png"/></div></figure></div>

<span id="native-lcd-display"></span>

## PANTALLA LCD

<div class="native-figure native-lcd-display native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-display" data-source-fragment-sha256="afbd65d1b59ea63a74a80c875eac7c6073098ecea14355586605cec61d9956d4" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="lcd-display.semantic"><img alt="LCD display: power percentage or fault code, and the charging indicator" class="hb-reference-art hb-composite-art" src="assets/es-lcd-display.png"/></div></figure></div>

<figure aria-label="PANTALLA LCD" class="hb-reference-composition hb-reference-lcd-descriptions" data-component-id="HB-TABLE-REFERENCE" data-component-variant="lcd-descriptions" tabindex="0"><table class="hb-reference-table"><tbody><tr><td><strong>Porcentaje de</strong><br/><strong>potencia/Código</strong><br/><strong>de fallo</strong></td><td>La potencia muestra el porcentaje del valor de potencia actual. Cuando el sistema falla, se mostrará el correspondiente código de fallo F0-FF. Si aparece el código FF, retire la carga y el producto podrá recuperarse por sí mismo, si no, por favor contacte con atención al cliente de Jackery.En caso de que aparezca cualquier otro código, por favor contacte con atención al cliente.</td></tr><tr><td><strong>Indicador de carga</strong></td><td>Durante la carga se muestra el indicador y desaparece cuando está completamente cargado.</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## OPERACIONES

### ENCENDIDO/APAGADO

<div class="native-figure native-power-on-off native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-on-off" data-source-fragment-sha256="94ac08852423403f669617e9674b7d1adf0f60bd5d59012850c671571b6ebfe8" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="power-on-off.semantic"><img alt="POWER button: press once to turn on; press and hold for 3 s to turn off" class="hb-reference-art hb-composite-art" src="assets/es-power-on-off.png"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">NOTA</td><td class="manual-callout-body"><p>Cuando se usa con el Jackery HomePower 3600 Plus, se puede controlar el encendido o apagado del Jackery Battery Pack 3600 a través del "Botón de Encendido Principal" del Jackery HomePower 3600 Plus.<br/>El producto se apagará automáticamente si no se carga o no se conectan cargos durante 2 horas.</p></td></tr></tbody></table>

### ENCENDIDO/APAGADO DE LA PANTALLA LCD

<div class="native-figure native-lcd-on-off native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-on-off" data-source-fragment-sha256="4f07316fdbc9b269e3bb8ece6af3191e88e91b49d5d22c006339be020740bdca"><div class="hb-reference-semantic" data-reference-id="lcd-on-off.semantic"><img alt="Pressing the POWER button switches the LCD display on or off" class="hb-reference-art hb-composite-art" src="assets/es-lcd-on-off.png"/></div></figure></div>

<p>Al pulsar el botón de encendido Principa o al cargar el producto, se enciende la pantalla LCD, y al pulsarlo de nuevo, se apagará la pantalla LCD.</p>

<span id="native-troubleshooting"></span>

## RESOLUCIÓN DE PROBLEMAS

<p>Si aparece alguno de los siguientes códigos de falla, siga las acciones correctivas listadas para resolver el problema.Si la falla persiste, por favor contacte con atención al cliente de Jackery.</p>

<div class="native-fit-phone"><figure aria-label="Código de error / Medidas correctivas" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Código de error</th><th class="hb-troubleshooting-measures" scope="col">Medidas correctivas</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code"><strong>F0</strong></td><td class="hb-troubleshooting-measures">Reiniciar el producto.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F1, F2</strong></td><td class="hb-troubleshooting-measures">Contacte con atención al cliente de Jackery.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F3</strong></td><td class="hb-troubleshooting-measures">Reiniciar el producto.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F4</strong></td><td class="hb-troubleshooting-measures">Conecte el producto a cargas para descargar su batería hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F5</strong></td><td class="hb-troubleshooting-measures">Cargue el producto mediante paneles solares o toma de corriente CA hasta que la falla desaparezca.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F6-F9,</strong><br/><strong>FA, FC, FE</strong></td><td class="hb-troubleshooting-measures">Contacte con atención al cliente de Jackery.</td></tr><tr><td class="hb-troubleshooting-code"><strong>FF</strong></td><td class="hb-troubleshooting-measures">Coloque el producto en un ambiente con temperatura adecuada y espere hasta que la falla desaparezca.</td></tr></tbody></table></figure></div>

<span id="native-connections"></span>

## CONEXIONES

<p>Se pueden usar hasta 5 juegos de estos productos junto con el Jackery HomePower 3600 Plus para cubrir las necesidades de mayor capacidad.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>Asegúrese de que todos los productos estén apagados antes de conectar el HomePower 3600 Plus al paquete de Jackery Battery Pack 3600.<br/>Para asegurar el funcionamiento adecuado del producto, asegúrese de que las rejillas de entrada y salida de aire en ambos lados estén despejadas. Deje al menos 0,66 pies (≈200 mm) de espacio entre las rejillas y cualquier objeto para permitir una disipación de calor adecuada.</p></td></tr></tbody></table>

<div class="native-figure native-clearance native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="clearance" data-source-fragment-sha256="f9ebd1504950935fee1743cd4fd3356ab515d08fee52d3c9317a47e2fe9e8806" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="clearance.semantic"><img alt="Battery packs connected to the Jackery HomePower 3600 Plus, with at least 0.66 ft (≈200 mm) of space between the vents and any objects" class="hb-reference-art hb-composite-art" src="assets/es-clearance.png"/></div></figure></div>

<div class="native-figure native-stacking native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stacking" data-source-fragment-sha256="cc6cfb4fceb0bb982ee2dc3cf920dd54ba485d6900ba0b9b6bd1e892bcb86bc9"><div class="hb-reference-semantic" data-reference-id="stacking.semantic"><img alt="Correct: up to three battery packs in one tower. Incorrect: four battery packs in one tower" class="hb-reference-art hb-composite-art" src="assets/stacking.png"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Observaciones</td><td class="manual-callout-body"><p>La aparición del icono<img alt="battery pack connection icon (HomePower 3600 Plus LCD)" class="native-inline-control" src="assets/inline-connection-icon.svg"/>en la pantalla LCD (Jackery HomePower 3600 Plus) indica que la conexión entre la batería y el Jackery HomePower 3600 Plus se ha realizado correctamente.<br/>Al usar el producto, no apile más de tres paquetes de baterías en vertical para evitar que se caigan y causen lesiones.<br/>No coloque el producto encima del Jackery HomePower 3600 Plus.</p></td></tr></tbody></table>

<div class="native-figure native-locking native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="locking" data-source-fragment-sha256="0920e155c9a022d8aa07133c7e0086b334a6fbdb474d063b7ef2938621dd6457" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="locking.semantic"><img alt="Expansion cable connections, with the steps to lock and unlock the cable terminal" class="hb-reference-art hb-composite-art" src="assets/es-locking.png"/></div></figure></div>

<span id="native-charging"></span>

## CARGANDO

### CARGA MEDIANTE UNA TOMA DE CORRIENTE DE PARED ALTERNA

<p>Cuando se carga desde la red, este producto debe utilizarse con Jackery HomePower 3600 Plus.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Advertencia</td><td class="manual-callout-body"><p>Asegúrese de que todos los productos estén apagados antes de conectar el HomePower 3600 Plus al paquete de Battery Pack 3600.</p></td></tr></tbody></table>

<div class="native-figure native-ac-charging native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charging" data-source-fragment-sha256="4d3dbf0cc8876dcebd28f7539ac76e5057d9b92072665e48b4dd419d40965776" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="ac-charging.semantic"><img alt="Charging via an AC wall outlet through the Jackery HomePower 3600 Plus" class="hb-reference-art hb-composite-art" src="assets/es-ac-charging.png"/></div></figure></div>

### CARGA MEDIANTE PANELES SOLARES <span class="native-sold-separately">SE VENDE POR SEPARADO</span>

<p>Cargue su producto con paneles solares y el Jackery HomePower 3600 Plus como se muestra en la siguiente figura. Consulte el manual de usuario de Jackery HomePower 3600 Plus para obtener más información.</p>

<div class="native-figure native-solar-charging native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-charging" data-source-fragment-sha256="ae8652bbb44b687ec73b0ca6182bbbaab160d69087ff621c9e193f0e25b612b4" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="solar-charging.semantic"><img alt="Charging via solar panels through the Jackery HomePower 3600 Plus" class="hb-reference-art hb-composite-art" src="assets/solar-charging.png"/></div></figure></div>

<span id="native-storage"></span>

## ALMACENAMIENTO

<p>Almacene el producto en un lugar seco y limpio con ventilación adecuada.Temperatura y humedad de almacenamiento:</p>

<ul class="native-bullets"><li>1 mes: -4°F a 113°F / -20 a 45 °C (0-60 % HR)</li><li>3 meses: 32°F a 113°F / 0 a 45 °C (0-60 % HR)</li><li>12 meses: 32°F a 77°F / 0 a 25 °C (0-60 % HR)</li></ul>

<p>Si este producto se almacena durante un período prolongado (de 3 a 6 meses) con la batería descargada, podría volverse imposible recargarlo. Para evitar esto y mantener la salud de la batería, se recomienda revisar y recargar el producto cada tres meses, y realizar un ciclo completo de carga y descarga al menos una vez cada 6 a 12 meses.</p>

<span id="native-specifications"></span>

## ESPECIFICACIONES

<h2 class="hb-spec-group">INFORMACIÓN GENERAL</h2>

<figure aria-label="INFORMACIÓN GENERAL" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 3600</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° de modelo</th><td class="manual-spec-value hb-spec-value">JBP-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacidad</th><td class="manual-spec-value hb-spec-value">80Ah / 44,8Vdc (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Química Celular</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 55.1 libras/25 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">14,8 × 12,5 × 9,0 pulgadas / 37,5 × 31,7 × 22,9 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Ciclo de vida</th><td class="manual-spec-value hb-spec-value">6000 ciclos de carga hasta 70 % + de capacidad</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PUERTOS DE ENTRADA/SALIDA</h2>

<figure aria-label="PUERTOS DE ENTRADA/SALIDA" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Entrada)</th><td class="manual-spec-value hb-spec-value">36,4V-50,4V⎓60A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Puerto de Expansión de CC (Salida)</th><td class="manual-spec-value hb-spec-value">36,4V-50,4V⎓100A Máx.</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente máxima de cortocircuito y duración</th><td class="manual-spec-value hb-spec-value">1160A/860μs</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPERATURA DE FUNCIONAMIENTO</h2>

<figure aria-label="TEMPERATURA DE FUNCIONAMIENTO" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de carga</th><td class="manual-spec-value hb-spec-value">-4°F a 113°F / -20°C a 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de descarga</th><td class="manual-spec-value hb-spec-value">-4°F a 113°F / -20°C a 45°C</td></tr></tbody></table></figure>

<span id="native-warranty"></span>

## GARANTÍA

<figure aria-label="GARANTÍA" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>Solo ofrecemos nuestra garantía a clientes que compren en el sitio web oficial de Jackery, plataformas de terceros con la marca Jackery o distribuidores autorizados locales.</strong></div><div class="hb-warranty-local-note">* El periodo de garantía y los detalles pueden variar según las leyes, regulaciones y distribuidores autorizados locales.</div></figure>

### Garantía limitada

<figure aria-label="Garantía limitada" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantiza al consumidor original que el producto Jackery estará libre de defectos relativos al acabado y a los materiales en condiciones normales de uso por parte del consumidor durante el período de garantía aplicable identificado en la sección "Período de garantía" que figura a continuación, sujeto a las exclusiones que se establecen a continuación.</p><p>Esta declaración de garantía establece la obligación de garantía total y exclusiva de Jackery. No asumiremos ni autorizaremos que ninguna persona asuma por nosotros ninguna otra responsabilidad en relación con la venta de nuestros productos.</p></figure>

### Período de garantía

<figure aria-label="Período de garantía" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 AÑOS Garantía Estándar" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía Estándar</strong></div></div><div class="hb-warranty-period-copy">El periodo de garantía estándar de Jackery Battery Pack 3600 es de 36 meses. En cada caso, el período de garantía se mide a partir de la fecha de compra por parte del comprador consumidor original. Para establecer la fecha de inicio del período de garantía, se necesita el recibo de venta de la primera compra del consumidor u otra prueba documental razonable.</div></div><div aria-label="2 AÑOS Garantía extendida" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">AÑOS</strong><strong class="hb-warranty-period-label">Garantía extendida</strong></div></div><div class="hb-warranty-period-copy">Para activar la extensión de garantia,debe registrar su producto en línea oponerse en contacto con nuestro equipo de atención al cliente en hello@jackery.com para ampliar laduración de la garantia estándar.</div></div></div></figure>

### Reparación o reemplazo

<figure aria-label="Reparación o reemplazo" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery reparará o reemplazará (a cargo de Jackery) cualquier producto Jackery que no funcione durante el periodo de garantía aplicable debido a defectos en la mano de obra o el material. El producto reparado o reemplazado asumirá el periodo restante de la garantía desde la fecha original de compra.</p></figure>

### Limitado al comprador consumidor original

<figure aria-label="Limitado al comprador consumidor original" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantía del producto de Jackery se limita al consumidor original y no es transferible a ningún propietario posterior.</p></figure>

### Exclusiones

<figure aria-label="Exclusiones" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantía de Jackery no se aplica a:<br/>Mal uso, abuso, modificación, daño por accidente, o uso para cualquier cosa que no sea el uso normal del consumidor según lo autorizado en los folletos actuales del producto de Jackery.<br/>Intento de reparación por cualquier persona que no sea un centro autorizado.<br/>Cualquier producto adquirido a través de una casa de subastas en línea.<br/>La garantía de Jackery no se aplica a la célula de la batería a menos que usted la cargue completamente en los siete días siguientes a la compra del producto y, a partir de entonces, al menos una vez cada 6 meses.</p></figure>

### Derechos de interpretación

<figure aria-label="Derechos de interpretación" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery se reserva el derecho a la interpretación final de la política posventa de los clientes anterior.</p></figure>
