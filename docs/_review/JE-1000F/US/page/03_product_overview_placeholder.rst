.. raw:: latex

   \HBApplyLang{en}

.. content-assembly-block: identity
   :type: product_identity
   :fields: product_name, model_no

.. content-assembly-block: asset_front
   :type: asset_callout
   :asset-key: front_product
   :asset-path: docs/templates/word_template/common_assets/overview/front_product.jpg

.. content-assembly-block: feature_front
   :type: feature_overview
   :title-key: FRONT_VIEW
   :fields: MAIN_POWER_BUTTON_LABEL, FRONT_DC12_PORT_LABEL, FRONT_DC12_PORT_SPEC, DC_USB_POWER_BUTTON_LABEL, FRONT_USB_C_LOW_LABEL, FRONT_USB_C_LOW_SPEC, FRONT_USB_C_HIGH_LABEL, FRONT_USB_C_HIGH_SPEC, AC_POWER_BUTTON_LABEL, FRONT_USB_A_LABEL, FRONT_USB_A_SPEC, FRONT_AC_OUTPUT_LABEL, FRONT_AC_OUTPUT_SPEC

.. only:: latex

   .. raw:: latex

      \section{PRODUCT OVERVIEW}
      \HBOverviewPanel{FRONT VIEW}{front_product.jpg}{%
      \HBOverviewPair{POWER Button}{}{Handle}{}
      \HBOverviewPair{DC 12 V Port}{12 V / 10 A max.}{LCD}{}
      \HBOverviewPair{DC / USB Power Button}{}{LED Light Button}{}
      \HBOverviewPair{USB-C 30 W Output}{30 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2.5 A, 15 V⎓2 A, 20 V⎓1.5 A}{LED Light}{}
      \HBOverviewPair{USB-C 100 W Output}{100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A}{AC Power Button}{}
      \HBOverviewPair{USB-A 18 W Output}{18 W max., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1.5 A}{AC Output}{120 V\textasciitilde{} 60 Hz, 12.5 A max., 1500 W Rated}
      \HBOverviewFull{Total Output}{1500 W Rated, 3000 W Surge Peak}
      }
      \HBOverviewPanel{RIGHT SIDE VIEW}{right_side_ports.png}{%
      \HBOverviewPair{Handle}{}{AC Input}{100 V-120 V\textasciitilde{} 60 Hz, 15 A max.}
      \HBOverviewPair{}{}{DC Input (2×DC8020 Ports)}{PV: 16-60 V⎓12 A max., Double to 21 A / 400 W max. \newline Car: 11-16 V⎓8 A max., Double to 8 A max.}
      }

.. only:: not latex

   PRODUCT OVERVIEW
   ================

   FRONT VIEW
   ----------

   .. image:: _assets/templates/word_template/common_assets/overview/front_product.jpg
      :alt: Front view diagram placeholder.
      :width: 420px

   .. list-table::
      :header-rows: 0
      :widths: 50 50

      * - **POWER Button**
        - **Handle**
      * - **DC 12 V Port**

          12 V / 10 A max.
        - **LCD**
      * - **DC / USB Power Button**
        - **LED Light Button**
      * - **USB-C 30 W Output**

          30 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓2.5 A, 15 V⎓2 A, 20 V⎓1.5 A
        - **LED Light**
      * - **USB-C 100 W Output**

          100 W max., 5 V⎓3 A, 9 V⎓3 A, 12 V⎓3 A, 15 V⎓3 A, 20 V⎓5 A
        - **AC Power Button**
      * - **USB-A 18 W Output**

          18 W max., 5-6 V⎓3 A, 6-9 V⎓2 A, 9-12 V⎓1.5 A
        - **AC Output**

          120 V~ 60 Hz, 12.5 A max., 1500 W Rated

   .. list-table::
      :header-rows: 0
      :widths: 100

      * - **Total Output**

          1500 W Rated, 3000 W Surge Peak

   RIGHT SIDE VIEW
   ---------------

   .. image:: _assets/templates/word_template/common_assets/overview/right_side_ports.png
      :alt: Right side view diagram placeholder.
      :width: 420px

   .. list-table::
      :header-rows: 0
      :widths: 50 50

      * - **Handle**
        - **AC Input**

          100 V-120 V~ 60 Hz, 15 A max.
      * -
        - **DC Input (2×DC8020 Ports)**

          PV: 16-60 V⎓12 A max., Double to 21 A / 400 W max.

          Car: 11-16 V⎓8 A max., Double to 8 A max.

.. content-assembly-block: asset_side
   :type: asset_callout
   :asset-key: right_side_ports
   :asset-path: docs/templates/word_template/common_assets/overview/right_side_ports.png

.. content-assembly-block: feature_side
   :type: feature_overview
   :title-key: RIGHT_SIDE_VIEW
   :fields: SIDE_AC_INPUT_LABEL, SIDE_AC_INPUT_SPEC, SIDE_DC_INPUT_LABEL, SIDE_DC_INPUT_PV_SPEC, SIDE_DC_INPUT_CAR_SPEC

.. content-assembly-block: spec_front_total
   :type: spec_summary
   :title-key: FRONT_TOTAL_OUTPUT
   :fields: FRONT_TOTAL_OUTPUT_LABEL, FRONT_TOTAL_OUTPUT_SPEC
