使い方
======

|MAIN_POWER_BUTTON_LABEL| オン/オフ
-----------------

.. image:: templates/word_template/common_assets/operation/main_power.png
   :alt: Main power operation diagram.
   :width: 360px

オン

1回押す

オフ

3秒間長押し

本製品のデフォルトの待機時間は|DEFAULT_STANDBY_DURATION|です（充電または放電がない場合、|DEFAULT_STANDBY_DURATION|後に自動的にシャットダウンします）。待機時間はJackeryアプリで設定できます。

省エネモードがオンのとき、AC出力またはDC/USB出力がオンでも、|ENERGY_SAVING_AUTO_OFF_DURATION|連続して充放電が行われない場合は、自動的に電源がオフになります。

AC出力のオン/オフ
-----------------

● 前提：|MAIN_POWER_BUTTON_LABEL|がオンになっていることを確認してください。

.. image:: templates/word_template/common_assets/operation/ac_output.png
   :alt: AC output operation diagram.
   :width: 360px

オン

1回押す

オフ

1回押す

**50Hz/60Hz周波数の切り替え**

※ 工場出荷時のデフォルト設定は60Hzに設定されています。

自動識別：お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。

手動調整：AC出力がオンの状態で、|AC_POWER_BUTTON_LABEL|を5秒間長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。

.. image:: templates/word_template/common_assets/operation/frequency_switch.png
   :alt: Frequency switch diagram.
   :width: 360px

USB/カーポート出力オン/オフ
---------------------------

● 前提：|MAIN_POWER_BUTTON_LABEL|がオンになっていることを確認してください。

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: DC and USB output operation diagram.
   :width: 360px

オン

1回押す

オフ

1回押す

**ご注意**

- |USB_C_HIGH_POWER_PORT_LABEL|は、USB-PD Power Source 3（PS3）の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたはアクセサリーに耐火安全保護が備わっていることを確認してください。
- |PRODUCT_NAME| は、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5条に準拠したデバイスまたはアクセサリーのみに接続してください。
- 最大出力を得るためには、公式の|USB_C_HIGH_POWER_CABLE_NAME|（20V DC/5A、100W）を使用してください。

本製品は、別売の|CAR_BATTERY_CHARGING_CABLE_NAME|を使用することで、車のバッテリーへの充電が可能です。

※ |CAR_BATTERY_CHARGING_CABLE_NAME|は付属しておりません。Jackery公式サイトよりお求めいただけます。

**ご注意**

- 12V車専用であり、24V車には対応しておりません。
- 本製品の12V DC出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障につながる恐れがあります。
- この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応しておりません。

省エネモード
------------

省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンになっています。AC出力が|ENERGY_SAVING_AC_THRESHOLD|以下、またはDC/USB出力が|ENERGY_SAVING_DC_THRESHOLD|以下の状態が|ENERGY_SAVING_AUTO_OFF_DURATION|続くと、自動的に出力がオフになります。ACまたはDC/USB出力がオンの状態では、画面に省エネアイコンが表示されます。アイコンの表示時間は、設定された省エネ時間に応じて変わります。

.. list-table::
   :header-rows: 1
   :widths: 30 25 45

   * - 出力ポートタイプ
     - 電力設定値
     - デフォルト設定
   * - AC 出力ポート
     - ≤|ENERGY_SAVING_AC_THRESHOLD|
     - |ENERGY_SAVING_AUTO_OFF_DURATION|経つとすべての出力は自動的にオフになります。
   * - DC/USB 出力ポート
     - ≤|ENERGY_SAVING_DC_THRESHOLD|
     - |ENERGY_SAVING_AUTO_OFF_DURATION|経つとすべての出力は自動的にオフになります。

※ 交流|ENERGY_SAVING_AC_THRESHOLD|および直流|ENERGY_SAVING_DC_THRESHOLD|以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフにならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上の省エネアイコンは表示されなくなります。

|AC_POWER_BUTTON_LABEL|がオンの状態で、|AC_POWER_BUTTON_LABEL|と|MAIN_POWER_BUTTON_LABEL|を同時に長押しし、省エネアイコンの表示（オン）/ 非表示（オフ）が切り替わるまで押し続けてください。

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Energy saving mode diagram.
   :width: 320px

オン/オフ

両方を3秒間長押し

**説明**

省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。

LEDライト
---------

LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しすることでLEDライトを消灯できます。

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: LED light operation diagram.
   :width: 360px

LEDスイッチを短く押すとLEDライトが点灯し、再度短く押すとSOSモードに切り替わります。さらにもう一度短く押すとライトが消灯します。

LCDスクリーン
-------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - 表示
     - モード
     - 操作
     - 動作
   * - .. image:: templates/word_template/common_assets/operation/lcd_mode.png
          :alt: LCD display mode diagram.
          :width: 140px
     - 短くオン
     - オンにする
     - |MAIN_POWER_BUTTON_LABEL|を押すか、充電入力がある場合。
   * -
     - 短くオン
     - オフにする
     - |MAIN_POWER_BUTTON_LABEL|を押します。
   * -
     - 短くオン
     - 自動オフ
     - 2分後にLCDは自動的に消灯し、スリープモードになります。
   * -
     - 常時オン
     - オンにする
     - デバイスが起動している状態で|MAIN_POWER_BUTTON_LABEL|を2回押します。
   * -
     - 常時オン
     - オフにする
     - |MAIN_POWER_BUTTON_LABEL|を押します。
   * -
     - 常時オン
     - 自動オフ
     - 常時点灯ディスプレイモードは、|DEFAULT_STANDBY_DURATION|操作がないと自動的に消灯します。

Jackeryアプリで画面表示モードを設定することもできます。

ボタン操作
----------

.. list-table::
   :header-rows: 1
   :widths: 46 24 30

   * - ボタン
     - 操作
     - 機能
   * - |MAIN_POWER_BUTTON_LABEL| + |AC_POWER_BUTTON_LABEL|
     - 両方を3秒間長押し
     - 省エネモードのオン/ オフを切り替えます。
   * - {{snippet:wireless_reset_buttons}}
     - 両方を3秒間長押し
     - Wi-Fiのリセット
   * - {{snippet:wireless_toggle_buttons}}
     - 両方を1秒間長押し
     - Wi-Fi＆Bluetooth オン/オフ
