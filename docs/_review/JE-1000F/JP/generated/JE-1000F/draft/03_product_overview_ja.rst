.. raw:: latex

   \HBApplyLang{ja}

.. content-assembly-block: identity
   :type: product_identity
   :fields: product_name, model_no

.. content-assembly-block: asset_front
   :type: asset_callout
   :asset-key: front_product
   :asset-path: docs/templates/word_template/common_assets/overview/front_product.jpg

.. content-assembly-block: feature_front
   :type: feature_overview
   :title-key: FRONT_VIEW_JA
   :fields: MAIN_POWER_BUTTON_LABEL, FRONT_DC12_PORT_LABEL, FRONT_DC12_PORT_SPEC, DC_USB_POWER_BUTTON_LABEL, FRONT_USB_C_LOW_LABEL, FRONT_USB_C_LOW_SPEC, FRONT_USB_C_HIGH_LABEL, FRONT_USB_C_HIGH_SPEC, AC_POWER_BUTTON_LABEL, FRONT_USB_A_LABEL, FRONT_USB_A_SPEC, FRONT_AC_OUTPUT_LABEL, FRONT_AC_OUTPUT_SPEC

.. only:: latex

   .. raw:: latex

      \section{各部の名称}
      \HBOverviewPanel{正面}{front_product.jpg}{%
      \HBOverviewPair{電源ボタン}{}{ハンドル}{}
      \HBOverviewPair{シガーソケット出力ポート}{12V⎓最大10A}{LCDディスプレイ}{}
      \HBOverviewPair{DC/USB出力ボタン}{}{LEDライトボタン}{}
      \HBOverviewPair{USB-C 30W出力ポート}{5V⎓3A，9V⎓3A，12V⎓2.5A，15V⎓2A，20V⎓1.5A，最大30W}{LEDライト}{}
      \HBOverviewPair{USB-C 100W出力ポート}{5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A，最大100W}{AC出力ボタン}{}
      \HBOverviewPair{USB-A 18W出力ポート}{5-6V⎓3A，6-9V⎓2A，9-12V⎓1.5A，最大18W}{AC出力ポート}{100V\textasciitilde{} 50Hz/60Hz，最大15A，定格1500W，瞬間最大3000W}
      }
      \HBOverviewPanel{右側面}{right_side_ports.png}{%
      \HBOverviewFull{DC入力ポート（DC8020）}{PV：16V-60V⎓12A，2ポート最大21A，最大400W \newline ｼｶﾞｰｿｹｯﾄ ：11V-16V⎓最大8A, 2ポート最大8A}
      \HBOverviewFull{AC入力ポート}{100V-120V\textasciitilde{} 50Hz/60Hz，最大15A，最大約1450W}
      }

.. only:: not latex

   各部の名称
   =====

   正面
   --

   .. image:: _assets/templates/word_template/common_assets/overview/front_product.jpg
      :alt: Front product image.
      :width: 420px

   .. list-table::
      :header-rows: 0
      :widths: 50 50

      * - **電源ボタン**
        - **ハンドル**
      * - **シガーソケット出力ポート**

          12V⎓最大10A
        - **LCDディスプレイ**
      * - **DC/USB出力ボタン**
        - **LEDライトボタン**
      * - **USB-C 30W出力ポート**

          5V⎓3A，9V⎓3A，12V⎓2.5A，15V⎓2A，20V⎓1.5A，最大30W
        - **LEDライト**
      * - **USB-C 100W出力ポート**

          5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A，最大100W
        - **AC出力ボタン**
      * - **USB-A 18W出力ポート**

          5-6V⎓3A，6-9V⎓2A，9-12V⎓1.5A，最大18W
        - **AC出力ポート**

          100V~ 50Hz/60Hz，最大15A，定格1500W，瞬間最大3000W

   右側面
   ---

   .. image:: _assets/templates/word_template/common_assets/overview/right_side_ports.png
      :alt: Right side port overview.
      :width: 420px

   .. list-table::
      :header-rows: 0
      :widths: 100

      * - **DC入力ポート（DC8020）**

          PV：16V-60V⎓12A，2ポート最大21A，最大400W

          ｼｶﾞｰｿｹｯﾄ ：11V-16V⎓最大8A, 2ポート最大8A
      * - **AC入力ポート**

          100V-120V~ 50Hz/60Hz，最大15A，最大約1450W

.. content-assembly-block: asset_side
   :type: asset_callout
   :asset-key: right_side_ports
   :asset-path: docs/templates/word_template/common_assets/overview/right_side_ports.png

.. content-assembly-block: feature_side
   :type: feature_overview
   :title-key: RIGHT_SIDE_VIEW
   :fields: SIDE_AC_INPUT_LABEL, SIDE_AC_INPUT_SPEC, SIDE_DC_INPUT_LABEL, SIDE_DC_INPUT_PV_SPEC, SIDE_DC_INPUT_CAR_SPEC
