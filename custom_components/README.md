# Imou Control (Home Assistant)

Integração custom para controlar câmeras **Imou** via **OpenAPI** (PTZ absoluto).

> **Status**: v0.0.3 (básico, `set_position`)

## Instalação (HACS)

1. HACS → Integrations → Menu ⋮ → **Custom repositories**  
   - URL: `https://github.com/<user>/<repo>`  
   - Category: **Integration**
2. Pesquise por **Imou Control** e instale.
3. Reinicie o Home Assistant.
4. Adicione a integração **Imou Control** e informe:
   - **App ID**
   - **App Secret**
   - **API base URL** (ex.: `https://openapi-or.easy4ip.com` — use seu datacenter)

## Serviços

### `imou_control.set_position`
Move a câmera para posição absoluta.

```yaml
service: imou_control.set_position
data:
  device_id: 8A06C29PAZD70C5
  h: -0.6
  v: 0.15
  z: 0

```


## ℹ️ Notas importantes

- A integração renova o `accessToken` automaticamente se o servidor retornar `TK1002` ou `TK1402`.
- O relógio do host deve estar sincronizado (diferença máxima de 5 minutos).
- Use a **API base URL** correspondente ao seu **datacenter** Imou (ex.: `openapi-or`, `openapi-sg`, etc.).

---

## 🗺️ Roadmap

- Descoberta de câmeras e criação de entidades por dispositivo  
- Presets (salvar, listar, ir para ID) com `select` por câmera  
- Métricas/diagnósticos e opções no fluxo de configuração  

---

## 💬 Suporte

Abra issues em:  
[https://github.com/<user>/<repo>/issues](https://github.com/<user>/<repo>/issues)
