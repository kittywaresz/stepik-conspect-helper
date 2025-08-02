import asyncio
import logging
import webbrowser

from stepik_conspect_helper.constants import (
    OAUTH_AUTH_CODE_RESPONSE_TYPE,
    OAUTH_READ_SCOPE,
    STEPIK_AUTHORIZATION_ENDPOINT,
    STEPIK_OATH_REDIRECT_URI,
    STEPIK_OAUTH_APP_CLIENT_ID,
    TOKEN_EXCHANGE_SERVER_HOST,
    TOKEN_EXCHANGE_SERVER_PORT,
)
from stepik_conspect_helper.stepa_api.client import StepaApiClient
from stepik_conspect_helper.token_exchanger import TokenExchangeServer


async def fake_main() -> None:
    server = TokenExchangeServer(
        TOKEN_EXCHANGE_SERVER_HOST,
        TOKEN_EXCHANGE_SERVER_PORT,
    )
    asyncio.create_task(server.listen())

    while not server.access_token:
        await asyncio.sleep(0.5)

    async with StepaApiClient(server.access_token) as client:
        course = await client.get_course(1)
        print(f"{course.slug}:")

        sections = await client.get_sections(course.sections)

        for section in sections:
            print(f"\t{section.slug}")


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
