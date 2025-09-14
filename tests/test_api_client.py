import aiohttp
import pytest


class FakeResponse:
    def __init__(self, data):
        self._data = data
        self.content_length = 1

    async def json(self, content_type=None):
        return self._data

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.mark.asyncio
async def test_retry_on_token_error(monkeypatch, api_module):
    calls = []

    def fake_post(self, url, json, **kwargs):
        calls.append(json["params"].get("token"))
        if len(calls) == 1:
            data = {"result": {"code": "TK1002", "msg": "bad"}}
        else:
            data = {"result": {"code": "0", "data": {}}}
        return FakeResponse(data)

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    token = "t1"

    async def get_token():
        return token

    async def refresh_token():
        nonlocal token
        token = "t2"
        return token

    api = api_module.ApiClient("id", "sec", "http://host", get_token, refresh_token)
    assert await api.set_position("dev", 0.1, 0.2, 0.3)
    assert calls == ["t1", "t2"]


@pytest.mark.asyncio
async def test_failure_raises(monkeypatch, api_module):
    def fake_post(self, url, json, **kwargs):
        data = {"result": {"code": "123", "msg": "fail"}}
        return FakeResponse(data)

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)

    async def get_token():
        return "tok"

    async def refresh_token():
        return "tok2"

    api = api_module.ApiClient("id", "sec", "http://host", get_token, refresh_token)
    with pytest.raises(RuntimeError):
        await api.set_position("dev", 0, 0, 0)
