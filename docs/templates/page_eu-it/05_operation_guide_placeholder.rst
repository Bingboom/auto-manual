OPERAZIONI
==========

ACCENSIONE/SPEGNIMENTO
----------------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Segnaposto operazione accensione/spegnimento.
   :width: 360px

| Accensione: premi una volta.
| Spegnimento: tieni premuto per 3 s.
|
| **Tempo di standby predefinito:** |DEFAULT_STANDBY_DURATION|.
| Il prodotto si spegnerà automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattività, senza ricarica o scarica.
| \*Il tempo di standby può essere impostato nell'App Jackery.
| Quando la Modalità risparmio energetico e attiva, il prodotto si spegnerà automaticamente dopo |ENERGY_SAVING_AUTO_OFF_DURATION| se l'uscita CA o DC/USB e attiva ma il prodotto non sta caricando o scaricando.

USCITA CA ATTIVA/DISATTIVA
--------------------------

**Prerequisito**: il prodotto e acceso.

.. image:: templates/word_template/common_assets/operation/ac_output.png
   :alt: Segnaposto operazione uscita CA attiva/disattiva.
   :width: 360px

| 
| **Accensione**
| Premi una volta
| **Spegnimento**
| Premi una volta
| 

USCITA CC 12 V/ USB ATTIVA/DISATTIVA
------------------------------------

**Prerequisito**: il prodotto e acceso.

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: Segnaposto operazione uscita CC USB attiva/disattiva.
   :width: 360px

| 
| **Accensione**
| Premi una volta
| **Spegnimento**
| Premi una volta
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENZIONE**
     -
       - Collega |PRODUCT_NAME| solo a dispositivi o accessori conformi alle clausole 6.3, 6.4 e 6.5 della norma IEC/EN/UL 62368-1 (o di altri standard equivalenti).
       - Per ottenere la massima potenza di uscita, usa il cavo da USB-C a USB-C da 5 A (20 V CC/5 A, 100 W).

| Il prodotto può ricaricare la batteria dell'auto utilizzando il cavo Jackery per la ricarica della batteria dell'auto a 12 V, venduto separatamente e disponibile sul nostro sito web.
 

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENZIONE**
     -
       - La porta CC 12 V e compatibile solo con batterie per auto da 12 V e non e adatta a sistemi da 24 V.
       - Non avviare l'auto mentre il prodotto sta ricaricando la batteria dell'auto tramite la porta di uscita CC da 12 V, poiché ciò potrebbe danneggiare il prodotto.
       - Questa funzione e destinata solo all'uso di emergenza e non può ricaricare una batteria dell'auto completamente scarica o danneggiata.

MODALITA RISPARMIO ENERGETICO
-----------------------------

Per evitare un consumo inutile della batteria dovuto al mancato spegnimento dell'uscita, il prodotto abilita per impostazione predefinita la Modalità risparmio energetico. Quando l'uscita CA o CC e attiva, l'icona della Modalità risparmio energetico viene visualizzata sullo schermo LCD. In questa modalità, se non e collegato alcun dispositivo oppure il consumo del dispositivo collegato e inferiore a una certa soglia (|ENERGY_SAVING_AC_THRESHOLD| per l'uscita CA o |ENERGY_SAVING_DC_THRESHOLD| per l'uscita DC/USB), l'uscita corrispondente si spegnerà automaticamente dopo il tempo impostato. L'impostazione predefinita e |ENERGY_SAVING_AUTO_OFF_DURATION|. La durata della Modalità risparmio energetico può essere impostata nell'App Jackery su 1 H, 2 H, 8 H, 12 H o 24 H. Se viene impostata su Mai spegnimento, la Modalità risparmio energetico sarà disattivata.

Per disattivare la Modalità risparmio energetico, tieni premuti per più di 3 secondi sia il pulsante CA sia il pulsante POWER principale. Una volta disattivata la Modalità risparmio energetico, l'icona non comparirà più sullo schermo LCD e il prodotto non spegnerà automaticamente l'uscita CA o DC/USB.

Quando si alimentano dispositivi a basso consumo (CA <= |ENERGY_SAVING_AC_THRESHOLD| oppure DC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), disattiva la Modalità risparmio energetico per evitare che l'uscita si spenga automaticamente durante il funzionamento.

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Segnaposto operazione tasti modalità risparmio energetico.
   :width: 320px


| Tieni premuti entrambi i pulsanti per più di 3 secondi.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTA**
     - La Modalità risparmio energetico riprende il suo stato precedente dopo l'accensione. Per cambiare modalità e necessario un intervento manuale.


LUCE LED ON/OFF
---------------

La luce LED ha due modalità: modalità luce e modalità SOS. In qualsiasi modalità, tieni premuto il pulsante della luce LED per spegnere la luce.

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: Segnaposto operazione modalità luce LED.
   :width: 360px

|
| Premi una volta il pulsante luce LED per accendere la luce.
| Premilo di nuovo per passare alla modalità SOS.
| Premilo una terza volta per spegnere la luce.

Funzione di ripristino delle uscite CA e CC
-------------------------------------------

La funzione di ripristino delle uscite CA e CC è disattivata per impostazione predefinita. Attivare questa funzione nell’App Jackery per consentire al dispositivo di memorizzare lo stato delle uscite CA e CC e ripristinare automaticamente le uscite CA e CC in condizioni definite.

+------------------------------------------------------------------------+------------------------------------------------------------------+
| Condizioni di ripristino automatico                                    | Condizioni senza ripristino automatico                           |
+========================================================================+==================================================================+
| Accensione/Riavvio dopo lo spegnimento o il riavvio                    | Spegnimento manuale delle uscite (pulsante/App)                  |
+------------------------------------------------------------------------+------------------------------------------------------------------+
| SOC batteria ≥ limite di scarica +10% al raggiungimento del limite     | Spegnimento delle uscite in modalità risparmio energetico        |
|                                                                        +------------------------------------------------------------------+
|                                                                        | Spegnimento delle uscite attivato da protezione                  |
+------------------------------------------------------------------------+------------------------------------------------------------------+
| Aggiornamento OTA completato                                           | Spegnimento delle uscite attivato dal timer di scarica           |
+------------------------------------------------------------------------+------------------------------------------------------------------+

SCHERMO LCD
-----------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="Segnaposto modalità display LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Acceso brevemente</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Accendi</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante POWER principale oppure quando il prodotto e in carica.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegni</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante POWER principale.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegnimento automatico</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Lo schermo LCD si spegne automaticamente ed entra in modalità sleep dopo 2 minuti di inattività.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Acceso fisso (in carica o in scarica)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Accendi</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi due volte il pulsante POWER principale quando il prodotto e acceso.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegni</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante POWER principale.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegnimento automatico</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Lo schermo LCD si spegne automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattività.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{Acceso brevemente}{Accendi}{Premi il pulsante POWER principale oppure quando il prodotto e in carica.}{Spegni}{Premi il pulsante POWER principale.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente ed entra in modalità sleep dopo 2 minuti di inattività.}
      \HBLcdModeSecondGroup{Acceso fisso (in carica o in scarica)}{Accendi}{Premi due volte il pulsante POWER principale quando il prodotto e acceso.}{Spegni}{Premi il pulsante POWER principale.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattività.}
      \end{HBLcdModeTable}

Puoi anche impostare la modalità di visualizzazione dello schermo nell'App Jackery.

COMBINAZIONI DI TASTI
---------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Pulsanti
     - Operazione
     - Funzione
   * - Pulsante POWER principale + Pulsante CA
     - Tieni premuti entrambi per 3 s
     - Attiva/disattiva la Modalità risparmio energetico
   * - Pulsante POWER principale + Pulsante DC/USB
     - Tieni premuti entrambi per 3 s
     - Ripristina Wi-Fi e Bluetooth
   * - Pulsante DC/USB + Pulsante CA
     - Tieni premuti entrambi per 1 s
     - Attiva/disattiva Wi-Fi e Bluetooth
   * - Pulsante POWER principale + Pulsante luce LED
     - Tieni premuti entrambi per 1 s
     - Attiva/disattiva la Modalità di ricarica di emergenza
