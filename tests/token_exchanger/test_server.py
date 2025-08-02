import asyncio
from http import HTTPStatus

import aiohttp
import pytest
import pytest_asyncio
from pytest_mock import MockerFixture

from stepik_conspect_helper.token_exchanger.server import TokenExchangeServer


@pytest_asyncio.fixture
async def exchange_server(unused_tcp_port: int):
    host, port = "127.0.0.1", unused_tcp_port

    server = TokenExchangeServer(host, port)
    server_task = asyncio.create_task(server.listen())

    await asyncio.sleep(0.1)

    try:
        yield server
    finally:
        server_task.cancel()


@pytest_asyncio.fixture
async def client_session():
    async with aiohttp.ClientSession() as session:
        yield session

    pass


class TestServer:
    @pytest.mark.asyncio
    async def test_exchange_token_accepted(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
        mocker: MockerFixture,
    ):
        expected_token = "SvbE7kWxHdj5dwlJNlTVCgW8Slsikc"
        stepik_mock = mocker.patch(
            "stepik_conspect_helper.token_exchanger.server.exchange_code_for_token"
        )
        stepik_mock.return_value = expected_token
        host, port = exchange_server.host, exchange_server.port

        async with client_session.get(
            f"http://{host}:{port}/auth",
            params={
                "code": "HZGGlezgHpAgaJ4ByaUYrSiymxzwHQ",
            },
        ) as response:
            assert response.content_type == "text/html"
            assert "Успешная авторизация" in await response.text()

        assert exchange_server.access_token == expected_token

    @pytest.mark.asyncio
    async def test_exchange_token_declined(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
    ):
        host, port = exchange_server.host, exchange_server.port

        async with client_session.get(
            f"http://{host}:{port}/auth",
            params={
                "error": "access_denied",
            },
        ) as response:
            assert response.content_type == "text/html"
            assert "Проблемы с авторизацией" in await response.text()

        assert exchange_server.access_token == ""

    @pytest.mark.asyncio
    async def test_exchange_token_bad_request(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
    ):
        host, port = exchange_server.host, exchange_server.port

        async with client_session.patch(f"http://{host}:{port}/something") as response:
            assert response.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_exchange_token_not_found(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
    ):
        host, port = exchange_server.host, exchange_server.port

        async with client_session.get(f"http://{host}:{port}/something") as response:
            assert response.status == HTTPStatus.NOT_FOUND

    @pytest.mark.asyncio
    async def test_exchange_token_invalid_auth_params(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
    ):
        host, port = exchange_server.host, exchange_server.port

        async with client_session.get(
            f"http://{host}:{port}/auth",
            params={
                "unexpected": "one",
            },
        ) as response:
            assert response.status == HTTPStatus.BAD_REQUEST

    @pytest.mark.asyncio
    async def test_exchange_token_stepa_exchange_error(
        self,
        exchange_server: TokenExchangeServer,
        client_session: aiohttp.ClientSession,
        mocker: MockerFixture,
    ):
        stepik_mock = mocker.patch(
            "stepik_conspect_helper.token_exchanger.server.exchange_code_for_token"
        )
        stepik_mock.side_effect = aiohttp.ConnectionTimeoutError
        host, port = exchange_server.host, exchange_server.port

        async with client_session.get(
            f"http://{host}:{port}/auth",
            params={
                "code": "HZGGlezgHpAgaJ4ByaUYrSiymxzwHQ",
            },
        ) as response:
            assert response.content_type == "text/html"
            assert "Проблемы с авторизацией" in await response.text()
