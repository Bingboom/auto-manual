OPERACIONES
===========

ENCENDIDO/APAGADO
----------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Operación de encendido/apagado.
   :width: 360px

Encendido: Presione una vez.

Apagado: Mantenga presionado durante 3 s.

**Tiempo de espera predeterminado:** |DEFAULT_STANDBY_DURATION|.

El producto se apagará automáticamente después de |DEFAULT_STANDBY_DURATION| de inactividad, sin carga ni descarga.

*El tiempo de espera puede configurarse en la App Jackery.*

Cuando el modo de ahorro de energía está activado, el producto se apagará automáticamente después de |ENERGY_SAVING_AUTO_OFF_DURATION| si la CA o |DC_USB_POWER_BUTTON_LABEL_LOWER| está activada, pero el producto no está cargando ni descargando.

ENCENDER/APAGAR SALIDA DE CA
---------------------------

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

Encendido: Presione una vez.

Apagado: Presione una vez.

**PRECAUCIÓN**

- **|USB_C_HIGH_POWER_PORT_LABEL| es un puerto de salida de alta potencia USB-PD Power Source 3 (PS3).** Si el dispositivo o accesorio conectado no cumple los requisitos de seguridad, puede existir riesgo de incendio. Antes de usar estos puertos, asegúrese de que el dispositivo o accesorio conectado tenga protección contra incendios.
- Conecte |PRODUCT_NAME| únicamente a dispositivos o accesorios que cumplan con las cláusulas 6.3, 6.4 y 6.5 de IEC/EN/UL 62368-1 (u otras normas equivalentes).
- Para obtener la máxima potencia de salida, utilice el cable oficial Jackery USB-C to USB-C 5A cable (20V DC/5A, 100W).

El producto puede cargar la batería de su automóvil utilizando el Jackery 12V automobile battery charging cable, que se vende por separado y está disponible en nuestro sitio web.

**PRECAUCIÓN**

- El puerto de CC de 12V solo es compatible con baterías de automóvil de 12V y no es adecuado para sistemas de 24V.
- No arranque el automóvil mientras el producto está cargando la batería a través del puerto de salida de CC de 12V, ya que podría dañar el producto.
- Esta función está diseñada únicamente para uso de emergencia y no puede cargar una batería de automóvil agotada o dañada.

MODO DE AHORRO DE ENERGÍA
-------------------------

Para evitar un consumo innecesario de batería por olvidar apagar la salida, el producto activa el Modo de Ahorro de Energía por defecto. Cuando la salida de CA o CC/USB está encendida, el icono del modo de ahorro de energía se mostrará en la pantalla LCD. Si no hay ningún dispositivo conectado, o si el consumo del dispositivo conectado está por debajo de cierto umbral (|ENERGY_SAVING_AC_THRESHOLD| en salida de CA o |ENERGY_SAVING_DC_THRESHOLD| en salida de CC/USB) durante |ENERGY_SAVING_AUTO_OFF_DURATION|, el producto apagará automáticamente las salidas. Configure la duración del Modo de Ahorro de Energía en la App Jackery.

Para desactivar el modo de ahorro de energía, mantenga presionados |AC_POWER_BUTTON_LABEL_LOWER| y |MAIN_POWER_BUTTON_LABEL_LOWER| durante más de 3 segundos. Una vez desactivado, el icono dejará de mostrarse en la pantalla LCD y el producto no apagará automáticamente la salida de CA o USB.

Cuando alimente dispositivos de baja potencia (CA <= |ENERGY_SAVING_AC_THRESHOLD| o CC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), desactive el modo de ahorro de energía para evitar que la salida se apague automáticamente durante el funcionamiento.

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Operación del modo de ahorro de energía.
   :width: 320px

Mantenga presionados ambos botones durante más de 3 segundos.

**NOTA**

El modo de ahorro de energía retoma el estado anterior después del encendido. Es necesario cambiarlo manualmente si se desea modificar el modo.

ENCENDER/APAGAR LA LUZ LED
--------------------------

La luz LED tiene dos modos: modo de iluminación y modo SOS. En cualquier modo, mantenga presionado el botón de la luz LED para apagarla.

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: Operación de la luz LED.
   :width: 360px

Presione una vez el botón de la luz LED para encenderla.

Presiónelo de nuevo para cambiar al modo SOS.

Presiónelo por tercera vez para apagar la luz.

PANTALLA LCD
------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Pantalla
     - Modo
     - Acción
     - Comportamiento
   * - .. image:: templates/word_template/common_assets/operation/lcd_mode.png
          :alt: Modo de pantalla LCD.
          :width: 140px
     - Encendido breve
     - Encender
     - Presione |MAIN_POWER_BUTTON_LABEL| o cuando el producto se esté cargando.
   * -
     - Encendido breve
     - Apagar
     - Presione |MAIN_POWER_BUTTON_LABEL|.
   * -
     - Encendido breve
     - Apagado automático
     - La pantalla LCD se apaga automáticamente y entra en modo de suspensión después de 2 minutos de inactividad.
   * -
     - Encendido continuo (durante la carga o descarga)
     - Encender
     - Presione |MAIN_POWER_BUTTON_LABEL_LOWER| dos veces cuando el producto esté encendido.
   * -
     - Encendido continuo (durante la carga o descarga)
     - Apagar
     - Presione |MAIN_POWER_BUTTON_LABEL|.
   * -
     - Encendido continuo (durante la carga o descarga)
     - Apagado automático
     - La pantalla LCD se apaga automáticamente después de |DEFAULT_STANDBY_DURATION| de inactividad.

También puede configurar el modo de visualización de la pantalla en la App Jackery.

COMBINACIONES DE TECLAS
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Botones
     - Operación
     - Función
   * - |MAIN_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Mantenga ambos presionados durante 3 s
     - Activar/desactivar el modo de ahorro de energía
   * - |MAIN_POWER_BUTTON_LABEL| + |DC_USB_POWER_BUTTON_LABEL_LOWER|
     - Mantenga ambos presionados durante 3 s
     - Restablecer Wi-Fi y Bluetooth
   * - |DC_USB_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Mantenga ambos presionados durante 1 s
     - Activar/desactivar Wi-Fi y Bluetooth
