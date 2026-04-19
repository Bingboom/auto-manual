OPERACIONES
===========

ENCENDIDO/APAGADO
-----------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Operación de encendido/apagado.
   :width: 360px

| Encendido: Presione una vez.
| Apagado: Mantenga presionado durante 3 segundos.
|
| **Tiempo de espera predeterminado:** |DEFAULT_STANDBY_DURATION|.
| El producto se apagará automáticamente después de |DEFAULT_STANDBY_DURATION| de inactividad, sin carga ni descarga.
| *El tiempo de espera puede configurarse en la aplicación Jackery.*
|
| Cuando el modo de ahorro de energía está activado, el producto se apagará automáticamente después de |ENERGY_SAVING_AUTO_OFF_DURATION| si el |AC_POWER_BUTTON_LABEL_LOWER| o el |DC_USB_POWER_BUTTON_LABEL_LOWER| está encendido, pero el producto no está cargando ni descargando.

ENCENDER/APAGAR SALIDA DE CA
----------------------------

**Requisito previo:** El producto está encendido.

.. image:: templates/word_template/common_assets/operation/ac_output.png
   :alt: Operación de salida de CA.
   :width: 360px

Encendido: Presione una vez.

Apagado: Presione una vez.

ENCENDER/APAGAR SALIDA DE CC 12V/USB
------------------------------------

**Requisito previo:** El producto está encendido.

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: Operación de salida de CC y USB.
   :width: 360px

|
| Encendido: Presione una vez.
| Apagado: Presione una vez.
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **PRECAUCIÓN**
     -
       - **Los puertos USB-C de 100 W son puertos de salida de alta potencia de tipo Fuente de Alimentación 3 (PS3) según USB-PD.** Si el dispositivo o accesorio conectado no cumple los requisitos de seguridad, puede existir riesgo de incendio. Antes de usar estos puertos, asegúrese de que el dispositivo o accesorio conectado tenga protección contra incendios.
       - Conecte |PRODUCT_NAME| únicamente a dispositivos o accesorios que cumplan con las cláusulas 6.3, 6.4 y 6.5 de IEC/EN/UL 62368-1 (u otras normas equivalentes).
       - Para obtener la máxima potencia de salida, utilice el cable USB-C a USB-C de 5 A (20 V CC/5 A, 100 W).

|
| El producto puede cargar la batería de su automóvil utilizando el cable de carga de batería para automóvil Jackery de 12 V, que se vende por separado y está disponible en nuestro sitio web.
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **PRECAUCIÓN**
     -
       - El puerto de CC de 12V solo es compatible con baterías de automóvil de 12V y no es adecuado para sistemas de 24V.
       - No arranque el automóvil mientras el producto está cargando la batería a través del puerto de salida de CC de 12V, ya que podría dañar el producto.
       - Esta función está diseñada únicamente para uso de emergencia y no puede cargar una batería de automóvil agotada o dañada.

MODO DE AHORRO DE ENERGÍA
-------------------------

Para evitar un consumo innecesario de batería por olvidar apagar la salida, el producto activa por defecto el Modo de Ahorro de Energía. Cuando la salida de CA o CC/USB está encendida, el icono del modo de ahorro de energía se mostrará en la pantalla LCD. En este modo, si no hay ningún dispositivo conectado o si el consumo del dispositivo conectado está por debajo de cierto umbral (|ENERGY_SAVING_AC_THRESHOLD| en salida de CA o |ENERGY_SAVING_DC_THRESHOLD| en salida de CC/USB), la salida correspondiente se apagará automáticamente después del tiempo configurado. La configuración predeterminada es |ENERGY_SAVING_AUTO_OFF_DURATION|. La duración del Modo de Ahorro de Energía puede configurarse en la aplicación Jackery en 2 h, 8 h, 12 h o 24 h. Si se establece en "Never Off", el Modo de Ahorro de Energía se desactivará.

Para desactivar el modo de ahorro de energía, mantenga pulsados simultáneamente el |AC_POWER_BUTTON_LABEL_LOWER| y el |MAIN_POWER_BUTTON_LABEL_LOWER| durante más de 3 segundos. Una vez desactivado el modo de ahorro de energía, el icono dejará de mostrarse en la pantalla LCD y el producto no apagará automáticamente la salida de CA o CC/USB.

Cuando alimente dispositivos de baja potencia (CA <= |ENERGY_SAVING_AC_THRESHOLD| o CC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), desactive el modo de ahorro de energía para evitar que la salida se apague automáticamente durante el funcionamiento.

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Operación del modo de ahorro de energía.
   :width: 320px

|
| Mantenga pulsados ambos botones durante 3 segundos.
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTA**
     - El modo de ahorro de energía retoma el estado anterior después del encendido. Es necesario cambiarlo manualmente si se desea modificar el modo.

ENCENDER/APAGAR LA LUZ LED
--------------------------

La luz LED tiene dos modos: modo de iluminación y modo SOS. En cualquier modo, mantenga presionado el botón de la luz LED para apagarla.

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: Operación de la luz LED.
   :width: 360px

|
| Presione una vez el botón de la luz LED para encenderla.
| Presiónelo nuevamente para cambiar al modo SOS.
| Presiónelo una tercera vez para apagar la luz.

PANTALLA LCD
------------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="Modo de pantalla LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">En breve</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Encender</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Presione el botón de encendido principal o cuando el producto se esté cargando.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Apagar</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Presione el botón de encendido principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Apagado automático</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Estable en (durante el estado de carga o descarga)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Encender</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Presione dos veces el botón de encendido principal cuando el producto esté encendido.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Apagar</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Presione el botón de encendido principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Apagado automático</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">La pantalla LCD se apaga automáticamente después de |DEFAULT_STANDBY_DURATION| de inactividad.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begingroup
      \renewcommand{\arraystretch}{1.25}
      \setlength{\tabcolsep}{6pt}
      \begin{tabular}{|m{0.24\linewidth}|m{0.16\linewidth}|m{0.12\linewidth}|m{0.36\linewidth}|}
      \hline
      \multirow{6}{*}{\parbox[c]{0.22\linewidth}{\centering\includegraphics[width=0.20\linewidth]{lcd_mode.png}}}
      & \multirow{3}{*}{\parbox[t]{0.14\linewidth}{En breve}} & Encender & Presione el botón de encendido principal o cuando el producto se esté cargando. \\ \cline{3-4}
      & & Apagar & Presione el botón de encendido principal. \\ \cline{3-4}
      & & Apagado automático & La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad. \\ \cline{2-4}
      & \multirow{3}{*}{\parbox[t]{0.14\linewidth}{Estable en (durante el estado de carga o descarga)}} & Encender & Presione dos veces el botón de encendido principal cuando el producto esté encendido. \\ \cline{3-4}
      & & Apagar & Presione el botón de encendido principal. \\ \cline{3-4}
      & & Apagado automático & La pantalla LCD se apaga automáticamente después de |DEFAULT_STANDBY_DURATION| de inactividad. \\ \hline
      \end{tabular}
      \endgroup

También puede configurar el modo de visualización de la pantalla en la aplicación Jackery.

COMBINACIONES DE TECLAS
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Botones
     - Operación
     - Función
   * - Botón de encendido principal + botón de energía de CA
     - Mantenga pulsados ambos botones durante 3 segundos
     - Encender/apagar el modo de ahorro de energía
   * - Botón de encendido principal + botón de energía CC/USB
     - Mantenga pulsados ambos botones durante 3 segundos
     - Restablecer Wi-Fi y Bluetooth
   * - Botón de energía CC/USB + botón de energía de CA
     - Mantenga pulsados ambos botones durante 1 segundo
     - Encender/apagar Wi-Fi y Bluetooth
   * - Botón de encendido principal + botón de luz LED
     - Mantenga pulsados ambos botones durante 1 segundo
     - Activar/desactivar el modo de carga rápida de emergencia
