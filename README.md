# Imou Control (Home Assistant)

Integração custom para controlar câmeras **Imou** via **OpenAPI** (PTZ absoluto).

## Status do projeto

Versão atual: **v0.0.3** (funcionalidades básicas com serviço `set_position`).

## Instalação (HACS)

1. Em HACS, acesse *Integrations* → Menu ⋮ → **Custom repositories**.
   - URL: `https://github.com/<user>/<repo>`
   - Category: **Integration**
2. Pesquise por **Imou Control** e instale.
3. Reinicie o Home Assistant.
4. Adicione a integração **Imou Control** e informe:
   - **App ID**
   - **App Secret**
   - **API base URL** (ex.: `https://openapi-or.easy4ip.com` — use seu datacenter)

## Uso

### Serviço `imou_control.set_position`
Move a câmera para uma posição absoluta.

```yaml
service: imou_control.set_position
data:
  device_id: 8A06C29PAZD70C5
  h: -0.6
  v: 0.15
  z: 0
```

## Suporte

Abra issues em: [https://github.com/<user>/<repo>/issues](https://github.com/<user>/<repo>/issues)
