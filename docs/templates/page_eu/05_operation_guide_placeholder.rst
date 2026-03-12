OPERATIONS
==========

POWER ON/OFF
------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Power on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press and hold for 3s.

**Default standby time:** 2 hours.

The product will automatically shut down after 2 hours of inactivity, with no charging or discharging.

*The standby time can be set in the Jackery app.*

When Energy Saving Mode is enabled, the product will automatically shut down after 12 hours if the AC or |USB_POWER_BUTTON_LABEL_LOWER| is ON but the product is neither charging nor discharging.

AC OUTPUT ON/OFF
----------------

**Prerequisite:** The product is powered on.

.. image:: templates/word_template/common_assets/operation/ac_output.png
   :alt: AC output on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press once.

USB OUTPUT ON/OFF
-----------------

**Prerequisite:** The product is turned on.

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: USB output on/off operation placeholder.
   :width: 360px

On: Press once.

Off: Press once.

**CAUTION**

- **USB-C 100W is USB-PD Power Source 3 (PS3) high-power output port.** If the connected user device or accessory does not meet safety requirements, there may be a fire risk. Before using these ports, ensure that the connected device or accessory has fire safety protection.
- Only connect |PRODUCT_NAME| to devices or accessories that comply with clauses 6.3, 6.4, and 6.5 of IEC/EN/UL 62368-1 (or other equivalent standards).
- To obtain maximum output power, use the official Jackery USB-C to USB-C 5A cable (20V DC/5A, 100W).

ENERGY SAVING MODE
------------------

To prevent unnecessary battery consumption from forgetting to turn off the output, the product enables Energy Saving Mode by default. If no device is connected or the connected device's power consumption is below a certain threshold (25W AC output or 2W USB output) for 12 hours, the product will automatically turn off the outputs.

To disable the energy saving mode, press and hold both the |AC_POWER_BUTTON_LABEL_LOWER| and |POWER_BUTTON_LABEL_LOWER| for more than 3 seconds. The product will not automatically turn off the AC or DC output.

**NOTE**

Energy Saving Mode resumes previous state after power-on. Manual switching is required for mode changes.

LCD SCREEN
----------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Display
     - Mode
     - Action
     - Behavior
   * - .. image:: templates/word_template/common_assets/operation/lcd_mode.png
          :alt: LCD display mode placeholder.
          :width: 140px
     - Shortly On
     - Turn on
     - Press the |POWER_BUTTON_LABEL| or when the product is charging.
   * -
     - Shortly On
     - Turn off
     - Press the |POWER_BUTTON_LABEL|.
   * -
     - Shortly On
     - Auto-off
     - The LCD turns off automatically and enters sleep mode after 2 minutes of inactivity.
   * -
     - Steady On (in charging or discharging state)
     - Turn on
     - Press the |POWER_BUTTON_LABEL_LOWER| twice when the product is powered on.
   * -
     - Steady On (in charging or discharging state)
     - Turn off
     - Press the |POWER_BUTTON_LABEL|.
   * -
     - Steady On (in charging or discharging state)
     - Auto-off
     - The LCD turns off automatically after 2 hours of inactivity.

You can also set the screen display mode in the Jackery App.

KEY COMBINATION
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Buttons
     - Operation
     - Function
   * - |POWER_BUTTON_LABEL| + |USB_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 3s
     - Reset Wi-Fi and Bluetooth
   * - |POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 3s
     - Turn on/off the Energy Saving Mode
   * - |USB_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL_LOWER|
     - Press and hold both for 1s
     - Turn on/off Wi-Fi and Bluetooth
