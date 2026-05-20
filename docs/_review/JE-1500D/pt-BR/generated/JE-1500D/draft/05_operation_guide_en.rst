.. raw:: latex

   \HBApplyLang{en}

OPERATIONS
==========

POWER ON/OFF
------------

.. image:: _assets/templates/word_template/common_assets/operation/main_power.png
   :alt: Power on/off operation placeholder.
   :width: 360px

| On: Press once.
| Off: Press and hold for 3s.
|
| **Default standby time:** 2 hours.
| The product will automatically shut down after 2 hours of inactivity, with no charging or discharging.
| \*The standby time can be set in the Jackery App.
| When Energy Saving Mode is enabled, the product will automatically shut down after 12 hours if the AC or DC/USB power button is ON but the product is neither charging nor discharging.

AC OUTPUT ON/OFF
----------------

**Prerequisite**: The product is powered on.

.. image:: _assets/templates/word_template/common_assets/operation/ac_output.png
   :alt: AC output on/off operation placeholder.
   :width: 360px

| 
| **On**
| Press once
| **Off**
| Press once
| 

DC 12V/USB OUTPUT ON/OFF
------------------------

**Prerequisite**: The product is powered on.

.. image:: _assets/templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: DC USB output on/off operation placeholder.
   :width: 360px

| 
| **On**
| Press once
| **Off**
| Press once
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     -
       - **USB-C 100W is a USB-PD Power Source 3 (PS3) high-power output port.** If the connected user device or accessory does not meet safety requirements, there may be a fire risk. Before using these ports, ensure that the connected device or accessory has fire safety protection.
       - Only connect Jackery Explorer 1500 to devices or accessories that comply with clauses 6.3, 6.4, and 6.5 of IEC/EN/UL 62368-1 (or other equivalent standards).
       - To obtain maximum output power, use the USB-C to USB-C 5A cable (20V DC/5A, 100W).


| The product can charge your car battery using the Jackery 12V automobile battery charging cable, which is sold separately and available on our website.
 

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CAUTION**
     -
       - The DC 12V port is only compatible with 12V car batteries and not suitable for 24V systems.
       - Do not start the car while the product is charging the car battery through the 12V DC output port, as this may damage the product.
       - This feature is intended for emergency use only and cannot charge a dead or damaged car battery.

ENERGY SAVING MODE
------------------

To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default. When the AC or DC/USB output is turned on, the Energy Saving Mode icon will be displayed on the LCD screen. In this mode, if no device is connected or the connected device's power consumption is below a certain threshold (25 W AC output or 2 W DC/USB output), the corresponding output will automatically turns off after the set time. The default setting is 12 hours. The Energy Saving Mode duration can be set in the Jackery App to 1H, 2 H, 8 H, 12 H or 24 H. If it is set to Never Off, Energy Saving Mode will be disabled.

To disable the energy saving mode, press and hold both the AC power button and the main POWER button for more than 3 seconds. Once Energy Saving Mode is disabled, the icon will no longer appear on the LCD screen, and the product will not automatically turn off the AC or USB output.

When powering low-power devices (AC ≤ 25 W or DC/USB ≤ 2 W), disable Energy Saving Mode to prevent the output from shutting down automatically during operation.

.. image:: _assets/templates/word_template/common_assets/operation/energy_saving.png
   :alt: Energy saving mode key operation placeholder.
   :width: 320px


| Press and hold both buttons for more than 3 seconds.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTE**
     - Energy Saving Mode resumes its previous state after powering on. Manual switching is required for mode changes.


LED LIGHT ON/OFF
----------------

The LED light has two modes: Light mode and SOS mode. In any mode, press and hold the LED light button to turn off the light.

.. image:: _assets/templates/word_template/common_assets/operation/led_light.png
   :alt: LED light mode operation placeholder.
   :width: 360px

|
| Press the LED Light button once to turn on the light.
| Press it again to switch to SOS Mode.
| Press it a third time to turn off the light.

AC and DC Output Resume Function
--------------------------------

The AC/DC Output Resume Function is disabled by default. Enable this function in the App to allow the device to memorize the AC/DC output status and automatically resume AC and DC outputs under defined conditions.

+---------------------------------------------------------------+-----------------------------------------------+
| Auto Resume Conditions                                        | Not Auto Resume Conditions                    |
+===============================================================+===============================================+
| Power-on/Restart after shutdown or restart                    | Manual output off (button/App)                |
+---------------------------------------------------------------+-----------------------------------------------+
| Battery SOC ≥ discharge limit +10% after reaching limit       | Energy Saving mode output off                 |
|                                                               +-----------------------------------------------+
|                                                               | Protection-triggered output off               |
+---------------------------------------------------------------+-----------------------------------------------+
| OTA upgrade completed                                         | Discharge timer-triggered output off          |
+---------------------------------------------------------------+-----------------------------------------------+

LCD SCREEN
----------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="LCD display mode placeholder." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Shortly On</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Turn on</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Press the main POWER button or when the product is charging.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Turn off</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Press the main POWER button.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Auto-off</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Steady On (in charging or discharging state)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Turn on</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Press the main POWER button twice when the product is powered on.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Turn off</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Press the main POWER button.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Auto-off</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">The LCD turns off automatically after 2 hours of inactivity.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{Shortly On}{Turn on}{Press the main POWER button or when the product is charging.}{Turn off}{Press the main POWER button.}{Auto-off}{The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.}
      \HBLcdModeSecondGroup{Steady On (in charging or discharging state)}{Turn on}{Press the main POWER button twice when the product is powered on.}{Turn off}{Press the main POWER button.}{Auto-off}{The LCD turns off automatically after 2 hours of inactivity.}
      \end{HBLcdModeTable}

You can also set the screen display mode in the Jackery App.

KEY COMBINATION
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Buttons
     - Operation
     - Function
   * - Main POWER button + AC Power Button
     - Press and hold both for 3s
     - Turn on/off the Energy Saving Mode
   * - Main POWER button + DC/USB Power Button
     - Press and hold both for 3s
     - Reset Wi-Fi and Bluetooth
   * - DC/USB Power Button + AC Power Button
     - Press and hold both for 1s
     - Turn on/off Wi-Fi and Bluetooth
   * - Main POWER button + LED Light button
     - Press and hold both for 1s
     - Turn on/off Emergency Charging Mode
