5. WICHTIGE SICHERHEITSHINWEISE
===============================

.. container:: hb-source-operation hb-source-note

   Während des Fahrzeugbetriebs nutzt der Jackery DC-DC Charger die überschüssige Leistung des Generators, um die tragbare Powerstation aufzuladen. Die tatsächliche Ladeleistung hängt von den Fahrbedingungen, dem Fahrzeugmodell und dem allgemeinen Zustand des Fahrzeugs ab.


Für einen sicheren Betrieb sind die folgenden Hinweise unbedingt zu beachten:

- Bewahren Sie dieses Handbuch zum späteren Nachschlagen auf.

- Betreiben oder lagern Sie das Produkt stets unter den in diesem Handbuch angegebenen Bedingungen.

- Lesen Sie alle Anweisungen und Warnhinweise auf diesem Produkt, der Autobatterie und der Jackery Powerstation sowie die jeweiligen Benutzerhandbücher sorgfältig durch.

- Zerlegen Sie das Produkt nicht und tauschen Sie keine Teile ohne Genehmigung aus, da dies zum Erlöschen der Garantie führt und das Produkt beschädigen kann. Wenden Sie sich für den Austausch von Komponenten an den Jackery-Kundendienst.

Produktkompatibilität
---------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: !
      :width: 40px

   Dieses Produkt ist ausschließlich mit tragbaren Powerstations von Jackery mit DC8020-Eingangsanschluss kompatibel. Die Verwendung von Adaptern, um dieses Produkt an einen DC7909- oder USB-C-Eingangsanschluss einer tragbaren Powerstation anzuschließen, ist strengstens untersagt. Eine solche Verbindung kann zu Geräteschäden, Brand oder sogar Explosion führen und stellt ein ernsthaftes Risiko für die persönliche Sicherheit dar.


- Dieses Produkt ist ausschließlich mit 12V/24V Fahrzeugbatterien kompatibel. Stellen Sie vor der Verwendung des Produkts sicher, dass die Nennspannung Ihres Fahrzeugs 12 V oder 24 V beträgt, und beachten Sie während des Betriebs stets die elektrischen Sicherheitsrichtlinien.

- Dieses Produkt ist mit tragbaren Powerstations von Jackery kompatibel, die über einen DC8020-Eingangsanschluss verfügen. Eine Auswahl kompatibler Modelle finden Sie in der folgenden Tabelle. Für weitere Informationen wenden Sie sich bitte an den Kundendienst oder besuchen Sie die offizielle Jackery-Website.

.. list-table::
   :header-rows: 1

   * - Tragbare Powerstation
     - Kapazität
     - Ladespannung und -strom
     - Ladeleistung
     - Ladezeit(0-100 %)
   * - Explorer 1000 Plus 1265
     - Wh ca.
     - 50 V / 8 A ca.
     - 400 W
     - ca. 3,5 Stunden
   * - Explorer 1000 v2 1070
     - Wh ca.
     - 50 V / 8 A ca.
     - 400 W
     - ca. 3,0 Stunden
   * - Explorer 2000 Plus 2042
     - Wh ca.
     - 50 V / 12 A
     - ca. 600 W
     - ca. 3,7 Stunden
   * - Explorer 2000 v2 2042
     - Wh ca.
     - 50 V / 8 A ca.
     - 400 W
     - ca. 5,6 Stunden
   * - Explorer 3000 Pro 3024
     - Wh ca.
     - 50 V / 12 A
     - ca. 600 W
     - ca. 5,5 Stunden
   * - Explorer 3000 v2 3072
     - Wh ca.
     - 50 V / 12 A
     - ca. 600 W
     - ca. 5,6 Stunden

Hinweis: Die Ladezeitangaben für dieses Produkt basieren auf simulierten Tests unter konstanten Bedingungen bei 25 °C. Im tatsächlichen Betrieb kann die Ladeleistung je nach Fahrbedingungen, Fahrzeugmodell und allgemeinem Zustand des Fahrzeugs variieren. Die Ladezeiten können zudem durch Änderungen der Umgebungstemperatur beeinflusst werden. Standard-Testbedingungen: Konstant 25 °C Datenquelle: Jackery Labor

.. image:: renderers/web/assets/ja_ad600a_eu_en/status_device.png
   :alt: status_device
   :width: 100%
   :class: hb-status-device-art

.. container:: hb-source-operation hb-source-power

   .. rubric:: Einschalten des Produkts



   1. Kurz die Ein-/Aus-Taste drücken: Liegt kein ACC-Signal an, kann das Gerät durch kurzes Drücken der Ein-/Aus-Taste eingeschaltet werden. 

   2. Einschalten über ACC-Signal: Wenn das ACC-Kabel angeschlossen ist, schaltet sich das Gerät automatisch ein, sobald ein ACC-Signal erkannt wird (z. B. nach dem Starten des Fahrzeugs).

   .. rubric:: Standby und Abschalten

   Liegt kein ACC-Signal an oder fällt die Spannung unter den Startschwellwert, wechselt das Produkt in den Standby-Modus. Hält der Standby-Modus länger als 24 Stunden an oder fällt die Spannung unter den Schutzschwellwert, schaltet sich das Gerät automatisch ab. Zum Neustart folgen Sie den oben beschriebenen Schritten. Befindet sich das Gerät im Standby-Modus und liegt kein ACC-Signal an, kann es auch manuell abgeschaltet werden, indem die Ein-/Aus-Taste 3 Sekunden lang gedrückt gehalten wird.


.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - Statusanzeige
        - Leuchtfarbe
        - Produktstatus
        - Hinweise
      * - Dauerlicht
        - :hb-lamp-green:`Grün`
        - Laden
        - /
      * - Dauerlicht
        - :hb-lamp-red:`Rot`
        - Störung
        - Wenn Probleme auftreten, wenden Sie sich umgehend an den Jackery-Kundendienst.
      * - Blinkend
        - :hb-lamp-blinking:`Grün`
        - Verbindung normal, wartet auf Ladevorgang.
        - Wenn das gleiche Problem nach dem Anschließen der tragbaren Powerstation weiterhin besteht, können folgende Ursachen vorliegen: 1. Instabile Verbindung zwischen Ausgangskabel und der tragbaren Powerstation. 2. Beschädigtes Kabel. 3. Die tragbare Powerstation ist vollständig geladen. Wenn das Problem nach der Fehlerbehebung weiterhin besteht, wenden Sie sich bitte an den Jackery-Kundendienst.
      * - Kein Licht
        - :hb-lamp-off:`Keine Farbe`
        - Das Produkt ist nicht eingeschaltet.
        - Wenn das Problem nach Abschluss der Verkabelung und dem Starten des Fahrzeugs weiterhin besteht, wenden Sie sich bitte an den Jackery-Kundendienst.


