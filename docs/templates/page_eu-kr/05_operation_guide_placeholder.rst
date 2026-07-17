조작
========

전원 켜기/끄기
------------------------

.. image:: asset:operation/main_power
   :alt: Power on/off operation placeholder.
   :width: 360px

| 켜짐: 한 번 누르기
| 꺼짐: 3초간 길게 누르기
|
| **기본 대기 시간:** |DEFAULT_STANDBY_DURATION|.
| 제품은 충전 또는 방전이 없는 비활성 상태가 |DEFAULT_STANDBY_DURATION| 지속되면 자동으로 전원이 꺼집니다.
| \*대기 시간은 Jackery App에서 설정할 수 있습니다.
| 에너지 절약 모드가 활성화된 경우, AC 출력 또는 DC/USB 출력이 켜져 있지만 제품이 충전 또는 방전 중이 아니면 |ENERGY_SAVING_AUTO_OFF_DURATION| 후 자동으로 전원이 꺼집니다.

AC 출력 켜기/끄기
------------------------

**사전 조건**: 제품의 전원이 켜져 있어야 합니다.

.. image:: asset:operation/ac_output
   :alt: AC output on/off operation placeholder.
   :width: 360px

|
| **켜기**
| 한 번 누르기
| **끄기**
| 한 번 누르기
|

DC 12V/USB 출력 켜기/끄기
------------------------

**사전 조건**: 제품의 전원이 켜져 있어야 합니다.

.. image:: asset:operation/dc_usb_output
   :alt: DC USB output on/off operation placeholder.
   :width: 360px

|
| **켜기**
| 한 번 누르기
| **끄기**
| 한 번 누르기
|

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **주의**
     -
       - **USB-C 100W는 USB-PD Power Source 3 (PS3) 고출력 포트입니다.** 연결된 기기 또는 액세서리가 안전 요구 사항을 충족하지 않으면 화재 위험이 있을 수 있습니다. 이러한 포트를 사용하기 전에 연결된 기기 또는 액세서리에 화재 안전 보호 기능이 있는지 확인하십시오.
       - |PRODUCT_NAME|은(는) IEC/EN/UL 62368-1(또는 기타 동등한 표준)의 6.3, 6.4 및 6.5항을 준수하는 기기 또는 액세서리에만 연결하십시오.
       - 최대 출력 전력을 얻으려면 USB-C to USB-C 5A 케이블(20V DC/5A, 100W)을 사용하십시오.


| 본 제품은 별도로 판매되며 당사 웹사이트에서 구매 가능한 Jackery 12V 차량 배터리 충전 케이블을 사용하여 차량 배터리를 충전할 수 있습니다.


.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **주의**
     -
       - DC 12V 포트는 12V 차량 배터리에만 호환되며 24V 시스템에는 적합하지 않습니다.
       - 제품이 12V DC 출력 포트를 통해 차량 배터리를 충전하는 동안에는 시동을 걸지 마십시오. 제품이 손상될 수 있습니다.
       - 이 기능은 비상용으로만 사용하도록 설계되었으며, 방전되었거나 손상된 차량 배터리는 충전할 수 없습니다.

에너지 절약 모드
------------------------

출력을 끄는 것을 잊어 발생하는 불필요한 배터리 소모를 방지하기 위해 본 제품은 기본적으로 에너지 절약 모드가 활성화되어 있습니다. AC 출력 또는 DC/USB 출력이 켜지면 LCD 화면에 에너지 절약 모드 아이콘이 표시됩니다. 이 모드에서는 연결된 기기가 없거나 연결된 기기의 소비 전력이 특정 임계값(AC 출력 |ENERGY_SAVING_AC_THRESHOLD| 또는 DC/USB 출력 |ENERGY_SAVING_DC_THRESHOLD|) 미만인 경우 설정된 시간이 지나면 해당 출력이 자동으로 꺼집니다. 기본 설정은 |ENERGY_SAVING_AUTO_OFF_DURATION|입니다. 에너지 절약 모드 지속 시간은 Jackery App에서 1H, 2H, 8H, 12H 또는 24H로 설정할 수 있습니다. Never Off로 설정하면 에너지 절약 모드는 비활성화됩니다.

에너지 절약 모드를 비활성화하려면 AC 전원 버튼과 전원 버튼을 동시에 3초 이상 길게 누르십시오. 에너지 절약 모드가 비활성화되면 LCD 화면에 아이콘이 더 이상 표시되지 않으며, 제품은 AC 또는 USB 출력을 자동으로 끄지 않습니다.

저전력 기기(AC ≤ |ENERGY_SAVING_AC_THRESHOLD| 또는 DC/USB ≤ |ENERGY_SAVING_DC_THRESHOLD|)에 전원을 공급할 때는 출력이 자동으로 꺼지는 것을 방지하려면 에너지 절약 모드를 비활성화하십시오.

.. image:: asset:operation/energy_saving
   :alt: Energy saving mode key operation placeholder.
   :width: 320px


| 두 버튼을 동시에 3초 이상 길게 누르십시오.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **참고**
     - 전원을 켠 후 에너지 절약 모드는 이전 상태로 복원됩니다. 모드는 수동으로 전환해야 합니다.


LED 조명 켜기/끄기
------------------------

LED 조명에는 두 가지 모드가 있습니다: 조명 모드 및 SOS 모드. 어떤 모드에서든 LED 조명 버튼을 길게 누르면 조명이 꺼집니다.

.. image:: asset:operation/led_light
   :alt: LED light mode operation placeholder.
   :width: 360px

|
| LED 조명 버튼을 한 번 눌러 조명을 켜십시오.
| 다시 한 번 누르면 SOS 모드로 전환됩니다.
| 세 번째로 누르면 조명이 꺼집니다.

AC 및 DC 출력 재개 기능
------------------------

AC/DC 출력 재개 기능은 기본적으로 비활성화되어 있습니다. App에서 이 기능을 활성화하면 장치가 AC/DC 출력 상태를 기억하고 정의된 조건에서 AC 및 DC 출력을 자동으로 재개할 수 있습니다.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - 자동 재개 조건
     - 자동 재개하지 않는 조건
   * - - 종료 또는 재시작 후 전원 켜기/재시작
       - 방전 하한 도달 후 배터리 SOC ≥ 방전 하한 +10%
       - OTA 업그레이드 완료
     - - 수동 출력 끄기(버튼/App)
       - 에너지 절약 모드 출력 끄기
       - 보호 작동으로 인한 출력 끄기
       - 방전 타이머 작동으로 인한 출력 끄기

LCD 화면
------------------------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="asset:operation/lcd_mode" alt="LCD display mode placeholder." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">잠시 켜기</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">켜기</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">전원 버튼을 누르거나 제품이 충전 중일 때 켜집니다.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">끄기</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">전원 버튼을 누르십시오.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">자동으로 끄기</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">2분 동안 조작이 없으면 LCD 화면이 자동으로 꺼지고 절전 모드로 전환됩니다.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">상시 켜짐(충전 또는 방전 상태에서)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">켜기</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">제품 전원이 켜진 상태에서 전원 버튼을 두 번 누르십시오.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">끄기</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">전원 버튼을 누르십시오.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">자동으로 끄기</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">|DEFAULT_STANDBY_DURATION| 동안 조작이 없으면 LCD 화면이 자동으로 꺼집니다.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{잠시 켜기}{켜기}{전원 버튼을 누르거나 제품이 충전 중일 때 켜집니다.}{끄기}{전원 버튼을 누르십시오.}{자동으로 끄기}{2분 동안 조작이 없으면 LCD 화면이 자동으로 꺼지고 절전 모드로 전환됩니다.}
      \HBLcdModeSecondGroup{상시 켜짐(충전 또는 방전 상태에서)}{켜기}{제품 전원이 켜진 상태에서 전원 버튼을 두 번 누르십시오.}{끄기}{전원 버튼을 누르십시오.}{자동으로 끄기}{|DEFAULT_STANDBY_DURATION| 동안 조작이 없으면 LCD 화면이 자동으로 꺼집니다.}
      \end{HBLcdModeTable}

또한 Jackery App에서 화면 표시 모드를 설정할 수 있습니다.

키 조합
------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - 버튼
     - 조작
     - 기능
   * - 전원 버튼 + AC 전원 버튼
     - 두 버튼을 3초 동안 길게 누르기
     - 에너지 절약 모드 켜기/끄기
   * - 전원 버튼 + DC/USB 전원 버튼
     - 두 버튼을 3초 동안 길게 누르기
     - Wi-Fi 및 블루투스 재설정
   * - DC/USB 전원 버튼 + AC 전원 버튼
     - 두 버튼을 1초 동안 길게 누르기
     - Wi-Fi 및 블루투스 켜기/끄기
   * - 전원 버튼 + LED 조명 버튼
     - 두 버튼을 1초 동안 길게 누르기
     - 비상 충전 모드 켜기/끄기
