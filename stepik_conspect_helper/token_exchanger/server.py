"""Простейшая реализация HTTP/1.1 протокола на сервере

Сервер служит единственной цели - реализовать клиетскую часть OAuth Authorization Code Grant Flow
Если работа выполнена, сервер возвращет access_token и успешно схлопывается
Если работа не выполнена, он все равно схлопывается
"""

import asyncio
import logging
from http import HTTPMethod

import aiohttp

from stepik_conspect_helper.stepa.utils import exchange_code_for_token
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

_stop_server = asyncio.Event()
_server_state = {
    "access_token": "",
}


async def exchange(server_host: str, server_port: int) -> str:
    aserver = await asyncio.start_server(
        handle_client_conn,
        server_host,
        server_port,
    )

    _ = asyncio.create_task(_monitor_server_stop(aserver))

    try:
        logger.info("Server listening on %s:%s", server_host, server_port)
        await aserver.serve_forever()
    except asyncio.CancelledError:
        logger.info("Server stopped")

    return _server_state["access_token"]


# FIXME: надо подумать, действительно ли я хочу поддерживать keep-alive
# если нет, то и цикл тут вообще не нужен
async def handle_client_conn(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> None:
    logger.info("New client connection established")

    should_close_conn = False
    while not should_close_conn:
        should_close_conn = await process_single_request(reader, writer)
        await writer.drain()

    writer.close()
    await writer.wait_closed()

    logger.info("Client connection closed")


# FIXME: надо порефакторить флоу этой функции, а то return True
# выглядит всратенько
async def process_single_request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bool:
    start_line = await extract_request_start_line(reader)

    if start_line.method != HTTPMethod.GET:
        await reply_with_bad_request(writer)
        return True

    match start_line.target:
        case _ if start_line.target.startswith("/auth"):
            await handle_auth_route(writer, start_line)
        case _ if start_line.target.startswith("/success"):
            await handle_success_route(writer, start_line)
        case _ if start_line.target.startswith("/error"):
            await handle_error_route(writer, start_line)
        case _:
            await reply_with_not_found(writer)

    return True


async def handle_auth_route(
    writer: asyncio.StreamWriter,
    start_line: RequestStartLine,
) -> None:
    query_dict = extract_request_query(start_line)

    if "error" in query_dict:
        return await reply_with_redirect(writer, "/error")

    if "code" not in query_dict:
        return await reply_with_bad_request(writer)

    try:
        access_token = await exchange_code_for_token(query_dict["code"])
        logger.debug("Token was exchanged succesfully")
        _server_state["access_token"] = access_token
        await reply_with_redirect(writer, "/success")
    except aiohttp.ClientResponseError:
        logger.debug("Error during token exchange")
        await reply_with_redirect(writer, "/error")


async def handle_success_route(
    writer: asyncio.StreamWriter,
    _: RequestStartLine,
) -> None:
    _stop_server.set()

    await reply_with_ok(
        writer,
        CONTENT_TYPE_HEADER_HTML,
        success_page.PAGE_HTML_IN_UTF_8,
    )


async def handle_error_route(
    writer: asyncio.StreamWriter,
    _: RequestStartLine,
) -> None:
    _stop_server.set()

    await reply_with_ok(
        writer,
        CONTENT_TYPE_HEADER_HTML,
        error_page.PAGE_HTML_IN_UTF_8,
    )


async def _monitor_server_stop(server: asyncio.Server) -> None:
    await _stop_server.wait()

    server.close()
    await server.wait_closed()
