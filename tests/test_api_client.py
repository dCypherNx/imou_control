import pytest


class DummyResp:
    def __init__(self, data):
        self._data = data
        self.content = b"1"

    def json(self):
        return self._data

    def raise_for_status(self):
        pass


def test_retry_on_token_error(monkeypatch, api_module):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json["params"].get("token"))
        if len(calls) == 1:
            data = {"result": {"code": "TK1002", "msg": "bad"}}
        else:
            data = {"result": {"code": "0", "data": {}}}
        return DummyResp(data)

    monkeypatch.setattr(api_module.requests, "post", fake_post)
    token = "t1"

    def get_token():
        return token

    def refresh_token():
        nonlocal token
        token = "t2"
        return token

    api = api_module.ApiClient("id", "sec", "http://host", get_token, refresh_token)
    assert api.set_position("dev", 0.1, 0.2, 0.3)
    assert calls == ["t1", "t2"]


def test_failure_raises(monkeypatch, api_module):
    def fake_post(url, json, timeout):
        data = {"result": {"code": "123", "msg": "fail"}}
        return DummyResp(data)

    monkeypatch.setattr(api_module.requests, "post", fake_post)
    api = api_module.ApiClient("id", "sec", "http://host", lambda: "tok", lambda: "tok2")
    with pytest.raises(RuntimeError):
        api.set_position("dev", 0, 0, 0)
