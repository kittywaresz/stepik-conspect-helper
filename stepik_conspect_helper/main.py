import asyncio
import logging
import sys
import webbrowser

import aiohttp

from stepik_conspect_helper import token_exchanger
from stepik_conspect_helper.constants import (
    OAUTH_AUTH_CODE_RESPONSE_TYPE,
    OAUTH_BEARER_TOKEN_TYPE,
    OAUTH_READ_SCOPE,
    STEPIK_AUTHORIZATION_ENDPOINT,
    STEPIK_OATH_REDIRECT_URI,
    STEPIK_OAUTH_APP_CLIENT_ID,
    TOKEN_EXCNHAGE_SERVER_HOST,
    TOKEN_EXCNHAGE_SERVER_PORT,
)


async def fake_main() -> None:
    access_token = await token_exchanger.exchange(
        TOKEN_EXCNHAGE_SERVER_HOST,
        TOKEN_EXCNHAGE_SERVER_PORT,
    )

    if not access_token:
        sys.exit(1)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://stepik.org/api/stepics/1",
            headers={
                "Authorization": f"{OAUTH_BEARER_TOKEN_TYPE} {access_token}",
            },
        ) as response:
            response.raise_for_status()
            data = await response.json()
            current_user_id = data["stepics"][0]["user"]
            print(f"Здарова #{current_user_id}!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)

    webbrowser.open_new(
        (
            f"{STEPIK_AUTHORIZATION_ENDPOINT}/?response_type={OAUTH_AUTH_CODE_RESPONSE_TYPE}"
            f"&client_id={STEPIK_OAUTH_APP_CLIENT_ID}"
            f"&redirect_uri={STEPIK_OATH_REDIRECT_URI}"
            f"&scope={OAUTH_READ_SCOPE}"
        )
    )

    main_coro = fake_main()
    asyncio.run(main_coro)
