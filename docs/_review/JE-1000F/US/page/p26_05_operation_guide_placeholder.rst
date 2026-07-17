.. raw:: latex

   \HBApplyLang{fr}

FONCTIONNEMENT
==============

MARCHE/ARRÊT
------------

.. image:: asset:operation/main_power
   :alt: Fonction marche/arrêt.
   :width: 360px

| Marche : appuyez une fois.
| Arrêt : appuyez et maintenez pendant 3 secondes.
| **Temps de veille par défaut :** 2 heures.
| Le produit s'éteindra automatiquement après 2 heures d'inactivité, sans charge ni décharge.
| \*Le temps de veille peut être réglé dans l'application Jackery.
| Lorsque le mode d'économie d'énergie est activé, le produit s'éteindra automatiquement après 12 heures si le bouton d’alimentation CA ou le bouton d’alimentation CC / USB est activé mais que le produit ne charge ni ne décharge.

SORTIE CA MARCHE/ARRÊT
----------------------

**Prérequis :** Le produit est allumé.

.. image:: asset:operation/ac_output
   :alt: Fonction de sortie CA.
   :width: 360px

| **Marche** 
| appuyez une fois
| **Arrêt** 
| appuyez une fois

SORTIE CC 12V/USB MARCHE/ARRÊT
------------------------------

**Prérequis :** Le produit est allumé.

.. image:: asset:operation/dc_usb_output
   :alt: Fonction de sortie CC et USB.
   :width: 360px

| **Marche** 
| appuyez une fois
| **Arrêt** 
| appuyez une fois

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENTION**
     -
       - **Les ports USB-C de 100 W sont des ports de sortie haute puissance de type Source d'alimentation 3 (PS3) selon USB-PD.** Si l'appareil utilisateur ou l'accessoire connecté ne répond pas aux exigences de sécurité, il peut présenter un risque d'incendie. Avant d'utiliser ces ports, assurez-vous que l'appareil ou l'accessoire connecté dispose d'une protection contre les incendies.
       - Ne connectez Jackery Explorer 1000 qu'à des appareils ou accessoires conformes aux clauses 6.3, 6.4 et 6.5 de la norme IEC/EN/UL 62368-1 (ou autres normes équivalentes).
       - Pour obtenir la puissance de sortie maximale, utilisez le câble USB-C vers USB-C 5 A (20 V CC/5A, 100 W).

| Le produit peut charger la batterie de votre voiture à l'aide du câble de charge de batterie automobile Jackery 12V, vendu séparément et disponible sur notre site web.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENTION**
     -
       - Le port CC 12V est uniquement compatible avec les batteries de voiture 12V et ne convient pas aux systèmes 24V.
       - Ne démarrez pas la voiture pendant que le produit charge la batterie via le port de sortie CC 12V, car cela pourrait endommager le produit.
       - Cette fonctionnalité est destinée à un usage d'urgence uniquement et ne peut pas charger une batterie de voiture morte ou endommagée.

MODE D'ÉCONOMIE D'ÉNERGIE
-------------------------

Pour éviter une consommation inutile de la batterie due à l'oubli de désactiver la sortie, le produit active par défaut le mode d'économie d'énergie. Lorsque la sortie CA ou CC/USB est activée, l'icône du mode d'économie d'énergie s'affiche sur l'écran LCD. Dans ce mode, si aucun appareil n'est connecté ou si la consommation de l'appareil connecté est inférieure à un certain seuil (sortie CA de 25 W ou sortie CC/USB de 2 W), la sortie correspondante s'éteint automatiquement après la durée définie. Le réglage par défaut est 12 heures. La durée du mode d'économie d'énergie peut être réglée dans l'application Jackery sur 1H, 2 H, 8 H, 12 H ou 24 H. Si l'option "Never Off" est sélectionnée, le mode d'économie d'énergie sera désactivé.

Pour désactiver le mode d'économie d'énergie, appuyez simultanément sur le bouton d’alimentation CA et sur le bouton d’alimentation principal pendant plus de 3 secondes. Une fois le mode d'économie d'énergie désactivé, l'icône ne s'affichera plus sur l'écran LCD et le produit n'éteindra pas automatiquement la sortie CA ou CC/USB.

Lors de l'alimentation d'appareils à faible puissance (CA ≤ 25 W ou CC/USB ≤ 2 W), désactivez le mode d'économie d'énergie afin d'éviter l'arrêt automatique de la sortie pendant le fonctionnement.

.. image:: asset:operation/energy_saving
   :alt: Fonction du mode d'économie d'énergie.
   :width: 320px

| Maintenez les deux boutons enfoncés pendant plus de 3 secondes.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **REMARQUE**
     - Le mode d'économie d'énergie reprend l'état précédent après l'allumage. Toute modification du mode doit être effectuée manuellement.


LAMPE LED MARCHE/ARRÊT
----------------------

La lampe LED dispose de deux modes : mode éclairage et mode SOS. Dans n'importe quel mode, appuyez et maintenez sur le bouton pour éteindre la lumière.

.. image:: asset:operation/led_light
   :alt: Fonction de la lampe LED.
   :width: 360px


| Appuyez une fois sur le bouton de la lampe LED pour l'allumer.
| Appuyez de nouveau pour passer en mode SOS.
| Appuyez une troisième fois pour éteindre la lampe.

Fonction de reprise de Sortie CA et CC
---------------------------------------

Cette fonction mémorise l’état de la sortie et reprend automatiquement les sorties CA et CC sous certaines conditions définies.

+-----------------------------------------------------------------------+------------------------------------------------------------+
| Conditions de reprise automatique                                     | Conditions sans reprise automatique                       |
+=======================================================================+============================================================+
| Mise sous tension/redémarrage après arrêt ou redémarrage              | Sortie désactivée manuellement (bouton/App)                |
+-----------------------------------------------------------------------+------------------------------------------------------------+
| SOC de la batterie ≥ limite de décharge +10% après avoir atteint      | Sortie désactivée en mode économie d’énergie              |
| la limite                                                             +------------------------------------------------------------+
|                                                                       | Sortie désactivée suite à un déclenchement de protection   |
+-----------------------------------------------------------------------+------------------------------------------------------------+
| Mise à niveau OTA terminée                                            | Sortie désactivée par le minuteur de décharge              |
+-----------------------------------------------------------------------+------------------------------------------------------------+

AFFICHAGE LCD
-------------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="asset:operation/lcd_mode" alt="Mode d'affichage LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Allumer en discontinu</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Allumer</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Appuyez sur le bouton d'alimentation principal ou lorsque le produit est en charge.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Éteindre</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Appuyez sur le bouton d'alimentation principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Arrêt automatique</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">L'écran LCD s'éteint automatiquement et entre en mode veille après 2 minutes d'inactivité.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Allumer en continu (en cours de charge ou de décharge)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Allumer</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Appuyez deux fois sur le bouton d'alimentation principal lorsque le produit est allumé.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Éteindre</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Appuyez sur le bouton d'alimentation principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Arrêt automatique</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">L'écran LCD s'éteint automatiquement après 2 heures d'inactivité.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{asset:operation/lcd_mode}
      \HBLcdModeFirstGroup{Allumer en discontinu}{Allumer}{Appuyez sur le bouton d'alimentation principal ou lorsque le produit est en charge.}{Éteindre}{Appuyez sur le bouton d'alimentation principal.}{Arrêt automatique}{L'écran LCD s'éteint automatiquement et entre en mode veille après 2 minutes d'inactivité.}
      \HBLcdModeSecondGroup{Allumer en continu (en cours de charge ou de décharge)}{Allumer}{Appuyez deux fois sur le bouton d'alimentation principal lorsque le produit est allumé.}{Éteindre}{Appuyez sur le bouton d'alimentation principal.}{Arrêt automatique}{L'écran LCD s'éteint automatiquement après 2 heures d'inactivité.}
      \end{HBLcdModeTable}

Vous pouvez également définir le mode d'affichage de l'écran dans l'application Jackery.

FONCTIONNEMENT DES BOUTONS
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Boutons
     - Utilisation
     - Fonction
   * - Bouton d'alimentation principal + Bouton d'alimentation CA
     - Appuyer 3 secondes sur les deux
     - Activer/désactiver le mode économie d'énergie
   * - Bouton d'alimentation principal + Bouton d'alimentation **CC/USB**
     - Appuyer 3 secondes sur les deux
     - Réinitialiser le Wi-Fi et le Bluetooth
   * - Bouton d'alimentation **CC/USB** + Bouton d'alimentation CA
     - Appuyer 1 seconde sur les deux
     - Activer/désactiver le Wi-Fi et le Bluetooth
   * - Bouton d'alimentation principal + Bouton d'éclairage LED
     - Appuyer 1 seconde sur les deux
     - Activer/désactiver le mode d'urgence
