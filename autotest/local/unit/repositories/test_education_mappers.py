import inspect
import uuid

from src.models.education import CardOrm, educationMaterialOrm, educationThemeOrm
from src.repositories.mappers.mappers import EducationThemeDataMapper
from src.schemas.education_material import EducationThemeResponse


def test_education_theme_mapper_returns_response_without_lazy_loading_materials():
    theme = educationThemeOrm(
        id=uuid.uuid4(),
        theme="Theme title",
        link="theme-link",
        link_to_picture="/images/theme.png",
        tags=["stress"],
        related_topics=[],
    )

    result = EducationThemeDataMapper.map_to_domain_entity(theme)

    assert not inspect.iscoroutine(result)
    assert isinstance(result, EducationThemeResponse)
    assert result.theme == "Theme title"
    assert result.link_to_picture == "/images/theme.png"
    assert result.tags == ["stress"]
    assert result.education_materials == []


def test_education_theme_mapper_sorts_materials_and_cards_by_number():
    first_material = educationMaterialOrm(
        id=uuid.uuid4(),
        type=1,
        number=1,
        title="First material",
        link_to_picture=None,
        subtitle=None,
    )
    first_material.cards = [
        CardOrm(id=uuid.uuid4(), text="Second card", number=2, link_to_picture=None),
        CardOrm(id=uuid.uuid4(), text="First card", number=1, link_to_picture=None),
    ]

    second_material = educationMaterialOrm(
        id=uuid.uuid4(),
        type=1,
        number=2,
        title="Second material",
        link_to_picture=None,
        subtitle=None,
    )

    theme = educationThemeOrm(
        id=uuid.uuid4(),
        theme="Theme title",
        link="theme-link",
        link_to_picture="/images/theme.png",
        tags=["stress"],
        related_topics=[],
    )
    theme.education_materials = [second_material, first_material]

    result = EducationThemeDataMapper.map_to_domain_entity(theme)

    assert [material.number for material in result.education_materials] == [1, 2]
    assert [card.number for card in result.education_materials[0].cards] == [1, 2]
