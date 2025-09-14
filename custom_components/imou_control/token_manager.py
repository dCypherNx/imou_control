from __future__ import annotations
import asyncio
import time, uuid, requests
from typing import Optional, Tuple, Dict, Any
from .const import TOKEN_ENDPOINT
from .utils import make_system


class TokenManager:
    """Gerencia o accessToken (cache + renovação) para a Imou OpenAPI."""

    def __init__(self, app_id: str, app_secret: str, base_url: str):
        self._app_id = app_id
        self._app_secret = app_secret
        self._base_url = base_url.rstrip("/")
        self._token: Optional[str] = None
        self._exp_ts: float = 0.0  # epoch seconds

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
        def do_post():
            return requests.post(self._url(TOKEN_ENDPOINT), json=payload, timeout=10)

        resp = await asyncio.get_event_loop().run_in_executor(None, do_post)
        resp.raise_for_status()
        data = resp.json() if getattr(resp, "content", None) else {}

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

    async def async_get_token(self) -> str:
        now = time.time()
        if not self._token or now >= self._exp_ts:
            token, exp_ts = await self._fetch_new_token()
            self._token, self._exp_ts = token, exp_ts
        return self._token

    def get_token(self) -> str:
        """Synchronous wrapper for tests."""
        return asyncio.get_event_loop().run_until_complete(self.async_get_token())

    # ==== NOVO: APIs para forçar renovação (usadas no retry) ====

    async def async_refresh_token(self) -> str:
        """Força renovação imediata do token e retorna o novo valor."""
        token, exp_ts = await self._fetch_new_token()
        self._token, self._exp_ts = token, exp_ts
        return self._token

    def refresh_token(self) -> str:
        """Synchronous wrapper for tests."""
        return asyncio.get_event_loop().run_until_complete(self.async_refresh_token())

    def invalidate(self) -> None:
        """Invalida o token atual (próxima get_token() renova)."""
        self._token = None
        self._exp_ts = 0.0

