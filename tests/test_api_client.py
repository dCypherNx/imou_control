import pytest


class DummyResp:
    def __init__(self, data=None):
        self._data = data
        self.content_length = None if data is None else 1

    async def json(self, content_type=None):
        if self._data is None:
            raise ValueError
        return self._data

    def raise_for_status(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class DummySession:
    def __init__(self, responses, calls=None):
        self._responses = responses
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json):
        if self.calls is not None:
            self.calls.append(json["params"].get("token"))
        data = self._responses.pop(0)
        return DummyResp(data)


@pytest.mark.asyncio
async def test_retry_on_token_error(monkeypatch, api_module):
    responses = [
        {"result": {"code": "TK1002", "msg": "bad"}},
        {"result": {"code": "0", "data": {}}},
    ]
    calls = []

    monkeypatch.setattr(
        api_module.aiohttp,
        "ClientSession",
        lambda timeout: DummySession(responses, calls),
    )

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
    responses = [{"result": {"code": "123", "msg": "fail"}}]

    monkeypatch.setattr(
        api_module.aiohttp,
        "ClientSession",
        lambda timeout: DummySession(responses),
    )

    async def get_token():
        return "tok"

    async def refresh_token():
        return "tok2"

    api = api_module.ApiClient("id", "sec", "http://host", get_token, refresh_token)
    with pytest.raises(RuntimeError):
        await api.set_position("dev", 0, 0, 0)


@pytest.mark.asyncio
async def test_empty_body_returns_empty_dict(monkeypatch, api_module):
    responses = [None]

    monkeypatch.setattr(
        api_module.aiohttp,
        "ClientSession",
        lambda timeout: DummySession(responses),
    )

    async def get_token():
        return "tok"

    api = api_module.ApiClient("id", "sec", "http://host", get_token)
    data = await api._do_call("/x", {}, include_token=False)
    assert data == {}

