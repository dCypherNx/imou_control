from __future__ import annotations

import asyncio
import inspect
import json
import logging
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

import aiohttp

from .const import PTZ_LOCATION_ENDPOINT, DEVICE_LIST_ENDPOINT
from .usage import ApiUsageTracker
from .utils import make_system

# Códigos de erro que indicam token inválido/expirado
_RETRY_TOKEN_CODES = {"TK1002"}


_LOGGER = logging.getLogger(__name__)


TokenCallable = Callable[[], Union[str, Awaitable[str]]]


class ApiClient:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str,
        session: aiohttp.ClientSession,
        token_getter: TokenCallable,
        token_refresher: Optional[TokenCallable] = None,
        usage: ApiUsageTracker | None = None,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._session = session
        self._get_token = token_getter
        self._refresh_token = token_refresher
        self._timeout = aiohttp.ClientTimeout(total=10)
        self._usage = usage

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    async def _resolve_token(self, func: TokenCallable) -> str:
        token = func()
        if inspect.isawaitable(token):
            return await token
        return token

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
            token = (
                token_override
                if token_override is not None
                else await self._resolve_token(self._get_token)
            )
            params = dict(params)  # cópia
            params["token"] = token

        payload: Dict[str, Any] = {
            "system": system,
            "id": str(uuid.uuid4()),
            "params": params,
        }

        try:
            async with self._session.post(
                self._url(path), json=payload, timeout=self._timeout
            ) as response:
                if self._usage is not None:
                    self._usage.note_call(response.headers.get("Date"))
                response.raise_for_status()
                text = await response.text()
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout ao chamar %s: %s", path, err)
            raise RuntimeError(f"Timeout ao chamar {path}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Erro de cliente ao chamar %s: %s", path, err)
            raise RuntimeError(f"Erro de cliente ao chamar {path}") from err

        if not text:
            return {}

        try:
            return json.loads(text)
        except json.JSONDecodeError as err:
            _LOGGER.error("Resposta inválida ao chamar %s: %s", path, err)
            raise RuntimeError(f"Resposta inválida ao chamar {path}") from err

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
            new_token = await self._resolve_token(self._refresh_token)
            data = await self._do_call(
                path,
                params,
                include_token=include_token,
                token_override=new_token,
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

    async def list_devices(self) -> List[Dict[str, Any]]:
        """Obtém a lista de dispositivos vinculados à conta Imou."""
        params = {
            "bindId": "-1",
            "limit": 128,
            "type": "bindAndShare",
            "needApInfo": "false",
        }
        try:
            data = await self._call_with_retry(DEVICE_LIST_ENDPOINT, params, include_token=True)
        except Exception as err:
            _LOGGER.error("Falha ao listar dispositivos: %s", err)
            return []

        result = data.get("result") or {}
        devices = (
            (result.get("data") or {}).get("deviceList")
            or result.get("devices")
            or result.get("list")
            or []
        )

        return devices if isinstance(devices, list) else []

    # Exemplo de uso genérico (se precisar depois):
    # def call_any(self, path: str, params: Dict[str, Any], require_token: bool = True) -> Dict[str, Any]:
    #     return self._call_with_retry(path, params, include_token=require_token)
