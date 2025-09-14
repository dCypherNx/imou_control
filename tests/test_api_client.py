import pytest


class FakeResponse:
    def __init__(self, data):
        self._data = data
        self.content_length = 1

    async def json(self, content_type=None):
        return self._data

    def raise_for_status(self):  # pragma: no cover - always OK
        pass

    async def __aenter__(self):  # pragma: no cover - simple stub
        return self

    async def __aexit__(self, exc_type, exc, tb):  # pragma: no cover - simple stub
        pass


class DummySession:
    def __init__(self):
        self.tokens = []
        self.calls = 0

    def post(self, url, json):  # pragma: no cover - behaviour tested indirectly
        self.tokens.append(json["params"].get("token"))
        self.calls += 1
        if self.calls == 1:
            data = {"result": {"code": "TK1002", "msg": "bad"}}
        else:
            data = {"result": {"code": "0", "data": {}}}
        return FakeResponse(data)


@pytest.mark.asyncio
async def test_retry_on_token_error(api_module):
    session = DummySession()
    token = "t1"

    async def get_token():
        return token

    async def refresh_token():
        nonlocal token
        token = "t2"
        return token

    api = api_module.ApiClient(
        "id",
        "sec",
        "http://host",
        get_token,
        session,
        refresh_token,
    )
    assert await api.async_set_position("dev", 0.1, 0.2, 0.3)
    assert session.tokens == ["t1", "t2"]


class FailSession:
    def post(self, url, json):  # pragma: no cover - behaviour tested indirectly
        data = {"result": {"code": "123", "msg": "fail"}}
        return FakeResponse(data)


@pytest.mark.asyncio
async def test_failure_raises(api_module):
    api = api_module.ApiClient(
        "id", "sec", "http://host", lambda: "tok", FailSession(), lambda: "tok2"
    )
    with pytest.raises(RuntimeError):
        await api.async_set_position("dev", 0, 0, 0)

