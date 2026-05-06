import uuid
from types import SimpleNamespace


USER_ID = uuid.UUID("31313131-3131-3131-3131-313131313131")
SECOND_USER_ID = uuid.UUID("32323232-3232-3232-3232-323232323232")
THEME_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
SECOND_THEME_ID = uuid.UUID("34343434-3434-3434-3434-343434343434")
MATERIAL_ID = uuid.UUID("35353535-3535-3535-3535-353535353535")
SECOND_MATERIAL_ID = uuid.UUID("36363636-3636-3636-3636-363636363636")
CARD_ID = uuid.UUID("37373737-3737-3737-3737-373737373737")
SECOND_CARD_ID = uuid.UUID("38383838-3838-3838-3838-383838383838")
PROGRESS_ID = uuid.UUID("39393939-3939-3939-3939-393939393939")
DAILY_TASK_ID = uuid.UUID("40404040-4040-4040-4040-404040404040")
ONTOLOGY_ID = uuid.UUID("41414141-4141-4141-4141-414141414141")


def build_complete_material_payload(material_id=MATERIAL_ID):
    return {"education_material_id": str(material_id)}


def build_complete_theme_payload(theme_id=THEME_ID):
    return {"education_theme_id": str(theme_id)}


def build_card_response(card_id=CARD_ID, text="Card text", number=1, link_to_picture=None):
    return {
        "id": str(card_id),
        "text": text,
        "number": number,
        "link_to_picture": link_to_picture,
    }


def build_material_response(
    material_id=MATERIAL_ID,
    material_type=0,
    number=1,
    title="Material title",
    link_to_picture="/images/material.png",
    subtitle="Material subtitle",
    cards=None,
):
    return {
        "id": str(material_id),
        "type": material_type,
        "number": number,
        "title": title,
        "link_to_picture": link_to_picture,
        "subtitle": subtitle,
        "cards": cards if cards is not None else [build_card_response()],
    }


def build_recommendation_response(
    theme_id=SECOND_THEME_ID,
    theme="Second theme",
    link="/education/second",
    link_to_picture="/images/second.png",
    tags=None,
):
    return {
        "id": str(theme_id),
        "theme": theme,
        "link": link,
        "link_to_picture": link_to_picture,
        "tags": tags if tags is not None else ["tag-2"],
    }


def build_theme_response(
    theme_id=THEME_ID,
    theme="Theme title",
    link="/education/theme",
    link_to_picture="/images/theme.png",
    tags=None,
    education_materials=None,
):
    return {
        "id": str(theme_id),
        "theme": theme,
        "link": link,
        "link_to_picture": link_to_picture,
        "tags": tags if tags is not None else ["tag-1"],
        "education_materials": education_materials if education_materials is not None else [build_material_response()],
    }


def build_theme_with_materials_response(
    theme_id=THEME_ID,
    theme="Theme title",
    link="/education/theme",
    link_to_picture="/images/theme.png",
    recommendations=None,
    education_materials=None,
):
    return {
        "id": str(theme_id),
        "theme": theme,
        "link": link,
        "link_to_picture": link_to_picture,
        "recommendations": recommendations if recommendations is not None else [build_recommendation_response()],
        "education_materials": education_materials if education_materials is not None else [build_material_response()],
    }


def build_progress_response(progress_id=PROGRESS_ID, user_id=USER_ID, material_id=MATERIAL_ID):
    return {
        "id": str(progress_id),
        "user_id": str(user_id),
        "education_material_id": str(material_id),
    }


def build_user_progress_response(user_id=USER_ID, material_id=MATERIAL_ID):
    return {
        "user_id": str(user_id),
        "education_material_id": str(material_id),
    }


def make_card(card_id=CARD_ID, text="Card text", number=1, link_to_picture=None):
    return SimpleNamespace(
        id=card_id,
        text=text,
        number=number,
        link_to_picture=link_to_picture,
    )


def make_material(
    material_id=MATERIAL_ID,
    material_type=0,
    number=1,
    title="Material title",
    link_to_picture="/images/material.png",
    subtitle="Material subtitle",
    cards=None,
    education_theme_id=THEME_ID,
):
    return SimpleNamespace(
        id=material_id,
        type=material_type,
        number=number,
        title=title,
        link_to_picture=link_to_picture,
        subtitle=subtitle,
        cards=cards if cards is not None else [make_card()],
        education_theme_id=education_theme_id,
    )


def make_theme(
    theme_id=THEME_ID,
    theme="Theme title",
    link="/education/theme",
    link_to_picture="/images/theme.png",
    tags=None,
    related_topics=None,
    education_materials=None,
):
    return SimpleNamespace(
        id=theme_id,
        theme=theme,
        link=link,
        link_to_picture=link_to_picture,
        tags=tags if tags is not None else ["tag-1"],
        related_topics=related_topics if related_topics is not None else [str(SECOND_THEME_ID)],
        education_materials=education_materials if education_materials is not None else [make_material()],
    )


def make_progress(progress_id=PROGRESS_ID, user_id=USER_ID, material_id=MATERIAL_ID):
    return SimpleNamespace(
        id=progress_id,
        user_id=user_id,
        education_material_id=material_id,
    )


def make_ontology_entry(user_id=USER_ID, destination_id=THEME_ID):
    return SimpleNamespace(
        id=ONTOLOGY_ID,
        user_id=user_id,
        destination_id=destination_id,
    )


def sample_themes_fixture():
    return [
        {
            "id": str(THEME_ID),
            "theme": "Theme title",
            "link": "/education/theme",
            "link_to_picture": "/images/theme.png",
            "tags": ["tag-1"],
            "related_topics": [str(SECOND_THEME_ID)],
        },
        {
            "id": str(SECOND_THEME_ID),
            "theme": "Second theme",
            "link": "/education/second",
            "link_to_picture": "/images/second.png",
            "tags": ["tag-2"],
            "related_topics": [],
        },
    ]


def sample_materials_fixture():
    return [
        {
            "id": str(MATERIAL_ID),
            "type": 0,
            "number": 1,
            "title": "Material title",
            "link_to_picture": "/images/material.png",
            "education_theme_id": str(THEME_ID),
            "subtitle": "Material subtitle",
        },
        {
            "id": str(SECOND_MATERIAL_ID),
            "type": 0,
            "number": 2,
            "title": "Second material",
            "link_to_picture": "/images/material-2.png",
            "education_theme_id": str(SECOND_THEME_ID),
            "subtitle": "Second subtitle",
        },
    ]


def sample_cards_fixture():
    return [
        {
            "id": str(CARD_ID),
            "text": "Card text",
            "number": 1,
            "link_to_picture": None,
            "education_material_id": str(MATERIAL_ID),
        },
        {
            "id": str(SECOND_CARD_ID),
            "text": "Second card",
            "number": 2,
            "link_to_picture": "/images/card-2.png",
            "education_material_id": str(MATERIAL_ID),
        },
    ]
