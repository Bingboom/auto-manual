5. WAŻNE INSTRUKCJE DOTYCZĄCE BEZPIECZEŃSTWA
============================================

.. container:: hb-source-operation hb-source-note

   Podczas pracy pojazdu ładowarka DC-DC wykorzystuje nadwyżkę mocy generatora do ładowania przenośnej stacji zasilającej. Rzeczywista moc ładowania zależy od warunków jazdy, modelu pojazdu oraz jego ogólnego stanu.


Aby zapewnić bezpieczną eksploatację, przestrzegaj poniższych wytycznych:

- Zachowaj niniejszą instrukcję do wykorzystania w przyszłości.

- Zawsze używaj lub przechowuj produkt w warunkach określonych w tej instrukcji.

- Przeczytaj wszystkie instrukcje i ostrzeżenia dotyczące tego produktu, akumulatora samochodowego oraz stacji zasilającej Jackery, a także dołączone do nich instrukcje obsługi.

- Nie demontuj produktu ani nie wymieniaj jego części bez upoważnienia, ponieważ spowoduje to utratę gwarancji i może uszkodzić produkt. Skontaktuj się z działem obsługi klienta Jackery w celu wymiany podzespołów.

Kompatybilność produktu
-----------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: !
      :width: 40px

   Ten produkt jest kompatybilny wyłącznie z przenośnymi stacjami zasilającymi Jackery wyposażonymi w port wejściowy DC8020. Surowo zabrania się stosowania adapterów do podłączania tego produktu do portu wejściowego DC7909 lub USB-C przenośnej stacji zasilającej. Takie podłączenie może spowodować uszkodzenie urządzenia, pożar, a nawet wybuch, stwarzając poważne zagrożenie dla bezpieczeństwa osobistego.


- Ten produkt jest kompatybilny wyłącznie z akumulatorami samochodowymi 12 V / 24 V. Przed użyciem produktu upewnij się, że znamionowe napięcie pojazdu wynosi 12 V lub 24 V, i zawsze przestrzegaj zasad bezpieczeństwa elektrycznego podczas użytkowania.

- Ten produkt jest kompatybilny z przenośnymi stacjami zasilającymi Jackery wyposażonymi w port wejściowy DC8020. Informacje o niektórych kompatybilnych modelach znajdują się w poniższej tabeli. Aby uzyskać więcej informacji, skontaktuj się z obsługą klienta lub odwiedź oficjalną stronę Jackery.

.. list-table::
   :header-rows: 1

   * - Przenośna stacja zasilająca
     - Pojemność
     - Napięcie i prąd ładowania
     - Moc ładowania
     - Czas ładowania (0-100%)
   * - Explorer 1000 Plus
     - 1265 Wh
     - Około 50 V, 8 A
     - Około 400 W
     - Około 3,5 godziny
   * - Explorer 1000 v2
     - 1070 Wh
     - Około 50 V, 8 A
     - Około 400 W
     - Około 3,0 godziny
   * - Explorer 2000 Plus
     - 2042 Wh
     - Około 50 V, 12A
     - Około 600W
     - Około 3,7 godziny
   * - Explorer 2000 v2
     - 2042 Wh
     - Około 50 V, 8 A
     - Około 400 W
     - Około 5,6 godziny
   * - Explorer 3000 Pro
     - 3024 Wh
     - Około 50 V, 12A
     - Około 600W
     - Około 5,5 godziny
   * - Explorer 3000 v2
     - 3072 Wh
     - Około 50 V, 12A
     - Około 600W
     - Około 5,6 godziny

Uwaga: Dane dotyczące czasu ładowania dla tego produktu opierają się na symulowanych testach przeprowadzonych w stałej temperaturze 25°C. W rzeczywistym użytkowaniu moc ładowania może się różnić w zależności od warunków jazdy, modelu pojazdu oraz jego ogólnego stanu. Na czas ładowania mogą również wpływać zmiany temperatury otoczenia. Standardowe środowisko testowe: Stała temperatura 25°C Źródło danych: Jackery Lab

.. image:: renderers/web/assets/ja_ad600a_eu_en/status_device.png
   :alt: status_device
   :width: 100%
   :class: hb-status-device-art

.. container:: hb-source-operation hb-source-power

   .. rubric:: Włączanie produktu



   ① Krótkie naciśnięcie przycisku zasilania: Gdy nie ma sygnału ACC, możesz włączyć urządzenie, krótko naciskając przycisk zasilania. 

   ② Włączanie poprzez sygnał ACC: Jeśli przewód ACC jest podłączony, urządzenie włączy się automatycznie po wykryciu sygnału ACC (np. po uruchomieniu pojazdu).

   .. rubric:: Tryb czuwania i wyłączanie

   Gdy nie ma sygnału ACC lub napięcie spadnie poniżej progu uruchomienia, produkt przejdzie w tryb czuwania. Jeśli tryb czuwania trwa dłużej niż 24 godziny lub napięcie spadnie poniżej progu ochrony, urządzenie wyłączy się automatycznie. Aby je ponownie uruchomić, wykonaj opisane powyżej kroki. W trybie czuwania, jeśli nie ma sygnału ACC, możesz również ręcznie wyłączyć urządzenie, naciskając i przytrzymując przycisk zasilania przez 3 sekundy.


.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - Stan wskaźnika
        - Kolor wskaźnika
        - Stan produktu
        - Uwagi
      * - Zaświecony
        - :hb-lamp-green:`Zielony`
        - Ładowanie
        - /
      * - Zaświecony
        - :hb-lamp-red:`Czerwony`
        - Nieprawidłowość
        - W przypadku wykrycia jakichkolwiek problemów niezwłocznie skontaktuj się z działem obsługi klienta Jackery.
      * - Miga
        - :hb-lamp-blinking:`Zielony`
        - Połączenie jest prawidłowe, oczekiwanie na ładowanie.
        - Jeśli ten sam problem występuje po podłączeniu przenośnej stacji zasilającej, przyczyny mogą być następujące: 1. Niestabilne połączenie między przewodem wyjściowym a przenośną stacją zasilającą. 2. Uszkodzony przewód. 3. Przenośna stacja zasilająca jest w pełni naładowana. Jeśli problem nie ustępuje po przeprowadzeniu procedury rozwiązywania problemów, skontaktuj się z działem obsługi klienta Jackery w celu uzyskania wsparcia.
      * - Zgaszony
        - :hb-lamp-off:`Brak koloru`
        - Produkt jest wyłączony.
        - Jeśli problem nie ustąpi po podłączeniu wszystkich przewodów i uruchomieniu pojazdu, skontaktuj się z działem obsługi klienta Jackery.


