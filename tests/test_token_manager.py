import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.helpers import load_imou_module

TokenManager = load_imou_module("token_manager").TokenManager


@pytest.mark.asyncio
async def test_get_token_returns_cached_value(monkeypatch):
    manager = TokenManager(
        app_id="app",
        app_secret="secret",
        base_url="https://example.com",
        session=MagicMock(),
    )

    manager._token = "cached-token"
    manager._exp_ts = time.time() + 60

    fetch_mock = AsyncMock()
    monkeypatch.setattr(manager, "_fetch_new_token", fetch_mock)

    token = await manager.get_token()

    assert token == "cached-token"
    fetch_mock.assert_not_called()


@pytest.mark.asyncio
async def test_get_token_refreshes_when_expired(monkeypatch):
    manager = TokenManager(
        app_id="app",
        app_secret="secret",
        base_url="https://example.com",
        session=MagicMock(),
    )

    manager._token = "old-token"
    manager._exp_ts = time.time() - 1

    new_expiration = time.time() + 120
    fetch_mock = AsyncMock(return_value=("new-token", new_expiration))
    monkeypatch.setattr(manager, "_fetch_new_token", fetch_mock)

    token = await manager.get_token()

    assert token == "new-token"
    assert manager._token == "new-token"
    assert manager._exp_ts == new_expiration
    assert fetch_mock.await_count == 1


@pytest.mark.asyncio
async def test_refresh_token_forces_new_token(monkeypatch):
    manager = TokenManager(
        app_id="app",
        app_secret="secret",
        base_url="https://example.com",
        session=MagicMock(),
    )

    manager._token = "valid-token"
    manager._exp_ts = time.time() + 120

    forced_expiration = time.time() + 300
    fetch_mock = AsyncMock(return_value=("forced-token", forced_expiration))
    monkeypatch.setattr(manager, "_fetch_new_token", fetch_mock)

    token = await manager.refresh_token()

    assert token == "forced-token"
    assert manager._token == "forced-token"
    assert manager._exp_ts == forced_expiration
    assert fetch_mock.await_count == 1
