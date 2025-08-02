from typing import Callable, Generator

import aiohttp
import pytest
import pytest_asyncio
from pytest_mock import MockerFixture

from stepik_conspect_helper.constants import (
    OAUTH_AUTH_CODE_GRANT_TYPE,
    STEPIK_OATH_REDIRECT_URI,
    STEPIK_OAUTH_APP_CLIENT_ID,
    STEPIK_TOKEN_ENDPOINT,
)
from stepik_conspect_helper.stepa import exchange_code_for_token


@pytest_asyncio.fixture
async def client_session(
    mocker: MockerFixture,
):
    session_mock = mocker.AsyncMock(aiohttp.ClientSession)
    yield session_mock


@pytest_asyncio.fixture
async def client_session_with_token(
    client_session,
    mocker: MockerFixture,
):
    def wrapper(expected_token: str) -> aiohttp.ClientSession:
        resp = mocker.AsyncMock()
        resp.json.return_value = {"access_token": expected_token}
        resp_ctx = mocker.AsyncMock()
        resp_ctx.__aenter__.return_value = resp
        client_session.post.return_value = resp_ctx

        return client_session

    yield wrapper


@pytest_asyncio.fixture
async def client_session_with_exc(
    client_session,
    mocker: MockerFixture,
):
    def wrapper(exc: Exception) -> aiohttp.ClientSession:
        resp = mocker.Mock()
        resp.raise_for_status.side_effect = exc
        resp_ctx = mocker.AsyncMock()
        resp_ctx.__aenter__.return_value = resp
        client_session.post.return_value = resp_ctx

        return client_session

    yield wrapper


class TestOauth:
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_ok(
        self,
        client_session_with_token: Callable,
    ) -> None:
        code = "HZGGlezgHpAgaJ4ByaUYrSiymxzwHQ"
        expected_token = "SvbE7kWxHdj5dwlJNlTVCgW8Slsikc"
        client_session = client_session_with_token(expected_token)

        token = await exchange_code_for_token(
            code,
            client_session,
        )

        client_session.post.assert_called_with(
            STEPIK_TOKEN_ENDPOINT,
            data={
                "client_id": STEPIK_OAUTH_APP_CLIENT_ID,
                "code": code,
                "grant_type": OAUTH_AUTH_CODE_GRANT_TYPE,
                "redirect_uri": STEPIK_OATH_REDIRECT_URI,
            },
        )

        assert token == expected_token

    @pytest.mark.asyncio
    async def test_exchange_code_for_token_unexpected_errro(
        self,
        client_session_with_exc: Callable,
    ) -> None:
        code = "HZGGlezgHpAgaJ4ByaUYrSiymxzwHQ"
        expected_exc = Exception
        client_session = client_session_with_exc(expected_exc)

        with pytest.raises(expected_exc):
            _ = await exchange_code_for_token(
                code,
                client_session,
            )
