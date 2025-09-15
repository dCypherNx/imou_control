# Imou Control

Integração personalizada para controlar câmeras Imou no Home Assistant.

## Visão geral

Após configurar as credenciais da Open API da Imou, a integração:

- Obtém automaticamente a lista de câmeras vinculadas à conta informada.
- Registra cada câmera no *Device Registry* do Home Assistant.
- Armazena localmente (em armazenamento persistente da integração) os *presets* definidos para cada dispositivo.
- Expõe entidades auxiliares para facilitar o controle de posição e o gerenciamento de *presets* diretamente da interface.
- Disponibiliza serviços para mover a câmera ou salvar/acionar *presets*.
- Dispara um evento no *event bus* sempre que um *preset* é chamado.

## Configuração

A integração utiliza *config flow*. Para configurá-la:

1. Acesse **Configurações > Dispositivos e Serviços > Adicionar integração** no Home Assistant.
2. Procure por **Imou Control**.
3. Informe os dados exigidos pela Open API da Imou:
   - `app_id`
   - `app_secret`
   - `url_base` (ex.: `https://openapi.easy4ipcloud.com`)

Apenas uma instância da integração é permitida. As credenciais são utilizadas para gerar e renovar automaticamente o `accessToken` utilizado pelas chamadas à API.

## Entidades criadas

Para cada câmera encontrada são criadas as seguintes entidades auxiliares:

| Tipo    | Identificador | Função |
|---------|---------------|--------|
| `number` | **Horizontal (h)** e **Vertical (v)** | Guardam os valores normalizados de -1.0 a 1.0 utilizados para mover a câmera. Eles não movimentam a câmera diretamente; utilizam-se desses valores no botão "Mover" ou nos serviços. |
| `text`   | **Nome do preset** | Campo livre para informar o nome de um *preset* antes de pressionar o botão "Salvar preset". |
| `button` | **Mover** | Chama a API `set_position` usando os valores atuais dos eixos `h`, `v` (e `z`, se definido). |
| `button` | **Salvar preset** | Salva localmente um *preset* com o nome definido na entidade de texto e os valores atuais de `h`, `v` e `z`. |
| `select` | **Presets** | Lista os *presets* salvos para a câmera. Selecionar uma opção chama automaticamente o serviço `call_preset`. |

Os *presets* são persistidos em armazenamento local (`.storage`) do Home Assistant. Ao adicionar, renomear ou remover *presets*, o seletor é atualizado automaticamente.

## Serviços disponíveis

A integração expõe quatro serviços no domínio `imou_control`:

### `imou_control.set_position`
Move a câmera para uma posição absoluta definida pelos valores `h`, `v` e `z`.

Campos obrigatórios: `device`, `h`, `v`. O campo `z` (zoom) é opcional.

### `imou_control.define_preset`
Registra um *preset* informando explicitamente os valores `h`, `v` e `z`.

Útil para configurar *presets* manualmente ou importar coordenadas conhecidas. Atualiza imediatamente o seletor de *presets* da câmera.

### `imou_control.save_preset`
Salva um *preset* utilizando os valores atualmente armazenados nas entidades `number` (`h`, `v`) e `z` (quando disponível).

Pode ser acionado pelo botão "Salvar preset" ou manualmente via serviço. Caso o *preset* já exista, ele é sobrescrito.

### `imou_control.call_preset`
Move a câmera para o *preset* informado. Se o *preset* já estiver ativo, a chamada é ignorada para evitar movimentações desnecessárias.

## Evento disparado

Sempre que um *preset* é acionado, a integração dispara o evento `imou_control_preset_called` no *event bus* do Home Assistant. O evento contém os campos:

- `device`: ID da câmera
- `preset`: nome do *preset* chamado

Esse evento pode ser utilizado em automações para executar ações após a movimentação da câmera.

## Referência de campos dos serviços

| Serviço | Campo | Descrição |
|---------|-------|-----------|
| `set_position` | `device` | Nome ou ID do dispositivo. |
|  | `h` | Posição horizontal (intervalo aproximado -1.0 a 1.0, de acordo com a API). |
|  | `v` | Posição vertical (intervalo aproximado -1.0 a 1.0, de acordo com a API). |
|  | `z` | Zoom (quando suportado). |
| `define_preset` | `device` | Nome ou ID do dispositivo. |
|  | `preset` | Nome do *preset* a ser salvo. |
|  | `h`, `v`, `z` | Coordenadas absolutas associadas ao *preset*. |
| `save_preset` | `device` | Nome ou ID do dispositivo. |
|  | `preset` | Nome do *preset* a ser salvo/atualizado. |
| `call_preset` | `device` | Nome ou ID do dispositivo. |
|  | `preset` | Nome do *preset* a ser chamado. |

## Observações

- Os intervalos aceitos para `h` e `v` dependem do modelo da câmera, mas a integração trabalha com o intervalo normalizado de `-1.0` a `1.0`.
- O campo `z` é opcional. Se a câmera não possuir zoom, mantenha o valor `0`.
- Em caso de erro de autenticação (`TK1002`), o token é renovado automaticamente antes de repetir a chamada.
- A integração não cria uma entidade dedicada para zoom; utilize os serviços `set_position` ou `define_preset` para ajustar `z` quando necessário.
