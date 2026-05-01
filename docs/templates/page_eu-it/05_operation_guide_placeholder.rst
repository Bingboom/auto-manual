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
| Il prodotto si spegnera automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattivita, senza ricarica o scarica.
| \*Il tempo di standby puo essere impostato nell'App Jackery.
| Quando la Modalita risparmio energetico e attiva, il prodotto si spegnera automaticamente dopo |ENERGY_SAVING_AUTO_OFF_DURATION| se l'uscita CA o CC/USB e attiva ma il prodotto non sta caricando o scaricando.

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
       - Collega Jackery Explorer 1000 solo a dispositivi o accessori conformi alle clausole 6.3, 6.4 e 6.5 della norma IEC/EN/UL 62368-1 (o di altri standard equivalenti).
       - Per ottenere la massima potenza di uscita, usa il cavo da USB-C a USB-C da 5 A (20 V CC/5 A, 100 W).

| Il prodotto puo ricaricare la batteria dell'auto utilizzando il cavo Jackery per la ricarica della batteria dell'auto a 12 V, venduto separatamente e disponibile sul nostro sito web.
 

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENZIONE**
     -
       - La porta CC 12 V e compatibile solo con batterie per auto da 12 V e non e adatta a sistemi da 24 V.
       - Non avviare l'auto mentre il prodotto sta ricaricando la batteria dell'auto tramite la porta di uscita CC da 12 V, poiche cio potrebbe danneggiare il prodotto.
       - Questa funzione e destinata solo all'uso di emergenza e non puo ricaricare una batteria dell'auto completamente scarica o danneggiata.

MODALITA RISPARMIO ENERGETICO
-----------------------------

Per evitare un consumo inutile della batteria dovuto al mancato spegnimento dell'uscita, il prodotto abilita per impostazione predefinita la Modalita risparmio energetico. Quando l'uscita CA o CC e attiva, l'icona della Modalita risparmio energetico viene visualizzata sullo schermo LCD. In questa modalita, se non e collegato alcun dispositivo oppure il consumo del dispositivo collegato e inferiore a una certa soglia (|ENERGY_SAVING_AC_THRESHOLD| per l'uscita CA o |ENERGY_SAVING_DC_THRESHOLD| per l'uscita CC/USB), l'uscita corrispondente si spegnera automaticamente dopo il tempo impostato. L'impostazione predefinita e |ENERGY_SAVING_AUTO_OFF_DURATION|. La durata della Modalita risparmio energetico puo essere impostata nell'App Jackery su 1 H, 2 H, 8 H, 12 H o 24 H. Se viene impostata su Mai spegnimento, la Modalita risparmio energetico sara disattivata.

Per disattivare la Modalita risparmio energetico, tieni premuti per piu di 3 secondi sia il pulsante di alimentazione CA sia il pulsante di alimentazione. Una volta disattivata la Modalita risparmio energetico, l'icona non comparira piu sullo schermo LCD e il prodotto non spegnera automaticamente l'uscita CA o USB.

Quando si alimentano dispositivi a basso consumo (CA <= |ENERGY_SAVING_AC_THRESHOLD| oppure CC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), disattiva la Modalita risparmio energetico per evitare che l'uscita si spenga automaticamente durante il funzionamento.

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Segnaposto operazione tasti modalita risparmio energetico.
   :width: 320px


| Tieni premuti entrambi i pulsanti per piu di 3 secondi.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTA**
     - La Modalita risparmio energetico riprende il suo stato precedente dopo l'accensione. Per cambiare modalita e necessario un intervento manuale.


LUCE LED ON/OFF
---------------

La luce LED ha due modalita: modalita luce e modalita SOS. In qualsiasi modalita, tieni premuto il pulsante della luce LED per spegnere la luce.

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: Segnaposto operazione modalita luce LED.
   :width: 360px

|
| Premi una volta il pulsante luce LED per accendere la luce.
| Premilo di nuovo per passare alla modalita SOS.
| Premilo una terza volta per spegnere la luce.

Funzione di ripristino delle uscite CA e CC
-------------------------------------------

Questa funzione memorizza lo stato delle uscite e ripristina automaticamente le uscite CA e CC in determinate condizioni.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Condizioni di ripristino automatico
     - Condizioni senza ripristino automatico
   * - Accensione/Riavvio dopo lo spegnimento o il riavvio
     - Spegnimento manuale delle uscite (pulsante/App)
   * - SOC della batteria ≥ limite di scarica +10% dopo aver raggiunto il limite
     - Spegnimento delle uscite in modalità risparmio energetico
   * -
     - Spegnimento delle uscite attivato da protezione
   * - Aggiornamento OTA completato
     - Spegnimento delle uscite attivato dal timer di scarica

SCHERMO LCD
-----------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="Segnaposto modalita display LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Acceso brevemente</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Accendi</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante di alimentazione oppure quando il prodotto e in carica.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegni</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante di alimentazione.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegnimento automatico</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Lo schermo LCD si spegne automaticamente ed entra in modalita sleep dopo 2 minuti di inattivita.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Acceso fisso (in carica o in scarica)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Accendi</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi due volte il pulsante di alimentazione quando il prodotto e acceso.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegni</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante di alimentazione.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Spegnimento automatico</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Lo schermo LCD si spegne automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattivita.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{Acceso brevemente}{Accendi}{Premi il pulsante di alimentazione oppure quando il prodotto e in carica.}{Spegni}{Premi il pulsante di alimentazione.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente ed entra in modalita sleep dopo 2 minuti di inattivita.}
      \HBLcdModeSecondGroup{Acceso fisso (in carica o in scarica)}{Accendi}{Premi due volte il pulsante di alimentazione quando il prodotto e acceso.}{Spegni}{Premi il pulsante di alimentazione.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattivita.}
      \end{HBLcdModeTable}

Puoi anche impostare la modalita di visualizzazione dello schermo nell'App Jackery.

COMBINAZIONI DI TASTI
---------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Pulsanti
     - Operazione
     - Funzione
   * - Pulsante di alimentazione + Pulsante di alimentazione CA
     - Tieni premuti entrambi per 3 s
     - Attiva/disattiva la Modalita risparmio energetico
   * - Pulsante di alimentazione + Pulsante di alimentazione CC/USB
     - Tieni premuti entrambi per 3 s
     - Ripristina Wi-Fi e Bluetooth
   * - Pulsante di alimentazione CC/USB + Pulsante di alimentazione CA
     - Tieni premuti entrambi per 1 s
     - Attiva/disattiva Wi-Fi e Bluetooth
   * - Pulsante di alimentazione + Pulsante luce LED
     - Tieni premuti entrambi per 1 s
     - Attiva/disattiva la Modalita di ricarica di emergenza
