from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional, Tuple

import aiohttp

from .const import TOKEN_ENDPOINT
from .utils import make_system


_LOGGER = logging.getLogger(__name__)


class TokenManager:
    """Gerencia o accessToken (cache + renovação) para a Imou OpenAPI."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str,
        session: aiohttp.ClientSession,
    ):
        self._app_id = app_id
        self._app_secret = app_secret
        self._base_url = base_url.rstrip("/")
        self._session = session
        self._token: Optional[str] = None
        self._exp_ts: float = 0.0  # epoch seconds
        self._timeout = aiohttp.ClientTimeout(total=10)
        self._lock = asyncio.Lock()

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    async def _fetch_new_token(self) -> Tuple[str, float]:
        """
        Faz POST em /openapi/accessToken com 'system' assinado (sign/nonce/time).
        Resposta esperada:
        {
          "result": {"code":"0","msg":"...","data":{"accessToken":"...","expireTime":259176}},
          "id":"..."
        }
        """
        system, now, _nonce = make_system(self._app_id, self._app_secret)
        payload: Dict[str, Any] = {
            "system": system,
            "id": str(uuid.uuid4()),
            "params": {},
        }
        try:
            async with self._session.post(
                self._url(TOKEN_ENDPOINT), json=payload, timeout=self._timeout
            ) as response:
                response.raise_for_status()
                text = await response.text()
        except asyncio.TimeoutError as err:
            _LOGGER.error("Timeout ao solicitar novo token: %s", err)
            raise RuntimeError("Timeout ao solicitar token") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Erro de cliente ao solicitar novo token: %s", err)
            raise RuntimeError("Erro de cliente ao solicitar token") from err

        if not text:
            data: Dict[str, Any] = {}
        else:
            try:
                data = json.loads(text)
            except json.JSONDecodeError as err:
                _LOGGER.error("Resposta inválida ao solicitar token: %s", err)
                raise RuntimeError("Resposta inválida ao solicitar token") from err

        result = data.get("result") or {}
        code = str(result.get("code", ""))
        if code != "0":
            msg = result.get("msg") or "error"
            raise RuntimeError(f"Falha ao obter token (code={code}): {msg}")

        rdata = result.get("data") or {}
        token = rdata.get("accessToken") or rdata.get("token")
        if not token:
            raise RuntimeError(f"Token ausente na resposta: {data}")

        expire_in = int(rdata.get("expireTime", 3600))
        exp_ts = now + expire_in - 30  # margem de 30s
        return token, exp_ts

    async def get_token(self) -> str:
        if self._token and time.time() < self._exp_ts:
            return self._token

        async with self._lock:
            if self._token and time.time() < self._exp_ts:
                return self._token

            token, exp_ts = await self._fetch_new_token()
            self._token, self._exp_ts = token, exp_ts
            return self._token

    # ==== NOVO: APIs para forçar renovação (usadas no retry) ====

    async def refresh_token(self) -> str:
        """Força renovação imediata do token e retorna o novo valor."""
        async with self._lock:
            token, exp_ts = await self._fetch_new_token()
            self._token, self._exp_ts = token, exp_ts
            return self._token

    async def invalidate(self) -> None:
        """Invalida o token atual (próxima get_token() renova)."""
        async with self._lock:
            self._token = None
            self._exp_ts = 0.0
