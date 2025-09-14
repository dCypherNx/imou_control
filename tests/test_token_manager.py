import pytest


class DummyResp:
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
        return False


class DummySession:
    def __init__(self, tokens, calls=None):
        self._tokens = tokens
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json):
        token = self._tokens.pop(0)
        if self.calls is not None:
            self.calls.append(1)
        return DummyResp(token)


@pytest.mark.asyncio
async def test_get_token_caches(monkeypatch, token_module):
    calls = []
    monkeypatch.setattr(
        token_module.aiohttp,
        "ClientSession",
        lambda timeout: DummySession(["abc"], calls),
    )

    tm = token_module.TokenManager("id", "secret", "http://host")
    t1 = await tm.get_token()
    t2 = await tm.get_token()
    assert t1 == t2 == "abc"
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_refresh_and_invalidate(monkeypatch, token_module):
    tokens = ["first", "second", "third"]

    monkeypatch.setattr(
        token_module.aiohttp,
        "ClientSession",
        lambda timeout: DummySession(tokens),
    )

    tm = token_module.TokenManager("id", "secret", "http://host")
    assert await tm.get_token() == "first"
    assert await tm.refresh_token() == "second"
    tm.invalidate()
    assert await tm.get_token() == "third"
