FONCTIONNEMENT
==============

MARCHE/ARRÊT
------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Fonction marche/arrêt.
   :width: 360px

| Marche : appuyez une fois.
| Arrêt : appuyez et maintenez pendant 3 secondes.
|
| **Temps de veille par défaut :** |DEFAULT_STANDBY_DURATION|.
| Le produit s'éteindra automatiquement après |DEFAULT_STANDBY_DURATION| d'inactivité, sans charge ni décharge.
| *Le temps de veille peut être réglé dans l'application Jackery.*
|
| Lorsque le mode d'économie d'énergie est activé, le produit s'éteindra automatiquement après |ENERGY_SAVING_AUTO_OFF_DURATION| si le |AC_POWER_BUTTON_LABEL_LOWER| ou le |DC_USB_POWER_BUTTON_LABEL_LOWER| est activé mais que le produit ne charge ni ne décharge.

SORTIE CA MARCHE/ARRÊT
----------------------

**Prérequis :** Le produit est allumé.

.. image:: templates/word_template/common_assets/operation/ac_output.png
   :alt: Fonction de sortie CA.
   :width: 360px

Marche : appuyez une fois.

Arrêt : appuyez une fois.

SORTIE CC 12V/USB MARCHE/ARRÊT
------------------------------

**Prérequis :** Le produit est allumé.

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: Fonction de sortie CC et USB.
   :width: 360px

|
| Marche : appuyez une fois.
| Arrêt : appuyez une fois.
|

**ATTENTION**

- **Les ports USB-C de 100 W sont des ports de sortie haute puissance de type Source d'alimentation 3 (PS3) selon USB-PD.** Si l'appareil utilisateur ou l'accessoire connecté ne répond pas aux exigences de sécurité, il peut présenter un risque d'incendie. Avant d'utiliser ces ports, assurez-vous que l'appareil ou l'accessoire connecté dispose d'une protection contre les incendies.
- Ne connectez |PRODUCT_NAME| qu'à des appareils ou accessoires conformes aux clauses 6.3, 6.4 et 6.5 de la norme IEC/EN/UL 62368-1 (ou autres normes équivalentes).
- Pour obtenir la puissance de sortie maximale, utilisez le câble USB-C vers USB-C 5 A (20 V CC/5A, 100 W).

|
| Le produit peut charger la batterie de votre voiture à l'aide du câble de charge de batterie automobile Jackery 12V, vendu séparément et disponible sur notre site web.
|

**ATTENTION**

- Le port CC 12V est uniquement compatible avec les batteries de voiture 12V et ne convient pas aux systèmes 24V.
- Ne démarrez pas la voiture pendant que le produit charge la batterie via le port de sortie CC 12V, car cela pourrait endommager le produit.
- Cette fonctionnalité est destinée à un usage d'urgence uniquement et ne peut pas charger une batterie de voiture morte ou endommagée.

MODE D'ÉCONOMIE D'ÉNERGIE
-------------------------

Pour éviter une consommation inutile de la batterie due à l'oubli de désactiver la sortie, le produit active par défaut le mode d'économie d'énergie. Lorsque la sortie CA ou CC/USB est activée, l'icône du mode d'économie d'énergie s'affiche sur l'écran LCD. Dans ce mode, si aucun appareil n'est connecté ou si la consommation de l'appareil connecté est inférieure à un certain seuil (sortie CA de |ENERGY_SAVING_AC_THRESHOLD| ou sortie CC/USB de |ENERGY_SAVING_DC_THRESHOLD|), la sortie correspondante s'éteint automatiquement après la durée définie. Le réglage par défaut est |ENERGY_SAVING_AUTO_OFF_DURATION|. La durée du mode d'économie d'énergie peut être réglée dans l'application Jackery sur 2 h, 8 h, 12 h ou 24 h. Si l'option "Never Off" est sélectionnée, le mode d'économie d'énergie sera désactivé.

Pour désactiver le mode d'économie d'énergie, appuyez simultanément sur le |AC_POWER_BUTTON_LABEL_LOWER| et sur le |MAIN_POWER_BUTTON_LABEL_LOWER| pendant plus de 3 secondes. Une fois le mode d'économie d'énergie désactivé, l'icône ne s'affichera plus sur l'écran LCD et le produit n'éteindra pas automatiquement la sortie CA ou CC/USB.

Lors de l'alimentation d'appareils à faible puissance (CA <= |ENERGY_SAVING_AC_THRESHOLD| ou CC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), désactivez le mode d'économie d'énergie afin d'éviter l'arrêt automatique de la sortie pendant le fonctionnement.

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Fonction du mode d'économie d'énergie.
   :width: 320px

|
| Appuyez et maintenez pendant 3 secondes.
|

**REMARQUE**

Le mode d'économie d'énergie reprend l'état précédent après l'allumage. Un changement de mode nécessite un commutateur manuel.

LAMPE LED MARCHE/ARRÊT
----------------------

La lampe LED dispose de deux modes : mode éclairage et mode SOS. Dans n'importe quel mode, appuyez et maintenez sur le bouton pour éteindre la lumière.

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: Fonction de la lampe LED.
   :width: 360px

|
| Appuyez une fois sur le bouton de la lampe LED pour l'allumer.
| Appuyez de nouveau pour passer en mode SOS.
| Appuyez une troisième fois pour éteindre la lampe.

AFFICHAGE LCD
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Affichage
     - Mode
     - Action
     - Comportement
   * - .. image:: templates/word_template/common_assets/operation/lcd_mode.png
          :alt: Mode d'affichage LCD.
          :width: 140px
     - Allumer en discontinu
     - Allumer
     - Appuyez sur le bouton d'alimentation principal ou lorsque le produit est en charge.
   * -
     - Allumer en discontinu
     - Éteindre
     - Appuyez sur le bouton d'alimentation principal.
   * -
     - Allumer en discontinu
     - Arrêt automatique
     - L'écran LCD s'éteint automatiquement et entre en mode veille après 2 minutes d'inactivité.
   * -
     - Allumer en continu (en cours de charge ou de décharge)
     - Allumer
     - Appuyez deux fois sur le bouton d'alimentation principal lorsque le produit est allumé.
   * -
     - Allumer en continu (en cours de charge ou de décharge)
     - Éteindre
     - Appuyez sur le bouton d'alimentation principal.
   * -
     - Allumer en continu (en cours de charge ou de décharge)
     - Arrêt automatique
     - L'écran LCD s'éteint automatiquement après |DEFAULT_STANDBY_DURATION| d'inactivité.

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
     - Activer/désactiver le mode de charge rapide d'urgence
