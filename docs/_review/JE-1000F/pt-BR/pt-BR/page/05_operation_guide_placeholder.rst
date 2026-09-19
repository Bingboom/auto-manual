.. raw:: latex

   \HBApplyLang{pt-BR}

OPERAÇÕES
=========

LIGAR/DESLIGAR
--------------

.. image:: _assets/templates/word_template/common_assets/operation/main_power.png
   :alt: Operação de ligar/desligar.
   :width: 360px

| Ligado: pressione uma vez.
| Desligado: pressione e segure por 3 s.

| **Tempo de espera padrão:** 2 horas.
| O produto será desligado automaticamente após 2 horas de inatividade, sem carregamento nem descarregamento.
| \*O tempo de espera pode ser definido no aplicativo Jackery.
| Quando o Modo de Economia de Energia estiver ativado, o produto será desligado automaticamente após 12 horas se o botão CA ou o botão CC/USB estiver ligado, mas o produto não estiver carregando nem descarregando.

SAÍDA CA LIGAR/DESLIGAR
-----------------------

**Pré-requisito:** o produto está ligado.

.. image:: _assets/templates/word_template/common_assets/operation/ac_output.png
   :alt: Operação da saída CA.
   :width: 360px


| **Ligado**
| Pressione uma vez
| **Desligado**
| Pressione uma vez


SAÍDA CC 12V/USB LIGAR/DESLIGAR
-------------------------------

**Pré-requisito:** o produto está ligado.

.. image:: _assets/templates/word_template/common_assets/operation/dc_usb_output.png
   :alt: Operação da saída CC/USB.
   :width: 360px


| **Ligado**
| Pressione uma vez
| **Desligado**
| Pressione uma vez


.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CUIDADO**
     -
       - **A porta USB-C 100W é uma porta de saída de alta potência USB-PD Power Source 3 (PS3).** Se o dispositivo ou acessório conectado não atender aos requisitos de segurança, pode haver risco de incêndio. Antes de usar essas portas, certifique-se de que o dispositivo ou acessório conectado tenha proteção contra incêndio.
       - Conecte o Jackery Explorer 1000 somente a dispositivos ou acessórios que estejam em conformidade com as cláusulas 6.3, 6.4 e 6.5 da IEC/EN/UL 62368-1 ou com normas equivalentes.
       - Para obter a potência máxima de saída, use o cabo USB-C para USB-C 5A (20V CC/5A, 100W).

| O produto pode carregar a bateria automotiva usando o cabo de carregamento veicular 12V da Jackery, vendido separadamente e disponível em nosso site.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **CUIDADO**
     -
       - A porta CC 12V é compatível apenas com baterias automotivas de 12V e não é adequada para sistemas de 24V.
       - Não dê partida no veículo enquanto o produto estiver carregando a bateria pela porta de saída CC 12V, pois isso pode danificar o produto.
       - Este recurso destina-se apenas ao uso emergencial e não pode carregar uma bateria de carro descarregada ou danificada.

MODO DE ECONOMIA DE ENERGIA
---------------------------

Para evitar consumo desnecessário da bateria caso o usuário esqueça de desligar a saída, o produto ativa o Modo de Economia de Energia por padrão. Quando a saída CA ou CC/USB estiver ligada, o ícone do Modo de Economia de Energia será exibido na tela LCD. Nesse modo, se nenhum dispositivo estiver conectado ou se o consumo de energia do dispositivo conectado estiver abaixo de um determinado limite (saída CA 25 W ou saída CC/USB 2 W), a saída correspondente será desligada automaticamente após o tempo definido. A configuração padrão é 12 horas. A duração do Modo de Economia de Energia pode ser definida no aplicativo Jackery para 1 h, 2 h, 8 h, 12 h ou 24 h. Se estiver definida como Nunca desligar, o Modo de Economia de Energia será desativado.

Para desativar o Modo de Economia de Energia, pressione e segure simultaneamente o botão CA e o botão Power principal por mais de 3 segundos. Depois que o Modo de Economia de Energia for desativado, o ícone não será mais exibido na tela LCD, e o produto não desligará automaticamente a saída CA ou USB.

Ao alimentar dispositivos de baixa potência (CA ≤ 25 W ou CC/USB ≤ 2 W), desative o Modo de Economia de Energia para evitar que a saída seja desligada automaticamente durante a operação.

.. image:: _assets/templates/word_template/common_assets/operation/energy_saving.png
   :alt: Operação das teclas do Modo de Economia de Energia.
   :width: 320px

| Pressione e segure os dois botões por mais de 3 segundos.

.. list-table::
   :header-rows: 0
   :widths: 12 88

   * - **NOTA**
     - O Modo de Economia de Energia retoma o estado anterior após ligar o produto. É necessário alternar manualmente para mudar o modo.

LUZ LED LIGAR/DESLIGAR
----------------------

A luz LED possui dois modos: modo de luz e modo SOS. Em qualquer modo, pressione e segure o botão da luz LED para desligar a luz.

.. image:: _assets/templates/word_template/common_assets/operation/led_light.png
   :alt: Operação do modo da luz LED.
   :width: 360px


| Pressione o botão da luz LED uma vez para ligar a luz.
| Pressione novamente para alternar para o modo SOS.
| Pressione uma terceira vez para desligar a luz.

FUNÇÃO DE RETOMADA DA SAÍDA CA E CC
-----------------------------------

A Função de Retomada da Saída CA/CC é desativada por padrão. Ative essa função no aplicativo para permitir que o dispositivo memorize o status da saída CA/CC e retome automaticamente as saídas CA e CC em condições definidas.

+---------------------------------------------------------------+------------------------------------------------+
| Condições de retomada automática                              | Condições sem retomada automática             |
+===============================================================+================================================+
| Ligar/reiniciar após desligamento ou reinicialização          | Saída desligada manualmente (botão/aplicativo) |
+---------------------------------------------------------------+------------------------------------------------+
| SOC da bateria ≥ limite de descarga +10% após atingir limite  | Saída desligada pelo Modo de Economia de Energia |
+---------------------------------------------------------------+------------------------------------------------+
|                                                               | Saída desligada por proteção acionada          |
+---------------------------------------------------------------+------------------------------------------------+
| Atualização OTA concluída                                     | Saída desligada por temporizador de descarga   |
+---------------------------------------------------------------+------------------------------------------------+

TELA LCD
--------

.. only:: html

   .. raw:: html

      <table style="width:100%; border-collapse:collapse; margin:0.75rem 0 0.5rem 0;">
        <tr>
          <td rowspan="6" style="width:24%; border:1px solid #cfcfcf; padding:8px; vertical-align:top; text-align:center;">
            <img src="_assets/templates/word_template/common_assets/operation/lcd_mode.png" alt="Modo de exibição LCD." style="max-width:140px; width:100%; height:auto; display:block; margin:0 auto;">
          </td>
          <td rowspan="3" style="width:18%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Ligado temporariamente</td>
          <td style="width:12%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Ligar</td>
          <td style="width:46%; border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Pressione o botão Power principal ou quando o produto estiver carregando.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Desligar</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Pressione o botão Power principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Desligamento automático</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">A tela LCD desliga automaticamente e entra em modo de suspensão após 2 minutos de inatividade.</td>
        </tr>
        <tr>
          <td rowspan="3" style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Sempre ligada (durante carregamento ou descarregamento)</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Ligar</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Pressione duas vezes o botão Power principal quando o produto estiver ligado.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Desligar</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Pressione o botão Power principal.</td>
        </tr>
        <tr>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">Desligamento automático</td>
          <td style="border:1px solid #cfcfcf; padding:8px; vertical-align:top;">A tela LCD desliga automaticamente após 2 horas de inatividade.</td>
        </tr>
      </table>

.. only:: latex

   .. raw:: latex

      \begin{HBLcdModeTable}{lcd_mode.png}
      \HBLcdModeFirstGroup{Ligado temporariamente}{Ligar}{Pressione o botão Power principal ou quando o produto estiver carregando.}{Desligar}{Pressione o botão Power principal.}{Desligamento automático}{A tela LCD desliga automaticamente e entra em modo de suspensão após 2 minutos de inatividade.}
      \HBLcdModeSecondGroup{Sempre ligada (durante carregamento ou descarregamento)}{Ligar}{Pressione duas vezes o botão Power principal quando o produto estiver ligado.}{Desligar}{Pressione o botão Power principal.}{Desligamento automático}{A tela LCD desliga automaticamente após 2 horas de inatividade.}
      \end{HBLcdModeTable}

Você também pode definir o modo de exibição da tela no aplicativo Jackery.

COMBINAÇÃO DE TECLAS
--------------------

.. list-table::
   :header-rows: 1
   :widths: 40 25 35

   * - Botões
     - Operação
     - Função
   * - Botão Power Principal + Botão CA
     - Mantenha ambos pressionados por 3 s
     - Ligar/desligar o Modo de Economia de Energia
   * - Botão Power Principal + Botão CC/USB
     - Mantenha ambos pressionados por 3 s
     - Redefinir Wi-Fi e Bluetooth
   * - Botão CC/USB + Botão CA
     - Mantenha ambos pressionados por 1 s
     - Ligar/desligar Wi-Fi e Bluetooth
   * - Botão Power Principal + botão da luz LED
     - Mantenha ambos pressionados por 1 s
     - Ligar/desligar o Modo de Carregamento de Emergência
