from __future__ import annotations
import uuid, requests
from typing import Any, Dict, Callable
from .const import PTZ_LOCATION_ENDPOINT
from .utils import make_system

class ApiClient:
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        base_url: str,
        token_getter: Callable[[], str],
        token_refresher: Callable[[], str] | None = None,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url.rstrip("/")
        self._get_token = token_getter
        self._refresh_token = token_refresher

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _ptz_call(self, device_id: str, h: float, v: float, z: float, token: str) -> Dict[str, Any]:
        # Gera novo system (time/nonce/sign) a cada tentativa
        system, _ts, _nonce = make_system(self.app_id, self.app_secret)
        payload: Dict[str, Any] = {
            "system": system,
            "id": str(uuid.uuid4()),
            "params": {
                "deviceId": device_id,
                "channelId": "0",
                "h": float(h),
                "v": float(v),
                "z": float(z)
            },
            "token": token
        }
        resp = requests.post(self._url(PTZ_LOCATION_ENDPOINT), json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def set_position(self, device_id: str, h: float, v: float, z: float = 0.0) -> bool:
        """
        PTZ absoluto via /openapi/controlLocationPTZ com retry automático em TK1002.
        """
        # 1ª tentativa
        token = self._get_token()
        data = self._ptz_call(device_id, h, v, z, token)
        result = data.get("result") or {}
        code = str(result.get("code", "0"))
        if code == "0":
            return True

        # Se o token expirou, tenta renovar e repetir uma única vez
        if code == "TK1002" and self._refresh_token is not None:
            new_token = self._refresh_token()
            data = self._ptz_call(device_id, h, v, z, new_token)
            result = data.get("result") or {}
            code = str(result.get("code", "0"))
            if code == "0":
                return True

        # Erro persistente
        raise RuntimeError(f"PTZ falhou (code={code}): {result.get('msg')}")
