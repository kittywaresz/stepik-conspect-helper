import pytest

from stepik_conspect_helper.stepa_api.client import StepaApiClient


class TestClient:
    @pytest.mark.asyncio
    async def test_client_no_session(self):
        client = StepaApiClient("fake")

        with pytest.raises(ValueError):
            await client.get_course(54403)

        with pytest.raises(ValueError):
            await client.get_courses([54403])

    @pytest.mark.asyncio
    async def test_get_course(self):
        async with StepaApiClient("fake") as client:
            course = await client.get_course(1)

            assert course.id == 1
            assert course.slug == "Epic-Guide-to-Stepik-1"

    @pytest.mark.asyncio
    async def test_get_courses(self):
        async with StepaApiClient("fake") as client:
            courses = await client.get_courses([1])

            assert len(courses) == 1
            assert courses[0].id == 1
            assert courses[0].slug == "Epic-Guide-to-Stepik-1"

    @pytest.mark.asyncio
    async def test_get_section(self):
        async with StepaApiClient("fake") as client:
            section = await client.get_section(1)

            assert section.id == 1
            assert section.slug == "Basics-1"

    @pytest.mark.asyncio
    async def test_get_sections(self):
        async with StepaApiClient("fake") as client:
            sections = await client.get_sections([1])

            assert len(sections) == 1
            assert sections[0].id == 1
            assert sections[0].slug == "Basics-1"
