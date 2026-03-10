OPERATIONS
==========

POWER ON/OFF
------------

.. image:: _static/manual_en/01_meaning_of_symbols/fig.png
   :alt: Power on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press and hold for 3s.

**Default standby time:** |DEFAULT_STANDBY_DURATION|.

The product will automatically shut down after |DEFAULT_STANDBY_DURATION| of inactivity, with no charging or discharging.

*The standby time can be set in the Jackery App.*

When Energy Saving Mode is enabled, the product will automatically shut down after |ENERGY_SAVING_AUTO_OFF_DURATION| if the AC or |DC_USB_POWER_BUTTON_LABEL_LOWER| is ON but the product is neither charging nor discharging.

AC OUTPUT ON/OFF
----------------

**Prerequisite:** The product is powered on.

.. image:: _static/manual_en/01_meaning_of_symbols/fig.png
   :alt: AC output on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press once.

DC 12V/USB OUTPUT ON/OFF
------------------------

**Prerequisite:** The product is powered on.

.. image:: _static/manual_en/01_meaning_of_symbols/fig.png
   :alt: DC USB output on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press once.

**CAUTION**

- **|USB_C_HIGH_POWER_PORT_LABEL| is a USB-PD Power Source 3 (PS3) high-power output port.** If the connected user device or accessory does not meet safety requirements, there may be a fire risk. Before using these ports, ensure that the connected device or accessory has fire safety protection.
- Only connect |PRODUCT_NAME| to devices or accessories that comply with clauses 6.3, 6.4, and 6.5 of IEC/EN/UL 62368-1 (or other equivalent standards).
- To obtain maximum output power, use the official |USB_C_HIGH_POWER_CABLE_NAME| (20V DC/5A, 100W).

The product can charge your car battery using the |CAR_BATTERY_CHARGING_CABLE_NAME|, which is sold separately and available on our website.

**CAUTION**

- The DC 12V port is only compatible with 12V car batteries and not suitable for 24V systems.
- Do not start the car while the product is charging the car battery through the 12V DC output port, as this may damage the product.
- This feature is intended for emergency use only and cannot charge a dead or damaged car battery.

ENERGY SAVING MODE
------------------

To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default. When the AC or DC/USB output is turned on, the Energy Saving Mode icon will be displayed on the LCD screen. If no device is connected or the connected device's power consumption is below a certain threshold (|ENERGY_SAVING_AC_THRESHOLD| AC output or |ENERGY_SAVING_DC_THRESHOLD| DC/USB output) for |ENERGY_SAVING_AUTO_OFF_DURATION|, the product automatically turns off the outputs. Please set the Energy Saving Mode duration in the Jackery app.

To disable the energy saving mode, press and hold both the |AC_POWER_BUTTON_LABEL_LOWER| and the |MAIN_POWER_BUTTON_LABEL_LOWER| for more than 3 seconds. Once Energy Saving Mode is disabled, the icon will no longer appear on the LCD screen, and the product will not automatically turn off the AC or USB output.

When powering low-power devices (AC <= |ENERGY_SAVING_AC_THRESHOLD| or DC/USB <= |ENERGY_SAVING_DC_THRESHOLD|), disable Energy Saving Mode to prevent the output from shutting down automatically during operation.

.. image:: _static/manual_en/01_meaning_of_symbols/fig.png
   :alt: Energy saving mode key operation placeholder.
   :width: 320px

Press and hold both buttons for more than 3 seconds.

**NOTE**

Energy Saving Mode resumes its previous state after powering on. Manual switching is required for mode changes.

LED LIGHT ON/OFF
----------------

The LED light has two modes: Light mode and SOS mode. In any mode, press and hold the LED light button to turn off the light.

.. image:: _static/manual_en/01_meaning_of_symbols/fig.png
   :alt: LED light mode operation placeholder.
   :width: 360px

Press the LED Light button once to turn on the light.

Press it again to switch to SOS Mode.

Press it a third time to turn off the light.

LCD SCREEN
----------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Display
     - Mode
     - Action
     - Behavior
   * - .. image:: _static/manual_en/01_meaning_of_symbols/fig.png
          :alt: LCD display mode placeholder.
          :width: 140px
     - Shortly On
     - Turn on
     - Press the |MAIN_POWER_BUTTON_LABEL| or when the product is charging.
   * -
     - Shortly On
     - Turn off
     - Press the |MAIN_POWER_BUTTON_LABEL|.
   * -
     - Shortly On
     - Auto-off
     - The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.
   * -
     - Steady On (in charging or discharging state)
     - Turn on
     - Press the |MAIN_POWER_BUTTON_LABEL_LOWER| twice when the product is powered on.
   * -
     - Steady On (in charging or discharging state)
     - Turn off
     - Press the |MAIN_POWER_BUTTON_LABEL|.
   * -
     - Steady On (in charging or discharging state)
     - Auto-off
     - The LCD turns off automatically after |DEFAULT_STANDBY_DURATION| of inactivity.

You can also set the screen display mode in the Jackery App.

KEY COMBINATION
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Buttons
     - Operation
     - Function
   * - |MAIN_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 3s
     - Turn on/off the Energy Saving Mode
   * - |MAIN_POWER_BUTTON_LABEL| + |DC_USB_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 3s
     - Reset Wi-Fi and Bluetooth
   * - |DC_USB_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 1s
     - Turn on/off Wi-Fi and Bluetooth
