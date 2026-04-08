LCD DISPLAY
===========

.. image:: templates/word_template/common_assets/lcd/lcd_map.png
   :alt: LCD icon map placeholder.
   :width: 420px

.. only:: model_je_2000e

   .. list-table::
      :header-rows: 1
      :widths: 12 28 60

      * - ID
        - Indicator
        - Description
      * - 1
        - Wi-Fi
        - **On:** Wi-Fi connected.

          **Blink:** Ready to connect to Wi-Fi.

          **Off:** Wi-Fi disconnected.
      * - 2
        - Bluetooth
        - **On:** Bluetooth connected.

          **Blink:** Ready to connect to Bluetooth.

          **Off:** Bluetooth disconnected.
      * - 3
        - Quiet Charging Mode
        - **On:** The noise during charging is significantly minimized, while the charging power is reduced, and the charging speed slows down.

          **Off:** Quiet Charging Mode is disabled.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 4
        - Charging Plan
        - Customizes the charging time of Jackery HomePower 2000 Plus. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 5
        - Self-powered Mode
        - Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs. The power station must be connected to both solar panels and the grid simultaneously, with the load power limited by bypass power.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 6
        - TOU Mode
        - **On:** TOU mode is enabled (default backup SOC: 60%). During peak periods, the product prioritizes discharging the battery to reduce peak electricity costs when the stored energy exceeds the backup SOC. During off-peak periods, the product charges the battery from the grid to achieve peak-shaving and valley-filling.

          **Off:** TOU mode is disabled. The product does not follow the TOU (time-of-use) strategy and operates according to the default power supply and charging logic.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 7
        - UPS
        - **On:** The product is in bypass mode, and the switchover time from grid power to the internal battery is 10 ms.

          **Off:** The product is not in bypass mode.
      * - 8
        - AC Power Indicator
        - The AC output (pure sine wave) is on.
      * - 9
        - Output Voltage and Frequency
        - Displays the output voltage and frequency when the AC output is turned on.
      * - 10
        - Input Power
        - Displays the input power in watts.
      * - 11
        - Remaining Charge Time
        - Displays the remaining charging time.
      * - 12
        - AC Wall Charging Indicator
        - The product is charged via the AC Input using grid power.
      * - 13
        - Car Charging Indicator
        - The product is charged via the DC Input (DC8020) using DC 12V (car charging).
      * - 14
        - Solar Charging Indicator
        - The product is charged via the DC Input (DC8020) using solar panel(s).
      * - 15
        - Battery Saving Mode
        - **On:** Limits the maximum usable battery capacity to extend battery life.

          **Off:** Battery Saving Mode is disabled.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.

          **Note 1:** This feature is not available when the product is connected to battery pack(s).

          **Note 2:** When this feature is enabled, the product occasionally performs a full charge and discharge cycle to calibrate the SOC.
      * - 16
        - Charging Power Limit
        - **On:** Charging Power limit is enabled in the Jackery app.

          **Off:** Charging Power limit is disabled in the Jackery app.

          The setting is retained when the device is powered off.
      * - 17
        - Battery Power Indicator
        - When the product is being charged, the orange circle around the battery percentage will light up in sequence.

          When charging other devices, the orange circle will stay on.
      * - 18
        - Remaining Battery Percentage
        - Displays the remaining battery percentage.
      * - 19
        - Low Battery Indicator
        - **On:** The battery level is below 20%.

          **Blink:** The battery level is below 5%.

          **Off:** The battery level is not below 20% or the product is charging.
      * - 20
        - Discharge Timer
        - **On:** A discharge timer is set.

          **Off:** No discharge timer is set.

          Enable/disable this feature in the Jackery App. The setting is not retained when the device is powered off.
      * - 21
        - Connected Batteries
        - Displays the quantity of battery packs if any are connected.
      * - 22
        - Energy Saving Mode
        - When the AC or DC output is turned on by pressing the AC1/2 or DC/USB power button:

          **On:** Energy Saving Mode is enabled.

          **Off:** Energy Saving Mode is disabled.
      * - 23
        - High Temperature Indicator
        - High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.
      * -
        - Low Temperature Indicator
        - Low temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.
      * - 24
        - Fault code
        - A product error has occurred. Please refer to the Troubleshooting section for details.
      * - 25
        - Output Power
        - Displays the output power in watts.
      * - 26
        - Remaining Discharge Time
        - Displays the remaining discharging time.

.. only:: not model_je_2000e

   .. list-table::
      :header-rows: 1
      :widths: 12 28 60

      * - ID
        - Indicator
        - Description
      * - 1
        - Wi-Fi
        - **On:** Wi-Fi connected.

          **Blink:** Ready to connect to Wi-Fi.

          **Off:** Wi-Fi disconnected.
      * - 2
        - Bluetooth
        - **On:** Bluetooth connected.

          **Blink:** Ready to connect to Bluetooth.

          **Off:** Bluetooth disconnected.
      * - 3
        - Quiet Charging Mode
        - **On:** The noise during charging is significantly minimized, while the charging power is reduced, and the charging speed slows down.

          **Off:** Quiet Charging Mode is disabled.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 5
        - Charging Plan
        - Customizes the charging time of |PRODUCT_NAME|. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * -
        - Self-powered Mode
        - Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs.The power station must be connected to both solar panels and the grid simultaneously, with the load power limited by bypass power.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 6
        - UPS
        - **On:** The product is operating in bypass mode. Loads connected to the AC ports consume power from the grid instead of the power station. If the grid suddenly fails, the product automatically switches to its battery power within 10 ms.

          **Off:** The product is not in bypass mode. Loads connected to the AC ports are powered by the internal battery of the power station.
      * - 7
        - AC Power Indicator
        - The AC output (pure sine wave) is on.
      * - 8
        - Output Voltage and Frequency
        - Displays the output voltage and frequency when the AC output is turned on.
      * - 9
        - Input Power
        - Displays the input power in watts.
      * - 10
        - Remaining Charge Time
        - Displays the remaining charging time.
      * - 11
        - AC Wall Charging Indicator
        - The product is charged via the AC Input using grid power.
      * - 12
        - Car Charging Indicator
        - The product is charged via the DC Input (DC8020) using DC 12V (car charging).
      * - 13
        - Solar Charging Indicator
        - The product is charged via the DC Input (DC8020) using solar panel(s).
      * - 4
        - Battery Saving Mode
        - **On:** Battery Saving Mode is enabled. Charge and discharge limits are applied to help extend battery lifespan.

          **Off:** Battery Saving Mode is disabled.

          Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.

          When this feature is enabled, the product occasionally performs a full charge and discharge cycle to calibrate the SOC.
      * - 14
        - Charging Power Limit
        - **On:** Charging Power limit is enabled in the Jackery app.

          **Off:** Charging Power limit is disabled in the Jackery app.

          The setting is retained when the device is powered off.
      * - 16
        - Battery Power Indicator
        - When the product is being charged, the orange circle around the battery percentage will light up in sequence.

          When charging other devices, the orange circle will stay on.
      * - 18
        - Remaining Battery Percentage
        - Displays the remaining battery percentage.
      * - 17
        - Low Battery Indicator
        - **On:** The battery level is below 20%.

          **Blink:** The battery level is below 5%.

          **Off:** The battery level is not below 20% or the product is charging.
      * - 22
        - Energy Saving Mode
        - When the AC or DC output is turned on by pressing the |AC_POWER_BUTTON_LABEL_LOWER| or |DC_USB_POWER_BUTTON_LABEL_LOWER|:

          **On:** Energy Saving Mode is enabled.

          **Off:** Energy Saving Mode is disabled.
      * - 21
        - High Temperature Indicator
        - High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.
      * -
        - Low Temperature Indicator
        - Low temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.
      * - 20
        - Fault code
        - A product error has occurred. Please refer to the Troubleshooting section for details.
      * - 23
        - Output Power
        - Displays the output power in watts.
      * - 24
        - Remaining Discharge Time
        - Displays the remaining discharging time.
