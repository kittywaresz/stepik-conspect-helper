from typing import TypeVar

import aiohttp

from stepik_conspect_helper.stepa_api.constants import STEPIK_API_BASE_PATH
from stepik_conspect_helper.stepa_api.schema import (
    ApiEntity,
    Course,
    Section,
)

API_ENTITY = TypeVar("API_ENTITY", bound=ApiEntity)


class StepaApiClient:
    def __init__(self, bearer_token: str) -> None:
        self.bearer_token = bearer_token
        self.client_session = None

    async def get_course(self, course_id: int) -> Course:
        return await self._get_one_entity(course_id, Course)

    async def get_courses(self, courses_ids: list[int]) -> list[Course]:
        return await self._get_entities_list(courses_ids, Course)

    async def get_section(self, section_id: int) -> Section:
        return await self._get_one_entity(section_id, Section)

    async def get_sections(self, sections_ids: list[int]) -> list[Section]:
        return await self._get_entities_list(sections_ids, Section)

    async def _get_one_entity(
        self,
        entity_id: int,
        entity: type[API_ENTITY],
    ) -> API_ENTITY:
        if not self.client_session:
            raise ValueError("No client session")

        async with self.client_session.get(
            f"{entity._url_path}/{entity_id}",
        ) as response:
            data = await response.json()
            entity_fields = data[entity._data_path][0]

            return entity(**entity_fields)

    async def _get_entities_list(
        self,
        entities_ids: list[int],
        entity: type[API_ENTITY],
    ) -> list[API_ENTITY]:
        if not self.client_session:
            raise ValueError("No client session")

        async with self.client_session.get(
            entity._url_path,
            params={
                "ids[]": entities_ids,
            },
        ) as response:
            data = await response.json()

            entities = []
            for entity_fields in data[entity._data_path]:
                entities.append(entity(**entity_fields))

            return entities

    async def __aenter__(self):
        self.client_session = aiohttp.ClientSession(
            f"{STEPIK_API_BASE_PATH}/",
            headers={
                "authorization": f"Bearer {self.bearer_token}",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb) -> None:
        if not self.client_session:
            return

        await self.client_session.close()
