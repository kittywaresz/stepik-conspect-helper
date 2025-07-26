import asyncio
from http import HTTPMethod

import pytest

from stepik_conspect_helper.token_exchanger.utils import (
    RequestStartLine,
    extract_request_headers,
    extract_request_query,
)


class TestUtils:
    @pytest.mark.asyncio
    async def test_extract_request_headers(self):
        reader = asyncio.StreamReader()
        reader.feed_data(b"Host: example.com\r\nContent-Type: text/html\r\n\r\n")

        headers = await extract_request_headers(reader)

        assert "host" in headers
        assert headers["host"] == "example.com"
        assert "content-type" in headers
        assert headers["content-type"] == "text/html"

    def test_extract_request_query(self):
        start_line = RequestStartLine(
            method=HTTPMethod.GET,
            target="/jopa?sobaka=123&sdfss=www&arr[]=xxx&arr[]=www",
            protocol="HTTP/1.1",
        )

        query_params = extract_request_query(start_line)

        assert "sobaka" in query_params
        assert query_params["sobaka"] == "123"
        assert "sdfss" in query_params
        assert query_params["sdfss"] == "www"
        assert "arr" not in query_params
