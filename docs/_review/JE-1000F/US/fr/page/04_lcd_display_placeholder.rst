.. raw:: latex

   \HBApplyLang{fr}

AFFICHAGE LCD
=============

.. image:: _assets/templates/word_template/common_assets/lcd/lcd_map.png
   :alt: Carte des icônes de l'écran LCD.
   :width: 420px

.. list-table::
   :header-rows: 1
   :widths: 12 28 60

   * - ID
     - Indicateur
     - Description
   * - 1
     - Wi-Fi
     - **Allumé :** Wi-Fi connecté.

       **Clignotant :** Prêt à se connecter au Wi-Fi.

       **Éteint :** Wi-Fi déconnecté.
   * - 2
     - Bluetooth
     - **Allumé :** Bluetooth connecté.

       **Clignotant :** Prêt à se connecter au Bluetooth.

       **Éteint :** Bluetooth déconnecté.
   * - 3
     - Mode de charge silencieuse
     - **Allumé :** Le bruit pendant la charge est considérablement réduit, tandis que la puissance de charge diminue et que la vitesse de charge ralentit.

       **Éteint :** Le mode de charge silencieuse est désactivé.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l'appareil est mis hors tension.
   * - 5
     - Plan de charge
     - Personnalise le temps de charge de Jackery Explorer 1000.
       Adapté aux situations où les tarifs d'électricité fluctuent, il permet de définir des plans de charge selon les heures pleines et creuses afin de réduire le coût de l'électricité.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l'appareil est mis hors tension.
   * -
     - Mode autonome
     - Maximise l'utilisation de l'énergie solaire et réduit la dépendance à l'électricité du réseau en donnant la priorité à l'énergie solaire stockée, ce qui permet de réduire le coût de l'électricité.

       La station d'énergie doit être connectée simultanément aux panneaux solaires et au réseau, avec une puissance de charge limitée par la puissance de bypass.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l'appareil est mis hors tension.
   * -
     - Mode TOU
     - **Allumé :** Le mode TOU est activé (SOC de secours par défaut : 60 %). Pendant les périodes de pointe, lorsque l'énergie stockée dépasse le SOC de secours, le produit privilégie la décharge de la batterie afin de réduire les coûts d'électricité. Pendant les heures creuses, le produit recharge la batterie à partir du réseau pour lisser la consommation.

       **Éteint :** Le mode TOU est désactivé. Le produit ne suit pas la stratégie TOU et fonctionne selon la logique par défaut d'alimentation et de charge.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l'appareil est mis hors tension.
   * - 6
     - UPS
     - **Allumé :** Le produit est en mode bypass et le temps de commutation entre le réseau et la batterie interne est de 10 ms.

       **Éteint :** Le produit n'est pas en mode bypass.
   * - 7
     - Indicateur d'alimentation CA
     - La sortie CA (onde sinusoïdale pure) est activée.
   * - 8
     - Tension et fréquence de sortie
     - Affiche la tension et la fréquence de sortie lorsque la sortie CA est activée.
   * - 9
     - Puissance d'entrée
     - Affiche la puissance d'entrée en watts.
   * - 10
     - Temps de charge restant
     - Affiche le temps de charge restant.
   * - 11
     - Indicateur de charge sur prise murale CA
     - Le produit est chargé via l'entrée CA à l'aide de l'alimentation du réseau.
   * - 12
     - Indicateur de charge voiture
     - Le produit est chargé via l'entrée CC (DC8020) à l'aide d'une alimentation CC 12 V (charge voiture).
   * - 13
     - Indicateur de charge solaire
     - Le produit est chargé via l'entrée CC (DC8020) à l'aide de panneau(x) solaire(s).
   * - 4
     - Mode d'économie de batterie
     - **Allumé :** Limite la capacité maximale utilisable de la batterie afin de prolonger sa durée de vie.

       **Éteint :** Le mode d'économie de batterie est désactivé.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage est conservé lorsque l'appareil est mis hors tension.

       Lorsque cette fonction est activée, le produit effectue occasionnellement un cycle complet de charge et de décharge pour calibrer le SOC.
   * - 14
     - Limite de puissance de charge
     - **Allumé :** La limite de puissance de charge est activée dans l'application Jackery.

       **Éteint :** La limite de puissance de charge est désactivée dans l'application Jackery.

       Le réglage est conservé lorsque l'appareil est mis hors tension.
   * - 16
     - Indicateur de puissance de la batterie
     - Lorsque le produit est en charge, le cercle orange autour du pourcentage de batterie s'allume de manière séquentielle.

       Lorsqu'il charge d'autres appareils, le cercle orange reste allumé.
   * - 18
     - Pourcentage de batterie restant
     - Affiche le pourcentage de batterie restant.
   * - 17
     - Indicateur de batterie faible
     - **Allumé :** Le niveau de batterie est inférieur à 20 %.

       **Clignotant :** Le niveau de batterie est inférieur à 5 %.

       **Éteint :** Le niveau de batterie n'est pas inférieur à 20 % ou le produit est en charge.
   * -
     - Minuteur de décharge
     - **Allumé :** Un minuteur de décharge est défini.

       **Éteint :** Aucun minuteur de décharge n'est défini.

       Activez/désactivez cette fonction dans l'application Jackery. Le réglage n'est pas conservé lorsque l'appareil est mis hors tension.
   * - 22
     - Mode d'économie d'énergie
     - Lorsque la sortie CA ou CC est activée en appuyant sur AC power button ou DC/USB power button :

       **Allumé :** Le mode d'économie d'énergie est activé.

       **Éteint :** Le mode d'économie d'énergie est désactivé.
   * - 21
     - Indicateur de température élevée
     - La protection contre les températures élevées est déclenchée. Le produit peut cesser de fonctionner jusqu'à ce que sa température revienne dans la plage normale de fonctionnement.
   * -
     - Indicateur de basse température
     - La protection contre les basses températures est déclenchée. Le produit peut cesser de fonctionner jusqu'à ce que sa température revienne dans la plage normale de fonctionnement.
   * - 20
     - Code d'erreur
     - Une erreur s'est produite sur le produit. Veuillez consulter la section Dépannage pour plus de détails.
   * - 23
     - Puissance de sortie
     - Affiche la puissance de sortie en watts.
   * - 24
     - Temps de décharge restant
     - Affiche le temps de décharge restant.
