import aiohttp

from stepik_conspect_helper.constants import (
    OAUTH_AUTH_CODE_GRANT_TYPE,
    STEPIK_OATH_REDIRECT_URI,
    STEPIK_OAUTH_APP_CLIENT_ID,
    STEPIK_TOKEN_ENDPOINT,
)


async def exchange_code_for_token(
    authorization_code: str,
) -> str:
    """Пытается обменить authorization_code на acces_token

    Если что-то пошло не так, просто рейзит aiohttp эксепшен :)

    Args:
        authorization_code (str): authorization_code

    Returns:
        str: acces_token
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(
            STEPIK_TOKEN_ENDPOINT,
            data={
                "grant_type": OAUTH_AUTH_CODE_GRANT_TYPE,
                "code": authorization_code,
                "redirect_uri": STEPIK_OATH_REDIRECT_URI,
                "client_id": STEPIK_OAUTH_APP_CLIENT_ID,
            },
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["access_token"]
