from __future__ import annotations

import aiohttp
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional

from .const import PTZ_LOCATION_ENDPOINT
from .utils import make_system

# Códigos de erro que indicam token inválido/expirado
_RETRY_TOKEN_CODES = {"TK1002"}


class ApiClient:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str,
        token_getter: Callable[[], Awaitable[str]],
        session: aiohttp.ClientSession,
        token_refresher: Optional[Callable[[], Awaitable[str]]] = None,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._get_token = token_getter
        self._refresh_token = token_refresher
        self._session = session

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    async def _do_call(
        self,
        path: str,
        params: Dict[str, Any],
        include_token: bool = True,
        token_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executa UMA chamada à OpenAPI com system assinado.
        Se include_token=True, injeta token em params['token'].
        Retorna o JSON (dict) da resposta já convertido.
        """
        # novo bloco 'system' a cada tentativa
        system, _ts, _nonce = make_system(self.app_id, self.app_secret)

        # injeta token dentro de params quando necessário (padrão dos métodos Imou)
        if include_token:
            token = token_override if token_override is not None else await self._get_token()
            params = dict(params)  # cópia
            params["token"] = token

        payload: Dict[str, Any] = {
            "system": system,
            "id": str(uuid.uuid4()),
            "params": params,
        }

        async with self._session.post(self._url(path), json=payload) as resp:
            resp.raise_for_status()
            if resp.content_length:
                return await resp.json(content_type=None)
            return {}

    async def _call_with_retry(
        self,
        path: str,
        params: Dict[str, Any],
        include_token: bool = True,
    ) -> Dict[str, Any]:
        """
        Chama o endpoint e, se retornar TK1002, renova o token e tenta de novo (1x).
        """
        # 1ª tentativa
        data = await self._do_call(path, params, include_token=include_token)
        result = data.get("result") or {}
        code = str(result.get("code", "0"))
        if code == "0" or not include_token:
            return data

        # Se for erro de token, renova e repete 1x
        if code in _RETRY_TOKEN_CODES and self._refresh_token is not None:
            new_token = await self._refresh_token()
            data = await self._do_call(
                path, params, include_token=include_token, token_override=new_token
            )
            result = data.get("result") or {}
            code = str(result.get("code", "0"))
            if code == "0":
                return data

        # Erro persistente
        msg = result.get("msg")
        raise RuntimeError(f"API falhou em {path} (code={code}): {msg}")

    # =======================
    #  Métodos Públicos
    # =======================

    async def set_position(self, device_id: str, h: float, v: float, z: float = 0.0) -> bool:
        """
        PTZ absoluto via /openapi/controlLocationPTZ com retry automático para TK1002.
        """
        params = {
            "deviceId": device_id,
            "channelId": "0",
            "h": float(h),
            "v": float(v),
            "z": float(z),
        }
        data = await self._call_with_retry(PTZ_LOCATION_ENDPOINT, params, include_token=True)
        # sucesso já garantido por _call_with_retry (code == "0")
        return True

    

    # Exemplo de uso genérico (se precisar depois):
    # def call_any(self, path: str, params: Dict[str, Any], require_token: bool = True) -> Dict[str, Any]:
    #     return self._call_with_retry(path, params, include_token=require_token)
