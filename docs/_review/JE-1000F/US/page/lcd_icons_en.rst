.. raw:: latex

   \HBApplyLang{en}

LCD DISPLAY
===========

.. image:: _assets/templates/word_template/common_assets/lcd/lcd_map.png
   :alt: LCD icon map placeholder.
   :width: 420px

.. only:: not latex

   .. list-table::
      :header-rows: 0
      :widths: 8 12 28 52

      * - 1
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/1_Wi-Fi_SIpvbSx1Xo6f4zxBRxDcvpghnQe.png
             :alt: Wi-Fi
             :width: 42px
        - Wi-Fi
        - | **On:** Wi-Fi connected.
          | **Blink:** Ready to connect to Wi-Fi.
          | **Off:** Wi-Fi disconnected.
      * - 2
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/2_Bluetooth_FUjEbkkm0o6tUQxgeagcUL4Cnyg.png
             :alt: Bluetooth
             :width: 42px
        - Bluetooth
        - | **On:** Bluetooth connected.
          | **Blink:** Ready to connect to Bluetooth.
          | **Off:**  Bluetooth disconnected.
      * - 3
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/3_Quiet_Charging_Mode_Msa6bzGhuoQAXbxRzTCcHkHOnZc.png
             :alt: Quiet Charging Mode
             :width: 42px
        - Quiet Charging Mode
        - | **On:** The noise
          | during charging is significantly minimized, while the charging power is reduced and the charging speed slows down.
          | **Off:** Quiet Charging Mode is disabled.
          | Enable/disable this feature in the Jackery App.
      * - 4
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/4_Charging_Plan_PBCtblGMaoHz4fx08tRcoXUJnIf.png
             :alt: Charging Plan
             :width: 42px
        - Charging Plan
        - | Customizes the charging time of the Jackery Explorer 1000. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs.
          | Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 5
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/5_Self-powered_Mode_Z0EobbQ6iogDRoxF9DbcAeXunOh.png
             :alt: Self-powered Mode
             :width: 42px
        - Self-powered Mode
        - | Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs. The power station must be connected to both solar panels and the grid simultaneously, with the load power limited by bypass power.
          | Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 6
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/6_TOU_Mode_KJ5VbskRpoIUC8xPrXBcnUSPnbd.png
             :alt: TOU Mode
             :width: 42px
        - TOU Mode
        - | **On:** TOU mode is enabled (default backup SOC: 60%). During peak periods, the product prioritizes discharging the battery to reduce peak electricity costs when the stored energy exceeds the backup SOC. During off peak periods, the product charges the battery from the grid to achieve peak shaving and valley filling.
          | **Off:** TOU mode is disabled. The product does not follow the TOU (time of use) strategy and operates according to the default power supply and charging logic.
          | Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
      * - 7
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/7_UPS_QbWXbfxlao3SU2xjrYncE5f5nBe.png
             :alt: UPS
             :width: 42px
        - UPS
        - | **On:** The product is in bypass mode, and the switchover time from grid power to the internal battery is 10 ms.
          | **Off:** The product is not in bypass mode.
      * - 8
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/8_AC_Power_Indicator_EXtsboEbfoAmFvxKJAFcHjhrnVc.png
             :alt: AC Power Indicator
             :width: 42px
        - AC Power Indicator
        - The AC output (pure sine wave) is on.
      * - 9
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/9_Output_Voltage_and_Frequency_FGEHbjpQIoyWhcxPQrncP1hDnLd.png
             :alt: Output Voltage and Frequency
             :width: 42px
        - Output Voltage and Frequency
        - Displays the output voltage and frequency when the AC output is turned on.
      * - 10
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/10_Input_Power_ECBhbzoMVokNUZxYjfYcnZVbnZg.png
             :alt: Input Power
             :width: 42px
        - Input Power
        - Displays the input power in watts.
      * - 11
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/11_Remaining_Charge_Time_KQNcbUvpeo99tpxGitEcABedneD.png
             :alt: Remaining Charge Time
             :width: 42px
        - Remaining Charge Time
        - Displays the remaining charging time.
      * - 12
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/12_AC_Wall_Charging_Indicator_E1P6bljXxoQpGMx3OuIcis4Mnxg.png
             :alt: AC Wall Charging Indicator
             :width: 42px
        - AC Wall Charging Indicator
        - The product is charged via the AC Input using grid power.
      * - 13
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/13_Car_Charging_Indicator_FBn4bBNUpoGUt0xzlxQcMiemnqb.png
             :alt: Car Charging Indicator
             :width: 42px
        - Car Charging Indicator
        - The product is charged via the DC Input (DC8020) using DC 12V (car charging).
      * - 14
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/14_Solar_Charging_Indicator_XBmTbm6oeoyLw5xZrckc3vCxnTd.png
             :alt: Solar Charging Indicator
             :width: 42px
        - Solar Charging Indicator
        - The product is charged via the DC Input (DC8020) using solar panel(s).
      * - 15
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/15_Battery_Saving_Mode_BppFbGLcdoRcUkx3RuUclFtonFb.png
             :alt: Battery Saving Mode
             :width: 42px
        - Battery Saving Mode
        - | **On:** Battery Saving Mode is enabled. Charge and discharge limits are applied to help extend battery lifespan.
          | **Off:** Battery Saving Mode is disabled.
          | Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.
          | When this feature is enabled, the product occasionally performs a full charge and discharge cycle to calibrate the SOC.
      * - 16
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/16_Charging_Power_Limit_F0BZbrBzjoAxpOxfziAc2BMgnyd.png
             :alt: Charging Power Limit
             :width: 42px
        - Charging Power Limit
        - | **On:** Charging Power limit is enabled in the Jackery app.
          | **Off:** Charging Power limit is disabled in the Jackery app.
          | The setting is retained when the device is powered off.
      * - 17
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/17_Battery_Power_Indicator_SbBPbnuPCosiFqxwrb7cCGj8nQh.png
             :alt: Battery Power Indicator
             :width: 42px
        - Battery Power Indicator
        - When the product is being charged, the orange circle around the battery percentage will light up in sequence. When charging other devices, the orange circle will stay on.
      * - 18
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/18_Remaining_Battery_Percentage_MYuhbRVFXohfBqx6VhbcdTqYnWd.png
             :alt: Remaining Battery Percentage
             :width: 42px
        - Remaining Battery Percentage
        - Displays the remaining battery percentage.
      * - 19
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/19_Low_Battery_Indicator_QUrSbwDTeo6nSyxNauGcsvGXn3b.png
             :alt: Low Battery Indicator
             :width: 42px
        - Low Battery Indicator
        - | **On:** The battery level is below 20%.
          | **Blink:** The battery level is below 5%.
          | **Off:** The battery level is not below 20% or the product is charging.
      * - 20
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/20_Discharge_Timer_HVoHb2DI2o4sfsxhe1fckZ6pnfH.png
             :alt: Discharge Timer
             :width: 42px
        - Discharge Timer
        - | **On:** A discharge timer is set.
          | **Off:** No discharge timer is set.
          | Enable/disable this feature in the Jackery App. The setting is not retained when the device is powered off.
      * - 22
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/22_Energy_Saving_Mode_VHOBbWed7oIoJVx9QPrc2V3Gnpc.png
             :alt: Energy Saving Mode
             :width: 42px
        - Energy Saving Mode
        - | When the AC or DC output is turned on by pressing the AC or DC/USB power button:
          | **On:** Energy Saving Mode is enabled.
          | **Off:** Energy Saving Mode is disabled.
      * - 23
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/23_High_Temperature_Indicator_VmlmbUHrzorWbHxGtMLcgo5RnUe.png
             :alt: High Temperature Indicator
             :width: 42px
        - High Temperature Indicator
        - High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.
      * - 24
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/24_Low_Temperature_Indicator_LW97bYSKio51UfxUi7OcWzMUnuc.png
             :alt: Low Temperature Indicator
             :width: 42px
        - Low Temperature Indicator
        - | Low temperature protection is triggered.
          | The product may stop functioning until its temperature returns to the normal operating range.
      * - 25
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/25_Fault_code_G7PLbJnW5ogmMwx0estcVG11nVd.png
             :alt: Fault code
             :width: 42px
        - Fault code
        - A product error has occurred. Please refer to the Troubleshooting section for details.
      * - 26
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/26_Output_Power_SDxHbEIbnoeTvAx9njvcvOKrnCb.png
             :alt: Output Power
             :width: 42px
        - Output Power
        - Displays the output power in watts.
      * - 27
        - .. image:: _repo_assets/data/phase2/_attachments/lcd_icons/27_Remaining_Discharge_Time_TO5TbTk2aoDOY0xkN6Oc3h6nnIc.png
             :alt: Remaining Discharge Time
             :width: 42px
        - Remaining Discharge Time
        - Displays the remaining discharging time.

.. only:: latex

   .. raw:: latex

      \begin{HBLcdIconTable}
      \HBLcdIconRow{1}{1_Wi-Fi_SIpvbSx1Xo6f4zxBRxDcvpghnQe.png}{Wi-Fi}{\textbf{On:} Wi-Fi connected. \newline \textbf{Blink:} Ready to connect to Wi-Fi. \newline \textbf{Off:} Wi-Fi disconnected.}
      \HBLcdIconRow{2}{2_Bluetooth_FUjEbkkm0o6tUQxgeagcUL4Cnyg.png}{Bluetooth}{\textbf{On:} Bluetooth connected. \newline \textbf{Blink:} Ready to connect to Bluetooth. \newline \textbf{Off:} Bluetooth disconnected.}
      \HBLcdIconRow{3}{3_Quiet_Charging_Mode_Msa6bzGhuoQAXbxRzTCcHkHOnZc.png}{Quiet Charging Mode}{\textbf{On:} The noise \newline during charging is significantly minimized, while the charging power is reduced and the charging speed slows down. \newline \textbf{Off:} Quiet Charging Mode is disabled. \newline Enable/disable this feature in the Jackery App.}
      \HBLcdIconRow{4}{4_Charging_Plan_PBCtblGMaoHz4fx08tRcoXUJnIf.png}{Charging Plan}{Customizes the charging time of the Jackery Explorer 1000. Suitable for situations with fluctuating electricity prices, it allows for charging plans based on peak and off-peak electricity times, reducing electricity costs. \newline Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.}
      \HBLcdIconRow{5}{5_Self-powered_Mode_Z0EobbQ6iogDRoxF9DbcAeXunOh.png}{Self-powered Mode}{Maximizes the use of solar energy and reduces reliance on grid electricity by prioritizing stored solar energy, reducing electricity costs. The power station must be connected to both solar panels and the grid simultaneously, with the load power limited by bypass power. \newline Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.}
      \HBLcdIconRow{6}{6_TOU_Mode_KJ5VbskRpoIUC8xPrXBcnUSPnbd.png}{TOU Mode}{\textbf{On:} TOU mode is enabled (default backup SOC: 60\%). During peak periods, the product prioritizes discharging the battery to reduce peak electricity costs when the stored energy exceeds the backup SOC. During off peak periods, the product charges the battery from the grid to achieve peak shaving and valley filling. \newline \textbf{Off:} TOU mode is disabled. The product does not follow the TOU (time of use) strategy and operates according to the default power supply and charging logic. \newline Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off.}
      \HBLcdIconRow{7}{7_UPS_QbWXbfxlao3SU2xjrYncE5f5nBe.png}{UPS}{\textbf{On:} The product is in bypass mode, and the switchover time from grid power to the internal battery is 10 ms. \newline \textbf{Off:} The product is not in bypass mode.}
      \HBLcdIconRow{8}{8_AC_Power_Indicator_EXtsboEbfoAmFvxKJAFcHjhrnVc.png}{AC Power Indicator}{The AC output (pure sine wave) is on.}
      \HBLcdIconRow{9}{9_Output_Voltage_and_Frequency_FGEHbjpQIoyWhcxPQrncP1hDnLd.png}{Output Voltage and Frequency}{Displays the output voltage and frequency when the AC output is turned on.}
      \HBLcdIconRow{10}{10_Input_Power_ECBhbzoMVokNUZxYjfYcnZVbnZg.png}{Input Power}{Displays the input power in watts.}
      \HBLcdIconRow{11}{11_Remaining_Charge_Time_KQNcbUvpeo99tpxGitEcABedneD.png}{Remaining Charge Time}{Displays the remaining charging time.}
      \HBLcdIconRow{12}{12_AC_Wall_Charging_Indicator_E1P6bljXxoQpGMx3OuIcis4Mnxg.png}{AC Wall Charging Indicator}{The product is charged via the AC Input using grid power.}
      \HBLcdIconRow{13}{13_Car_Charging_Indicator_FBn4bBNUpoGUt0xzlxQcMiemnqb.png}{Car Charging Indicator}{The product is charged via the DC Input (DC8020) using DC 12V (car charging).}
      \HBLcdIconRow{14}{14_Solar_Charging_Indicator_XBmTbm6oeoyLw5xZrckc3vCxnTd.png}{Solar Charging Indicator}{The product is charged via the DC Input (DC8020) using solar panel(s).}
      \HBLcdIconRow{15}{15_Battery_Saving_Mode_BppFbGLcdoRcUkx3RuUclFtonFb.png}{Battery Saving Mode}{\textbf{On:} Battery Saving Mode is enabled. Charge and discharge limits are applied to help extend battery lifespan. \newline \textbf{Off:} Battery Saving Mode is disabled. \newline Enable/disable this feature in the Jackery App. The setting is retained when the device is powered off. \newline When this feature is enabled, the product occasionally performs a full charge and discharge cycle to calibrate the SOC.}
      \HBLcdIconRow{16}{16_Charging_Power_Limit_F0BZbrBzjoAxpOxfziAc2BMgnyd.png}{Charging Power Limit}{\textbf{On:} Charging Power limit is enabled in the Jackery app. \newline \textbf{Off:} Charging Power limit is disabled in the Jackery app. \newline The setting is retained when the device is powered off.}
      \HBLcdIconRow{17}{17_Battery_Power_Indicator_SbBPbnuPCosiFqxwrb7cCGj8nQh.png}{Battery Power Indicator}{When the product is being charged, the orange circle around the battery percentage will light up in sequence. When charging other devices, the orange circle will stay on.}
      \HBLcdIconRow{18}{18_Remaining_Battery_Percentage_MYuhbRVFXohfBqx6VhbcdTqYnWd.png}{Remaining Battery Percentage}{Displays the remaining battery percentage.}
      \HBLcdIconRow{19}{19_Low_Battery_Indicator_QUrSbwDTeo6nSyxNauGcsvGXn3b.png}{Low Battery Indicator}{\textbf{On:} The battery level is below 20\%. \newline \textbf{Blink:} The battery level is below 5\%. \newline \textbf{Off:} The battery level is not below 20\% or the product is charging.}
      \HBLcdIconRow{20}{20_Discharge_Timer_HVoHb2DI2o4sfsxhe1fckZ6pnfH.png}{Discharge Timer}{\textbf{On:} A discharge timer is set. \newline \textbf{Off:} No discharge timer is set. \newline Enable/disable this feature in the Jackery App. The setting is not retained when the device is powered off.}
      \HBLcdIconRow{22}{22_Energy_Saving_Mode_VHOBbWed7oIoJVx9QPrc2V3Gnpc.png}{Energy Saving Mode}{When the AC or DC output is turned on by pressing the AC or DC/USB power button: \newline \textbf{On:} Energy Saving Mode is enabled. \newline \textbf{Off:} Energy Saving Mode is disabled.}
      \HBLcdIconRow{23}{23_High_Temperature_Indicator_VmlmbUHrzorWbHxGtMLcgo5RnUe.png}{High Temperature Indicator}{High temperature protection is triggered. The product may stop functioning until its temperature returns to the normal operating range.}
      \HBLcdIconRow{24}{24_Low_Temperature_Indicator_LW97bYSKio51UfxUi7OcWzMUnuc.png}{Low Temperature Indicator}{Low temperature protection is triggered. \newline The product may stop functioning until its temperature returns to the normal operating range.}
      \HBLcdIconRow{25}{25_Fault_code_G7PLbJnW5ogmMwx0estcVG11nVd.png}{Fault code}{A product error has occurred. Please refer to the Troubleshooting section for details.}
      \HBLcdIconRow{26}{26_Output_Power_SDxHbEIbnoeTvAx9njvcvOKrnCb.png}{Output Power}{Displays the output power in watts.}
      \HBLcdIconRow{27}{27_Remaining_Discharge_Time_TO5TbTk2aoDOY0xkN6Oc3h6nnIc.png}{Remaining Discharge Time}{Displays the remaining discharging time.}
      \end{HBLcdIconTable}

