OPERAZIONI
==========

ACCENSIONE/SPEGNIMENTO
----------------------

.. image:: asset:operation/main_power
   :alt: Operazione accensione/spegnimento.
   :width: 360px

| Accensione: premi una volta.
| Spegnimento: tieni premuto per 3 s.
|
| **Tempo di standby predefinito:** |DEFAULT_STANDBY_DURATION|.
| Il prodotto si spegnerà automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattività, senza ricarica o scarica.
| \*Il tempo di standby può essere impostato nell'App Jackery.
| Quando la Modalità risparmio energetico è attiva, il prodotto si spegnerà automaticamente dopo |ENERGY_SAVING_AUTO_OFF_DURATION| se l'uscita CA o DC/USB è attiva ma il prodotto non sta caricando o scaricando.

USCITA CA ATTIVA/DISATTIVA
--------------------------

**Prerequisito**: il prodotto è acceso.

.. image:: asset:operation/ac_output
   :alt: Operazione uscita CA attiva/disattiva.
   :width: 360px

| 
| **Accensione**
| Premi una volta
| **Spegnimento**
| Premi una volta
| 

USCITA CC 12 V/ USB ATTIVA/DISATTIVA
------------------------------------

**Prerequisito**: il prodotto è acceso.

.. image:: asset:operation/dc_usb_output
   :alt: Operazione uscita CC USB attiva/disattiva.
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
       - **USB-C 100W è una porta di uscita ad alta potenza USB-PD Power Source 3 (PS3).** Se il dispositivo o l'accessorio collegato non soddisfa i requisiti di sicurezza, potrebbe esserci un rischio di incendio. Prima di utilizzare queste porte, assicurarsi che il dispositivo o l'accessorio collegato sia dotato di protezione antincendio.
       - Collega |PRODUCT_NAME| solo a dispositivi o accessori conformi alle clausole 6.3, 6.4 e 6.5 della norma IEC/EN/UL 62368-1 (o di altri standard equivalenti).
       - Per ottenere la massima potenza di uscita, usa il cavo da USB-C a USB-C da 5 A (20 V CC/5 A, 100 W).

| Il prodotto può ricaricare la batteria dell'auto utilizzando il cavo Jackery per la ricarica della batteria dell'auto a 12 V, venduto separatamente e disponibile sul nostro sito web.
 

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **ATTENZIONE**
     -
       - La porta CC 12 V è compatibile solo con batterie per auto da 12 V e non è adatta a sistemi da 24 V.
       - Non avviare l'auto mentre il prodotto sta ricaricando la batteria dell'auto tramite la porta di uscita CC da 12 V, poiché ciò potrebbe danneggiare il prodotto.
       - Questa funzione è destinata solo all'uso di emergenza e non può ricaricare una batteria dell'auto completamente scarica o danneggiata.

MODALITÀ RISPARMIO ENERGETICO
-----------------------------

Per prevenire un consumo inutile della batteria dimenticando di spegnere l'uscita, il prodotto attiva la Modalità di risparmio energetico per impostazione predefinita. Quando il pulsante di alimentazione CA è acceso, l’icona della MODALITÀ DI RISPARMIO ENERGETICO verrà visualizzata sullo schermo LCD. Se non è collegato alcun dispositivo o il consumo del dispositivo collegato è inferiore a una determinata soglia (uscita AC ≤ |ENERGY_SAVING_AC_THRESHOLD| oppure uscita USB-C ≤ |ENERGY_SAVING_DC_THRESHOLD|), il dispositivo spegne automaticamente tutte le uscite dopo |ENERGY_SAVING_AUTO_OFF_DURATION|.

Per disattivare la Modalità risparmio energetico, tenere premuti entrambi i pulsanti di accensione AC e POWER per più di 3 secondi. Il prodotto non disattiva automaticamente l’uscita CA o l’uscita CC/USB.

.. image:: asset:operation/energy_saving
   :alt: Operazione tasti modalità risparmio energetico.
   :width: 320px


| Tieni premuti entrambi i pulsanti per più di 3 secondi.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTA**
     - La Modalità risparmio energetico riprende il suo stato precedente dopo l'accensione. Per cambiare modalità è necessario un intervento manuale.

.. only:: not latex

   .. list-table::
      :header-rows: 0
      :widths: 12 88

      * - **AVVERTENZA**
        - Quando la Modalità di risparmio energetico è attiva, il prodotto disattiva automaticamente l'uscita CA se il consumo energetico del dispositivo collegato rimane basso per il periodo di tempo impostato. Quando si alimentano dispositivi che richiedono un'alimentazione continua, come frigoriferi, router, telecamere di sicurezza o pompe ad aria per acquari, si consiglia di disattivare la Modalità di risparmio energetico per evitare che un'interruzione imprevista ne comprometta il funzionamento.


SCHERMO LCD
-----------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="asset:operation/lcd_mode" alt="Modalità display LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Acceso brevemente</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Accendi</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi il pulsante POWER principale oppure quando il prodotto è in carica.</td>
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
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Premi due volte il pulsante POWER principale quando il prodotto è acceso.</td>
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

      \begin{HBLcdModeTable}{asset:operation/lcd_mode}
      \HBLcdModeFirstGroup{Acceso brevemente}{Accendi}{Premi il pulsante POWER principale oppure quando il prodotto è in carica.}{Spegni}{Premi il pulsante POWER principale.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente ed entra in modalità sleep dopo 2 minuti di inattività.}
      \HBLcdModeSecondGroup{Acceso fisso (in carica o in scarica)}{Accendi}{Premi due volte il pulsante POWER principale quando il prodotto è acceso.}{Spegni}{Premi il pulsante POWER principale.}{Spegnimento automatico}{Lo schermo LCD si spegne automaticamente dopo |DEFAULT_STANDBY_DURATION| di inattività.}
      \end{HBLcdModeTable}

Puoi anche impostare la modalità di visualizzazione dello schermo nell'App Jackery.

.. hb-capability-begin: AC/DC输出记忆恢复

Funzione di ripristino delle uscite CA e CC
-------------------------------------------

Questa funzione memorizza lo stato delle uscite e ripristina automaticamente le uscite CA e CC in determinate condizioni.

+---------------------------------------------------------------------------+------------------------------------------------------------------+
| Condizioni di ripristino automatico                                       | Condizioni senza ripristino automatico                           |
+===========================================================================+==================================================================+
| Accensione/Riavvio dopo lo spegnimento o il riavvio                       | Spegnimento manuale delle uscite (pulsante/App)                  |
+---------------------------------------------------------------------------+------------------------------------------------------------------+
| SOC della batteria ≥ limite di scarica +10% dopo aver raggiunto il limite | Spegnimento delle uscite in modalità risparmio energetico        |
|                                                                           +------------------------------------------------------------------+
|                                                                           | Spegnimento delle uscite attivato da protezione                  |
+---------------------------------------------------------------------------+------------------------------------------------------------------+
| Aggiornamento OTA completato                                              | Spegnimento delle uscite attivato dal timer di scarica           |
+---------------------------------------------------------------------------+------------------------------------------------------------------+

.. hb-capability-end:

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
