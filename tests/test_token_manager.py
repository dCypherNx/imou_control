import pytest


class DummyResp:
    def __init__(self, token: str):
        self._token = token
        self.content = b"1"

    def json(self):
        return {
            "result": {
                "code": "0",
                "data": {"accessToken": self._token, "expireTime": 60},
            }
        }

    def raise_for_status(self):
        pass


def test_get_token_caches(monkeypatch, token_module):
    calls = []

    def fake_post(url, json, timeout):
        calls.append(1)
        return DummyResp("abc")

    monkeypatch.setattr(token_module.requests, "post", fake_post)
    tm = token_module.TokenManager("id", "secret", "http://host")
    t1 = tm.get_token()
    t2 = tm.get_token()
    assert t1 == t2 == "abc"
    assert len(calls) == 1


def test_refresh_and_invalidate(monkeypatch, token_module):
    tokens = ["first", "second", "third"]

    def fake_post(url, json, timeout):
        return DummyResp(tokens.pop(0))

    monkeypatch.setattr(token_module.requests, "post", fake_post)
    tm = token_module.TokenManager("id", "secret", "http://host")
    assert tm.get_token() == "first"
    assert tm.refresh_token() == "second"
    tm.invalidate()
    assert tm.get_token() == "third"
    assert tokens == []
