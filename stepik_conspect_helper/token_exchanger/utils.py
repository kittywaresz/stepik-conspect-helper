import asyncio
from http import HTTPMethod, HTTPStatus
from typing import NamedTuple

from .constants import (
    CONNECTION_HEADER,
    CONNECTION_HEADER_CLOSE,
    CONTENT_LENGTH_HEADER,
    CONTENT_TYPE_HEADER,
    HTTP_LINE_TERMINATOR,
    HTTP_VERSION,
    LOCATION_HEADER,
    PATH_QUERY_SEPARATOR,
    QUERY_ELEMENT_KEY_VALUE_SEPARATOR,
    QUERY_ELEMENTS_SEPARATOR,
)


class RequestStartLine(NamedTuple):
    method: HTTPMethod
    target: str
    protocol: str


async def reply_with_bad_request(
    writer: asyncio.StreamWriter,
) -> None:
    """Отправляет 400 и указание закрыть соединение

    Args:
        writer (asyncio.StreamWriter): буфер данных клиентского сокета на запись
    """

    _add_response_start_line(writer, HTTPStatus.BAD_REQUEST)

    _add_response_header(writer, CONNECTION_HEADER, CONNECTION_HEADER_CLOSE)
    writer.write(HTTP_LINE_TERMINATOR)


async def reply_with_not_found(
    writer: asyncio.StreamWriter,
) -> None:
    """Отправляет 404 и указание закрыть соединение

    Args:
        writer (asyncio.StreamWriter): буфер данных клиентского сокета на запись
    """

    _add_response_start_line(writer, HTTPStatus.NOT_FOUND)

    _add_response_header(writer, CONNECTION_HEADER, CONNECTION_HEADER_CLOSE)
    writer.write(HTTP_LINE_TERMINATOR)


async def reply_with_ok(
    writer: asyncio.StreamWriter,
    content_type: str,
    data: bytes,
) -> None:
    """Отправляет 200 и тело ответного сообщения

    В теле можно передать только JSON строку

    Args:
        writer (asyncio.StreamWriter): буфер данных клиентского сокета на запись
        data (bytes): данные для отправки клиенту
    """

    _add_response_start_line(writer, HTTPStatus.OK)

    _add_response_header(writer, CONNECTION_HEADER, CONNECTION_HEADER_CLOSE)
    _add_response_header(writer, CONTENT_LENGTH_HEADER, str(len(data)))
    _add_response_header(writer, CONTENT_TYPE_HEADER, content_type)
    writer.write(HTTP_LINE_TERMINATOR)

    writer.write(data)


async def reply_with_redirect(
    writer: asyncio.StreamWriter,
    target: str,
) -> None:
    """Отправляет 302 и новый адрес

    Args:
        writer (asyncio.StreamWriter): буфер данных клиентского сокета на запись
        data (bytes): данные для отправки клиенту
    """

    _add_response_start_line(writer, HTTPStatus.FOUND)

    _add_response_header(writer, CONNECTION_HEADER, CONNECTION_HEADER_CLOSE)
    _add_response_header(writer, LOCATION_HEADER, target)
    writer.write(HTTP_LINE_TERMINATOR)


async def extract_request_start_line(
    reader: asyncio.StreamReader,
) -> RequestStartLine:
    """Парсит heading line запроса

    Args:
        reader (asyncio.StreamReader): буфер данных клиентского сокета на чтение

    Returns:
        RequestStartLine: кортеж значений heading line
    """

    raw_start_line = await reader.readuntil(HTTP_LINE_TERMINATOR)
    method, target, protocol = raw_start_line.rstrip(HTTP_LINE_TERMINATOR).split(b" ")

    return RequestStartLine(
        HTTPMethod(method.decode()),
        target.decode(),
        protocol.decode(),
    )


async def extract_request_headers(
    reader: asyncio.StreamReader,
) -> dict[str, str]:
    """Парсит хедеры из запроса

    Ключи хедеров приводятся к нижнему кейсу, значения хедерова парсятся as is

    Args:
        start_line (RequestStartLine): heading line запрсоа

    Returns:
        dict[str, str]: словарь хедерова
    """

    headers = {}

    while header_line := await reader.readuntil(HTTP_LINE_TERMINATOR):
        if header_line == HTTP_LINE_TERMINATOR:
            break
        head, tail = header_line.rstrip(HTTP_LINE_TERMINATOR).split(b": ")
        headers[head.decode().lower()] = tail.decode()

    return headers


def extract_request_query(
    start_line: RequestStartLine,
) -> dict[str, str]:
    """Парсит query params из строки запроса в словарь

    Ключи вида val[] тупо игнорируются

    Args:
        start_line (RequestStartLine): heading line запрсоа

    Returns:
        dict[str, str]: словарь query params
    """

    _, query_line = start_line.target.split(PATH_QUERY_SEPARATOR)
    query_elements = query_line.split(QUERY_ELEMENTS_SEPARATOR)

    query_dict = {}
    for elem in query_elements:
        key, value = elem.split(QUERY_ELEMENT_KEY_VALUE_SEPARATOR)

        if key.endswith("[]"):
            continue

        query_dict[key] = value

    return query_dict


def _add_response_start_line(
    writer: asyncio.StreamWriter,
    status_code: HTTPStatus,
    http_version: str = HTTP_VERSION,
) -> None:
    start_line = f"{http_version} {status_code} {status_code.phrase}"
    writer.write(start_line.encode() + HTTP_LINE_TERMINATOR)


def _add_response_header(
    writer: asyncio.StreamWriter,
    key: str,
    value: str,
) -> None:
    writer.write(f"{key}: {value}".encode() + HTTP_LINE_TERMINATOR)
