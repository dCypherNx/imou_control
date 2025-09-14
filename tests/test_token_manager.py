import aiohttp
import pytest


class FakeResponse:
    def __init__(self, token: str):
        self._token = token
        self.content_length = 1

    async def json(self, content_type=None):
        return {
            "result": {
                "code": "0",
                "data": {"accessToken": self._token, "expireTime": 60},
            }
        }

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.mark.asyncio
async def test_get_token_caches(monkeypatch, token_module):
    calls = []

    def fake_post(self, url, json, **kwargs):
        calls.append(1)
        return FakeResponse("abc")

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    tm = token_module.TokenManager("id", "secret", "http://host")
    t1 = await tm.get_token()
    t2 = await tm.get_token()
    assert t1 == t2 == "abc"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_refresh_and_invalidate(monkeypatch, token_module):
    tokens = ["first", "second", "third"]

    def fake_post(self, url, json, **kwargs):
        return FakeResponse(tokens.pop(0))

    monkeypatch.setattr(aiohttp.ClientSession, "post", fake_post)
    tm = token_module.TokenManager("id", "secret", "http://host")
    assert await tm.get_token() == "first"
    assert await tm.refresh_token() == "second"
    tm.invalidate()
    assert await tm.get_token() == "third"
    assert tokens == []
