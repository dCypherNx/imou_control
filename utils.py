from __future__ import annotations
import time, uuid, hashlib
from typing import Tuple, Dict

def make_system(app_id: str, app_secret: str) -> Tuple[Dict, int, str]:
    """
    Monta 'system' conforme especificação Imou:
    sign = md5( f"time:{time},nonce:{nonce},appSecret:{app_secret}" ).hexdigest().lower()
    Retorna (system_dict, time_ts, nonce_str)
    """
    ts = int(time.time())
    nonce = str(uuid.uuid4())
    raw = f"time:{ts},nonce:{nonce},appSecret:{app_secret}"
    sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
    system = {
        "ver": "1.0",
        "appId": app_id,
        "sign": sign,
        "time": ts,
        "nonce": nonce
    }
    return system, ts, nonce
