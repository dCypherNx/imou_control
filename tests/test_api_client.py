import pytest


class DummyResp:
    def __init__(self, data):
        self._data = data
        self.content_length = 1

    async def json(self, content_type=None):  # pragma: no cover - simple stub
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
        return DummyResp(data)


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
        "id", "sec", "http://host", get_token, refresh_token, session=session
    )
    assert await api.set_position("dev", 0.1, 0.2, 0.3)
    assert session.tokens == ["t1", "t2"]


@pytest.mark.asyncio
async def test_failure_raises(api_module):
    class FailSession:
        def post(self, url, json):
            data = {"result": {"code": "123", "msg": "fail"}}
            return DummyResp(data)

    async def get_token():
        return "tok"

    async def refresh_token():
        return "tok2"

    api = api_module.ApiClient(
        "id", "sec", "http://host", get_token, refresh_token, session=FailSession()
    )
    with pytest.raises(RuntimeError):
        await api.set_position("dev", 0, 0, 0)
