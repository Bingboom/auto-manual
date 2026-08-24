CHARGE
======

CHARGEMENT PAR PRISE MURALE CA
------------------------------

En cas de charge murale, ce dispositif doit être utilisé avec le Jackery HomePower 2000 Plus.

.. TODO(资产): AC 壁插接线示意图**尚未提取** — 源=HTP017 US 出货书 printed p14
   上半幅(放大镜示意插头插入 HomePower 面板 DC 输入 + 墙插)。资产提取那一轮
   把它记为「同页可取但超出范围」:容器 #12 bbox 27.71,118.05-339.28,269.13,
   与太阳能图同一页、同样零引线结构。提取并入册后在此加一条 `.. image::` 指向那条资产键。此处**故意不写出键名**:
   资产还没入册,而 tests/test_asset_registry.py 会断言 page_bp 下出现的每个
   asset: 键都解析得通——先前两条面包屑就是点名了不存在的键。

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **AVERTISSEMENT**
     - Assurez-vous que tous les produits sont éteints avant de connecter le HomePower 2000 Plus au(x) Battery Pack 2000.

CHARGEMENT PAR PANNEAUX SOLAIRES (VENDU SÉPARÉMENT)
---------------------------------------------------

Rechargez votre dispositif à l'aide de panneaux solaires et du Jackery HomePower 2000 Plus, comme indiqué dans la figure ci-dessous. Pour plus d'informations, veuillez vous reporter au manuel d'utilisation du Jackery HomePower 2000 Plus.

.. TODO(资产): 太阳能充电接线示意图已入库、待整合 — 源=HTP017 US 出货书 printed p14。
   已注册为 charging/jbp2000b/solar(适用区域 US:主机面板画的是 NEMA 5-20R;
   去字后板子无名,是否需要本地化标题槽待定)。整合切换时在此加
   `.. image:: asset:charging/jbp2000b/solar`。
