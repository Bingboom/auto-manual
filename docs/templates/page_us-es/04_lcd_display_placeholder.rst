PANTALLA LCD
============

.. image:: templates/word_template/common_assets/lcd/lcd_map.png
   :alt: Mapa de iconos de la pantalla LCD.
   :width: 420px

.. list-table::
   :header-rows: 1
   :widths: 12 28 60

   * - ID
     - Indicador
     - Descripción
   * - 1
     - Wi-Fi
     - **Encendido:** Wi-Fi conectado.

       **Parpadeo:** Listo para conectarse a Wi-Fi.

       **Apagado:** Wi-Fi desconectado.
   * - 2
     - Bluetooth
     - **Encendido:** Bluetooth conectado.

       **Parpadeo:** Listo para conectarse a Bluetooth.

       **Apagado:** Bluetooth desconectado.
   * - 3
     - Modo de carga silenciosa
     - **Encendido:** El ruido durante la carga se reduce significativamente, mientras que la potencia de carga se reduce y la velocidad de carga disminuye.

       **Apagado:** El modo de carga silenciosa está desactivado.

       Active/desactive esta función en la App Jackery. La configuración se conserva cuando el dispositivo se apaga.
   * - 5
     - Plan de carga
     - Personaliza el tiempo de carga de |PRODUCT_NAME|.
       Es adecuado para situaciones con precios de electricidad variables, ya que permite definir planes de carga según los periodos punta y valle, reduciendo así el coste eléctrico.

       Active/desactive esta función en la App Jackery. La configuración se conserva cuando el dispositivo se apaga.
   * -
     - Modo autónomo
     - Maximiza el uso de la energía solar y reduce la dependencia de la red eléctrica al priorizar la energía solar almacenada, lo que ayuda a reducir los costes eléctricos.

       La estación de energía debe estar conectada simultáneamente a paneles solares y a la red, con la potencia de carga limitada por la potencia de bypass.

       Active/desactive esta función en la App Jackery. La configuración se conserva cuando el dispositivo se apaga.
   * -
     - Modo TOU
     - **Encendido:** El modo TOU está activado (SOC de respaldo predeterminado: 60 %). Durante los periodos punta, cuando la energía almacenada supera el SOC de respaldo, el producto prioriza la descarga de la batería para reducir el coste eléctrico. Durante los periodos valle, el producto carga la batería desde la red para desplazar la carga.

       **Apagado:** El modo TOU está desactivado. El producto no sigue la estrategia TOU y funciona según la lógica predeterminada de alimentación y carga.

       Active/desactive esta función en la App Jackery. La configuración se conserva cuando el dispositivo se apaga.
   * - 6
     - UPS
     - **Encendido:** El producto está en modo bypass y el tiempo de conmutación desde la red a la batería interna es de 10 ms.

       **Apagado:** El producto no está en modo bypass.
   * - 7
     - Indicador de alimentación de CA
     - La salida de CA (onda sinusoidal pura) está activada.
   * - 8
     - Voltaje y frecuencia de salida
     - Muestra el voltaje y la frecuencia de salida cuando la salida de CA está encendida.
   * - 9
     - Potencia de entrada
     - Muestra la potencia de entrada en vatios.
   * - 10
     - Tiempo restante de carga
     - Muestra el tiempo restante de carga.
   * - 11
     - Indicador de carga por toma de CA
     - El producto se carga mediante la entrada de CA usando energía de la red eléctrica.
   * - 12
     - Indicador de carga del automóvil
     - El producto se carga mediante la entrada de CC (DC8020) usando CC de 12 V (carga desde el vehículo).
   * - 13
     - Indicador de carga solar
     - El producto se carga mediante la entrada de CC (DC8020) usando panel(es) solares.
   * - 4
     - Modo de ahorro de batería
     - **Encendido:** Limita la capacidad máxima utilizable de la batería para prolongar su vida útil.

       **Apagado:** El modo de ahorro de batería está desactivado.

       Active/desactive esta función en la App Jackery. La configuración se conserva cuando el dispositivo se apaga.

       Cuando esta función está activada, el producto realiza ocasionalmente un ciclo completo de carga y descarga para calibrar el SOC.
   * - 14
     - Límite de potencia de carga
     - **Encendido:** El límite de potencia de carga está activado en la App Jackery.

       **Apagado:** El límite de potencia de carga está desactivado en la App Jackery.

       La configuración se conserva cuando el dispositivo se apaga.
   * - 16
     - Indicador de potencia de la batería
     - Cuando el producto se está cargando, el círculo naranja alrededor del porcentaje de batería se ilumina secuencialmente.

       Cuando está cargando otros dispositivos, el círculo naranja permanece encendido.
   * - 18
     - Porcentaje restante de batería
     - Muestra el porcentaje restante de batería.
   * - 17
     - Indicador de batería baja
     - **Encendido:** El nivel de batería está por debajo del 20 %.

       **Parpadeo:** El nivel de batería está por debajo del 5 %.

       **Apagado:** El nivel de batería no está por debajo del 20 % o el producto se está cargando.
   * -
     - Temporizador de descarga
     - **Encendido:** Se ha configurado un temporizador de descarga.

       **Apagado:** No se ha configurado ningún temporizador de descarga.

       Active/desactive esta función en la App Jackery. La configuración no se conserva cuando el dispositivo se apaga.
   * - 22
     - Modo de ahorro de energía
     - Cuando la salida de CA o CC se activa presionando |AC_POWER_BUTTON_LABEL_LOWER| o |DC_USB_POWER_BUTTON_LABEL_LOWER|:

       **Encendido:** El modo de ahorro de energía está activado.

       **Apagado:** El modo de ahorro de energía está desactivado.
   * - 21
     - Indicador de alta temperatura
     - Se ha activado la protección por alta temperatura. El producto puede dejar de funcionar hasta que su temperatura vuelva al rango normal de funcionamiento.
   * -
     - Indicador de baja temperatura
     - Se ha activado la protección por baja temperatura. El producto puede dejar de funcionar hasta que su temperatura vuelva al rango normal de funcionamiento.
   * - 20
     - Código de fallo
     - Se ha producido un error en el producto. Consulte la sección de resolución de problemas para obtener más información.
   * - 23
     - Potencia de salida
     - Muestra la potencia de salida en vatios.
   * - 24
     - Tiempo restante de descarga
     - Muestra el tiempo restante de descarga.
