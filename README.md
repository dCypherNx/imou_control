# Imou Control

Integração personalizada para controlar câmeras Imou no Home Assistant.

## Serviços disponíveis

### `imou_control.set_position`
Move a câmera para uma posição absoluta definindo os valores `h`, `v` e `z`.

### `imou_control.define_preset`
Registra localmente um preset (nome e h/v/z) para um dispositivo específico.

### `imou_control.call_preset`
Posiciona a câmera em um preset previamente definido. Se o preset solicitado já
for o último executado para o dispositivo, nenhum comando é enviado à nuvem
para evitar consumo da cota mensal.
