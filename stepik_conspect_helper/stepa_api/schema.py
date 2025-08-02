from stepik_conspect_helper.stepa_api.constants import (
    COURSES_PATH,
    SECTIONS_PATH,
)


class ApiEntity:
    _url_path: str
    _data_path: str


class Course(ApiEntity):
    _url_path: str = COURSES_PATH
    _data_path: str = COURSES_PATH

    def __init__(
        self,
        id: int,
        slug: str,
        title: str,
        first_lesson: int,
        first_unit: int,
        sections: list[int],
        *_args,
        **_kwargs,
    ) -> None:
        self.id = id
        self.slug = slug
        self.title = title
        self.first_lesson = first_lesson
        self.first_unit = first_unit
        self.sections = sections


class Section(ApiEntity):
    _url_path: str = SECTIONS_PATH
    _data_path: str = SECTIONS_PATH

    id: int
    position: int
    slug: str
    title: str
    description: str
    units: list[int]

    def __init__(
        self,
        id: int,
        position: int,
        slug: str,
        title: str,
        description: str,
        units: list[int],
        *_args,
        **_kwargs,
    ) -> None:
        self.id = id
        self.position = position
        self.slug = slug
        self.title = title
        self.description = description
        self.units = units
