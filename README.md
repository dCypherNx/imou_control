# Imou Control

Integração personalizada para controlar câmeras Imou no Home Assistant.

Após configurar as credenciais, a integração consulta a conta na nuvem e
registra automaticamente todas as câmeras encontradas. Para cada dispositivo são
criadas entidades numéricas (modo caixa) para os eixos **H** e **V** com faixa de
`-1` a `1` e casas decimais. Após informar os valores desejados, um botão
"Move" executa o comando para testar o posicionamento. Cada câmera também possui
uma entidade de texto para informar o nome do preset e um botão "Save Preset"
que grava os valores atuais de H e V sob o nome escolhido. Os presets definidos
ficam disponíveis em uma entidade *select* e podem ser acionados diretamente
nela ou via serviço.

## Serviços disponíveis

### `imou_control.set_position`
Move a câmera para uma posição absoluta definindo os valores `h`, `v` e `z`.

### `imou_control.define_preset`
Registra localmente um preset (nome e h/v/z) para um dispositivo específico.

### `imou_control.save_preset`
Registra um preset usando os valores atuais das entidades de posição.

### `imou_control.call_preset`
Posiciona a câmera em um preset previamente definido. Se o preset solicitado já
for o último executado para o dispositivo, nenhum comando é enviado à nuvem
para evitar consumo da cota mensal. Um evento `imou_control_preset_called` é
emitido sempre que um preset é acionado, permitindo visualizar no histórico quem
executou o comando.
