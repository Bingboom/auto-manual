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

## INFORMATIONS DE SÉCURITÉ IMPORTANTES

<p><strong>Les précautions de base doivent être respectées lors de l'utilisation de ce produit, y compris :</strong></p>

<p>Veuillez lire toutes les instructions avant d'utiliser ce produit.<br/>Une surveillance délicate est nécessaire lors de l'utilisation de ce produit à proximité d'enfants afin de réduire les risques.<br/>L'utilisation d'accessoires recommandés ou vendus par des fabricants de produits non professionnels peut entraîner un risque d'électrocution.<br/>Lorsque le produit n'est pas utilisé, veuillez débrancher l'alimentation de la prise du produit.<br/>Ne pas démonter le produit, ce qui pourrait entraîner des risques imprévisibles tels qu'un incendie, une explosion ou un choc électrique.<br/>N'utilisez pas le produit avec des cordons ou des prises endommagés, ou des câbles de sortie endommagés, ce qui pourrait provoquer un choc électrique.<br/>Charger le produit dans un endroit bien ventilé et ne pas restreindre la ventilation de quelque manière que ce soit.<br/>Placez le produit dans un endroit ventilé et sec afin d'éviter que la pluie et l'eau ne provoquent un choc électrique.<br/>N'exposez pas le produit au feu ou à des températures élevées (sous la lumière directe du soleil ou dans un véhicule soumis à une forte chaleur), ce qui pourrait provoquer des accidents tels qu'un incendie ou une explosion.</p>

<span id="native-symbols"></span>

## SIGNIFICATION DES SYMBOLES

<figure aria-label="Signal words" class="hb-symbol-signal-composition" data-component-id="HB-TABLE-SYMBOL-SIGNAL"><table class="hb-symbol-signal-table"><colgroup><col class="hb-symbol-signal-col-label"/><col class="hb-symbol-signal-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-signal-label-heading" scope="col">Symbole</th><th class="hb-symbol-signal-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-signal-label-cell"><span aria-label="AVERTISSEMENT" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">AVERTISSEMENT</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures graves, la mort et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="ATTENTION" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">ATTENTION</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des blessures corporelles et/ou des dommages matériels.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="REMARQUE" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">REMARQUE</span></span></td><td class="hb-symbol-signal-meaning-cell">Pratiques dangereuses pouvant entraîner des dommages à l'équipement, une perte de données, une détérioration des performances ou des résultats inattendus.</td></tr><tr><td class="hb-symbol-signal-label-cell"><span aria-label="CONSEILS" class="hb-signal-badge"><span aria-hidden="true" class="hb-signal-icon">⚠</span><span class="hb-signal-label">CONSEILS</span></span></td><td class="hb-symbol-signal-meaning-cell">Complémente les informations importantes ou les conseils d'utilisation dans le texte.</td></tr></tbody></table></figure>

<figure aria-label="Meaning of symbols" class="hb-symbol-pair-composition" data-component-id="HB-TABLE-SYMBOL-ICON"><div class="hb-symbol-pair-grid"><div class="hb-symbol-panel hb-symbol-panel-1"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Mlise en garde! Le non-respect des messages d'avertissement peut entraîner des blessures." class="hb-symbol-art" src="assets/symbol_warning_triangle.svg"/></td><td class="hb-symbol-meaning">Mlise en garde! Le non-respect des messages d'avertissement peut entraîner des blessures.</td></tr><tr><td class="hb-symbol-icon"><img alt="Lire le manuel de l'opérateur" class="hb-symbol-art" src="assets/symbol_read_manual.svg"/></td><td class="hb-symbol-meaning">Lire le manuel de l'opérateur</td></tr><tr><td class="hb-symbol-icon"><img alt="Risque de choc électrique" class="hb-symbol-art" src="assets/symbol_electric_shock.svg"/></td><td class="hb-symbol-meaning">Risque de choc électrique</td></tr><tr><td class="hb-symbol-icon"><img alt="Chargement de la batterie" class="hb-symbol-art" src="assets/symbol_battery_charging.svg"/></td><td class="hb-symbol-meaning">Chargement de la batterie</td></tr><tr><td class="hb-symbol-icon"><img alt="Matière explosive" class="hb-symbol-art" src="assets/symbol_explosive_material_native_v2_3e3a39.svg"/></td><td class="hb-symbol-meaning">Matière explosive</td></tr><tr><td class="hb-symbol-icon"><img alt="Objet lourd" class="hb-symbol-art" src="assets/symbol_heavy_object.svg"/></td><td class="hb-symbol-meaning">Objet lourd</td></tr></tbody></table></div><div class="hb-symbol-panel hb-symbol-panel-2"><table class="hb-symbol-panel-table"><colgroup><col class="hb-symbol-col-icon"/><col class="hb-symbol-col-meaning"/></colgroup><thead><tr><th class="hb-symbol-icon-heading" scope="col">Symbole</th><th class="hb-symbol-meaning-heading" scope="col">Signification</th></tr></thead><tbody><tr><td class="hb-symbol-icon"><img alt="Ne démontez pas le produit." class="hb-symbol-art" src="assets/screwdriver-prohibited-tw-477dfbd7.svg"/></td><td class="hb-symbol-meaning">Ne démontez pas le produit.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ne pas fumer ni utiliser de flamme nue" class="hb-symbol-art" src="assets/symbol_no_open_flame.svg"/></td><td class="hb-symbol-meaning">Ne pas fumer ni utiliser de flamme nue</td></tr><tr><td class="hb-symbol-icon"><img alt="Les enfants ne sont pas admis" class="hb-symbol-art" src="assets/symbol_keep_away_from_children.svg"/></td><td class="hb-symbol-meaning">Les enfants ne sont pas admis</td></tr><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée." class="hb-symbol-art" src="assets/symbol_li_ion_htp017.svg"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit contient une batterie lithium-ion (Li-ion), qui doit être éliminée ou recyclée de manière appropriée.</td></tr><tr><td class="hb-symbol-icon"><img alt="Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères. Il doit être apporté à un point de collecte désigné pour un recyclage approprié. Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit." class="hb-symbol-art" src="assets/symbol_weee.png"/></td><td class="hb-symbol-meaning">Ce symbole indique que le produit ne doit pas être jeté avec les ordures ménagères.<br/>Il doit être apporté à un point de collecte désigné pour un recyclage approprié.<br/>Une élimination et un recyclage corrects contribuent à la protection de l’environnement. Pour plus d’informations, veuillez contacter votre autorité locale, le service de gestion des déchets ou le revendeur du produit.</td></tr></tbody></table></div></div></figure>

<div class="native-fcc"><figure aria-label="FCC" class="hb-fcc-composition" data-component-id="HB-SPECIAL-FCC"><div class="hb-fcc-grid"><div class="hb-fcc-column hb-fcc-column-left"><div class="hb-fcc-opening"><img alt="FCC" class="hb-fcc-mark" loading="lazy" src="assets/fcc_mark.svg"/><div class="hb-fcc-opening-copy"><div class="line-block"></div></div></div><p><strong>REMARQUE :</strong> Cet équipement a été testé et déclaré conforme aux limites concernant les appareils numériques de classe B, conformément à la partie 15 du règlement de la FCC. Ces limites sont conçues pour offrir une protection raisonnable contre les interférences dangereuses dans le cadre d'une installation résidentielle. Cet équipement génère, utilise et émet des ondes radios qui peuvent, si cet équipement n'est pas installé et utilisé conformément aux instructions, perturber les communications radios. Toutefois, il n'y a aucune garantie qu'aucune interférence ne se produise lors d'une installation particulière. Si cet équipement trouble la réception de la radio ou de la télévision, ce qui peut être déterminé en éteignant et en allumant cet équipement, l'utilisateur est encouragé à tenter de corriger ces interférences en essayant une ou plusieurs des mesures suivantes :</p></div><div class="hb-fcc-column hb-fcc-column-right"><ul class="simple"><li><p>Réorientez ou déplacez l'antenne de réception.</p></li><li><p>Éloignez l'équipement du récepteur.</p></li><li><p>Connectez l'équipement à une prise d'un autre circuit que celui auquel le récepteur est connecté.</p></li><li><p>Consultez le revendeur ou bien demandez de l'aide à un technicien de radio/télévision expérimenté.</p></li></ul><p><strong>MODIFICATION:</strong> Tout changement ou modification non expressément approuvé par le titulaire de cet appareil pourrait annuler l'autorisation de l'utilisateur à utiliser l'appareil.</p></div></div></figure></div>

<span id="native-in-the-box"></span>

## CONTENU DE LA BOÎTE

<figure aria-label="CONTENU DE LA BOÎTE" class="hb-inbox-composition" data-card-count="3" data-component-id="HB-SPECIAL-INBOX" data-inbox-variant="responsive-card-grid"><ol class="hb-inbox-grid"><li class="hb-inbox-card" data-item-number="1"><img alt="Jackery Battery Pack 3600" class="hb-inbox-art" src="assets/fr-inbox-unit.png"/><div class="hb-inbox-label"><p>Jackery Battery Pack 3600</p></div></li><li class="hb-inbox-card" data-item-number="2"><img alt="Câble de rallonge" class="hb-inbox-art" src="assets/fr-inbox-cable.png"/><div class="hb-inbox-label"><p>Câble de rallonge</p></div></li><li class="hb-inbox-card" data-item-number="3"><img alt="Manuel d’utilisation" class="hb-inbox-art" src="assets/fr-inbox-manual.png"/><div class="hb-inbox-label"><p>Manuel d’utilisation</p></div></li></ol></figure>

<span id="native-product-overview"></span>

## APERÇU DU PRODUIT

### VUE DE FACE

<div class="native-figure native-overview-front native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-front" data-source-fragment-sha256="3b8a386afe760754d905aeaf227db833f579ca615ea7ea8563a1e4fe907eeb37" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-front.semantic"><img alt="Front view: LCD display and POWER button" class="hb-reference-art hb-composite-art" src="assets/fr-overview-front.png"/></div></figure></div>

### VUE LATÉRALE GAUCHE

<div class="native-figure native-overview-left native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="overview-left" data-source-fragment-sha256="bfcc1c09df1ca41e5f77386db0c28da3ea8d4833398e80e819d1989aefe1fa5f" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="overview-left.semantic"><img alt="Left side view: handle, DC Expansion Port A (connect to Expansion Cable Terminal A) and DC Expansion Port B (connect to Expansion Cable Terminal B)" class="hb-reference-art hb-composite-art" src="assets/fr-overview-left.png"/></div></figure></div>

<span id="native-lcd-display"></span>

## AFFICHAGE LCD

<div class="native-figure native-lcd-display native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-display" data-source-fragment-sha256="afbd65d1b59ea63a74a80c875eac7c6073098ecea14355586605cec61d9956d4" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="lcd-display.semantic"><img alt="LCD display: power percentage or fault code, and the charging indicator" class="hb-reference-art hb-composite-art" src="assets/fr-lcd-display.png"/></div></figure></div>

<figure aria-label="AFFICHAGE LCD" class="hb-reference-composition hb-reference-lcd-descriptions" data-component-id="HB-TABLE-REFERENCE" data-component-variant="lcd-descriptions" tabindex="0"><table class="hb-reference-table"><tbody><tr><td><strong>Pourcentage de</strong><br/><strong>puissance/code</strong><br/><strong>d’erreur</strong></td><td>L’affichage de la puissance représente le pourcentage de la valeur actuelle de la puissance. En cas de défaillance du système, le code d’erreur correspondant (F0-FF) s’affiche. Si le code FF s’affiche, retirez la charge et le dispositif peut se rétablir de lui-même. Si ce n'est pas le cas, veuillez contacter le service à la clientèle de Jackery. Si un autre code apparaît, veuillez contacter notre service à la clientèle.</td></tr><tr><td><strong>Témoin de charge</strong></td><td>Le témoin s’affiche pendant la charge et disparaît lorsque l’appareil est complètement chargé.</td></tr></tbody></table></figure>

<span id="native-operations"></span>

## FONCTIONNEMENT

### MARCHE/ARRÊT

<div class="native-figure native-power-on-off native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="power-on-off" data-source-fragment-sha256="94ac08852423403f669617e9674b7d1adf0f60bd5d59012850c671571b6ebfe8" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="power-on-off.semantic"><img alt="POWER button: press once to turn on; press and hold for 3 s to turn off" class="hb-reference-art hb-composite-art" src="assets/fr-power-on-off.png"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarques</td><td class="manual-callout-body"><p>Lorsque vous utilisez le Jackery HomePower 3600 Plus, vous pouvez contrôler la mise sous tension ou hors tension du Jackery Battery Pack 3600 via le « bouton d’alimentation principale » du Jackery HomePower 3600 Plus.<br/>Le dispositif s’éteint automatiquement s’il n’est pas chargé ou si aucune charge n’est connectée pendant 2 heures.</p></td></tr></tbody></table>

### ACTIVATION/DÉSACTIVATION DE L’ÉCRAN LCD

<div class="native-figure native-lcd-on-off native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="lcd-on-off" data-source-fragment-sha256="4f07316fdbc9b269e3bb8ece6af3191e88e91b49d5d22c006339be020740bdca"><div class="hb-reference-semantic" data-reference-id="lcd-on-off.semantic"><img alt="Pressing the POWER button switches the LCD display on or off" class="hb-reference-art hb-composite-art" src="assets/lcd-on-off.png"/></div></figure></div>

<p>Lorsque vous appuyez sur le « bouton d’alimentation principale » ou lorsque vous chargez le produit, l’écran LCD s’allume, et lorsque vous appuyez à nouveau sur ce bouton, l’écran LCD s’éteint.</p>

<span id="native-troubleshooting"></span>

## DÉPANNAGE

<p>Si l'un des codes d'erreur suivants apparaît, suivez les actions correctives indiquées pour résoudre le problème.Si l'erreur persiste, veuillez contacter le service à la clientèle de Jackery.</p>

<div class="native-fit-phone"><figure aria-label="Code d'erreur / Mesures correctives" class="hb-troubleshooting-composition" data-component-id="HB-TABLE-TROUBLESHOOTING" tabindex="0"><table class="hb-troubleshooting-table"><colgroup><col class="hb-troubleshooting-col-code"/><col class="hb-troubleshooting-col-measures"/></colgroup><thead><tr><th class="hb-troubleshooting-code" scope="col">Code d'erreur</th><th class="hb-troubleshooting-measures" scope="col">Mesures correctives</th></tr></thead><tbody><tr><td class="hb-troubleshooting-code"><strong>F0</strong></td><td class="hb-troubleshooting-measures">Redémarrez le produit.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F1, F2</strong></td><td class="hb-troubleshooting-measures">Contacter le service à la clientèle de Jackery.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F3</strong></td><td class="hb-troubleshooting-measures">Redémarrez le produit.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F4</strong></td><td class="hb-troubleshooting-measures">Connectez le produit à des charges pour décharger sa batterie jusqu'à ce que l'erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F5</strong></td><td class="hb-troubleshooting-measures">Chargez le produit via des panneaux solaires ou une prise murale CA jusqu'à ce que l'erreur disparaisse.</td></tr><tr><td class="hb-troubleshooting-code"><strong>F6-F9,</strong><br/><strong>FA, FC, FE</strong></td><td class="hb-troubleshooting-measures">Contacter le service à la clientèle de Jackery.</td></tr><tr><td class="hb-troubleshooting-code"><strong>FF</strong></td><td class="hb-troubleshooting-measures">Placez le produit dans un environnement à température appropriée et attendez que l'erreur disparaisse.</td></tr></tbody></table></figure></div>

<span id="native-connections"></span>

## CONNEXIONS

<p>Pour répondre à des besoins de capacité accrue, jusqu’à 5 dispositifs peuvent être utilisés avec le Jackery HomePower 3600 Plus.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Important</td><td class="manual-callout-body"><p>Assurez-vous que tous les produits sont éteints avant de connecter le HomePower 3600 Plus au(x) Jackery Battery Pack 3600.<br/>Pour assurer le bon fonctionnement du produit, assurez-vous que les entrées et sorties d'air sur les deux côtés ne sont pas obstruées. Laissez un espace d'au moins 0,66 pied (≈200 mm) entre les ouvertures et tout objet pour permettre une dissipation thermique adéquate.</p></td></tr></tbody></table>

<div class="native-figure native-clearance native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="clearance" data-source-fragment-sha256="f9ebd1504950935fee1743cd4fd3356ab515d08fee52d3c9317a47e2fe9e8806" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="clearance.semantic"><img alt="Battery packs connected to the Jackery HomePower 3600 Plus, with at least 0.66 ft (≈200 mm) of space between the vents and any objects" class="hb-reference-art hb-composite-art" src="assets/fr-clearance.png"/></div></figure></div>

<div class="native-figure native-stacking native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="stacking" data-source-fragment-sha256="cc6cfb4fceb0bb982ee2dc3cf920dd54ba485d6900ba0b9b6bd1e892bcb86bc9"><div class="hb-reference-semantic" data-reference-id="stacking.semantic"><img alt="Correct: up to three battery packs in one tower. Incorrect: four battery packs in one tower" class="hb-reference-art hb-composite-art" src="assets/fr-stacking.png"/></div></figure></div>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Remarques</td><td class="manual-callout-body"><p>L’apparition de l’icône<img alt="battery pack connection icon (HomePower 3600 Plus LCD)" class="native-inline-control" src="assets/inline-connection-icon.svg"/>sur l’écran LCD (Jackery HomePower 3600 Plus) signifie que la connexion entre l’unité de batterie et le Jackery HomePower 3600 Plus est réussie.<br/>Lors de l'utilisation du produit, ne superposez pas plus de trois blocs-batterie dans une même tour pour éviter qu'ils ne tombent et ne causent des blessures.<br/>Veuillez ne pas empiler le dispositif sur le Jackery HomePower 3600 Plus.</p></td></tr></tbody></table>

<div class="native-figure native-locking native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="locking" data-source-fragment-sha256="0920e155c9a022d8aa07133c7e0086b334a6fbdb474d063b7ef2938621dd6457" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="locking.semantic"><img alt="Expansion cable connections, with the steps to lock and unlock the cable terminal" class="hb-reference-art hb-composite-art" src="assets/fr-locking.png"/></div></figure></div>

<span id="native-charging"></span>

## CHARGE

### CHARGEMENT PAR PRISE MURALE CA

<p>En cas de charge murale, ce dispositif doit être utilisé avec le Jackery HomePower 3600 Plus.</p>

<table class="manual-callout-table manual-callout-table"><tbody><tr><td class="manual-callout-label">Avertissement</td><td class="manual-callout-body"><p>Assurez-vous que tous les produits sont éteints avant de connecter le HomePower 3600 Plus au(x) Battery Pack 3600.</p></td></tr></tbody></table>

<div class="native-figure native-ac-charging native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="ac-charging" data-source-fragment-sha256="4d3dbf0cc8876dcebd28f7539ac76e5057d9b92072665e48b4dd419d40965776" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="ac-charging.semantic"><img alt="Charging via an AC wall outlet through the Jackery HomePower 3600 Plus" class="hb-reference-art hb-composite-art" src="assets/fr-ac-charging.png"/></div></figure></div>

### CHARGEMENT PAR PANNEAUX SOLAIRES <span class="native-sold-separately">VENDU SÉPARÉMENT</span>

<p>Rechargez votre dispositif à l’aide de panneaux solaires et du Jackery HomePower 3600 Plus, comme indiqué dans la figure ci-dessous.Pour plus d’informations, veuillez vous reporter au manuel d’utilisation du Jackery HomePower 3600 Plus.</p>

<div class="native-figure native-solar-charging native-wide"><figure class="hb-reference-figure" data-component-id="HB-SPECIAL-REFERENCE-FIGURE" data-reference-id="solar-charging" data-source-fragment-sha256="ae8652bbb44b687ec73b0ca6182bbbaab160d69087ff621c9e193f0e25b612b4" data-step-captions="embedded"><div class="hb-reference-semantic" data-reference-id="solar-charging.semantic"><img alt="Charging via solar panels through the Jackery HomePower 3600 Plus" class="hb-reference-art hb-composite-art" src="assets/fr-solar-charging.png"/></div></figure></div>

<span id="native-storage"></span>

## STOCKAGE

<p>Conservez le produit dans un endroit propre et sec avec une ventilation adéquate.Température et humidité de stockage :<br/>1 mois : -4°F à 113°F / -20 à 45°C (0-60% HR)<br/>3 mois : 32°F à 113°F / 0 à 45°C (0-60% HR)<br/>12 mois : 32°F à 77°F / 0 à 25°C (0-60% HR)<br/>Si ce produit est stocké pendant une longue période (3 à 6 mois) avec la batterie déchargée, il peut devenir impossible de le recharger. Pour éviter cela et préserver la santé de la batterie, il est recommandé de vérifier et de recharger le produit tous les trois mois, et d'effectuer un cycle de charge et de décharge complet au moins une fois tous les 6 à 12 mois.</p>

<span id="native-specifications"></span>

## SPÉCIFICATIONS

<h2 class="hb-spec-group">INFORMATIONS GÉNÉRALES</h2>

<figure aria-label="INFORMATIONS GÉNÉRALES" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Nom du produit</th><td class="manual-spec-value hb-spec-value">Jackery Battery Pack 3600</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">N° modèle</th><td class="manual-spec-value hb-spec-value">JBP-3600A</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Capacité</th><td class="manual-spec-value hb-spec-value">80Ah / 44.8Vdc (3584 Wh)</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Cellule Chimique</th><td class="manual-spec-value hb-spec-value">LiFePO₄</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Poids</th><td class="manual-spec-value hb-spec-value">Environ 55.1 lbs/25 kg</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Dimensions</th><td class="manual-spec-value hb-spec-value">14,8 x 12,5 x 9,0 po/37,5 x 31,7x 22,9 cm</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Durée de vie</th><td class="manual-spec-value hb-spec-value">Capacité de 6000 cycles à 70 % ou plus</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">PORTS D’ENTRÉE/SORTIE</h2>

<figure aria-label="PORTS D’ENTRÉE/SORTIE" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Entrée)</th><td class="manual-spec-value hb-spec-value">36,4V-50,4V⎓60A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Port d’extension CC (Sortie)</th><td class="manual-spec-value hb-spec-value">36,4V-50,4V⎓100A Max</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Courant et durée maximum du court-circuit</th><td class="manual-spec-value hb-spec-value">1160A/860μs</td></tr></tbody></table></figure>

<h2 class="hb-spec-group">TEMPÉRATURE DE FONCTIONNEMENT</h2>

<figure aria-label="TEMPÉRATURE DE FONCTIONNEMENT" class="hb-spec-table-composition"><table class="manual-table manual-spec-table hb-spec-table"><colgroup><col class="hb-spec-col-label"/><col class="hb-spec-col-value"/></colgroup><tbody><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de charge</th><td class="manual-spec-value hb-spec-value">-4°F à 113°F / -20°C à 45°C</td></tr><tr><th class="manual-spec-label hb-spec-label" scope="row">Température de décharge</th><td class="manual-spec-value hb-spec-value">-4°F à 113°F / -20°C à 45°C</td></tr></tbody></table></figure>

<span id="native-warranty"></span>

## GARANTIE

<figure aria-label="GARANTIE" class="hb-warranty-intro-composition" data-component-id="HB-WARRANTY-LEAD"><div class="hb-warranty-intro-panel"><strong>Nous ne fournissons notre garantie qu'aux clients qui achètent sur le site officiel de Jackery, sur des plateformes tierces portant la marque Jackery, ou auprès de revendeurs autorisés locaux.</strong></div><div class="hb-warranty-local-note">*La durée et les détails de la garantie peuvent varier en fonction des lois, réglementations et revendeurs autorisés locaux.</div></figure>

### Garantie limitée

<figure aria-label="Garantie limitée" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="1"><p>Jackery Inc. garantit à l'acheteur et consommateur d'origine que le produit de Jackery sera exempt de tout défaut de fabrication et de matériaux dans le cadre d'une utilisation normale pendant toute la durée de la période de garantie applicable identifiée dans la section « Période de garantie » ci-dessous, sous réserve des exceptions énoncées ci-dessous.</p><p>Cette déclaration de garantie énonce les obligations totales et exclusives de garantie de Jackery. Nous n'assumerons pas et nous n'autorisons personne à assumer pour nous toute autre responsabilité en lien avec la vente de nos produits.</p></figure>

### Période de garantie

<figure aria-label="Période de garantie" class="hb-warranty-period-card" data-component-id="HB-WARRANTY-YEARS"><div class="hb-warranty-period-grid"><div aria-label="3 ANS Garantie standard" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">3</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie standard</strong></div></div><div class="hb-warranty-period-copy">La période de garantie standard du Jackery Battery Pack 3600 est de 36 mois. Dans tous les cas, la période de garantie commence à compter de la date d'achat par l'acheteur et consommateur d'origine. La facture du premier achat du consommateur ou toute autre preuve documentaire raisonnable est nécessaire afin d'établir la date de début de la période de garantie.</div></div><div aria-label="2 ANS Garantie prolongée" class="hb-warranty-period-item"><div class="hb-warranty-period-heading"><span class="hb-warranty-year-badge">2</span><div class="hb-warranty-period-title"><strong class="hb-warranty-years-unit">ANS</strong><strong class="hb-warranty-period-label">Garantie prolongée</strong></div></div><div class="hb-warranty-period-copy">Pour activer l'extension de garantie, vous devez enregistrer votre produit en ligne ou bien contacter notre service client à hello@jackery.com afin de prolonger la durée de la garantie standard.</div></div></div></figure>

### Réparation ou remplacement

<figure aria-label="Réparation ou remplacement" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="3"><p>Jackery remplacera (aux frais de Jackery) tout produit de Jackery qui ne fonctionne plus en raison d'un défaut de fabrication ou de matériau pendant la période de garantie applicable. Un produit remplacé reprend la garantie restante du produit d'origine.</p></figure>

### Limitée à l'acheteur et consommateur d'origine

<figure aria-label="Limitée à l'acheteur et consommateur d'origine" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="4"><p>Jackery réparera ou remplacera (aux frais de Jackery) tout produit Jackery qui cesse de fonctionner pendant la période de garantie applicable en raison d'un défaut de fabrication ou de matériau. Le produit réparé ou remplacé bénéficie de la garantie restante de la date d'achat d'origine.</p></figure>

### Exclusions

<figure aria-label="Exclusions" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="5"><p>La garantie de Jackery ne s'applique pas à :</p><ul><li>Une utilisation incorrecte, abusée, modifiée, aux dégâts provoqués par un accident ou toute autre utilisation qui n'est pas une utilisation normale de ce produit et autorisée par la documentation actuelle du produit de Jackery.</li><li>À une réparation tentée par quelqu'un d'autre qu'un établissement agréé.</li><li>Tout autre produit acheté par l'intermédiaire d'une vente aux enchères en ligne.</li><li>La garantie de Jackery ne s'applique pas aux cellules de la batterie, sauf si vous avez entièrement chargé les cellules de la batterie dans les sept jours suivant l'achat du produit et au moins une fois tous les 6 mois par la suite.</li></ul></figure>

### Droits d'interprétation

<figure aria-label="Droits d'interprétation" class="hb-warranty-card" data-component-id="HB-WARRANTY-SECTION" data-warranty-card-index="6"><p>Jackery Inc. se réserve le droit d'interpréter de manière définitive la politique après-vente des clients ci-dessus.</p></figure>
