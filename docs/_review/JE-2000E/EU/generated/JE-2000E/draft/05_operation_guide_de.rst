.. raw:: latex

   \HBApplyLang{de}

GRUNDLEGENDE OPERATIONEN
========================

HAUPTSTROMVERSORGUNG EIN/AUS
----------------------------

.. image:: _assets/templates/word_template/common_assets/operation/main_power.png
   :alt: Platzhalter für Ein-/Ausschalten.
   :width: 360px

| Ein: Einmal drücken.
| Aus: 3 s lang gedrückt halten.
|
| **Standard-Standby-Zeit:** 2 Stunden.
| Das Produkt schaltet sich nach 2 Stunden Inaktivität automatisch aus, wenn weder geladen noch entladen wird.
| \*Die Standby-Zeit kann in der Jackery-App eingestellt werden.
| Wenn der Energiesparmodus aktiviert ist, schaltet sich das Produkt automatisch nach 12 Stunden aus, wenn der AC- oder DC/USB-Ausgang eingeschaltet ist, das Produkt jedoch weder lädt noch entlädt.

AC-AUSGANG EIN/AUS
------------------

**Voraussetzung**: Das Produkt ist eingeschaltet.

.. image:: _assets/templates/word_template/common_assets/operation/ac_output.png
   :alt: Platzhalter für AC-Ausgang Ein/Aus.
   :width: 360px

| 
| **Ein**
| Einmal drücken
| **Aus**
| Einmal drücken
| 

DC 12V/USB-AUSGANG EIN/AUS
-------------------------

**Voraussetzung**: Das Produkt ist eingeschaltet.

.. image:: _assets/templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: Platzhalter für DC/USB-Ausgang Ein/Aus.
   :width: 360px

| 
| **Ein**
| Einmal drücken
| **Aus**
| Einmal drücken
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **VORSICHT**
     -
       - Schließen Sie Jackery Explorer 2000 nur an Geräte oder Zubehör an, die den Abschnitten 6.3, 6.4 und 6.5 der IEC/EN/UL 62368-1 (oder anderen gleichwertigen Normen) entsprechen.
       - Verwenden Sie für die maximale Ausgangsleistung das USB-C-auf-USB-C-5 A-Kabel (20 V DC/5 A, 100 W).

| Das Produkt kann Ihre Fahrzeugbatterie mit dem Jackery 12-V-Autobatterie-Ladekabel aufladen, das separat erhältlich und auf unserer Website verfügbar ist.
 

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **VORSICHT**
     -
       - Die DC-12V-Buchse ist nur mit 12-V-Autobatterien kompatibel und nicht für 24-V-Systeme geeignet.
       - Starten Sie das Fahrzeug nicht, während das Produkt die Fahrzeugbatterie über den 12-V-DC-Ausgang lädt, da dies das Produkt beschädigen kann.
       - Diese Funktion ist nur für den Notfall vorgesehen und kann eine leere oder beschädigte Fahrzeugbatterie nicht aufladen.

ENERGIESPARMODUS
----------------

Um zu verhindern, dass die Batterie unnötig entladen wird, wenn das Ausschalten des Ausgangs vergessen wird, ist der Energiesparmodus standardmäßig aktiviert. Wenn der AC- oder DC/USB-Ausgang eingeschaltet wird, wird das Energiesparmodus-Symbol auf dem LCD angezeigt. In diesem Modus schaltet sich der entsprechende Ausgang nach der eingestellten Zeit automatisch aus, wenn kein Gerät angeschlossen ist oder die Leistungsaufnahme des angeschlossenen Geräts unter einem bestimmten Schwellenwert liegt (25 W beim AC-Ausgang oder 2 W beim DC/USB-Ausgang). Die Standardeinstellung ist 12 Stunden. Die Dauer des Energiesparmodus kann in der Jackery-App auf 1 H, 2 H, 8 H, 12 H oder 24 H eingestellt werden. Wenn "Nie ausschalten" eingestellt ist, wird der Energiesparmodus deaktiviert.

Um den Energiesparmodus zu deaktivieren, halten Sie sowohl die AC-Stromtaste als auch die POWER-Taste länger als 3 Sekunden gedrückt. Sobald der Energiesparmodus deaktiviert ist, wird das Symbol nicht mehr auf dem LCD angezeigt, und das Produkt schaltet den AC- oder DC/USB-Ausgang nicht mehr automatisch aus.

Wenn Sie Geräte mit geringem Stromverbrauch betreiben (AC <= 25 W oder DC/USB <= 2 W), deaktivieren Sie den Energiesparmodus, damit der Ausgang während des Betriebs nicht automatisch ausgeschaltet wird.

.. image:: _assets/templates/word_template/common_assets/operation/energy_saving.png
   :alt: Platzhalter für die Tastenbedienung des Energiesparmodus.
   :width: 320px


| Halten Sie beide Tasten länger als 3 Sekunden gedrückt.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **HINWEIS**
     - Der Energiesparmodus kehrt nach dem Einschalten in seinen vorherigen Zustand zurück. Für einen Moduswechsel ist ein manuelles Umschalten erforderlich.


LED-LICHT EIN/AUS
-----------------

Die LED-Leuchte verfügt über zwei Modi: Lichtmodus und SOS-Modus. Halten Sie in jedem Modus die LED-Lichttaste gedrückt, um das Licht auszuschalten.

.. image:: _assets/templates/word_template/common_assets/operation/led_light.png
   :alt: Platzhalter für den LED-Licht-Modus.
   :width: 360px

|
| Drücken Sie die LED-Lichttaste einmal, um das Licht einzuschalten.
| Drücken Sie sie erneut, um in den SOS-Modus zu wechseln.
| Drücken Sie sie ein drittes Mal, um das Licht auszuschalten.

Wiederaufnahmefunktion für AC- und DC-Ausgänge
----------------------------------------------

Die Wiederaufnahmefunktion für AC- und DC-Ausgänge ist standardmäßig deaktiviert. Aktivieren Sie diese Funktion in der Jackery-App, damit das Gerät den Status der AC- und DC-Ausgänge speichert und die AC- und DC-Ausgänge unter festgelegten Bedingungen automatisch wiederherstellt.

+-------------------------------------------------------------------+-------------------------------------------------------------+
| Bedingungen für automatische Wiederherstellung                    | Bedingungen ohne automatische Wiederherstellung             |
+===================================================================+=============================================================+
| Einschalten/Neustart nach Abschalten oder Neustart                | Manuelles Ausschalten der Ausgänge (Taste/App)              |
+-------------------------------------------------------------------+-------------------------------------------------------------+
| Batterie-SOC ≥ Entladegrenze +10% nach Erreichen der Grenze       | Ausgang im Energiesparmodus deaktiviert                     |
|                                                                   +-------------------------------------------------------------+
|                                                                   | Schutzbedingter Ausgang deaktiviert                         |
+-------------------------------------------------------------------+-------------------------------------------------------------+
| OTA-Update abgeschlossen                                          | Durch Entlade-Timer gesteuerter Ausgang deaktiviert         |
+-------------------------------------------------------------------+-------------------------------------------------------------+

LCD-ANZEIGE
-----------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="Platzhalter für den LCD-Anzeigemodus." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Kurzzeitig an</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Ein</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Drücken Sie die POWER-Taste oder während das Produkt geladen wird.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Aus</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Drücken Sie die POWER-Taste.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Autom. aus</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Die LCD-Anzeige schaltet sich nach 2 Minuten Inaktivität automatisch aus und wechselt in den Schlafmodus.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Dauerhaft an (beim Laden oder Entladen)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Ein</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Drücken Sie die POWER-Taste zweimal, wenn das Produkt eingeschaltet ist.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Aus</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Drücken Sie die POWER-Taste.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Autom. aus</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Die LCD-Anzeige schaltet sich nach 2 Stunden Inaktivität automatisch aus.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{Kurzzeitig an}{Ein}{Drücken Sie die POWER-Taste oder während das Produkt geladen wird.}{Aus}{Drücken Sie die POWER-Taste.}{Autom. aus}{Die LCD-Anzeige schaltet sich nach 2 Minuten Inaktivität automatisch aus und wechselt in den Schlafmodus.}
      \HBLcdModeSecondGroup{Dauerhaft an (beim Laden oder Entladen)}{Ein}{Drücken Sie die POWER-Taste zweimal, wenn das Produkt eingeschaltet ist.}{Aus}{Drücken Sie die POWER-Taste.}{Autom. aus}{Die LCD-Anzeige schaltet sich nach 2 Stunden Inaktivität automatisch aus.}
      \end{HBLcdModeTable}

Sie können den Bildschirm-Anzeigemodus auch in der Jackery-App einstellen.

TASTENKOMBINATION
-----------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Tasten
     - Bedienung
     - Funktion
   * - POWER-Taste + AC-Stromtaste
     - Beide 3 s lang gedrückt halten
     - Energiesparmodus ein-/ausschalten
   * - POWER-Taste + DC/USB-Stromtaste
     - Beide 3 s lang gedrückt halten
     - WLAN und Bluetooth zurücksetzen
   * - DC/USB-Stromtaste + AC-Stromtaste
     - Beide 1 s lang gedrückt halten
     - WLAN und Bluetooth ein-/ausschalten
   * - POWER-Taste + LED-Lichttaste
     - Beide 1 s lang gedrückt halten
     - Notfall-Lademodus ein-/ausschalten
