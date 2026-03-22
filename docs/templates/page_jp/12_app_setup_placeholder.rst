Jackeryアプリ ユーザーマニュアル
================================

アプリをダウンロードしてログインするには
------------------------------------------------

.. image:: templates/word_template/common_assets/app/download.png
   :alt: App download QR and marketplace image.
   :width: 320px

Google PlayまたはApp Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを行ってください。

または、下のQRコードをスキャンしてアプリをダウンロードし、インストールしてください。

デバイスを追加するには
--------------------------------

2.1 APPの右上にあるデバイス追加ボタンをクリックします。

2.2 デバイスの|MAIN_POWER_BUTTON_LABEL|を長押しして電源を入れると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中にボタンをクリックし、アプリが近くのデバイスに接続し、Bluetoothのアクセス許可を開くことを許可します。

.. image:: templates/word_template/common_assets/app/add_device.png
   :alt: App add-device steps.
   :width: 320px

.. image:: templates/word_template/common_assets/overview/front_controls.png
   :alt: Front panel button reference.
   :width: 520px

{{snippet:app_button_reference}}

2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。

**備考**

バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます。

- デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。
- {{snippet:wireless_reset_buttons}}を同時に3秒間押すと、Wi-FiとBluetoothが初期化されます。

2.4 デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは自動的にWi-Fiネットワークに接続します。

**備考**

2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応していません。

2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fiアイコンは常にオンになります。

.. image:: templates/word_template/common_assets/app/connect_result.png
   :alt: App connection result screens.
   :width: 360px

上記のスクリーンショットは参考用となります。

**備考**

Jackeryアプリは、一度に1台のポータブル電源としかBluetooth接続できません。デバイスリストに戻ると、自動的にBluetoothが切断されます。リスト内のポータブル電源をもう一度タップすると、自動的に再接続されます。

デバイスのバインドを解除するには
------------------------------------------------

デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。

ご確認
------

4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）

- デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します。
- 上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、{{snippet:wireless_toggle_buttons}}を同時長押しします。

4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）

{{snippet:wireless_toggle_buttons}}を同時長押しし、ディスプレーにWi-FiとBluetoothのアイコンが消えるまで押し続けます。

4.3 Wi-FiとBluetoothをリセットするには

- {{snippet:wireless_reset_buttons}}を同時に3秒間押すと、Wi-FiとBluetoothが初期化され、接続されているポータブル電源はバインド解除されます。
