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

    def raise_for_status(self):  # pragma: no cover - always OK
        pass

    async def __aenter__(self):  # pragma: no cover - simple stub
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - simple stub
        pass


class DummySession:
    def __init__(self, tokens):
        self._tokens = list(tokens)
        self.calls = 0

    def post(self, url, json):  # pragma: no cover - behaviour tested indirectly
        token = self._tokens.pop(0)
        self.calls += 1
        return FakeResponse(token)


@pytest.mark.asyncio
async def test_get_token_caches(token_module):
    session = DummySession(["abc"])
    tm = token_module.TokenManager("id", "secret", "http://host", session)
    t1 = await tm.async_get_token()
    t2 = await tm.async_get_token()
    assert t1 == t2 == "abc"
    assert session.calls == 1


@pytest.mark.asyncio
async def test_refresh_and_invalidate(token_module):
    session = DummySession(["first", "second", "third"])
    tm = token_module.TokenManager("id", "secret", "http://host", session)
    assert await tm.async_get_token() == "first"
    assert await tm.async_refresh_token() == "second"
    tm.invalidate()
    assert await tm.async_get_token() == "third"
    assert session._tokens == []

