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

</style>

<h1 class="hb-preface-heading" id="preface"><span class="hb-preface-region">FR</span> <span>IMPORTANT</span></h1>

<div class="hb-preface-prose"><p>Félicitations pour votre nouveau Jackery Battery Pack. Veuillez lire attentivement ce manuel avant d'utiliser le produit, en particulier les précautions à prendre pour garantir une utilisation correcte du produit. Conservez ce manuel dans un endroit accessible pour pouvoir vous y référer ultérieurement.</p><p>Conformément aux lois et réglementations en vigueur, le droit d'interprétation final de ce document et de tous les documents associés à ce produit appartient à l'entreprise. Bien que tous les efforts aient été déployés pour garantir l'exactitude de ce manuel, Jackery Inc. n'assume aucune responsabilité pour les erreurs qui pourraient y figurer.</p><p>Veuillez noter qu'aucune autre notification ne sera faite en cas de mise à jour, de révision ou de résiliation. Pour la dernière version des manuels du produit, consultez support.jackery.com.</p><p>* Les chiffres sont donnés à titre indicatif uniquement. Veuillez vous référer au produit réel.</p></div>

<span id="safety"></span>

# INFORMATIONS DE SÉCURITÉ IMPORTANTES

<p>Les précautions de base doivent être respectées lors de l'utilisation de ce produit, y compris :</p>

<ul><li>Veuillez lire toutes les instructions avant d'utiliser ce produit.</li><li>Une surveillance délicate est nécessaire lors de l'utilisation de ce produit à proximité d'enfants aﬁn de réduire les risques.</li><li>L'utilisation d'accessoires recommandés ou vendus par des fabricants de produits non professionnels peut entraîner un risque d'électrocution.</li><li>Lorsque le produit n'est pas utilisé, veuillez débrancher l'alimentation de la prise du produit.</li><li>Ne pas démonter le produit, ce qui pourrait entraîner des risques imprévisibles tels qu'un incendie, une explosion ou un choc électrique.</li><li>N'utilisez pas le produit avec des cordons ou des prises endommagés, ou des câbles de sortie d'éviter que la pluie et l'eau ne provoquent un choc électrique.</li><li>Charger le produit dans un endroit bien ventilé et ne pas restreindre la ventilation de quelque manière que ce soit.</li><li>Placez le produit dans un endroit ventilé et sec aﬁn d'éviter que la pluie et l'eau ne provoquent un choc électrique.</li><li>N'exposez pas le produit au feu ou à des températures élevées (sous la lumière directe du soleil ou dans un véhicule soumis à une forte chaleur), ce qui pourrait provoquer des accidents tels qu'un incendie ou une explosion.</li><li>Si ce produit est stocké pendant une longue période (3 mois - 6 mois) alors qu'il n'est plus alimenté, il pourrait même devenir impossible à recharger.</li></ul>

<span id="symbols"></span>

# SIGNIFICATION DES SYMBOLES

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbole</th><th class="hb-symbol-signal-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="AVERTISSEMENT" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">AVERTISSEMENT</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ATTENTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ATTENTION</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures corporelles et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="REMARQUE" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">REMARQUE</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des dommages à l'équipement, une perte de données, une détérioration des performances ou des résultats inattendus.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEILS" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CONSEILS</span></span></td><td class="hb-symbol-signal-meaning-cell">Complémente les informations importantes ou les conseils d'utilisation dans le texte.</td></tr></tbody></table></figure>

<figure aria-label="Safety symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Mlise en garde! Le non-respect des messages d’avertissement peut entraîner des blessures." class="hb-symbol-art" src="assets/symbol-1.svg"/></td><td class="hb-symbol-meaning">Mlise en garde! Le non-respect des messages d’avertissement peut entraîner des blessures.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lire le manuel de l’opérateur" class="hb-symbol-art" src="assets/symbol-2.svg"/></td><td class="hb-symbol-meaning">Lire le manuel de l’opérateur</td></tr><tr><td class="hb-symbol-icon"><img alt="Ne démontez pas le produit." class="hb-symbol-art" src="assets/symbol-3.svg"/></td><td class="hb-symbol-meaning">Ne démontez pas le produit.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ne pas fumer ni utiliser de ﬂamme nue" class="hb-symbol-art" src="assets/symbol-4.svg"/></td><td class="hb-symbol-meaning">Ne pas fumer ni utiliser de ﬂamme nue</td></tr><tr><td class="hb-symbol-icon"><img alt="Les enfants ne sont pas admis" class="hb-symbol-art" src="assets/symbol-5.svg"/></td><td class="hb-symbol-meaning">Les enfants ne sont pas admis</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée." class="hb-symbol-art" src="assets/symbol-6.svg"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères. Il doit être apporté à un point de collecte désigné pour un recyclage approprié. Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit." class="hb-symbol-art" src="assets/symbol-7.png"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères. Il doit être apporté à un point de collecte désigné pour un recyclage approprié. Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit.</td></tr></tbody></table></div></div></figure>

<span id="fcc"></span>

# FCC

<figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc-mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"><div class="line">Cet appareil est conforme à la partie 15 des règles de la FCC. Son fonctionnement est soumis aux deux conditions suivantes :</div><div class="line">(1) cet appareil ne doit pas causer d’interférences nuisibles, et</div><div class="line">(2) cet appareil doit accepter toute interférence reçue, y compris les interférences pouvant entraîner un fonctionnement indésirable.</div></div></div></div><p><strong>REMARQUE :</strong> Cet équipement a été testé et déclaré conforme aux limites concernant les appareils numériques de classe B, conformément à la partie 15 du règlement de la FCC. Ces limites sont conçues pour offrir une protection raisonnable contre les interférences dangereuses dans le cadre d’une installation résidentielle. Cet équipement génère, utilise et émet des ondes radios qui peuvent, si cet équipement n’est pas installé et utilisé conformément aux instructions, perturber les communications radios.</p></div><div class="hb-fcc-column hb-fcc-column-right"><p>Toutefois, il n’y a aucune garantie qu’aucune interférence ne se produise lors d’une installation particulière. Si cet équipement trouble la réception de la radio ou de la télévision, ce qui peut être déterminé en éteignant et en allumant cet équipement, l’utilisateur est encouragé à tenter de corriger ces interférences en essayant une ou plusieurs des mesures suivantes :</p><ul class="simple"><li><p>Réorientez ou déplacez l’antenne de réception.</p></li><li><p>Éloignez l’équipement du récepteur.</p></li><li><p>Connectez l’équipement à une prise d’un autre circuit que celui auquel le récepteur est connecté.</p></li><li><p>Consultez le revendeur ou bien demandez de l’aide à un technicien de radio/télévision expérimenté.</p></li></ul><p><strong>MODIFICATION :</strong> Tout changement ou modification non expressément approuvé par le titulaire de cet appareil pourrait annuler l’autorisation de l’utilisateur à utiliser l’appareil.</p></div></div></figure>

<span id="inbox"></span>

# CONTENU DE LA BOÎTE

<figure aria-label="What's in the box" class="hb-inbox-composition" data-card-count="4" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Battery Pack" class="hb-inbox-art" src="assets/inbox-1.png"/><div class="hb-inbox-label"><p>Jackery Battery Pack</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Câble de rallonge" class="hb-inbox-art" src="assets/inbox-2.png"/><div class="hb-inbox-label"><p>Câble de rallonge</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Documents" class="hb-inbox-art" src="assets/inbox-3.png"/><div class="hb-inbox-label"><p>Documents</p></div></li><li class="hb-inbox-card" data-item-number="4"><img alt="Support vertical" class="hb-inbox-art" src="assets/inbox-4.png"/><div class="hb-inbox-label"><p>Support vertical</p></div></li></ol></figure>

<span id="overview"></span>

# APERÇU DU PRODUIT

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview" data-source-fragment-sha256="d753caa031b21d0d82fa007ef4da83dc82785f723f4230facf5241e96c55f330" data-web-base-art-ref="overview" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="overview.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/overview.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:63%;--hb-y:2%;--hb-width:34%;--hb-height:5%">Port d'extension</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:62%;--hb-y:7%;--hb-width:36%;--hb-height:3%">Entrée:40V-57,6V⎓24A Max</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:62%;--hb-y:10%;--hb-width:36%;--hb-height:3%">Sortie:40V-57,6V⎓50A Max</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:62%;--hb-y:34%;--hb-width:36%;--hb-height:5%">Bouton d'alimentation principale</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:65%;--hb-y:49%;--hb-width:33%;--hb-height:5%">Écran LCD</span></div></div></figure>

<span id="lcd"></span>

# AFFICHAGE LCD

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd" data-source-fragment-sha256="03e21106852d242795966b24aa9810919ea195cada895b83a1562d154766433f" data-web-base-art-ref="lcd" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="lcd.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/lcd.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:8.7534%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:22.8417%;--hb-y:4.22%;--hb-width:2.1667%;--hb-height:5.3299%">2</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:39.3679%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:39.4125%;--hb-y:94.2347%;--hb-width:2.0889%;--hb-height:5.3299%">7</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:10.8057%;--hb-y:95.0695%;--hb-width:2.2%;--hb-height:5.3299%">5</span><span class="hb-reference-live-label" data-source-line="5" style="--hb-x:3.1402%;--hb-y:95.0695%;--hb-width:2.2889%;--hb-height:5.3299%">4</span><span class="hb-reference-live-label" data-source-line="6" style="--hb-x:24.0513%;--hb-y:95.0695%;--hb-width:2.1778%;--hb-height:5.3299%">6</span><span class="hb-reference-live-label" data-source-line="7" style="--hb-x:58.7708%;--hb-y:4.5878%;--hb-width:1.7556%;--hb-height:5.3299%">1</span><span class="hb-reference-live-label" data-source-line="8" style="--hb-x:89.3849%;--hb-y:4.22%;--hb-width:2.1778%;--hb-height:5.3299%">3</span></div></div></figure>

<figure aria-label="LCD indicators" class="hb-lcd-table-composition" data-component-id="HB-TABLE-LCD-ICON" tabindex="0"><table class="hb-lcd-icon-table"><colgroup><col class="hb-lcd-col-number"/><col class="hb-lcd-col-icon"/><col class="hb-lcd-col-name"/><col class="hb-lcd-col-description"/></colgroup><tbody><tr><td class="hb-lcd-number">1</td><td class="hb-lcd-icon"><img alt="Puissance d’Entrée / Temps de Charge Restant" class="hb-lcd-icon-art" src="assets/lcd-icon-1.svg"/></td><td class="hb-lcd-name">Puissance d’Entrée / Temps de Charge Restant</td><td class="hb-lcd-description">Affiche alternativement la puissance d'entrée et le temps de charge restant.</td></tr><tr><td class="hb-lcd-number">2</td><td class="hb-lcd-icon"><img alt="Pourcentage de Batterie Restant" class="hb-lcd-icon-art" src="assets/lcd-icon-2.svg"/></td><td class="hb-lcd-name">Pourcentage de Batterie Restant</td><td class="hb-lcd-description">Affiche le pourcentage de batterie restant.</td></tr><tr><td class="hb-lcd-number">3</td><td class="hb-lcd-icon"><img alt="Puissance de Sortie / Temps de Décharge Restant" class="hb-lcd-icon-art" src="assets/lcd-icon-3.svg"/></td><td class="hb-lcd-name">Puissance de Sortie / Temps de Décharge Restant</td><td class="hb-lcd-description">Affiche alternativement la puissance de sortie et le temps de décharge restant.</td></tr><tr><td class="hb-lcd-number">4</td><td class="hb-lcd-icon"><img alt="Indicateur de charge" class="hb-lcd-icon-art" src="assets/lcd-icon-4.svg"/></td><td class="hb-lcd-name">Indicateur de charge</td><td class="hb-lcd-description"><strong>Allumé :</strong> Le Jackery Battery Pack est en cours de charge. <strong>Éteint :</strong> Le Jackery Battery Pack n'est pas en cours de charge.</td></tr><tr><td class="hb-lcd-number">5</td><td class="hb-lcd-icon"><img alt="Indicateur de Puissance de la Batterie" class="hb-lcd-icon-art" src="assets/lcd-icon-5.svg"/></td><td class="hb-lcd-name">Indicateur de Puissance de la Batterie</td><td class="hb-lcd-description">Le cercle orange indique le niveau de batterie restant.</td></tr><tr><td class="hb-lcd-number">6</td><td class="hb-lcd-icon"><img alt="Entrée CC" class="hb-lcd-icon-art" src="assets/lcd-icon-6.svg"/></td><td class="hb-lcd-name">Entrée CC</td><td class="hb-lcd-description"><strong>Activé :</strong> Le module d'entrée CC Jackery est connecté. <strong>Désactivé :</strong> Le module d'entrée CC Jackery est déconnecté.</td></tr><tr><td class="hb-lcd-number">7</td><td class="hb-lcd-icon"><img alt="Code d’erreur" class="hb-lcd-icon-art" src="assets/lcd-icon-7.svg"/></td><td class="hb-lcd-name">Code d’erreur</td><td class="hb-lcd-description">Une erreur produit s’est produite. Veuillez consulter la section « Dépannage » pour plus de détails.</td></tr></tbody></table></figure>

<span id="operations"></span>

# FONCTIONNEMENT

## MARCHE/ARRÊT

<div class="native-power-panel"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power" data-source-fragment-sha256="123e7f48c81cbbecc9bb5c4942627b804de2bd362e05d91feea4e2cf0a87591a" data-web-base-art-ref="power" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-preserve-art-frame="true" data-reference-id="power.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/power.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:71%;--hb-y:10%;--hb-width:27%;--hb-height:9%">Marche</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:71%;--hb-y:18%;--hb-width:27%;--hb-height:7%">Appuyez une fois</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:71%;--hb-y:29%;--hb-width:27%;--hb-height:9%">Arrêt</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:71%;--hb-y:36%;--hb-width:27%;--hb-height:7%">Appuyez et maintenez pendant 3 secondes</span><span class="hb-reference-live-label" data-source-line="4" style="--hb-x:77%;--hb-y:46%;--hb-width:12%;--hb-height:8%">3s</span></div></div></figure><table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarques</td><td class="manual-callout-body"><p>Le dispositif s’éteint automatiquement s’il n’est pas chargé ou si aucune charge n’est connectée pendant 2 heures.</p></td></tr></tbody></table></div>

## AFFICHAGE LCD MARCHE/ARRÊT

<figure aria-label="AFFICHAGE LCD MARCHE/ARRÊT" class="hb-lcd-mode-composition hb-lcd-mode-portrait" data-component-id="HB-TABLE-LCD-MODE"><div class="hb-lcd-mode-art-panel"><img alt="AFFICHAGE LCD MARCHE/ARRÊT" class="hb-lcd-mode-art" src="assets/lcd-button.png"/></div><div class="hb-lcd-mode-table-panel"><table class="hb-lcd-mode-table"><colgroup><col class="hb-lcd-mode-col-state"/><col class="hb-lcd-mode-col-action"/><col class="hb-lcd-mode-col-copy"/></colgroup><tbody><tr><td class="hb-lcd-mode-state" rowspan="3">Allumer en discontinu</td><td class="hb-lcd-mode-action">Allumer</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d'alimentation principal ou lorsque le produit est en charge.</td></tr><tr><td class="hb-lcd-mode-action">Éteindre</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d'alimentation principal.</td></tr><tr><td class="hb-lcd-mode-action">Arrêt automatique</td><td class="hb-lcd-mode-copy">L'écran LCD s'éteint automatiquement et entre en mode veille après 2 minutes d'inactivité.</td></tr><tr><td class="hb-lcd-mode-state" rowspan="3">Allumer en continu (en cours de charge ou de décharge)</td><td class="hb-lcd-mode-action">Allumer</td><td class="hb-lcd-mode-copy">Appuyez deux fois sur le bouton d'alimentation principal lorsque le produit est allumé.</td></tr><tr><td class="hb-lcd-mode-action">Éteindre</td><td class="hb-lcd-mode-copy">Appuyez sur le bouton d'alimentation principal.</td></tr><tr><td class="hb-lcd-mode-action">Arrêt automatique</td><td class="hb-lcd-mode-copy">Le mode Allumer en continu s'éteint automatiquement après 2 heures d'inactivité.</td></tr></tbody></table></div></figure>

<span id="troubleshooting"></span>

# DÉPANNAGE

<p>Si l'un des codes d'erreur suivants apparaît, suivez les actions correctives indiquées pour résoudre le problème.Si l'erreur persiste, veuillez contacter le service à la clientèle de Jackery.</p>

<figure aria-label="Code d’erreur / Mesures correctives" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Code d’erreur</th><th class="hb-troubleshooting-measures" scope="col">Mesures correctives</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code">F0 / F2 / F3</td><td class="hb-troubleshooting-measures">Redémarrez le produit.</td></tr><tr><td class="hb-troubleshooting-code">F1 / F6 / F7 / F8</td><td class="hb-troubleshooting-measures">Contacter le service à la clientèle de Jackery.</td></tr><tr><td class="hb-troubleshooting-code">F4</td><td class="hb-troubleshooting-measures">Connectez le produit à des charges pour décharger sa batterie jusqu'à ce que l'erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">F5</td><td class="hb-troubleshooting-measures">Chargez le produit via des panneaux solaires ou une prise murale CA jusqu'à ce que l'erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code">FF</td><td class="hb-troubleshooting-measures"><p><strong>En condition de température élevée:</strong></p><ol><li>Débranchez tous les câbles de charge et de décharge du produit (y compris le chargeur mural, les panneaux solaires, le chargeur de voiture et les appareils de charge).</li><li>Placez le produit dans un endroit ombragé et bien ventilé où la température ambiante est inférieure à 113°F (45 °C).</li><li>Maintenez le produit au repos et attendez que le défaut disparaisse.</li><li>Si le défaut persiste après plusieurs tentatives, veuillez contacter le distributeur ou le service à la clientèle de Jackery.</li></ol><p><strong>En condition de basse température:</strong></p><ol><li>Déplacez le produit vers un environnement plus chaud au-dessus de 32°F (0 °C).</li><li>N’utilisez pas et ne rechargez pas le produit à l'extérieur dans des conditions extrêmement froides. Si nécessaire, préchauﬀez-le à l'intérieur.</li><li>Si l'appareil est déplacé de l'extérieur vers l'intérieur depuis un environnement froid, laissez-le reposer un moment avant de l’utiliser.</li><li>Lorsque l'indicateur de basse température apparaît, maintenez le produit au repos et attendez que le système se rétablisse automatiquement.</li><li>Si le défaut persiste après plusieurs tentatives, veuillez contacter le distributeur ou le service à la clientèle de Jackery.</li></ol></td></tr></tbody></table></figure>

<span id="positioning"></span>

# POSITIONNÉ AVEC LE JACKERY FRIDGEGUARD

## DISPOSITION EN PARALLÈLE

<p>Positionnez le Jackery Battery Pack et le Jackery FridgeGuard en une disposition en parallèle.</p>

<div class="hb-reference-figure"><img alt="parallel" class="hb-reference-art" src="assets/parallel.png"/></div>

## EMPILÉ

<p>Placez le Jackery Battery Pack et le Jackery FridgeGuard en pile.</p>

<div class="hb-reference-figure"><img alt="stacked" class="hb-reference-art" src="assets/stacked.png"/></div>

## AVEC SUPPORTS

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">ATTENTION</td><td class="manual-callout-body"><ul><li>N’installez pas le produit sur une structure non porteuse, comme les cloisons en placoplâtre, les murs isolants ou les briques creuses, car le produit pourrait tomber.</li><li>Évitez les fils électriques, les conduites d'eau, les conduites de gaz et autres installations à l'intérieur des murs.</li></ul></td></tr></tbody></table>

<span id="vertical"></span>

# SUPPORT VERTICAL

<p>Le Jackery Battery Pack installé avec le support vertical peut être posé au sol. Veuillez suivre les étapes d'installation ci-dessous:</p>

<p>Préparation avant l'installation:</p>

<div class="native-step-grid"><div class="native-step-card"><div class="hb-reference-figure"><img alt="vertical-prep" class="hb-reference-art" src="assets/vertical-prep.png"/></div></div><div class="native-step-card"><div class="hb-reference-figure"><img alt="Vertical stand installation result" class="hb-reference-art" src="assets/vertical-result.png"/></div></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Retirez deux vis du bas du produit.</p><div class="hb-reference-figure"><img alt="vertical-1" class="hb-reference-art" src="assets/vertical-1.png"/></div></div><div class="native-step-card"><p>2. Alignez les trous de montage sur le bas du produit avec les trous sur le support vertical.</p><div class="hb-reference-figure"><img alt="vertical-2" class="hb-reference-art" src="assets/vertical-2.png"/></div></div><div class="native-step-card"><p>3. Serrez les vis.</p><div class="hb-reference-figure"><img alt="vertical-3" class="hb-reference-art" src="assets/vertical-3.png"/></div></div></div>

<span id="wall-mount"></span>

# JACKERY WALL-MOUNTED BRACKET (VENDUS SÉPARÉMENT)

<p>Le Jackery Battery Pack installé avec le support de montage peut être fixé au mur. Veuillez suivre les étapes d'installation ci-dessous:</p>

## SUR LES MURS EN BOIS

<p>Preparation before installation:</p>

<div class="native-step-grid"><div class="native-step-card"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-prep" data-source-fragment-sha256="9ed9d0b9b227073cc103dd36f25690a550dd5a7e0bf72fd1b31e22b14c49e869" data-web-base-art-ref="wood-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:57%;--hb-y:24%;--hb-width:21%;--hb-height:18%">VENDUS SÉPARÉMENT</span></div></div></figure></div><div class="native-step-card"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-result" data-source-fragment-sha256="129360730940bd03e8d476c10bdf8fca0d60667660354e680473b85b4f9355b1" data-web-base-art-ref="wood-result" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-result.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-result.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:10%;--hb-y:0%;--hb-width:80%;--hb-height:10%">Ossature en bois</span></div></div></figure></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Installez le Jackery FridgeGuard conformément au manuel d'utilisation. 2. Retirez deux vis du bas du produit.</p><div class="hb-reference-figure"><img alt="wood-1-2" class="hb-reference-art" src="assets/wood-1-2.png"/></div></div><div class="native-step-card"><p>3. Fixez solidement les supports de montage supérieur et inférieur à l'arrière du produit.</p><div class="hb-reference-figure"><img alt="wood-3" class="hb-reference-art" src="assets/wood-3.png"/></div></div><div class="native-step-card"><p>4. Utilice un buscador de montantes para identificar los montantes de madera detrás de la pared.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-4" data-source-fragment-sha256="55cdbf5c89891820f4ca74adc5e421e1690c91a5f1d883953bd8a4d5b1c7f569" data-web-base-art-ref="wood-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65%;--hb-y:32%;--hb-width:32%;--hb-height:11%">Ossature en bois</span></div></div></figure></div><div class="native-step-card"><p>5. Mesurez une distance horizontale de 406 mm (16 po) à partir de la position du boulon sur le Jackery FridgeGuard, et marquez le point de montage sur le montant de bois du mur.</p><p>* 406 mm (16 po) est la distance recommandée, et la distance réelle dépend des conditions du mur.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-5" data-source-fragment-sha256="4e6338802f7198c21d5237c33e746c8a676ead2fc0b6945e9ef6c9c01d1b1805" data-web-base-art-ref="wood-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:33.5914%;--hb-y:21.1809%;--hb-width:16.2108%;--hb-height:7.557%">Ossature en bois</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:58.5429%;--hb-y:20.5752%;--hb-width:16.2108%;--hb-height:7.557%">Ossature en bois</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:44.8879%;--hb-y:40.1803%;--hb-width:19.0607%;--hb-height:7.557%">406 mm (16 po)</span><span class="hb-reference-live-label" data-source-line="3" style="--hb-x:4.6084%;--hb-y:67.2917%;--hb-width:25.3171%;--hb-height:7.557%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>6. Enfoncez la vis à bois dans le mur au point de montage, en laissant un espace de 2-4 mm entre la vis et le mur.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="wood-6" data-source-fragment-sha256="414a2e5bf010610403b51c9544e7a14807805764b3eda8a86993e6b6885526fa" data-web-base-art-ref="wood-6" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="wood-6.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/wood-6.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:66.3707%;--hb-y:31.4483%;--hb-width:13.4462%;--hb-height:9.2069%">2~4mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:44.5016%;--hb-y:21.3514%;--hb-width:16.2108%;--hb-height:9.2069%">Ossature en bois</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:1.9525%;--hb-y:39.2574%;--hb-width:22.2641%;--hb-height:8.1724%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>7. Accrochez le produit verticalement sur la vis. Enfoncez la vis auto-taraudeuse à travers le trou de montage du support inférieur dans le mur et serrez-la. Ensuite, serrez complètement la vis à bois.</p><div class="hb-reference-figure"><img alt="wood-7" class="hb-reference-art" src="assets/wood-7.png"/></div></div></div>

## SUR LES MURS EN BÉTON

<p>Préparation avant l'installation:</p>

<div class="native-step-grid"><div class="native-step-card"><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-prep" data-source-fragment-sha256="74b7e91766c47d0bb5af118d5a55141ba5787aa073b9a5859879377f1dfd9b31" data-web-base-art-ref="concrete-prep" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-prep.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-prep.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:54%;--hb-y:27%;--hb-width:25%;--hb-height:18%">VENDUS SÉPARÉMENT</span></div></div></figure></div><div class="native-step-card"><div class="hb-reference-figure"><img alt="concrete-result" class="hb-reference-art" src="assets/concrete-result.png"/></div></div></div>

<div class="native-step-grid"><div class="native-step-card"><p>1. Installez le Jackery FridgeGuard conformément au manuel d'utilisation. 2. Retirez deux vis du bas du produit.</p><div class="hb-reference-figure"><img alt="concrete-1-2" class="hb-reference-art" src="assets/concrete-1-2.png"/></div></div><div class="native-step-card"><p>3. Fixez solidement les supports de montage supérieur et inférieur à l'arrière du produit.</p><div class="hb-reference-figure"><img alt="concrete-3" class="hb-reference-art" src="assets/concrete-3.png"/></div></div><div class="native-step-card"><p>4. Mesurez une distance horizontale de 406 mm (16 po) à partir de la position du boulon sur le Jackery FridgeGuard, et marquez le point de montage sur le montant de bois du mur.</p><p>* 406 mm (16 po) est la distance recommandée, et la distance réelle dépend des conditions du mur.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-4" data-source-fragment-sha256="f991bc8f9293b3c809e19ee9fbbeb3c0a0e49463c43cfa5d6b3b7eed127a5ebd" data-web-base-art-ref="concrete-4" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-4.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-4.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:24%;--hb-y:30%;--hb-width:31%;--hb-height:7%">406 mm (16 po)</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:41%;--hb-y:78%;--hb-width:55%;--hb-height:7%">Jackery FridgeGuard</span></div></div></figure></div><div class="native-step-card"><p>5. Percez un trou au point de montage à l'aide d'une perceuse à percussion pour maçonnerie de 8 mm, jusqu'à une profondeur d'environ 70 mm. Insérez une cheville d'expansion et desserrez son écrou de 2 à 4 mm.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-5" data-source-fragment-sha256="c0c60625d2ef6a1ea7b4fa5a4a61d36e0fd0ab71e593053c9907f6fc16b1bf98" data-web-base-art-ref="concrete-5" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-5.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-5.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:52%;--hb-y:41%;--hb-width:21%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:45%;--hb-y:73%;--hb-width:24%;--hb-height:7%">2~4mm</span><span class="hb-reference-live-label" data-source-line="2" style="--hb-x:72%;--hb-y:52%;--hb-width:23%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-step-card"><p>6. Accrochez le produit verticalement sur la cheville d'expansion et marquez le point de montage sur le mur.</p><div class="hb-reference-figure"><img alt="concrete-6" class="hb-reference-art" src="assets/concrete-6.png"/></div></div><div class="native-step-card"><p>7. Retirez le produit. Percez un trou au point de montage et insérez une cheville d'expansion sans écrou ni rondelle dans le trou.</p><figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="concrete-7" data-source-fragment-sha256="e9b8f2a12516dd6c38815f9d180d037acc45d3b1908a69418abd6f0103020a04" data-web-base-art-ref="concrete-7" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="concrete-7.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/concrete-7.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:61%;--hb-y:39%;--hb-width:24%;--hb-height:7%">70mm</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:75%;--hb-y:50%;--hb-width:20%;--hb-height:7%">8mm</span></div></div></figure></div><div class="native-step-card"><p>8. Accrochez le produit sur la cheville d'expansion supérieure.</p><div class="hb-reference-figure"><img alt="concrete-8" class="hb-reference-art" src="assets/concrete-8.png"/></div></div><div class="native-step-card"><p>9. Soulevez le produit pour aligner le boulon préinstallé et abaissez-le en place. Serrez l'écrou.</p><div class="hb-reference-figure"><img alt="concrete-9" class="hb-reference-art" src="assets/concrete-9.png"/></div></div></div>

<span id="connections"></span>

# CONNEXIONS

<p>Le Jackery Battery Pack peut être utilisée avec le Jackery FridgeGuard pour répondre aux besoins de capacité accrus.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">IMPORTANT</td><td class="manual-callout-body"><p>Assurez-vous que tous les produits sont éteints avant de connecter le Jackery FridgeGuard au(x) Jackery Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="connections" class="hb-reference-art" src="assets/connections.png"/></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarques</td><td class="manual-callout-body"><p>L’apparition de l’icône <img alt="" class="native-inline-pack" src="assets/connection-icon.svg"/> sur l’écran LCD (Jackery FridgeGuard) signifie que la connexion entre l’unité de batterie et le Jackery FridgeGuard est réussie.</p></td></tr></tbody></table>

<span id="charging"></span>

# CHARGE

## CHARGEMENT PAR PRISE MURALE CA

<p>En cas de charge murale, ce dispositif doit être utilisé avec le Jackery FridgeGuard.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Avertissement</td><td class="manual-callout-body"><p>Assurez-vous que tous les produits sont éteints avant de connecter le Jackery FridgeGuard au(x) Battery Pack.</p></td></tr></tbody></table>

<div class="hb-reference-figure"><img alt="ac" class="hb-reference-art" src="assets/ac.png"/></div>

## CHARGEMENT PAR PANNEAUX SOLAIRES (VENDU SÉPARÉMENT)

<p>Rechargez votre dispositif à l’aide de panneaux solaires et du Jackery DC Input Module(Vendu séparément), comme indiqué dans la figure ci-dessous. Pour plus d’informations, veuillez vous reporter au manuel d’utilisation du Jackery DC Input Module.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar" data-source-fragment-sha256="f22437451b71c691729af99ef4443af2145b0d02b6d23ae7128a0012024e57d7" data-web-base-art-ref="solar" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="solar.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/solar.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:23.2139%;--hb-y:51.0353%;--hb-width:14.2673%;--hb-height:5.1953%">SolarSaga 500 X</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:57.8558%;--hb-y:76.2323%;--hb-width:8.3319%;--hb-height:5.1953%">DC8020</span></div></div></figure>

## CHARGEMENT PAR PRISE DE VOITURE(VENDU SÉPARÉMENT)

<p>Chargez votre produit avec le chargeur de voiture et le Jackery DC Input Module(Vendu séparément) comme indiqué dans la figure ci-dessous. Veuillez consulter le manuel d'utilisation du Jackery DC Input Module pour plus d'informations.</p>

<figure class="hb-reference-figure hb-base-art-live-copy" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="car" data-source-fragment-sha256="333ad48bebbfb72488e7f798422d80b57a3675d24a3e639ac73df62121c89d42" data-web-base-art-ref="car" data-web-presentation-mode="base-art-live-copy"><div class="hb-reference-semantic" data-mobile-labels="overlay" data-preserve-art-frame="true" data-reference-id="car.semantic"><div class="hb-reference-art-panel" style="--hb-panel-top:0%;--hb-panel-fill:#ffffff"><img alt="" class="hb-reference-art hb-composite-art" src="assets/car.png"/><span class="hb-reference-live-label" data-source-line="0" style="--hb-x:65%;--hb-y:14%;--hb-width:25%;--hb-height:9%">Vehícule</span><span class="hb-reference-live-label" data-source-line="1" style="--hb-x:30%;--hb-y:63%;--hb-width:20%;--hb-height:9%">DC8020</span><span class="hb-reference-live-label hb-reference-live-pill" data-source-line="2" style="--hb-x:53%;--hb-y:65%;--hb-width:43%;--hb-height:18%;--hb-fill:#f2f2f2">※ Le câble de chargement de voiture est vendu séparément.</span></div></div></figure>

<span id="storage"></span>

# STOCKAGE

<p>Conservez le produit dans un endroit propre et sec avec une ventilation adéquate.Température et humidité de stockage :</p>

<ul><li>1 mois : -4°F à 113°F / -20 à 45°C (0-60% HR)</li><li>3 mois : 32°F à 113°F / 0 à 45°C (0-60% HR)</li><li>2 mois : 32°F à 77°F / 0 à 25°C (0-60% HR)</li></ul>

<p>Si ce produit est stocké pendant une longue période (3 à 6 mois) avec la batterie déchargée, il peut devenir impossible de le recharger. Pour éviter cela et préserver la santé de la batterie, il est recommandé de vérifier et de recharger le produit tous les trois mois, et d'effectuer un cycle de charge et de décharge complet au moins une fois tous les 6 à 12 mois.</p>

<span id="specifications"></span>

# SPÉCIFICATIONS

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JBP-1000B-SIL</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">20Ah / 51,2Vdc (1024 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cellule Chimique</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 19,8 lbs / 9 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">23,6 × 12,8 × 2,4 pouces/60 × 32,5 × 6 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 6000 cycles à 70 % ou plus</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS D’ENTRÉE/SORTIE</h2>

<figure aria-label="PORTS D’ENTRÉE/SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">40V-57,6V⎓24A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">40V-57,6V⎓50A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1250A/1.55ms</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPÉRATURE DE FONCTIONNEMENT</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">-4°F à 113°F / -20°C à 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-4°F à 113°F / -20°C à 45°C</td></tr></tbody></table></figure>

<span id="warranty"></span>

# GARANTIE

<figure aria-label="Warranty" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel">Nous ne fournissons notre garantie qu'aux clients qui achètent sur le site officiel de Jackery, sur des plateformes tierces portant la marque Jackery, ou auprès de revendeurs autorisés locaux.</div><div class="hb-warranty-local-note">* La durée et les détails de la garantie peuvent varier en fonction des lois, réglementations et revendeurs autorisés locaux.</div></figure>

## Garantie limitée

<figure aria-label="Garantie limitée" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantit à l'acheteur et consommateur d'origine que le produit de Jackery sera exempt de tout défaut de fabrication et de matériaux dans le cadre d'une utilisation normale pendant toute la durée de la période de garantie applicable identifiée dans la section « Période de garantie » ci-dessous, sous réserve des exceptions énoncées ci-dessous.</p><p>Cette déclaration de garantie énonce les obligations totales et exclusives de garantie de Jackery. Nous n'assumerons pas et nous n'autorisons personne à assumer pour nous toute autre responsabilité en lien avec la vente de nos produits.</p></figure>

## Période de garantie

<figure aria-label="Période de garantie" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 ANS Garantie standard" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie standard</strong></div></div><div class="hb-warranty-period-copy">La période de garantie standard du Jackery Battery Pack est de 36 mois. Dans tous les cas, la période de garantie commence à compter de la date d'achat par l'acheteur et consommateur d'origine. La facture du premier achat du consommateur ou toute autre preuve documentaire raisonnable est nécessaire afin d'établir la date de début de la période de garantie.</div></div><div aria-label="2 ANS Garantie prolongée" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie prolongée</strong></div></div><div class="hb-warranty-period-copy">Pour activer l'extension de garantie, vous devez enregistrer votre produit en ligne ou bien contacter notre service client à hello@jackery.com afin de prolonger la durée de la garantie standard.</div></div></div></figure>

## Réparation ou remplacement

<figure aria-label="Réparation ou remplacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery réparera ou remplacera (aux frais de Jackery) tout produit Jackery qui cesse de fonctionner pendant la période de garantie applicable en raison d'un défaut de fabrication ou de matériau. Le produit réparé ou remplacé bénéficie de la garantie restante de la date d'achat d'origine.</p></figure>

## Limitée à l'acheteur et consommateur d'origine

<figure aria-label="Limitée à l'acheteur et consommateur d'origine" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>La garantie d'un produit Jackery est limitée à l'acheteur et consommateur d'origine, elle ne peut pas être transférée à un autre propriétaire.</p></figure>

## Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantie de Jackery ne s'applique pas à :</p><ul><li>Une utilisation incorrecte, abusée, modifiée, aux dégâts provoqués par un accident ou toute autre utilisation qui n'est pas une utilisation normale de ce produit et autorisée par la documentation actuelle du produit de Jackery.</li><li>À une réparation tentée par quelqu'un d'autre qu'un établissement agréé.</li><li>Tout autre produit acheté par l'intermédiaire d'une vente aux enchères en ligne.</li><li>La garantie de Jackery ne s'applique pas aux cellules de la batterie, sauf si vous avez entièrement chargé les cellules de la batterie dans les sept jours suivant l'achat du produit et au moins une fois tous les 6 mois par la suite.</li></ul></figure>

## Droits d'interprétation

<figure aria-label="Droits d'interprétation" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery Inc. se réserve le droit d'interpréter de manière définitive la politique après-vente des clients ci-dessus.</p></figure>

<span id="contact"></span>

# JACKERY INC.

<p>5310 Bunche Dr., Fremont, CA 94538-8301</p>

<p>hello@jackery.com www.jackery.com 1-888-502-2236 (US)</p>
