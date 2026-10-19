5. IMPORTANT SAFETY INSTRUCTIONS
================================

.. container:: hb-source-operation hb-source-note

   During vehicle operation, the DC-DC charger utilizes the generator's surplus power to charge the portable power station. The actual charging power depends on the vehicle's driving conditions, model, and overall condition.

To ensure safe operation, it's crucial to observe the following guidelines:

- Keep this manual for future reference.
- Always operate or store the product under the conditions specified in this manual.
- Read all instructions and warnings on this product, the car battery, and the Jackery power station, as well as their respective user manuals.
- Do not disassemble the product or replace its parts without authorization, as this will void the warranty and may damage the product. Seek assistance from Jackery customer service for component replacement.

Product Compatibility
---------------------

.. container:: hb-source-safety-heading hb-source-compatibility

   .. image:: renderers/web/assets/shared/symbols/native-v1/symbol_warning_triangle.svg
      :alt: Warning
      :width: 40px

   This product is only compatible with Jackery portable power stations with a DC8020 input port. Users are strictly prohibited from using adapters to connect this product to a DC7909 or USB-C input port of a portable power station. Such connecting may cause device damage, fire, or even explosion, posing serious personal safety risks.

- This product is compatible only with 12V/24V car batteries. Before using the product, ensure that your vehicle's rated voltage is either 12V or 24V, and always follow electrical safety guidelines during use.
- This product is compatible with Jackery portable power stations equipped with a DC8020 input port. Refer to the table below for some compatible models. For more information, please contact customer service or visit the official Jackery website.

.. list-table:: Compatible portable power stations
   :header-rows: 1
   :widths: 24 14 22 18 22

   * - Portable Power Station
     - Capacity
     - Charging Voltage and Current
     - Charging Power
     - Charging Time (0–100%)
   * - Explorer 1000 Plus
     - 1265 Wh
     - Around 50V 8A
     - Around 400W
     - Around 3.5 Hour
   * - Explorer 1000 v2
     - 1070 Wh
     - Around 50V 8A
     - Around 400W
     - Around 3.0 Hour
   * - Explorer 2000 Plus
     - 2042 Wh
     - Around 50V 12A
     - Around 600W
     - Around 3.7 Hour
   * - Explorer 2000 v2
     - 2042 Wh
     - Around 50V 8A
     - Around 400W
     - Around 5.6 Hour
   * - Explorer 3000 Pro
     - 3024 Wh
     - Around 50V 12A
     - Around 600W
     - Around 5.5 Hour
   * - Explorer 3000 v2
     - 3072 Wh
     - Around 50V 12A
     - Around 600W
     - Around 5.6 Hour

Note: The charging time data for this product is based on simulated tests conducted under a constant temperature of 25°C. In actual use, charging power may vary due to driving conditions, vehicle model, and overall condition. Charging times may also be affected by changes in ambient temperature.

**Standard Test Environment:** Constant 25°C

**Data Source:** Jackery Lab

.. image:: asset:web/ja-ad600a/eu/en/status-device
   :alt: Product with green status indicator on the top surface.
   :class: hb-status-device-art
   :width: 100%

.. container:: hb-source-operation hb-source-power

   .. rubric:: Powering On the Product

   1. **Short press the power button:** When there is no ACC signal input, you can power on the device by briefly pressing the power button.
   2. **Powering on via ACC signal:** If the ACC wire is connected, the device will automatically power on when it detects an ACC signal input (e.g., after the vehicle is started).

   .. rubric:: Standby and Shutdown

   When there is no ACC signal input or the voltage falls below the startup threshold, the product will enter standby mode. If standby lasts longer than 24 hours or the voltage drops below the protection threshold, the device will automatically shut down. To restart it, follow the same steps as described above.

   While in standby mode, if there is no ACC signal input, you can also manually shut down the device by pressing and holding the power button for 3 seconds.

.. role:: hb-lamp-green
.. role:: hb-lamp-red
.. role:: hb-lamp-blinking
.. role:: hb-lamp-off

.. container:: hb-source-operation hb-source-status

   .. list-table::
      :class: hb-source-status-table
      :header-rows: 1
      :widths: 18 18 25 39

      * - Light Status
        - Light Color
        - Product Status
        - Remarks
      * - Solid
        - :hb-lamp-green:`Green`
        - Charging
        - /
      * - Solid
        - :hb-lamp-red:`Red`
        - Abnormal
        - If any issues are detected, promptly contact Jackery customer service for support.
      * - Blinking
        - :hb-lamp-blinking:`Green`
        - Connection is normal, waiting for charging.
        - If the same issue occurs after connecting the portable power station, possible causes include:

          1. Unstable connection between the output cable and the portable power station.
          2. Damaged cable.
          3. The portable power station is fully charged.

          If the issue persists after troubleshooting, please contact Jackery customer service for support.
      * - No light
        - :hb-lamp-off:`No color`
        - The product is not powered on.
        - If the problem remains after completing wiring and starting the vehicle, please contact Jackery customer service.
