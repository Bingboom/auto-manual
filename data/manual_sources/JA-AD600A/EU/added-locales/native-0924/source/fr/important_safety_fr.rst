5. INSTRUCTIONS DE SÉCURITÉ IMPORTANTES
=======================================

.. container:: hb-source-operation hb-source-note

   Pendant la conduite, le chargeur DC-DC utilise l’excédent de puissance du générateur pour charger la station d’énergie portable. La puissance de charge effective dépend des conditions de conduite, du modèle et de l’état général du véhicule.


Pour garantir une utilisation sûre, il est essentiel de respecter les consignes suivantes :

- Conservez ce manuel pour référence future.

- Utilisez ou stockez toujours le produit conformément aux conditions spécifiées dans ce manuel.

- Lisez toutes les instructions et avertissements relatifs à ce produit, à la batterie du véhicule et à la station d’énergie Jackery, ainsi qu’à leurs manuels d'utilisation respectifs.

- Ne démontez pas le produit et ne remplacez pas ses pièces sans autorisation, car cela annulera la garantie et pourrait endommager le produit. Contactez le service à la clientèle de Jackery pour toute assistance concernant le remplacement des composants.

Compatibilité du produit
------------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: !
      :width: 40px

   Ce produit est uniquement compatible avec les stations d’énergie portables Jackery dotées d’un port d’entrée DC8020. L’utilisation d’adaptateurs pour connecter ce produit à un port d’entrée DC7909 ou USB-C est strictement interdite. Une telle connexion peut endommager l’appareil, provoquer un incendie, voire une explosion, mettant gravement en danger la sécurité personnelle.


- Ce produit est uniquement compatible avec les batteries de voiture 12V/24V. Avant d’utiliser le produit, vérifiez que la tension nominale de votre véhicule est de 12V ou 24V et suivez toujours les consignes de sécurité électrique pendant son utilisation.

- Ce produit est compatible avec les stations d’énergie portables Jackery équipées d’un port d’entrée DC8020. Veuillez consulter le tableau ci-dessous pour quelques modèles compatibles. Pour plus d’informations, veuillez contacter le service client ou visiter le site officiel de Jackery.

.. list-table::
   :header-rows: 1

   * - Station d'Alimentation Portable
     - Capacité
     - Tension et courant de charge
     - Puissance de charge
     - TEMPS DE CHARGE (0-100%)
   * - Explorer 1000 Plus
     - 1265 Wh
     - Environ 50V 8A
     - Environ 400W
     - Environ 3,5 heures
   * - Explorer 1000 v2
     - 1070 Wh
     - Environ 50V 8A
     - Environ 400W
     - Environ 3,0 heures
   * - Explorer 2000 Plus
     - 2042 Wh
     - Environ 50V 12A
     - Environ 600W
     - Environ 3,7 heures
   * - Explorer 2000 v2
     - 2042 Wh
     - Environ 50V 8A
     - Environ 400W
     - Environ 5,6 heures
   * - Explorer 3000 Pro
     - 3024 Wh
     - Environ 50V 12A
     - Environ 600W
     - Environ 5,5 heures
   * - Explorer 3000 v2
     - 3072 Wh
     - Environ 50V 12A
     - Environ 600W
     - Environ 5,6 heures

Remarque : Les données relatives au temps de charge de ce produit sont basées sur des tests simulés réalisés à une température constante de 25°C. En usage réel, la puissance de charge peut varier en fonction des conditions de conduite, du modèle de véhicule et de son état général. Les temps de charge peuvent également être affectés par la température ambiante. Environnement de test standard : 25°C constant Source des données : Laboratoire Jackery

.. image:: renderers/web/assets/ja_ad600a_eu_en/status_device.png
   :alt: status_device
   :width: 100%
   :class: hb-status-device-art

.. container:: hb-source-operation hb-source-power

   .. rubric:: Mise en marche du produit



   1. Appuyez brièvement sur le bouton d’alimentation : en l’absence de signal ACC, vous pouvez allumer l’appareil en appuyant brièvement sur le bouton d’alimentation. 

   2. Mise en marche via signal ACC : si le câble ACC est connecté, l’appareil s’allumera automatiquement dès qu’un signal ACC sera détecté (par exemple, après le démarrage du véhicule).

   .. rubric:: Veille et arrêt

   Lorsqu’il n’y a pas de signal ACC ou si la tension chute en dessous du seuil de démarrage, le produit passe en mode veille. Si la veille dépasse 24 heures ou si la tension descend sous le seuil de protection, l’appareil s’éteint automatiquement. Pour le redémarrer, suivez les mêmes étapes décrites ci-dessus. En mode veille, s’il n’y a pas de signal ACC, vous pouvez également éteindre manuellement l’appareil en maintenant le bouton d’alimentation enfoncé pendant 3 secondes.


.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - STATUT DES LUMIÈRES
        - Couleur des lumières
        - État du produit
        - REMARQUES
      * - Fixe
        - :hb-lamp-green:`Vert`
        - En charge
        - /
      * - Fixe
        - :hb-lamp-red:`Rouge`
        - Anormal
        - En cas de problème, contactez immédiatement le service à la clientèle Jackery pour obtenir de l’aide.
      * - Clignotant
        - :hb-lamp-blinking:`Vert`
        - 1. Connexion normale, en attente de charge
        - Si le même problème persiste après avoir connecté la station d’énergie portable, les causes possibles incluent: Connexion instable entre le câble de sortie et la station d’énergie portable. 2. Câble endommagé. 3. La station d’énergie portable est complètement chargée. Si le problème persiste après le dépannage, contactez le service à la clientèle Jackery.
      * - Aucune lumière
        - :hb-lamp-off:`Aucune couleur`
        - Le produit n’est pas sous tension
        - Si le problème persiste après avoir terminé le câblage et démarré le véhicule, veuillez contacter le service à la clientèle Jackery.


