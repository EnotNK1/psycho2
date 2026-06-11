import uuid
from types import SimpleNamespace

import pytest

import src.services.education as education_service_module
from autotest.factories.education import (
    CARD_ID,
    MATERIAL_ID,
    SECOND_THEME_ID,
    THEME_ID,
    USER_ID,
    build_card_create_payload,
    build_material_create_payload,
    build_theme_create_payload,
    make_card,
    make_material,
    make_ontology_entry,
    make_progress,
    make_theme,
    sample_cards_fixture,
    sample_materials_fixture,
    sample_themes_fixture,
)
from src.exceptions import MyAppException, ObjectAlreadyExistsException, ObjectNotFoundException
from src.services.education import EducationService
from src.services.fixtures.education import EDUCATION


class FakeEducationThemeRepository:
    def __init__(self):
        self.add_calls = []
        self.get_one_or_none_map = {}
        self.get_all_result = []
        self.get_with_materials_result = None
        self.get_orm_one_or_none_map = {}
        self.raise_on_get_all = None
        self.last_edit = None
        self.delete_calls = []
        self.flush_count = 0

    async def get_one_or_none(self, **filter_by):
        return self.get_one_or_none_map.get(filter_by.get("id"))

    async def add(self, data):
        self.add_calls.append(data)
        return data

    async def get_one(self, **filter_by):
        item = self.get_one_or_none_map.get(filter_by.get("id"))
        if item is None:
            raise ObjectNotFoundException()
        return item

    async def edit(self, data, exclude_unset=False, **filter_by):
        self.last_edit = (data, exclude_unset, filter_by)

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)

    async def get_all_with_materials_and_cards(self):
        if self.raise_on_get_all:
            raise self.raise_on_get_all
        return self.get_all_result

    async def get_with_materials(self, theme_id):
        return self.get_with_materials_result

    async def get_orm_one_or_none(self, theme_id):
        return self.get_orm_one_or_none_map.get(theme_id)

    async def add_entity(self, entity):
        self.add_calls.append(entity)
        self.get_orm_one_or_none_map[entity.id] = entity

    async def flush(self):
        self.flush_count += 1


class FakeEducationMaterialRepository:
    def __init__(self):
        self.add_calls = []
        self.get_one_or_none_map = {}
        self.last_edit = None
        self.delete_calls = []
        self.delete_not_in_calls = []

    async def get_one_or_none(self, **filter_by):
        return self.get_one_or_none_map.get(filter_by.get("id"))

    async def add(self, data):
        self.add_calls.append(data)
        return data

    async def get_one(self, **filter_by):
        item = self.get_one_or_none_map.get(filter_by.get("id"))
        if item is None:
            raise ObjectNotFoundException()
        return item

    async def edit(self, data, exclude_unset=False, **filter_by):
        self.last_edit = (data, exclude_unset, filter_by)

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)

    async def get_orm_one_or_none(self, material_id):
        return self.get_one_or_none_map.get(material_id)

    async def add_entity(self, entity):
        self.add_calls.append(entity)
        self.get_one_or_none_map[entity.id] = entity

    async def delete_not_in(self, theme_id, material_ids):
        self.delete_not_in_calls.append((theme_id, material_ids))


class FakeEducationCardRepository:
    def __init__(self):
        self.add_calls = []
        self.get_one_or_none_map = {}
        self.last_edit = None
        self.delete_calls = []
        self.delete_not_in_calls = []

    async def get_one_or_none(self, **filter_by):
        return self.get_one_or_none_map.get(filter_by.get("id"))

    async def add(self, data):
        self.add_calls.append(data)
        return data

    async def get_one(self, **filter_by):
        item = self.get_one_or_none_map.get(filter_by.get("id"))
        if item is None:
            raise ObjectNotFoundException()
        return item

    async def edit(self, data, exclude_unset=False, **filter_by):
        self.last_edit = (data, exclude_unset, filter_by)

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)

    async def get_orm_one_or_none(self, card_id):
        return self.get_one_or_none_map.get(card_id)

    async def add_entity(self, entity):
        self.add_calls.append(entity)
        self.get_one_or_none_map[entity.id] = entity

    async def delete_not_in(self, material_id, card_ids):
        self.delete_not_in_calls.append((material_id, card_ids))


class FakeEducationProgressRepository:
    def __init__(self):
        self.one_or_none_map = {}
        self.filtered_result = []
        self.add_calls = []

    async def get_one_or_none(self, **filter_by):
        return self.one_or_none_map.get((filter_by.get("user_id"), filter_by.get("education_material_id")))

    async def get_filtered(self, **filter_by):
        return self.filtered_result

    async def add(self, data):
        self.add_calls.append(data)


class FakeOntologyEntryRepository:
    def __init__(self):
        self.filtered_result = []
        self.delete_calls = []

    async def get_filtered(self, **filter_by):
        return self.filtered_result

    async def delete(self, **filter_by):
        self.delete_calls.append(filter_by)


class FakeEducationDb:
    def __init__(self):
        self.education_theme = FakeEducationThemeRepository()
        self.education_material = FakeEducationMaterialRepository()
        self.education_card = FakeEducationCardRepository()
        self.education_progress = FakeEducationProgressRepository()
        self.ontology_entry = FakeOntologyEntryRepository()
        self.commit_count = 0
        self.rollback_count = 0
        self.execute_calls = []
        self.raise_on_commit = None

    async def commit(self):
        if self.raise_on_commit:
            raise self.raise_on_commit
        self.commit_count += 1

    async def rollback(self):
        self.rollback_count += 1

    async def execute(self, query):
        self.execute_calls.append(query)


class DummyDailyTaskService:
    tasks_response = []
    complete_calls = []
    raise_on_get = None
    raise_on_complete = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.tasks_response = []
        cls.complete_calls = []
        cls.raise_on_get = None
        cls.raise_on_complete = None

    async def get_daily_tasks(self, user_id):
        if type(self).raise_on_get:
            raise type(self).raise_on_get
        return type(self).tasks_response

    async def complete_daily_task(self, payload, user_id):
        if type(self).raise_on_complete:
            raise type(self).raise_on_complete
        type(self).complete_calls.append((payload, user_id))


class DummyGamificationService:
    add_calls = []
    raise_on_add = None

    def __init__(self, db):
        self.db = db

    @classmethod
    def reset(cls):
        cls.add_calls = []
        cls.raise_on_add = None

    async def add_points_for_activity(self, user_id, activity_type):
        if type(self).raise_on_add:
            raise type(self).raise_on_add
        type(self).add_calls.append((user_id, activity_type))
        return 10


@pytest.fixture
def fake_education_db(monkeypatch):
    DummyDailyTaskService.reset()
    DummyGamificationService.reset()
    monkeypatch.setattr(education_service_module, "DailyTaskService", DummyDailyTaskService)
    monkeypatch.setattr(education_service_module, "GamificationService", DummyGamificationService)
    return FakeEducationDb()


def sample_nested_education_fixture():
    themes = sample_themes_fixture()
    materials = sample_materials_fixture()
    cards = sample_cards_fixture()
    result = []
    for theme in themes:
        theme_data = dict(theme)
        theme_data["materials"] = []
        for material in materials:
            if material["education_theme_id"] != theme["id"]:
                continue
            material_data = dict(material)
            material_data.pop("education_theme_id")
            material_data["cards"] = [
                {
                    key: value
                    for key, value in card.items()
                    if key != "education_material_id"
                }
                for card in cards
                if card["education_material_id"] == material["id"]
            ]
            theme_data["materials"].append(material_data)
        result.append(theme_data)
    return result


@pytest.mark.asyncio
async def test_auto_create_education_creates_fixture_tree(fake_education_db, monkeypatch):
    monkeypatch.setattr(
        education_service_module,
        "EDUCATION",
        sample_nested_education_fixture(),
    )

    result = await EducationService(fake_education_db).auto_create_education()

    assert result["status"] == "OK"
    assert len(fake_education_db.education_theme.add_calls) == 2
    assert len(fake_education_db.education_material.add_calls) == 2
    assert len(fake_education_db.education_card.add_calls) == 2
    assert fake_education_db.education_theme.flush_count == 1
    assert len(fake_education_db.education_material.delete_not_in_calls) == 2
    assert fake_education_db.commit_count == 1


@pytest.mark.asyncio
async def test_education_service_crud_methods(fake_education_db):
    fake_education_db.education_theme.get_one_or_none_map[THEME_ID] = make_theme()
    fake_education_db.education_material.get_one_or_none_map[MATERIAL_ID] = make_material()
    fake_education_db.education_card.get_one_or_none_map[CARD_ID] = make_card()

    created_theme = await EducationService(fake_education_db).create_theme(
        education_service_module.EducationThemeCreate.model_validate(build_theme_create_payload())
    )
    updated_theme = await EducationService(fake_education_db).update_theme(
        THEME_ID,
        education_service_module.EducationThemeUpdate(theme="Updated"),
    )
    await EducationService(fake_education_db).delete_theme(THEME_ID)
    created_material = await EducationService(fake_education_db).create_material(
        THEME_ID,
        education_service_module.EducationMaterialCreate.model_validate(build_material_create_payload()),
    )
    updated_material = await EducationService(fake_education_db).update_material(
        MATERIAL_ID,
        education_service_module.EducationMaterialUpdate(title="Updated material"),
    )
    await EducationService(fake_education_db).delete_material(MATERIAL_ID)
    created_card = await EducationService(fake_education_db).create_card(
        MATERIAL_ID,
        education_service_module.CardCreate.model_validate(build_card_create_payload()),
    )
    updated_card = await EducationService(fake_education_db).update_card(
        CARD_ID,
        education_service_module.CardUpdate(text="Updated card"),
    )
    await EducationService(fake_education_db).delete_card(CARD_ID)

    assert created_theme.theme == "Theme title"
    assert updated_theme.id == THEME_ID
    assert created_material.title == "Material title"
    assert updated_material.id == MATERIAL_ID
    assert created_card.text == "Card text"
    assert updated_card.id == CARD_ID


@pytest.mark.asyncio
async def test_auto_create_education_updates_existing_entities(fake_education_db, monkeypatch):
    fixture = [sample_nested_education_fixture()[0]]
    material_data = fixture[0]["materials"][0]
    card_data = material_data["cards"][0]
    theme = SimpleNamespace(
        id=THEME_ID,
        theme="Old theme",
        link="old",
        link_to_picture=None,
        tags=None,
        related_topics=None,
    )
    material = SimpleNamespace(
        id=MATERIAL_ID,
        type=99,
        number=99,
        title="Old material",
        link_to_picture=None,
        subtitle=None,
        education_theme_id=SECOND_THEME_ID,
    )
    card = SimpleNamespace(
        id=uuid.UUID(card_data["id"]),
        text="Old card",
        number=99,
        link_to_picture=None,
        education_material_id=uuid.uuid4(),
    )
    fake_education_db.education_theme.get_orm_one_or_none_map[THEME_ID] = theme
    fake_education_db.education_material.get_one_or_none_map[MATERIAL_ID] = material
    fake_education_db.education_card.get_one_or_none_map[card.id] = card
    monkeypatch.setattr(education_service_module, "EDUCATION", fixture)

    await EducationService(fake_education_db).auto_create_education()

    assert theme.theme == fixture[0]["theme"]
    assert material.title == material_data["title"]
    assert material.education_theme_id == THEME_ID
    assert card.text == card_data["text"]
    assert card.education_material_id == MATERIAL_ID


@pytest.mark.asyncio
async def test_auto_create_education_rolls_back_when_commit_fails(fake_education_db, monkeypatch):
    monkeypatch.setattr(
        education_service_module,
        "EDUCATION",
        sample_nested_education_fixture(),
    )
    fake_education_db.raise_on_commit = RuntimeError("boom")

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).auto_create_education()

    assert fake_education_db.rollback_count == 1


@pytest.mark.asyncio
async def test_get_all_education_themes_returns_repository_payload(fake_education_db):
    fake_education_db.education_theme.get_all_result = [make_theme()]

    result = await EducationService(fake_education_db).get_all_education_themes()

    assert len(result) == 1
    assert result[0].id == THEME_ID


@pytest.mark.asyncio
async def test_get_all_education_themes_propagates_not_found(fake_education_db):
    fake_education_db.education_theme.raise_on_get_all = ObjectNotFoundException()

    with pytest.raises(ObjectNotFoundException):
        await EducationService(fake_education_db).get_all_education_themes()


@pytest.mark.asyncio
async def test_get_all_education_themes_wraps_unexpected_error(fake_education_db):
    fake_education_db.education_theme.raise_on_get_all = RuntimeError("boom")

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).get_all_education_themes()


@pytest.mark.asyncio
async def test_get_education_theme_materials_builds_recommendations_and_clears_ontology(fake_education_db):
    second_theme = make_theme(theme_id=SECOND_THEME_ID, theme="Second theme", link="/education/second", related_topics=[])
    fake_education_db.education_theme.get_with_materials_result = make_theme()
    fake_education_db.education_theme.get_orm_one_or_none_map[str(SECOND_THEME_ID)] = second_theme
    fake_education_db.ontology_entry.filtered_result = [make_ontology_entry()]

    result = await EducationService(fake_education_db).get_education_theme_materials(THEME_ID, USER_ID)

    assert result.id == THEME_ID
    assert len(result.recommendations) == 1
    assert result.recommendations[0].id == SECOND_THEME_ID
    assert len(result.education_materials[0].cards) == 1
    assert fake_education_db.ontology_entry.delete_calls == [{"user_id": USER_ID, "destination_id": THEME_ID}]


@pytest.mark.asyncio
async def test_get_education_theme_materials_raises_not_found_for_missing_theme(fake_education_db):
    fake_education_db.education_theme.get_with_materials_result = None

    with pytest.raises(ObjectNotFoundException):
        await EducationService(fake_education_db).get_education_theme_materials(THEME_ID, USER_ID)


@pytest.mark.asyncio
async def test_get_education_theme_materials_wraps_unexpected_error(fake_education_db):
    fake_education_db.education_theme.get_with_materials_result = make_theme()
    fake_education_db.ontology_entry.get_filtered = _raise_async(RuntimeError("boom"))

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).get_education_theme_materials(THEME_ID, USER_ID)


@pytest.mark.asyncio
async def test_complete_education_theme_completes_matching_daily_task(fake_education_db):
    DummyDailyTaskService.tasks_response = [
        {"id": THEME_ID, "destination_id": MATERIAL_ID},
        {"id": SECOND_THEME_ID, "destination_id": THEME_ID},
    ]

    await EducationService(fake_education_db).complete_education_theme(
        SimpleNamespace(education_theme_id=THEME_ID),
        USER_ID,
    )

    assert len(DummyDailyTaskService.complete_calls) == 1
    payload, user_id = DummyDailyTaskService.complete_calls[0]
    assert payload.daily_task_id == SECOND_THEME_ID
    assert user_id == USER_ID


@pytest.mark.asyncio
async def test_complete_education_theme_skips_when_no_matching_task(fake_education_db):
    DummyDailyTaskService.tasks_response = [{"id": SECOND_THEME_ID, "destination_id": MATERIAL_ID}]

    await EducationService(fake_education_db).complete_education_theme(
        SimpleNamespace(education_theme_id=THEME_ID),
        USER_ID,
    )

    assert DummyDailyTaskService.complete_calls == []


@pytest.mark.asyncio
async def test_complete_education_theme_wraps_unexpected_error(fake_education_db):
    DummyDailyTaskService.raise_on_get = RuntimeError("boom")

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).complete_education_theme(
            SimpleNamespace(education_theme_id=THEME_ID),
            USER_ID,
        )

    assert fake_education_db.rollback_count == 1


@pytest.mark.asyncio
async def test_complete_education_material_creates_progress_and_adds_score(fake_education_db):
    fake_education_db.education_material.get_one_or_none_map[MATERIAL_ID] = make_material()

    await EducationService(fake_education_db).complete_education_material(
        SimpleNamespace(education_material_id=MATERIAL_ID),
        USER_ID,
    )

    created = fake_education_db.education_progress.add_calls[0]
    assert created.user_id == USER_ID
    assert created.education_material_id == MATERIAL_ID
    assert DummyGamificationService.add_calls == [(USER_ID, "theory_read")]
    assert fake_education_db.commit_count == 1


@pytest.mark.asyncio
async def test_complete_education_material_raises_not_found_for_missing_material(fake_education_db):
    with pytest.raises(ObjectNotFoundException):
        await EducationService(fake_education_db).complete_education_material(
            SimpleNamespace(education_material_id=MATERIAL_ID),
            USER_ID,
        )


@pytest.mark.asyncio
async def test_complete_education_material_raises_duplicate_for_existing_progress(fake_education_db):
    fake_education_db.education_material.get_one_or_none_map[MATERIAL_ID] = make_material()
    fake_education_db.education_progress.one_or_none_map[(USER_ID, MATERIAL_ID)] = make_progress()

    with pytest.raises(ObjectAlreadyExistsException):
        await EducationService(fake_education_db).complete_education_material(
            SimpleNamespace(education_material_id=MATERIAL_ID),
            USER_ID,
        )


@pytest.mark.asyncio
async def test_complete_education_material_rolls_back_on_unexpected_error(fake_education_db):
    fake_education_db.education_material.get_one_or_none_map[MATERIAL_ID] = make_material()
    DummyGamificationService.raise_on_add = RuntimeError("boom")

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).complete_education_material(
            SimpleNamespace(education_material_id=MATERIAL_ID),
            USER_ID,
        )

    assert fake_education_db.rollback_count == 1


@pytest.mark.asyncio
async def test_get_user_progress_returns_mapped_entries(fake_education_db):
    fake_education_db.education_progress.filtered_result = [make_progress()]

    result = await EducationService(fake_education_db).get_user_progress(USER_ID)

    assert len(result) == 1
    assert result[0].user_id == USER_ID
    assert result[0].education_material_id == MATERIAL_ID


@pytest.mark.asyncio
async def test_get_user_progress_returns_empty_list(fake_education_db):
    result = await EducationService(fake_education_db).get_user_progress(USER_ID)

    assert result == []


@pytest.mark.asyncio
async def test_get_user_progress_wraps_unexpected_error(fake_education_db):
    fake_education_db.education_progress.get_filtered = _raise_async(RuntimeError("boom"))

    with pytest.raises(MyAppException):
        await EducationService(fake_education_db).get_user_progress(USER_ID)


def _raise_async(error):
    async def _inner(*args, **kwargs):
        raise error

    return _inner


def test_education_fixture_contains_self_regulation_theme():
    theme = next(item for item in EDUCATION if item["theme"] == "Саморегуляция")

    assert [material["subtitle"] for material in theme["materials"]] == [
        "Что это такое?",
        "В чем помогает саморегуляция?",
        "Как выстроить процесс саморегуляции?",
        "Техники саморегуляции",
        "Ловушки саморегуляции: важное отличие",
        "Выводы",
    ]
    assert [len(material["cards"]) for material in theme["materials"]] == [
        2,
        3,
        7,
        5,
        3,
        1,
    ]
    assert theme["link_to_picture"] is None
    assert all(
        material["link_to_picture"] is None
        and all(card["link_to_picture"] is None for card in material["cards"])
        for material in theme["materials"]
    )
