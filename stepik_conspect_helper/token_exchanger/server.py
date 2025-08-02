"""Простейшая реализация HTTP/1.1 протокола на сервере

Сервер служит единственной цели - реализовать клиетскую часть OAuth Authorization Code Grant Flow
Если работа выполнена, сервер возвращет access_token и успешно схлопывается
Если работа не выполнена, он все равно схлопывается
"""

import asyncio
import logging
from http import HTTPMethod

import aiohttp

from stepik_conspect_helper.stepa import exchange_code_for_token
from stepik_conspect_helper.token_exchanger.constants import CONTENT_TYPE_HEADER_HTML
from stepik_conspect_helper.token_exchanger.templates import error_page, success_page
from stepik_conspect_helper.token_exchanger.utils import (
    RequestStartLine,
    extract_request_query,
    extract_request_start_line,
    reply_with_bad_request,
    reply_with_not_found,
    reply_with_ok,
    reply_with_redirect,
)

logger = logging.getLogger(__name__)


class TokenExchangeServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.access_token = ""

    async def listen(
        self,
    ) -> None:
        aserver = await asyncio.start_server(
            self.handle_client_conn,
            self.host,
            self.port,
        )

        logger.info("Server listening on %s:%s", self.host, self.port)

        try:
            await aserver.serve_forever()
        except asyncio.CancelledError:
            aserver.close()
            await aserver.wait_closed()

    # FIXME: надо подумать, действительно ли я хочу поддерживать keep-alive
    # если нет, то и цикл тут вообще не нужен
    async def handle_client_conn(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        logger.info("New client connection established")

        should_close_conn = False
        while not should_close_conn:
            should_close_conn = await self.process_single_request(reader, writer)
            await writer.drain()

        writer.close()
        await writer.wait_closed()

        logger.info("Client connection closed")

    # FIXME: надо порефакторить флоу этой функции, а то return True
    # выглядит всратенько
    async def process_single_request(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> bool:
        start_line = await extract_request_start_line(reader)

        if start_line.method != HTTPMethod.GET:
            await reply_with_bad_request(writer)
            return True

        match start_line.target:
            case _ if start_line.target.startswith("/auth"):
                await self.handle_auth_route(writer, start_line)
            case _ if start_line.target.startswith("/success"):
                await self.handle_success_route(writer, start_line)
            case _ if start_line.target.startswith("/error"):
                await self.handle_error_route(writer, start_line)
            case _:
                await reply_with_not_found(writer)

        return True

    async def handle_auth_route(
        self,
        writer: asyncio.StreamWriter,
        start_line: RequestStartLine,
    ) -> None:
        query_dict = extract_request_query(start_line)

        if "error" in query_dict:
            return await reply_with_redirect(writer, "/error")

        if "code" not in query_dict:
            return await reply_with_bad_request(writer)

        async with aiohttp.ClientSession() as client_session:
            try:
                access_token = await exchange_code_for_token(
                    query_dict["code"],
                    client_session,
                )

                logger.debug("Token was exchanged succesfully")
                self.access_token = access_token

                await reply_with_redirect(writer, "/success")
            except aiohttp.ClientError as exc:
                logger.error("Error during token exchange: %s", exc)
                await reply_with_redirect(writer, "/error")

    async def handle_success_route(
        self,
        writer: asyncio.StreamWriter,
        _: RequestStartLine,
    ) -> None:
        await reply_with_ok(
            writer,
            CONTENT_TYPE_HEADER_HTML,
            success_page.PAGE_HTML_IN_UTF_8,
        )

    async def handle_error_route(
        self,
        writer: asyncio.StreamWriter,
        _: RequestStartLine,
    ) -> None:
        await reply_with_ok(
            writer,
            CONTENT_TYPE_HEADER_HTML,
            error_page.PAGE_HTML_IN_UTF_8,
        )
