<style>
/* JA-TS02A French and Spanish source geometry only. The shared Web theme owns every colour,
   border, fill, heading, callout, table and figure style (prepared-document shared-style gate).
   Figures are selected by their shared data attributes, images by their packaged file names. */

/* Complete print panels keep the print's own width; no visible caption. */
#furo-main-content .hb-reference-figure { max-width: 680px; margin-left: auto; margin-right: auto; }
#furo-main-content .hb-reference-figure img { width: 100% !important; height: auto !important; }
#furo-main-content .hb-reference-figure:is([data-reference-id="package-list"], [data-reference-id="optional-tools"],
  [data-reference-id="dimensions"], [data-reference-id="mounting-template"], [data-reference-id="mounting-fasteners"],
  [data-reference-id="external-emergency-stop"], [data-reference-id="deadfront-installation"],
  [data-reference-id="app-wifi"], [data-reference-id="app-voltage-menu"], [data-reference-id="app-circuit-list"],
  [data-reference-id="app-circuit-name"], [data-reference-id="app-circuits"]) { max-width: 620px; }
#furo-main-content .hb-reference-figure:is([data-reference-id="locking-panel"], [data-reference-id="iot-pairing"]) { max-width: 420px; }
#furo-main-content .hb-reference-figure[data-reference-id="mounting-brackets"] { max-width: 400px; }
/* App screenshots at phone size. */
#furo-main-content .hb-reference-figure:is([data-reference-id="app-add-device"], [data-reference-id="app-dashboard"],
  [data-reference-id="app-working-modes"], [data-reference-id="app-backup-only"],
  [data-reference-id="app-backup-priority"], [data-reference-id="app-ups-mode"]) { max-width: 260px; }

/* Inline App controls at text size. */
#furo-main-content :is(p, li) > img[src*="inline-"] {
  display: inline-block; width: 1.25em !important; height: 1.25em !important;
  margin: 0 0.1em !important; vertical-align: -0.22em; object-fit: contain;
}

/* Symbol glyphs at the print's size: the ingestion-hazard mark beside its list, the table icons in their cells. */
#furo-main-content img[src*="symbol_ingestion_hazard"] { float: left; width: 2.2rem !important; height: auto !important; margin: 0.2rem 0.6rem 0 0 !important; }
#furo-main-content img[src*="symbol_ingestion_hazard"] + ul { display: flow-root; margin-top: 0; }
#furo-main-content td > img[src*="symbol_"] { width: 2.1rem !important; height: auto !important; margin: 0 auto !important; display: block; }

/* Room for two-digit step numbers (the print's 1-24 safety list). */
#furo-main-content ol { padding-left: 2.4em; }

/* Print case for subheadings (the print sets them in bold title case); shared markers stay. */
#furo-main-content h2:not(.hb-spec-section), #furo-main-content :is(h3, h4) { text-transform: none; }

/* Phones: the plain tables fit the screen as in the English edition (R8); the six-column torque table still scrolls. */
@media (max-width: 760px) {
  #furo-main-content table[class="manual-table"] { min-width: 0 !important; }
}
@media (max-width: 420px) {
  #furo-main-content table[class="manual-table"] :is(td, th) { padding: 0.42rem 0.4rem !important; }
}

</style>

<span id="native-safety"></span>

## INSTRUCCIONES DE SEGURIDAD

### Descargo de Responsabilidad

<p>Felicitaciones por su nuevo Jackery Smart Transfer Switch. Antes de utilizar el producto, lea cuidadosamente este manual, especialmente las precauciones relevantes para asegurar un uso adecuado. Mantenga este manual en un lugar accesible para futuras consultas.<br/>De acuerdo con las leyes y regulaciones, el derecho de interpretación final de este documento y todos los documentos relacionados con este producto corresponde a la Empresa.<br/>Tenga en cuenta que no se realizarán notificaciones adicionales en caso de actualizaciones, revisiones o terminaciones.</p>

### Advertencia

<ol><li>La instalación o el mantenimiento de este producto debe ser realizado únicamente por personal eléctrico cualificado.</li><li>Antes de la instalación, operación o mantenimiento de este producto, lea detenidamente el manual de instrucciones.</li><li>La instalación de este producto debe cumplir con las normas locales, normas nacionales de seguridad eléctrica e instrucciones del fabricante.</li><li>Las especificaciones de los cables proporcionados por el usuario deben cumplir con los requisitos de la Guía de Instalación y con las normativas locales.</li><li>Los cables de CA son cables de alta tensión. Riesgo de muerte o lesiones graves por descarga eléctrica.</li><li>Existe una alta posibilidad de descarga eléctrica o quemaduras graves debido a la alta tensión en el producto.</li><li>Utilice equipo de protección personal (PPE) adecuado y siga las prácticas seguras de trabajo eléctrico.</li><li>No toque los cables expuestos con las manos.</li><li>Tenga cuidado para evitar lesiones al mover objetos pesados. Use equipo de protección personal como guantes y zapatos protectores al mover manualmente el producto.</li><li>No instale ni opere el equipo en condiciones meteorológicas extremas como rayos, nieve, lluvia intensa, viento fuerte, etc.</li><li>No instale ni opere el producto en un área donde se almacenen materiales inflamables o explosivos.</li><li>Inspeccione el producto y los cables en busca de daños antes de la instalación. No instale el producto ni los cables si están dañados de alguna manera.</li><li>Apague toda la energía que suministra este producto antes de la instalación. Desconecte cada circuito individualmente antes del mantenimiento.</li><li>Siempre utilice un dispositivo de detección de voltaje correctamente calibrado para confirmar que la energía está apagada.</li><li>Durante el proceso de perforación, cubra el producto interior para evitar que los desechos caigan en el producto y limpie los desechos después de la perforación para evitar interferencias con el equipo.</li><li>No dañe, manche ni cubra las etiquetas de advertencia en el dispositivo. Todas las etiquetas deben ser visibles después de la instalación.</li><li>Antes de operar el producto, verifique las conexiones eléctricas para asegurar que el producto esté correctamente y permanentemente conectado a tierra.</li><li>No coloque ningún objeto sobre el producto durante su funcionamiento.</li><li>Para desenergizar completamente el producto, asegúrese de que todos los disyuntores principales y derivados estén apagados y desconecte físicamente todas las cargas. No hacerlo puede representar un riesgo de descarga eléctrica.</li><li>No coloque ni instale objetos inflamables o potencialmente explosivos cerca del producto o en atmósferas explosivas.</li><li>No inserte objetos extraños en ninguna parte del equipo.</li><li>No conecte a circuitos que puedan ser conmutados de forma remota los sistemas de soporte vital, equipos médicos, ni ningún otro equipo donde la falla del producto pueda causar lesiones a personas o pérdida de vidas.</li><li>Instale el producto en un lugar que evite daños por inundaciones. Asegúrese de que no haya fuentes de agua arriba o cerca del producto, incluidos bajantes, aspersores o grifos.</li><li>Si es necesario, reemplace todos los dispositivos, puertas y cubiertas antes de encender la alimentación.</li></ol>

### Precaución

<ol><li>En caso de daños en el cable, debe ser reemplazado por el fabricante, servicio al cliente o personal calificado para evitar un riesgo de seguridad.</li><li>No utilice disolventes para limpiar el producto.</li><li>El producto debe ser desechado de acuerdo con los códigos y regulaciones locales.</li><li>Este producto no está destinado a ser utilizado como desconexión de servicio.</li><li>No utilice partes o accesorios que no sean los especificados para su uso con el producto.</li><li>Al instalar el producto, los tornillos deben ser apretados con una herramienta especial de acuerdo con el par especificado.</li><li>Mantenga el producto fuera del alcance de niños o animales.</li><li>Este producto está diseñado únicamente para uso residencial.</li></ol>

### Declaración de la FCC

<p>Este dispositivo cumple con la parte 15 de las Reglas de la FCC. El funcionamiento está sujeto a las siguientes dos condiciones: (1) Este dispositivo no debe causar interferencias dañinas, y (2) este dispositivo debe aceptar cualquier interferencia recibida, incluidas las interferencias que puedan causar un funcionamiento no deseado.<br/>MODIFICACIÓN: Cualquier cambio o modificación no expresamente aprobado por el concesionario de este dispositivo podría anular la autoridad del usuario para operar el dispositivo.<br/>NOTA: Este equipo ha sido probado y se ha encontrado que cumple con los límites para un dispositivo digital Clase B, en virtud de la parte 15 de las Reglas de la FCC. Estos límites están diseñados para proporcionar una protección razonable contra interferencias perjudiciales en una instalación residencial. Este equipo genera, utiliza y puede irradiar energía de radiofrecuencia y, si no se instala y utiliza de acuerdo con las instrucciones, puede causar interferencias perjudiciales a las comunicaciones por radio. Sin embargo, no hay garantía de que no ocurran interferencias en una instalación particular. Si este equipo causa interferencias perjudiciales a la recepción de radio o televisión, lo cual puede determinarse apagando y encendiendo el equipo, se recomienda al usuario que intente corregir las interferencias mediante una o más de las siguientes medidas:<br/>-- Reorientar o reubicar la antena receptora.<br/>-- Aumentar la separación entre el equipo y el receptor.<br/>-- Conectar el equipo a una toma de corriente en un circuito diferente al que está conectado el receptor.<br/>-- Consultar al distribuidor o a un técnico experimentado en radio/TV para obtener ayuda.</p>

### Advertencia IC

<p>Este dispositivo cumple con el estándar RSS exento de licencia de la Industria de Canadá.<br/>El funcionamiento está sujeto a las siguientes dos condiciones:<br/>(1) este dispositivo no debe causar interferencias y (2) este dispositivo debe aceptar cualquier interferencia, incluidas las interferencias que puedan causar un funcionamiento no deseado del dispositivo.<br/>Este aparato digital de Clase B cumple con lCES-003 de Canadá.</p>

<p>Declaración de RF de IC:<br/>Al utilizar el producto, mantenga una distancia de 20 cm del cuerpo para cumplir con los requisitos de exposición a RF.</p>

<img alt="" src="assets/symbol_ingestion_hazard-print.svg"/>

<ul><li>PELIGRO DE INGESTIÓN: Este producto contiene una pila de botón o batería tipo moneda.</li><li>La MUERTE o lesiones graves pueden ocurrir si se ingiere.</li><li>Una pila de botón o batería tipo moneda ingerida puede causar Quemaduras Químicas Internas en tan solo 2 horas.</li><li>MANTENGA las baterías nuevas y usadas FUERA DEL ALCANCE de los NIÑOS.</li><li>Busque atención médica inmediata si se sospecha que una batería fue ingerida o introducida en cualquier parte del cuerpo.</li></ul>

### Significado de símbolos

<p>Las siguientes tablas explican el significado de los símbolos utilizados en el manual de instrucciones y su embalaje.</p>

<div class="table-wrapper docutils container"><table class="manual-table"><thead><tr><th scope="col">Símbolo</th><th scope="col">Significado</th></tr></thead><tbody><tr><td><img alt="La posición para conectar el cable de tierra de protección." src="assets/symbol_grounding-print.svg"/></td><td>La posición para conectar el cable de tierra de protección.</td></tr><tr><td><img alt="Precaución, riesgo de peligro." src="assets/symbol_warning_triangle-print.svg"/></td><td>Precaución, riesgo de peligro.</td></tr><tr><td><img alt="Precaución, riesgo de descarga eléctrica." src="assets/symbol_electric_shock-print.svg"/></td><td>Precaución, riesgo de descarga eléctrica.</td></tr><tr><td><img alt="Consulte las instrucciones de operación." src="assets/symbol_read_manual.svg"/></td><td>Consulte las instrucciones de operación.</td></tr></tbody></table></div>

<span id="native-specifications"></span>

## ESPECIFICACIONES

<h2 class="hb-spec-group">ESPECIFICACIONES</h2>

<figure aria-label="ESPECIFICACIONES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nombre del producto</th><td class="manual-spec-value hb-spec-value">Jackery Smart Transfer Switch</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Número de Modelo</th><td class="manual-spec-value hb-spec-value">JA-TS02A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Voltaje CA (Nominal)</th><td class="manual-spec-value hb-spec-value">120V/240V~ 60Hz</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tipo de Alimentación</th><td class="manual-spec-value hb-spec-value">Fase Dividida</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Entrada Máxima</th><td class="manual-spec-value hb-spec-value">Red de 100A / Estación de Energía de 60A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente de Salida Máxima</th><td class="manual-spec-value hb-spec-value">Carga Doméstica de 60A / Estación de Energía de 33,4A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Corriente Máxima de Cortocircuito de Entrada</th><td class="manual-spec-value hb-spec-value">10KA</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Categoría de Sobretensión</th><td class="manual-spec-value hb-spec-value">IV</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">UPS</th><td class="manual-spec-value hb-spec-value">≤20ms</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Tipo de Caja (Panel de Distribución)</th><td class="manual-spec-value hb-spec-value">NEMA Tipo 1</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Número de Ramas de Carga</th><td class="manual-spec-value hb-spec-value">12</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito Principal</th><td class="manual-spec-value hb-spec-value">2 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Circuito Derivado</th><td class="manual-spec-value hb-spec-value">14 AWG 12 AWG 10 AWG</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Comunicación</th><td class="manual-spec-value hb-spec-value">Wi-Fi y Bluetooth</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Temperatura de Funcionamiento</th><td class="manual-spec-value hb-spec-value">-20°C~40°C (-4°F~104°F)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensiones</th><td class="manual-spec-value hb-spec-value">22 x 14,7 x 7,87 pulgadas/ 56 x 37,4 x 20 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Peso</th><td class="manual-spec-value hb-spec-value">Aproximadamente 25,57 libras/11,6 kg</td></tr></tbody></table></figure>

<p>* Cuando utilice el producto, asegúrese de que esté conectado a una tensión de red de fase partida de 240 V.</p>

<span id="native-package-list"></span>

## LISTA DE PAQUETES

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="package-list" data-source-fragment-sha256="e6b5adf6998ad1577c3b939e04a74588b6c061f91c3fd74288ebba8885465edb" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="package-list.semantic"><img alt="Lista de paquetes" class="hb-reference-art hb-composite-art" src="assets/es-package-list.png"/></div></figure>

<span id="native-what-you-need"></span>

## LO QUE NECESITAS

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="optional-tools" data-source-fragment-sha256="e4dc1b016278b4f47086fe1b57f04d032779ae5f2382e27de92caf4a83475bf5" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="optional-tools.semantic"><img alt="Componentes de instalación opcionales" class="hb-reference-art hb-composite-art" src="assets/es-optional-tools.png"/></div></figure>

### Opcionales

<div class="table-wrapper docutils container"><table class="manual-table"><thead><tr><th colspan="2" scope="col">Cable</th><th scope="col">Color</th><th scope="col">Corriente</th><th scope="col">Calibre</th></tr></thead><tbody><tr><td rowspan="4">Red (Conecte al Panel Principal)</td><td>L1</td><td>Negro</td><td rowspan="4">100A Máx</td><td>2 AWG</td></tr><tr><td>L2</td><td>Rojo</td><td>2 AWG</td></tr><tr><td>N</td><td>Blanco</td><td>2 AWG</td></tr><tr><td>GND</td><td>Verde</td><td>6 AWG</td></tr><tr><td rowspan="4">Cargas Domésticas (Conecte a 12 Circuitos Derivados)</td><td>L1</td><td>Negro</td><td rowspan="4">30A Máx</td><td>14 AWG -10 AWG</td></tr><tr><td>L2</td><td>Rojo</td><td>14 AWG -10 AWG</td></tr><tr><td>N</td><td>Blanco</td><td>14 AWG -10 AWG</td></tr><tr><td>GND</td><td>Verde</td><td>14 AWG -10 AWG</td></tr><tr><td>Circuito de parada de emergencia (Conectar al botón de parada de emergencia)</td><td>/</td><td>/</td><td>2A Máx</td><td>24 AWG</td></tr></tbody></table></div>

<p>*Prepare un disyuntor derivado de 100A y 2 polos para instalarlo en el cuadro de distribución de la vivienda. Este interruptor se utilizará para conectar con el Smart Transfer Switch (STS).</p>

<span id="native-product-overview"></span>

## DESCRIPCIÓN DEL PRODUCTO

### Dimensiones

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="dimensions" data-source-fragment-sha256="4b5c87d09252b3e3f720fd7044d439498e77f4c7f1081d3ae3450373e3cc75fe" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="dimensions.semantic"><img alt="Dimensiones" class="hb-reference-art hb-composite-art" src="assets/es-dimensions.png"/></div></figure>

<p>*Las figuras son solo para referencia, consulte el producto real.</p>

### Con Cubierta de Frente Muerto Instalada

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="covered-overview" data-source-fragment-sha256="6b88c7800c87d030127102501242bb423e197dd89acbd18e843c3fcb81206ff0" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="covered-overview.semantic"><img alt="Con Cubierta de Frente Muerto Instalada" class="hb-reference-art hb-composite-art" src="assets/es-covered-overview.png"/></div></figure>

#### Botón de IoT con Indicador

<ul><li>Pulse brevemente el botón para encender/apagar el Bluetooth y el Wi-Fi.</li><li>Mantenga pulsado el botón durante 5 segundos para reiniciar el Bluetooth y el Wi-Fi (el Interruptor de Transferencia Automática conservará la configuración anterior).</li></ul>

<p>*Encienda el Wi-Fi y el Bluetooth. Si no se emparejan en dos horas, se apagarán automáticamente.</p>

#### Botón de Parada de Emergencia

<p>En caso de emergencia, este botón puede ser activado manualmente para apagar inmediatamente la salida de todo el sistema.</p>

### Indicadores LED

<div class="table-wrapper docutils container"><table class="manual-table"><thead><tr><th scope="col">Indicador</th><th scope="col">Estado</th><th scope="col">Descripción</th></tr></thead><tbody><tr><td rowspan="3">Indicador de Red</td><td>Azul intermitente</td><td>Presencia de energía de la red, no suministra carga a los dispositivos del hogar.</td></tr><tr><td>Azul Sólido</td><td>La energía de la red suministra cargas al hogar</td></tr><tr><td>Apagado</td><td>Sin energía de la red.</td></tr><tr><td rowspan="3">Estación de Energía Indicador (AC1/AC2)</td><td>Verde intermitente</td><td>La estación de energía está conectada y en espera, no suministra energía a las cargas del hogar.</td></tr><tr><td>Verde Sólido</td><td>La estación de energía está conectada y suministrando energía a las cargas del hogar. En el STS, el suministro de energía a las cargas del hogar depende de la configuración de puesta en marcha.</td></tr><tr><td>Apagado</td><td>Estación de Energía No Conectada</td></tr><tr><td rowspan="3">Indicador de IoT</td><td>Verde intermitente</td><td>Wi-Fi y Bluetooth Encendidos, No Emparejados</td></tr><tr><td>Verde Sólido</td><td>Wi-Fi y Bluetooth Encendidos, Emparejados</td></tr><tr><td>Apagado</td><td>Wi-Fi y Bluetooth Apagados</td></tr><tr><td rowspan="2">Indicador de Error</td><td>Rojo Sólido</td><td>Mal Funcionamiento del Producto</td></tr><tr><td>Apagado</td><td>Operación Normal</td></tr></tbody></table></div>

### Con Cubierta de Frente Muerto Retirada

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="uncovered-overview" data-source-fragment-sha256="2ad1671437d09c327d7f1e6d3f53629035e380578dbb090df9814c9e6efae8e3" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="uncovered-overview.semantic"><img alt="Con Cubierta de Frente Muerto Retirada" class="hb-reference-art hb-composite-art" src="assets/es-uncovered-overview.png"/></div></figure>

#### Modo de respaldo normal

<p>La función UPS está desactivada por defecto. En caso de un apagón, la estación de energía portátil alimentará automáticamente las cargas del hogar con la energía almacenada en 5 segundos. En caso de un apagón, la estación de energía portátil alimentará automáticamente las cargas del hogar con la energía almacenada entre 5 segundos.</p>

<table class="manual-callout-table manual-callout-table hb-callout-label-shaded"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>La estación de energía debe permanecer encendida; de lo contrario, el STS no podrá cambiar a la energía de la batería después de un apagón.</p></td></tr></tbody></table>

#### Modo UPS

<p>En este modo, la función UPS está activada. Durante un apagón, el sistema cambia automáticamente a la energía de la batería en 20 milisegundos.</p>

<ul><li>La estación de energía portátil permanece activa en todo momento y consume continuamente una pequeña cantidad de energía, incluso cuando no está en uso.</li><li>Si la estación de energía está siendo cargada por el STS, el tiempo de cambio puede exceder los 20 milisegundos.</li><li>Cuando se restablezca el suministro eléctrico de la red, el sistema cambiará automáticamente de vuelta a la alimentación por red.</li></ul>

<table class="manual-callout-table manual-callout-table hb-callout-label-shaded"><tbody><tr><td class="manual-callout-label">PRECAUCIÓN</td><td class="manual-callout-body"><p>La función UPS solo puede funcionar si el STS está conectado exitosamente al Jackery Explorer 5000 Plus o al Jackery HomePower 5000 Plus. Antes de usar el modo UPS, asegúrese de lo siguiente:</p><ol><li>La función UPS está habilitada en la aplicación Jackery.</li><li>La estación de energía portátil está encendida y no se está cargando.</li></ol></td></tr></tbody></table>

<span id="native-pre-installation"></span>

## PRE-INSTALACIÓN

### Descripción General del Sistema

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="system-overview" data-source-fragment-sha256="38c5bfef60cc10f9081f92882fdd26de1b32f3d36bc3525d0a2c4bbd3cf9ca58" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="system-overview.semantic"><img alt="Descripción General del Sistema" class="hb-reference-art hb-composite-art" src="assets/es-system-overview.png"/></div></figure>

<p>* Si no hay Wi-Fi disponible, conecta tu dispositivo con Bluetooth.<br/><strong>* Si el Wi-Fi y el Bluetooth del dispositivo están activados y no se han conectado a la aplicación Jackery en dos horas, ambos se apagarán automáticamente.</strong></p>

### Ubicación de Instalación

<p>Instale el Jackery Smart Transfer Switch en interiores.</p>

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/symbol_warning_triangle_yellow.svg"/>Advertencia</span></td><td class="manual-callout-body"><ul><li>Asegúrese de que el producto esté ubicado en un lugar seco y bien ventilado.</li><li>Asegúrese de que la puerta se abra a un ángulo de al menos 90 grados.</li><li>El personal de instalación debe usar guantes aislantes, gafas de seguridad y zapatos con suela de goma.</li><li>Antes de la instalación, asegúrese de que el disyuntor principal y todos los circuitos derivados estén apagados.</li></ul></td></tr></tbody></table>

<span id="native-installation-guide"></span>

## GUÍA DE INSTALACIÓN

<p>Los detalles a continuación son pautas generales para el espacio de instalación y no se garantiza su aplicabilidad. Consulte con su AHJ local o su compañía de servicios públicos antes de usar.</p>

### Montaje en Superficie

<table class="manual-callout-table manual-callout-table hb-source-warning-lockup"><tbody><tr><td class="manual-callout-label"><span class="hb-warning-lockup"><img alt="" src="assets/symbol_warning_triangle_yellow.svg"/>Advertencia</span></td><td class="manual-callout-body"><p>El producto no es impermeable y está diseñado específicamente para uso en interiores.</p></td></tr></tbody></table>

<ol><li>Instale los soportes de pared superiores e inferiores en la parte posterior del Smart Transfer Switch con 4 tornillos M4. Apriete todos los tornillos con un par de 0.8 N·m.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-brackets" data-source-fragment-sha256="53d5b007ab864789866a3f4f5e9d6808af636cc2e718319b33a00b51b12e5aef"><div class="hb-reference-semantic" data-reference-id="mounting-brackets.semantic"><img alt="Instalar los soportes de pared" class="hb-reference-art hb-composite-art" src="assets/es-mounting-brackets.png"/></div></figure>

<ol start="2"><li>Fije la plantilla en la superficie de montaje y marque cuidadosamente cada ubicación del agujero con un lápiz.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-template" data-source-fragment-sha256="0a441549a74e66d3baaf1b316aaa638523113f518663393f5c25de78f2cf5b08" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="mounting-template.semantic"><img alt="Posiciones de la plantilla de marcado" class="hb-reference-art hb-composite-art" src="assets/es-mounting-template.png"/></div></figure>

<ol start="3"><li>Fije el Smart Transfer Switch con 4 pernos de expansión M6 o tornillos M6.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="mounting-fasteners" data-source-fragment-sha256="4c2ccff92cd4dbd601dc7a7c5e6e0dc71a3988c657c3dcafa6db951df6f7582c" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="mounting-fasteners.semantic"><img alt="Fijar el Smart Transfer Switch" class="hb-reference-art hb-composite-art" src="assets/es-mounting-fasteners.png"/></div></figure>

### Selección de Entrada de Cables

<ul><li>Durante el proceso de perforación, cubra el equipo interior para evitar que los desechos caigan dentro del equipo.</li><li>Quite los desechos después de la perforación para evitar interferencias con el equipo.</li></ul>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="cable-entry" data-source-fragment-sha256="f014dbad4c8a55809e40c1c50164e202bf5bc102bb43bdeb639bc56906de0a80" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="cable-entry.semantic"><img alt="Selección de Entrada de Cables. Por favor, apague la energía antes de trabajar en el cableado. No perfore fuera del área designada." class="hb-reference-art hb-composite-art" src="assets/es-cable-entry.png"/></div></figure>

### Conexiones Eléctricas

<p>Advertencia</p>

<ul><li>Riesgo de descarga eléctrica. Antes de realizar el cableado, asegúrese de que la energía esté apagada. Asegúrese de que los disyuntores principales y derivados estén apagados.</li><li>Asegúrese de que los conductos estén instalados antes de realizar el cableado entre el panel principal y el Jackery Smart Transfer Switch para mejorar la seguridad y proteger los cables de daños.</li></ul>

<p>*Como se muestra en la imagen, puede mover los disyuntores del panel principal al Smart Transfer Switch.<br/>*La instalación del disyuntor derivado de 100A y 2 polos en el panel principal es como se muestra en la imagen.<br/>*Los disyuntores en el interruptor de transferencia no deben exceder los 30A.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="grid-preparation" data-source-fragment-sha256="1c01943635e1742444ab63855ca2e5daa10549e532290d4b88ca606d3b840ad7" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="grid-preparation.semantic"><img alt="Panel principal y Smart Transfer Switch. Solo disyuntores unipolares y bipolares, no disyuntores en tándem." class="hb-reference-art hb-composite-art" src="assets/es-grid-preparation.png"/></div></figure>

#### Conexión de Conductores de la Red

<ol><li>Asegúrese de que todos los disyuntores derivados y el disyuntor principal estén apagados.</li><li>Retire la cubierta tanto del panel principal como del Smart Transfer Switch.</li><li>Retire el orificio ciego del panel eléctrico y taladre los orificios de entrada de cables permitidos en el Smart Transfer Switch.</li><li>Instale un conducto(no incluido) entre el panel principal y el Smart Transfer Switch.</li><li>Tire de los cables precableados del panel principal agrupados a través del conducto.</li><li>Instale un disyuntor derivado compatible de 100A y 2 polos(no incluido) en el panel principal.</li><li>Ubique el cable de TIERRA del panel principal y conéctelo a los terminales de tierra de la red del Smart Transfer Switch.</li><li>Ubique el cable de NEUTRO del panel principal y conéctelo a los terminales neutros de la red del Smart Transfer Switch.</li><li>Ubique los cables VIVOS del disyuntor derivado de 100A agregado al panel principal y conéctelos al Smart Transfer Switch. Instale la cubierta de la fuente de alimentación del Smart Transfer Switch.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="grid-wiring" data-source-fragment-sha256="f5fcfbdc1c39407ec629a2b12c8de4ef456d5056f36b0a509d1da4acc7db86bd" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="grid-wiring.semantic"><img alt="Conexión de Conductores de la Red" class="hb-reference-art hb-composite-art" src="assets/es-grid-wiring.png"/></div></figure>

#### Conexión de Conductores de Carga Doméstica

<p>*La carga doméstica admite la conexión simultánea de circuitos de 120V y 240V, con un máximo de 12 circuitos para 120V y 6 circuitos para 240V.</p>

<ol><li>Seleccione un circuito derivado del panel principal para ser alimentado por el Smart Transfer Switch durante un corte de energía; cuando no haya corte de energía, los circuitos seleccionados serán alimentados por la red eléctrica.</li><li>Apague el disyuntor seleccionado en el panel principal.</li><li>Retire el cable VIVO del disyuntor seleccionado.</li><li>Retire el cable NEUTRO del circuito seleccionado de la barra colectora NEUTRO.</li><li>Retire el cable TIERRA del disyuntor seleccionado de la barra colectora de tierra.</li><li>Conecte el cable VIVO retirado del panel principal al disyuntor en el Smart Transfer Switch.</li><li>Conecte el cable NEUTRO retirado del panel principal a la barra colectora neutra en el Smart Transfer Switch.</li><li>El cable de tierra del panel eléctrico no necesita estar conectado al STS.</li><li>Etiquete el disyuntor en la cubierta del Smart Transfer Switch.</li><li>Repite el proceso para cada circuito.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="load-wiring" data-source-fragment-sha256="3fadc6e772006777449e48adc3bcadb8af36118b773a7afd79fb589e7c5f6f8d" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="load-wiring.semantic"><img alt="Conexión de Conductores de Carga Doméstica" class="hb-reference-art hb-composite-art" src="assets/es-load-wiring.png"/></div></figure>

<p><strong>Par de Apriete del Conductor</strong></p>

<div class="table-wrapper docutils container"><table class="manual-table"><thead><tr><th scope="col">Red</th><th scope="col">Par</th><th scope="col">Longitud de Desforre</th><th scope="col">Carga Doméstica</th><th scope="col">Par</th><th scope="col">Longitud de Desforre</th></tr></thead><tbody><tr><td>L1</td><td>30.98 pulgadas-libra/3.5 N·m</td><td>0.47 pulgada (12 mm)</td><td>L1</td><td>20.36 pulgadas-libra/2.3 N·m</td><td>0.39 pulgada (10 mm)</td></tr><tr><td>L2</td><td>30.98 pulgadas-libra/3.5 N·m</td><td>0.47 pulgada (12 mm)</td><td>L2</td><td>20.36 pulgadas-libra/2.3 N·m</td><td>0.39 pulgada (10 mm)</td></tr><tr><td>N</td><td>46.02 pulgadas-libra/5.2 N·m</td><td>0.47 pulgada (12 mm)</td><td>N</td><td>17.7 pulgadas-libra/2.0 N·m</td><td>0.47 pulgada (12 mm)</td></tr><tr><td>GND</td><td>46.02 pulgadas-libra/5.2 N·m</td><td>0.79 pulgada (20 mm)</td><td>GND</td><td>17.7 pulgadas-libra/2.0 N·m</td><td>0.47 pulgada (12 mm)</td></tr></tbody></table></div>

#### Instalar el botón de parada de emergencia (opcional)

<p><strong>*Asegúrese de comprar un botón de parada de emergencia normalmente abierto.</strong><br/>Instalar en un lugar externo de fácil acceso. Esto permite desconectar inmediatamente la alimentación de las cargas del STS en caso de emergencia.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="external-emergency-stop" data-source-fragment-sha256="06394b7d8503f7291a5235ca2795fdc3d244b5e78f5aa4b712c7bc6c10377a84" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="external-emergency-stop.semantic"><img alt="Botón de parada de emergencia - conexiones interior y exterior" class="hb-reference-art hb-composite-art" src="assets/es-external-emergency-stop.png"/></div></figure>

#### Instalación de Cubierta de Frente Muerto

<p>Advertencia<br/>*Confirme que todas las conexiones estén correctas, seguras y puestas a tierra.<br/>*Confirme que todos los tornillos estén apretados.<br/>*Utilice un multímetro en la configuración de continuidad para asegurarse de que el cable vivo no esté en cortocircuito con el neutro.<br/>*Utilice un multímetro en la configuración de continuidad para asegurarse de que el cable vivo no esté en cortocircuito con tierra.</p>

<p>Primero, retire los recortes para las cargas domésticas, llene cualquier espacio abierto no utilizado en la cubierta y luego apriete los tornillos para asegurar el frente muerto.</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="deadfront-installation" data-source-fragment-sha256="95ebba04f9e30f47d6e9042d1317eaa346b70ea74a52caa53f4464f2ce057237" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="deadfront-installation.semantic"><img alt="Instalación de Cubierta de Frente Muerto" class="hb-reference-art hb-composite-art" src="assets/es-deadfront-installation.png"/></div></figure>

#### Conexión con Estación de Energía

<p>Para Jackery Explorer 5000 Plus(Máx. 2 unidades)</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-station-connections" data-source-fragment-sha256="d62e38b755b56133a1ef387acec411380f70688b94e74d2becfc61b27138a428" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="power-station-connections.semantic"><img alt="Conexión con Estación de Energía - máximo dos unidades" class="hb-reference-art hb-composite-art" src="assets/es-power-station-connections.png"/></div></figure>

#### Energizando

<p>Antes de la energización, asegúrese de que los disyuntores principales y derivados estén en la posición APAGADO.<br/>Para energizar, enciende el disyuntor principal y luego enciende cada disyuntor derivado.</p>

#### Bloqueo del Panel

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="locking-panel" data-source-fragment-sha256="ca9f15fb1d68bc3fe77f64763f81440a16f9a274dd88a08485b3c0ce9347d078"><div class="hb-reference-semantic" data-reference-id="locking-panel.semantic"><img alt="Bloqueo del Panel" class="hb-reference-art hb-composite-art" src="assets/es-locking-panel.png"/></div></figure>

#### Disyuntores Recomendados

<p>Disyuntores de 15A, disyuntores de 20A, disyuntores de 30A; no interruptores tandem ni cuádruples. Marcas y modelos de disyuntores compatibles: GE - THQL, Siemens - Tipo QP, Square D-HOM y HOMT, Eaton-BR<br/>El STS no es compatible con los interruptores automáticos de neutro enchufable.</p>

<span id="native-internet-setup"></span>

## USO DE LA APLICACIÓN DE JACKERY

### Para descargar la aplicación e iniciar sesión

<figure aria-label="App Store y Google Play" class="hb-app-download-composition" data-component-id="HB-SPECIAL-APP"><div class="hb-app-download-grid"><div class="hb-app-download-column hb-app-download-column-store"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-store" loading="lazy" src="assets/app-store-badges.png"/></div><div class="hb-app-download-copy hb-app-download-copy-store"><p>Método 1: Busca "Jackery" en Google Play o App Store para instalar la aplicación. Después, podrá registrarte e iniciar sesión.</p></div></div><div class="hb-app-download-column hb-app-download-column-qr"><div class="hb-app-download-art-frame"><img alt="" aria-hidden="true" class="hb-app-download-art hb-app-download-art-qr" loading="lazy" src="assets/es-app-download-qr.png"/></div><div class="hb-app-download-copy hb-app-download-copy-qr"><p>Alternativamente, escanee el código QR a continuación para descargar e instalar la aplicación.</p></div></div></div><div class="hb-app-download-semantic"><img alt="App Store y Google Play" class="hb-app-download-semantic-art" src="assets/app-store-badges.png"/></div></figure>

### Añadir un dispositivo

<ol><li>Presiona el botón de IoT para activar el Wi-Fi y Bluetooth; la luz indicadora de IoT comenzará a parpadear.</li></ol>

<p>Parpadeando - listo para conectar<br/>Fijo - conectado con éxito</p>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="iot-pairing" data-source-fragment-sha256="448715d8820222db7db464da9a99ec166e4509f61006bd5a9e5b586bcb918fd1" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="iot-pairing.semantic"><img alt="Pulsación del botón de IoT" class="hb-reference-art hb-composite-art" src="assets/es-iot-pairing.png"/></div></figure>

<ol start="2"><li>Pulsa <img alt="Añadir dispositivo" src="assets/inline-add-device.png"/> en la aplicación para agregar tu dispositivo. Esto permite que la aplicación se conecte a dispositivos cercanos y habilite los permisos de Bluetooth</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-add-device" data-source-fragment-sha256="b3735fed03368f9436ab06bac1587decb4e94c655ea41c4be1265dae33300227" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-add-device.semantic"><img alt="Añadir un dispositivo en la aplicación Jackery" class="hb-reference-art hb-composite-art" src="assets/es-app-add-device.png"/></div></figure>

<ol start="3"><li>Pulsa el icono Smart Transfer Switch (STS) en la aplicación para entrar en la página principal de STS y conectar el dispositivo a la red Wi-Fi.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-wifi" data-source-fragment-sha256="91f1ef9f0b6aa5248d869decfd589c65f51f8ef2856cb30c02af9e0afc6674e6" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-wifi.semantic"><img alt="Conectar el Smart Transfer Switch al Wi-Fi" class="hb-reference-art hb-composite-art" src="assets/es-app-wifi.png"/></div></figure>

### Configuración de voltaje

<ol><li>Pulsa <img alt="Ajustes" src="assets/inline-settings.png"/> en la página principal de STS.</li> <li>Seleccionar Configuración de voltaje <img alt="Configuración de voltaje" src="assets/inline-voltage-config.png"/></li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-voltage-menu" data-source-fragment-sha256="8da997187d809258952e6d1711a9a49ee5e8007451961347b22a345807517eb6" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-voltage-menu.semantic"><img alt="Configuración de voltaje" class="hb-reference-art hb-composite-art" src="assets/es-app-voltage-menu.png"/></div></figure>

<ol start="3"><li>Pulsa <img alt="Editar" src="assets/inline-edit.png"/> en la esquina superior derecha. Después, pulsa <img alt="Vincular circuitos" src="assets/inline-link-circuits.png"/> para ajustar el voltaje a 240 V de acuerdo con la conexión real del circuito STS. Finalmente, pulsa <img alt="Guardar" src="assets/inline-save.png"/> para guardar los ajustes.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-voltage-settings" data-source-fragment-sha256="3b0a3650e97c4fd108a147860f561759846892783008ef22dbdb3b9efe690fa9" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-voltage-settings.semantic"><img alt="Ajustar y guardar el voltaje del circuito" class="hb-reference-art hb-composite-art" src="assets/es-app-voltage-settings.png"/></div></figure>

### Editar el nombre del circuito

<ol><li>Pulsa 'circuitos' en la página principal del STS para entrar en la página principal de circuitos.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuit-list" data-source-fragment-sha256="3a13b01cdc1ddec134ec0501744c659aff5329526771faf0bb6d7925acb92e9e" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-circuit-list.semantic"><img alt="Seleccionar un circuito" class="hb-reference-art hb-composite-art" src="assets/es-app-circuit-list.png"/></div></figure>

<ol start="2"><li>Selecciona el circuito deseado y pulsa <img alt="Editar el nombre del circuito" src="assets/inline-edit-name.png"/> para editar su nombre.</li></ol>

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuit-name" data-source-fragment-sha256="bfb44f80e9e9aec68148bd2e63f43a35cf863a6572e0c0bca6fe3b5639546eaf" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="app-circuit-name.semantic"><img alt="Editar el nombre del circuito" class="hb-reference-art hb-composite-art" src="assets/es-app-circuit-name.png"/></div></figure>

<span id="native-app-quick-start"></span>

## GUÍA DE INICIO RÁPIDO DE LA APLICACIÓN JACKERY

### Tablero

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-dashboard" data-source-fragment-sha256="488d7aa77a885de9908c8e9e65c6bcd210c9652e60b15d828acb5cffee8db5b0"><div class="hb-reference-semantic" data-reference-id="app-dashboard.semantic"><img alt="Tablero" class="hb-reference-art hb-composite-art" src="assets/es-app-dashboard.png"/></div></figure>

<p>Observe y monitoree el consumo eléctrico en tiempo real del hogar, la estación de energía y la red.<br/>Consulte la fuente de energía actual del hogar. Cambie manualmente la fuente de energía del hogar a la estación de energía bajo las siguientes condiciones:</p>

<ol><li>La batería de la estación de energía supera la reserva de respaldo.</li><li>El modo «Solo Respaldo» está desactivado. Generación de energía solar diaria y consumo eléctrico del hogar.</li></ol>

### Circuitos

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-circuits" data-source-fragment-sha256="10504f7e72b77c10ad0043e539cdfbedf873031b1b2f9abb04f7f4486a2502f4"><div class="hb-reference-semantic" data-reference-id="app-circuits.semantic"><img alt="Circuitos" class="hb-reference-art hb-composite-art" src="assets/es-app-circuits.png"/></div></figure>

<p>Encienda o apague manualmente cada circuito doméstico, cámbieles el nombre y consulte el consumo histórico de energía de cada circuito.</p>

### Modos de funcionamiento

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-working-modes" data-source-fragment-sha256="0b96c0bbe047fa5f20479623aa3fefe84879d8ebf3adf1e53856f739d0c241bd"><div class="hb-reference-semantic" data-reference-id="app-working-modes.semantic"><img alt="Modos de funcionamiento" class="hb-reference-art hb-composite-art" src="assets/es-app-working-modes.png"/></div></figure>

### Establecer la reserva de respaldo

<p>Cuando la estación de energía se esté descargando, la batería se descargará hasta alcanzar la reserva de respaldo. Durante un corte de energía, se descargará hasta llegar al límite de descarga (0%). Puede modificar el nivel en Configuraciones &gt; Modos de funcionamiento. *La configuración de reserva de respaldo se puede activar en cualquier modo.<br/>*Durante un corte de energía, el nivel de la reserva de respaldo se descargará a 0% en cualquier modo.</p>

### Modo de carga automática

<p>Se utiliza comúnmente para la energía de respaldo doméstica diaria. <strong>La estación de energía se recargará automáticamente al 100% cuando AC1 o AC2 estén por debajo de la reserva de respaldo.</strong></p>

#### Modo autoalimentación

<p>Aproveche al máximo la energía solar para su hogar.<br/>En este modo, la estación de energía se carga exclusivamente con energía solar. Dos horas después de alcanzar la carga completa, empezará a suministrar energía al hogar. Si no está completamente cargada, solo suministrará energía al hogar durante la noche.</p>

#### *Plan de carga y descarga

<p>Idóneo para situaciones con tarifas eléctricas fluctuantes, ya que permite planes de carga y descarga según las horas de mayor y menor consumo eléctrico, lo que reduce los costes de electricidad.<br/>Función de carga: Establece el período de carga.<br/>Función de descarga: Establece el período de descargar. En este período, si las baterías exceden la reserva de respaldo, se descargarán.<br/>Cuando la estación de energía está conectada al Smart Transfer Switch, desactiva temporalmente el Modo de ahorro de batería, el Apagado automático, el Modo de ahorro de energía, el Modo de carga silenciosa y el Plan de carga.</p>

### Modo respaldo

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-backup-only" data-source-fragment-sha256="b99732debf93e9ec9be402e32dfa82cb86eb4d56dd19eaa01a9797a750bfaeac"><div class="hb-reference-semantic" data-reference-id="app-backup-only.semantic"><img alt="Modo respaldo" class="hb-reference-art hb-composite-art" src="assets/es-app-backup-only.png"/></div></figure>

<p>Cuando se habilita el modo de solo respaldo, la red eléctrica suministrará energía al hogar mientras carga la estación de energía por completo, la cual solo suministrará energía durante un corte de energía. El plan de carga-descarga y el modo autoalimentación se desactivarán temporalmente. El cambio manual a la estación de energía no está disponible en modo de solo reserva.</p>

### Prioridad de respaldo

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-backup-priority" data-source-fragment-sha256="260d312502c70d5cbb5d999936f0e770ba74234c4e5ad015e38af0b339428067"><div class="hb-reference-semantic" data-reference-id="app-backup-priority.semantic"><img alt="Prioridad de respaldo" class="hb-reference-art hb-composite-art" src="assets/es-app-backup-priority.png"/></div></figure>

<p>Durante un corte de energía, el sistema prioriza el suministro de energía de batería a los circuitos domésticos. Clasifique sus circuitos domésticos en 3 niveles: necesarios, deseables, y sin suministro de energía. Prioridades de circuitos</p>

<ol><li>Circuitos esenciales: mientras haya energía en las baterías, se suministrará a estos circuitos.</li><li>Circuitos deseables: estos circuitos recibirán energía cuando el nivel de batería sea igual o superior al porcentaje que se haya establecido.</li><li>Circuitos no prioritarios: estos circuitos no recibirán energía cuando se utilice la batería durante un corte de energía.</li></ol>

### Modo UPS

<figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="app-ups-mode" data-source-fragment-sha256="3259b17bc956b714ce3a9830351b0f5a4475075b382279ba91f463f80b3e71a0"><div class="hb-reference-semantic" data-reference-id="app-ups-mode.semantic"><img alt="Modo UPS" class="hb-reference-art hb-composite-art" src="assets/es-app-ups-mode.png"/></div></figure>

<p>Cuando el modo UPS está activado, si se produce un corte de energía, el STS cambiará automáticamente al suministro de la estación de energía dentro de 20 ms. Si el STS está cargando la estación de energía en ese momento, el tiempo de conmutación será superior a 20 ms y, una vez se restablezca la energía, cambiará automáticamente al suministro de la red eléctrica.<br/>En modo sin UPS, el tiempo de conmutación es de aproximadamente 5 segundos solo si la estación de energía está encendida.<br/>*El STS permanecerá encendido cuando esté conectado a la estación de energía, por lo que se recomienda no apagarla manualmente.</p>

<span id="native-warranty"></span>

## GARANTÍA

<figure aria-label="GARANTÍA" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel">Solo ofrecemos nuestra garantía a clientes que compren a través del sitio web oficial de Jackery, plataformas de terceros de marca Jackery o distribuidores locales autorizados.</div><div class="hb-warranty-local-note">*El período de garantía y los detalles pueden variar según las leyes, regulaciones y distribuidores autorizados locales.</div></figure>

### Garantía Limitada

<figure aria-label="Garantía Limitada" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantiza al comprador consumidor original que el producto de Jackery estará libre de defectos de fabricación y material bajo uso normal durante el período de garantía aplicable identificado en la sección 'Período de Garantía' a continuación, sujeto a las exclusiones establecidas a continuación.<br/>Esta declaración de garantía establece la obligación total y exclusiva de garantía de Jackery. No asumiremos, ni autorizaremos a nadie a asumir por nosotros, ninguna otra responsabilidad en relación con la venta de nuestros productos.</p></figure>

### Período de Garantía

<figure aria-label="Período de Garantía" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="2"><p>Garantía Estándar de 5 Años: El período de garantía estándar para Jackery Smart Transfer Switch es de 5 años. En cada caso, el período de garantía se mide a partir de la fecha de compra por el comprador consumidor original. Se requiere el recibo de venta de la primera compra del consumidor u otra prueba documental razonable para establecer la fecha de inicio del período de garantía.</p></figure>

### Reparación o reemplazo

<figure aria-label="Reparación o reemplazo" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery reparará o reemplazará (a expensas de Jackery) cualquier producto de Jackery que no funcione durante el período de garantía aplicable debido a un defecto de fabricación o material. El producto reparado/reemplazado asume la garantía restante de la fecha de compra original.</p></figure>

### Limitada al Comprador Consumidor Original

<figure aria-label="Limitada al Comprador Consumidor Original" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantía del producto de Jackery está limitada al comprador consumidor original y no es transferible a ningún propietario posterior.</p></figure>

### Exclusiones

<figure aria-label="Exclusiones" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantía de Jackery no se aplica a:<br/>Mal uso, abuso, modificaciones, daños por accidente o uso para algo diferente al uso normal del consumidor autorizado en la documentación actual del producto de Jackery.<br/>Reparaciones intentadas por alguien que no sea de una instalación autorizada.<br/>Cualquier producto comprado a través de una casa de subastas en línea.<br/>La garantía de Jackery no se aplica a la celda de batería a menos que la celda de batería esté completamente cargada por usted dentro de los siete días posteriores a la compra del producto y al menos una vez cada 6 meses a partir de entonces.</p></figure>

### Derechos de Interpretación

<figure aria-label="Derechos de Interpretación" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery Inc. se reserva el derecho de interpretación final de la política de postventa anterior.</p></figure>
