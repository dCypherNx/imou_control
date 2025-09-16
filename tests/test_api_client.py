from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.helpers import load_imou_module

ApiClient = load_imou_module("api").ApiClient


@pytest.mark.asyncio
async def test_call_with_retry_refreshes_token_on_tk1002(monkeypatch):
    session = MagicMock()
    token_getter = AsyncMock(return_value="cached-token")
    token_refresher = AsyncMock(return_value="refreshed-token")

    client = ApiClient(
        app_id="app",
        app_secret="secret",
        base_url="https://example.com",
        session=session,
        token_getter=token_getter,
        token_refresher=token_refresher,
    )

    calls = []
    responses = [
        {"result": {"code": "TK1002", "msg": "token expired"}},
        {"result": {"code": "0", "msg": "ok", "data": {"value": 1}}},
    ]

    async def fake_do_call(path, params, include_token=True, token_override=None):
        call_index = len(calls)
        calls.append(
            {
                "path": path,
                "params": dict(params),
                "include_token": include_token,
                "token_override": token_override,
            }
        )
        return responses[call_index]

    monkeypatch.setattr(client, "_do_call", fake_do_call)

    result = await client._call_with_retry("/test", {"foo": "bar"}, include_token=True)

    assert result == responses[1]
    assert len(calls) == 2
    assert calls[0]["token_override"] is None
    assert calls[1]["token_override"] == "refreshed-token"
    assert token_refresher.await_count == 1
