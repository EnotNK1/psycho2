import inspect
import uuid

from src.models.education import educationThemeOrm
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
