ALIMENTATION SANS INTERRUPTION (ASI)
====================================

| Connectez le produit à une prise murale à l'aide du câble de charge CA, puis appuyez sur le bouton d’alimentation CA pour alimenter vos appareils en même temps.

.. image:: asset:operation/ups_mode
   :alt: Schéma de connexion ASI.
   :width: 360px

| Une alimentation sans coupure (UPS) est un système d'alimentation continue qui fournit automatiquement une alimentation électrique de secours à une charge lorsque l'alimentation du réseau principal est interrompue.
| En cas de perte soudaine de l'alimentation du réseau, le |PRODUCT_NAME| basculera automatiquement sur l'alimentation stockée en moins de |UPS_TRANSFER_TIME| pour maintenir vos appareils en fonctionnement.
| En mode UPS, la puissance de crête de sortie de l'appareil atteint |UPS_BYPASS_OUTPUT_TEXT| avant les coupures de courant. Comme la charge et la décharge simultanées sont activées en mode bypass, la puissance de sortie réelle est inférieure à la puissance nominale en mode bypass, mais revient à la puissance nominale lors des coupures.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **AVERTISSEMENT**
     - N’utilisez pas ce produit dans des applications telles que des serveurs de données ou des dispositifs médicaux, où un dysfonctionnement pourrait mettre la vie en danger ou entraîner des dommages matériels importants.

       Pour les équipements suivants, une perte d’alimentation pendant l’utilisation pourrait entraîner de graves atteintes à la sécurité des personnes ou des biens :

       - Dispositifs médicaux et autres équipements étroitement liés à la sécurité des personnes.
       - Équipements essentiels tels que les infrastructures publiques et les services publics.
       - Équipements essentiels aux activités de l’entreprise, etc.

       Les personnes portant un stimulateur cardiaque (pacemaker) ne doivent pas utiliser ce produit.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENTION**
     -
       - Ce produit ne prend pas en charge un basculement instantané (0 ms). Ne le connectez pas à des équipements nécessitant une alimentation avec commutation en 0 ms, tels que des serveurs de données ou des stations de travail.
       - Avant toute utilisation, testez plusieurs fois la compatibilité avec votre appareil.
       - Ne connectez pas de charges dépassant la puissance maximale de sortie du produit. Sinon, la protection contre les surcharges sera déclenchée.
       - La fonction UPS ne fonctionne que lorsqu'un seul appareil est raccordé directement à une prise murale. Ne raccordez pas plusieurs stations d'énergie portables en série (montage en cascade). Dans une configuration en cascade, la fonction UPS ne fonctionne pas : l'appareil peut ne pas basculer lors d'une coupure de courant, ce qui entraîne l'arrêt des appareils connectés.
