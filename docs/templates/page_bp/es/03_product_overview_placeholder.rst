{{ copy:product_overview.page_title }}
=====================================

{{ copy:product_overview.front_view }}
-------------------------------------

.. TODO(资产): 加电包正面图待入库 — 源=HTP017 US 出货书 printed p02 FRONT VIEW。
   不能复用 overview/front_controls：那是 Explorer/HomePower 主机面板,与加电包
   (仅 LCD + POWER)不是同一件产品。入库后在此加
   `.. image:: asset:overview/jbp2000b/front_controls`。

.. list-table::
   :header-rows: 0
   :widths: 50 50

   * - **|MAIN_POWER_BUTTON_LABEL|**
     - **{{ copy:product_overview.part.lcd }}**

{{ copy:product_overview.left_side_view }}
-----------------------------------------

.. TODO(资产): 加电包左侧视图待入库 — 源=HTP017 US 出货书 printed p02 LEFT SIDE
   VIEW(把手 + DC 扩容口 A/B)。现有 overview/right_side_ports 是主机右侧图,方位
   与部件都不同。入库后在此加
   `.. image:: asset:overview/jbp2000b/left_side_ports`。

.. list-table::
   :header-rows: 0
   :widths: 50 50

   * - **{{ copy:product_overview.part.handle }}**
     - **|SIDE_DC_EXPANSION_PORT_A_LABEL|**

       |SIDE_DC_EXPANSION_PORT_A_SPEC|
   * -
     - **|SIDE_DC_EXPANSION_PORT_B_LABEL|**

       |SIDE_DC_EXPANSION_PORT_B_SPEC|
