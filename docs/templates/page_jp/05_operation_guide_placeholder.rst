使い方
======

主電源ボタン オン/オフ
----------------------

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

● **前提：** 主電源ボタンがオンになっていることを確認してください。

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

手動調整：AC出力がオンの状態で、AC出力ボタンを5秒間長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。

.. image:: templates/word_template/common_assets/operation/frequency_switch.png
   :alt: Frequency switch diagram.
   :width: 360px

USB/カーポート出力オン/オフ
---------------------------

● **前提：** 主電源ボタンがオンになっていることを確認してください。

.. image:: templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: DC and USB output operation diagram.
   :width: 360px

オン

1回押す

オフ

1回押す

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - ご注意
     - ● |USB_C_HIGH_POWER_PORT_LABEL|は、USB-PD Power Source 3（PS3）の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたはアクセサリーに耐火安全保護が備わっていることを確認してください。

       ● |PRODUCT_NAME|は、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5条に準拠したデバイスまたはアクセサリーのみに接続してください。

       ● 最大出力を得るためには、USB-C to USB-C 5Aケーブル（20V DC/5A、100W）を使用してください。

本製品は、別売のJackery 12V 自動車用バッテリー充電ケーブルを使用することで、車のバッテリーへの充電が可能です。

※ Jackery 12V 自動車用バッテリー充電ケーブルは付属しておりません。Jackery公式サイトよりお求めいただけます。

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - ご注意
     - ● 12V車専用であり、24V車には対応しておりません。

       ● 本製品の12V DC出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障につながる恐れがあります。

       ● この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応しておりません。

省エネモード
------------

省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンになっています。AC出力が|ENERGY_SAVING_AC_THRESHOLD|以下、またはDC/USB出力が|ENERGY_SAVING_DC_THRESHOLD|以下の状態が|ENERGY_SAVING_AUTO_OFF_DURATION|続くと、自動的に出力がオフになります。ACまたはDC/USB出力がオンの状態では、画面に省エネアイコンが表示されます。アイコンの表示時間は、設定された省エネ時間に応じて変わります。省エネ時間は、Jackeryアプリで2H、8H、12H、24Hに設定できます。「オフにしない」に設定すると、省エネモードは無効になります。

.. |es_ac| replace:: ≤|ENERGY_SAVING_AC_THRESHOLD|
.. |es_dc| replace:: ≤|ENERGY_SAVING_DC_THRESHOLD|
.. |es_auto| replace:: |ENERGY_SAVING_AUTO_OFF_DURATION|経つとすべての出力は自動的にオフになります。

+----------------------+--------------+--------------------------------------------+
| 出力ポートタイプ     | 電力設定値   | デフォルト設定                             |
+======================+==============+============================================+
| AC出力ポート         | |es_ac|      | |es_auto|                                  |
+----------------------+--------------+                                            |
| DC/USB出力ポート     | |es_dc|      |                                            |
+----------------------+--------------+--------------------------------------------+

| ※ 交流|ENERGY_SAVING_AC_THRESHOLD|および直流|ENERGY_SAVING_DC_THRESHOLD|以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフにならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上の省エネアイコンは表示されなくなります。
|
| AC出力ボタンがオンの状態で、AC出力ボタンと主電源ボタンを同時に長押しし、省エネアイコンの表示（オン）／非表示（オフ）が切り替わるまで押し続けてください。

.. image:: templates/word_template/common_assets/operation/energy_saving.png
   :alt: Energy saving mode diagram.
   :width: 320px

オン/オフ

両方を3秒間長押し

.. list-table::
   :header-rows: 0
   :widths: 10 90

   * - 説明
     - 省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。

LEDライト
---------

LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しすることでLEDライトを消灯できます。

.. image:: templates/word_template/common_assets/operation/led_light.png
   :alt: LED light operation diagram.
   :width: 360px

| LED スイッチを短く押すと LED ライトが点灯し。
| 再度短く押すと SOS モードに切り替わります。
| 再度短く押すとライトが消灯します。

LCDスクリーン
-------------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="LCD display mode diagram." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">短くオン</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">オンにする</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">主電源ボタンを押すか、充電入力がある場合。</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">オフにする</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">主電源ボタンを押します。</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">自動オフ</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">2分後にLCDは自動的に消灯し、スリープモードになります。</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">常時オン</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">オンにする</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">デバイスが起動している状態で主電源ボタンを2回押します。</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">オフにする</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">主電源ボタンを押します。</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">自動オフ</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">常時点灯ディスプレイモードは、|DEFAULT_STANDBY_DURATION|操作がないと自動的に消灯します。</td>
        </tr>
      </table>


.. only:: latex

   .. raw:: latex

      \begingroup
      \renewcommand{\arraystretch}{1.25}
      \setlength{\tabcolsep}{6pt}
      \begin{tabular}{|m{0.24\linewidth}|m{0.12\linewidth}|m{0.12\linewidth}|m{0.40\linewidth}|}
      \hline
      \multirow{6}{*}{\parbox[c]{0.22\linewidth}{\centering\includegraphics[width=0.20\linewidth]{lcd_mode.png}}}
      & \multirow{3}{*}{短くオン} & オンにする & 主電源ボタンを押すか、充電入力がある場合。 \\ \cline{3-4}
      & & オフにする & 主電源ボタンを押します。 \\ \cline{3-4}
      & & 自動オフ & 2分後にLCDは自動的に消灯し、スリープモードになります。 \\ \cline{2-4}
      & \multirow{3}{*}{常時オン} & オンにする & デバイスが起動している状態で主電源ボタンを2回押します。 \\ \cline{3-4}
      & & オフにする & 主電源ボタンを押します。 \\ \cline{3-4}
      & & 自動オフ & 常時点灯ディスプレイモードは、|DEFAULT_STANDBY_DURATION|操作がないと自動的に消灯します。 \\ \hline
      \end{tabular}
      \endgroup

Jackeryアプリで画面表示モードを設定することもできます。

ボタン操作
----------

.. list-table::
   :header-rows: 1
   :widths: 46 24 30

   * - ボタン
     - 操作
     - 機能
   * - 主電源ボタン + AC出力ボタン
     - 両方を3秒間長押し
     - 省エネモードのオン/ オフを切り替えます。
   * - 主電源ボタン + DC/USB出力ボタン
     - 両方を3秒間長押し
     - Wi-Fiのリセット
   * - AC出力ボタン + DC/USB出力ボタン
     - 両方を1秒間長押し
     - Wi-Fi＆Bluetooth オン/オフ
   * - 主電源ボタン + ライトボタン
     - 両方を1秒間長押し
     - 緊急充電モードのオン/オフを切り替えます。
