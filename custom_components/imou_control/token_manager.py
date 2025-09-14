from __future__ import annotations
import time, uuid, requests
from typing import Optional, Tuple, Dict, Any
from . import TOKEN_ENDPOINT
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

    def _fetch_new_token(self) -> Tuple[str, float]:
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
            "params": {}
        }
        resp = requests.post(self._url(TOKEN_ENDPOINT), json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

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

    def get_token(self) -> str:
        now = time.time()
        if not self._token or now >= self._exp_ts:
            token, exp_ts = self._fetch_new_token()
            self._token, self._exp_ts = token, exp_ts
        return self._token

    # ==== NOVO: APIs para forçar renovação (usadas no retry) ====

    def refresh_token(self) -> str:
        """Força renovação imediata do token e retorna o novo valor."""
        token, exp_ts = self._fetch_new_token()
        self._token, self._exp_ts = token, exp_ts
        return self._token

    def invalidate(self) -> None:
        """Invalida o token atual (próxima get_token() renova)."""
        self._token = None
        self._exp_ts = 0.0
