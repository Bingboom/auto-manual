5. IMPORTANTI ISTRUZIONI DI SICUREZZA
=====================================

.. container:: hb-source-operation hb-source-note

   Durante il funzionamento del veicolo, il Jackery DC-DC Charger utilizza la potenza in eccesso del generatore per caricare la centrale elettrica portatile. La potenza di carica effettiva dipende dalle condizioni di guida, dal modello del veicolo e dallo stato generale del veicolo.


Per garantire un funzionamento sicuro, è fondamentale osservare le seguenti linee guida:

- Conservare questo manuale per future consultazioni.

- Utilizzare o conservare sempre il prodotto nelle condizioni specificate nel presente manuale.

- Leggere tutte le istruzioni e le avvertenze relative a questo prodotto, alla batteria dell’auto e alla centrale elettrica portatile Jackery, nonché i rispettivi manuali utente.

- Non smontare il prodotto né sostituirne i componenti senza autorizzazione, poiché ciò invaliderà la garanzia e potrebbe danneggiare il prodotto. Per la sostituzione dei componenti, rivolgersi al servizio clienti Jackery.

Compatibilità del prodotto
--------------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: !
      :width: 40px

   Questo prodotto è compatibile solo con centrali elettriche portatili Jackery dotate di una porta di ingresso DC8020. È severamente vietato utilizzare adattatori per collegare questo prodotto alla porta di ingresso DC7909 o USB-C di una centrale elettrica portatile. Tale collegamento può causare danni al dispositivo, incendi o persino esplosioni, con gravi rischi per la sicurezza personale.


- Questo prodotto è compatibile solo con batterie per auto da 12V/24V. Prima di utilizzare il prodotto, assicurarsi che la tensione nominale del veicolo sia di 12V o 24V e seguire sempre le linee guida di sicurezza elettrica durante l’uso.

- Questo prodotto è compatibile con centrali elettriche portatili Jackery dotate di una porta di ingresso DC8020. Consultare la tabella seguente per alcuni modelli compatibili. Per ulteriori informazioni, contattare il servizio clienti o visitare il sito ufficiale Jackery.

.. list-table::
   :header-rows: 1

   * - Centrale elettrica portatile
     - Capacità corrente
     - Tensione e di carica
     - Potenza di carica
     - Tempo di ricarica (0-100%)
   * - Explorer 1000 Plus 1265
     - Wh
     - Circa 50V 8A
     - Circa 400W
     - Circa 3,5 ore
   * - Explorer 1000 v2 1070
     - Wh
     - Circa 50V 8A
     - Circa 400W
     - Circa 3,0 ore
   * - Explorer 2000 Plus 2042
     - Wh Circa
     - 50V 12A
     - Circa 600W
     - Circa 3,7 ore
   * - Explorer 2000 v2 2042
     - Wh
     - Circa 50V 8A
     - Circa 400W
     - Circa 3,7 ore
   * - Explorer 3000 Pro 3024
     - Wh
     - Circa 50V 8A
     - Circa 600W
     - Circa 5,5 ore
   * - Explorer 3000 v2 3072
     - Wh Circa
     - 50V 12A
     - Circa 600W
     - Circa 5,6 ore

Nota: I dati relativi al tempo di carica di questo prodotto si basano su test simulati condotti a una temperatura costante di 25°C. Nell’uso effettivo, la potenza di carica può variare in base alle condizioni di guida, al modello del veicolo e al suo stato generale. I tempi di ricarica possono essere influenzati anche da variazioni della temperatura ambiente. Ambiente di prova standard: Costante a 25 °C Fonte dei dati: Jackery Lab

.. image:: renderers/web/assets/ja_ad600a_eu_en/status_device.png
   :alt: status_device
   :width: 100%
   :class: hb-status-device-art

.. container:: hb-source-operation hb-source-power

   .. rubric:: Accensione del prodotto



   1. Premere brevemente il pulsante di alimentazione: In assenza di segnale ACC, è possibile accendere il dispositivo premendo brevemente il pulsante di alimentazione. 

   2. Accensione tramite segnale ACC: Se il cavo ACC è collegato, il dispositivo si accende automaticamente quando rileva un segnale ACC in ingresso (ad esempio, dopo l’avvio del veicolo).

   .. rubric:: Standby e spegnimento

   In assenza di segnale ACC in ingresso o se la tensione scende al di sotto della soglia di avvio, il prodotto entra in modalità standby. Se lo standby dura più di 24 ore o la tensione scende sotto la soglia di protezione, il dispositivo si spegnerà automaticamente. Per riavviarlo, seguire gli stessi passaggi descritti sopra. In modalità standby, se non viene rilevato alcun segnale ACC, è possibile spegnere manualmente il dispositivo anche tenendo premuto il pulsante di alimentazione per 3 secondi.


.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - Stato della spia
        - Colore della spia
        - Stato del prodotto
        - Note
      * - Fisso
        - :hb-lamp-green:`Verde`
        - In carica
        - /
      * - Fisso
        - :hb-lamp-red:`Rosso`
        - Anomalia
        - Se vengono rilevati problemi, contattare immediatamente il servizio clienti Jackery per assistenza.
      * - Lampeggiante
        - :hb-lamp-blinking:`Verde`
        - Connessione normale, in attesa di ricarica.
        - Se lo stesso problema si verifica dopo aver collegato la centrale elettrica portatile, le possibili cause includono: 1. Connessione instabile tra il cavo di uscita e la centrale elettrica portatile. 2. Cavo danneggiato. 3. La centrale elettrica portatile è completamente carica. Se il problema persiste anche dopo aver effettuato la risoluzione dei problemi, contattare l'assistenza clienti di Jackery.
      * - Nessuna luce
        - :hb-lamp-off:`Nessun colore`
        - Il prodotto è acceso.
        - Se il problema persiste anche dopo aver non completato il cablaggio e avviato il veicolo, contattare il servizio clienti Jackery.


