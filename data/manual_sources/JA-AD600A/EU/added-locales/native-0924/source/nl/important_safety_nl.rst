5. BELANGRIJKE VEILIGHEIDSINSTRUCTIES
=====================================

.. container:: hb-source-operation hb-source-note

   Tijdens het gebruik van het voertuig gebruikt de DC-DC-oplader het overtollige vermogen van de generator om het draagbare powerstation op te laden. Het werkelijke oplaadvermogen varieert afhankelijk van de rijomstandigheden, voertuigmodel en algemene toestand.


Om veilig gebruik te garanderen, is het van cruciaal belang om de volgende richtlijnen in acht te nemen:

- Bewaar deze handleiding voor toekomstig gebruik.

- Gebruik of bewaar het product altijd onder de in deze handleiding gespecificeerde omstandigheden.

- Lees alle instructies en waarschuwingen op dit product, de auto-accu en het Jackery-powerstation, evenals de bijbehorende gebruikershandleidingen.

- Demonteer het product niet en vervang geen onderdelen zonder toestemming, omdat dit de garantie doet vervallen en het product kan beschadigen. Neem contact op met de klantenservice van Jackery voor het vervangen van onderdelen.

Productcompatibiliteit
----------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: !
      :width: 40px

   Dit product is alleen compatibel met Jackery draagbare powerstations met een DC8020-ingangspoort. Het is gebruikers ten strengste verboden om dit product met adapters aan te sluiten op een DC7909- of USB-C-ingangspoort van een draagbaar powerstation. Een dergelijke aansluiting kan apparaatschade, brand of zelfs explosie veroorzaken, wat ernstige risico's voor de persoonlijke veiligheid met zich meebrengt.


- Dit product is uitsluitend compatibel met 12 V/24 V auto-accu's. Voordat u het product gebruikt, zorgt u ervoor dat de nominale spanning van uw voertuig 12 V of 24 V is. Volg tijdens het gebruik altijd de richtlijnen inzake elektrische veiligheid op.

- Dit product is compatibel met Jackery draagbare powerstations die zijn uitgerust met een DC8020-ingangspoort. Raadpleeg de onderstaande tabel voor enkele compatibele modellen. Neem voor meer informatie contact op met de klantenservice of bezoek de officiële website van Jackery.

.. list-table::
   :header-rows: 1

   * - Draagbare powerstation
     - Capaciteit
     - Oplaadspanning en -stroom
     - Oplaadvermo gen
     - Oplaadtijd (0-100%)
   * - Explorer 1000 Plus
     - 1265 Wh
     - Ongeveer 50 V 8A
     - Ongeveer 400W
     - Ongeveer 3,5 uur
   * - Explorer 1000 v2
     - 1070 Wh
     - Ongeveer 50 V 8A
     - Ongeveer 400W
     - Ongeveer 3,0 uur
   * - Explorer 2000 Plus
     - 2042 Wh
     - Ongeveer 50 V 12A
     - Ongeveer 600W
     - Ongeveer 3,7 uur
   * - Explorer 2000 v2
     - 2042 Wh
     - Ongeveer 50 V 8A
     - Ongeveer 400W
     - Ongeveer 5,6 uur
   * - Explorer 3000 Pro
     - 3024 Wh
     - Ongeveer 50 V 12A
     - Ongeveer 600W
     - Ongeveer 5,5 uur
   * - Explorer 3000 v2
     - 3072 Wh
     - Ongeveer 50 V 12A
     - Ongeveer 600W
     - Ongeveer 5,6 uur

Opmerking: De informatie over de oplaadtijd van dit product is gebaseerd op gesimuleerde tests die zijn uitgevoerd bij een constante temperatuur van 25 °C. In de praktijk kan het oplaadvermogen variëren afhankelijk van rijomstandigheden, voertuigmodel en algemene toestand. Oplaadtijden kunnen ook worden beïnvloed door veranderingen in de omgevingstemperatuur. Standaard testomgeving: Constant 25°C Gegevensbron: Jackery Lab

.. image:: renderers/web/assets/ja_ad600a_eu_en/status_device.png
   :alt: status_device
   :width: 100%
   :class: hb-status-device-art

.. container:: hb-source-operation hb-source-power

   .. rubric:: Het product inschakelen



   ① Druk kort op de aan/uit-knop: Wanneer er geen ACC-signaalingang is, kunt u het apparaat inschakelen door kort op de aan/uit-knop te drukken. 

   ② Inschakelen via ACC-signaal: Indien de ACC-kabel is aangesloten, wordt het apparaat automatisch ingeschakeld zodra het een ACC-signaalingang detecteert (bijvoorbeeld nadat het voertuig is gestart).

   .. rubric:: Stand-bymodus en uitschakelen

   Wanneer er geen ACC-signaalingang is of de spanning onder de startdrempelwaarde zakt, gaat het product in de stand-bymodus. Als de stand-bymodus langer dan 24 uur duurt of de spanning onder de beschermingsdrempelwaarde zakt, wordt het apparaat automatisch uitgeschakeld. Om het opnieuw te starten, volgt u dezelfde stappen als hierboven beschreven. In de stand-bymodus kunt u, als er geen ACC-signaalingang is, het apparaat ook handmatig uitschakelen door de aan/uit-knop 3 seconden ingedrukt te houden.


.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - Lampstatus
        - Lampkleur
        - Productstatus
        - Opmerkingen
      * - Continu
        - :hb-lamp-green:`Groen`
        - Opladen
        - /
      * - Continu
        - :hb-lamp-red:`RED`
        - Afwijkend
        - Als er problemen worden geconstateerd, neem dan onmiddellijk contact op met de klantenservice van Jackery voor ondersteuning.
      * - Knipperend
        - :hb-lamp-blinking:`Groen`
        - Normale verbinding, in afwachting op het opladen.
        - Als hetzelfde probleem optreedt na het aansluiten van het draagbare powerstation, kan dit mogelijke oorzaken hebben: 1. Onstabiele verbinding tussen de uitgangskabel en het draagbare powerstation. 2. Beschadigde kabel. 3. Het draagbare powerstation is volledig opgeladen. Als het probleem na het oplossen ervan aanhoudt, neem dan contact op met de klantenservice van Jackery voor ondersteuning.
      * - Geen licht
        - :hb-lamp-off:`Geen kleur`
        - Het product is niet ingeschakeld.
        - Als het probleem na het voltooien van de bedrading en het starten van het voertuig blijft bestaan, neem dan contact op met de klantenservice van Jackery.


