import pytest
from fastapi.exceptions import ResponseValidationError

import src.api.chat_bot as chat_bot_module
from autotest4.factories.chat_bot import build_faq_data


@pytest.fixture
def faq_data(monkeypatch):
    faq_data = build_faq_data()
    monkeypatch.setattr(chat_bot_module, "load_faq_data", lambda: faq_data)
    return faq_data


@pytest.mark.asyncio
async def test_get_all_groups_returns_id_and_name_only(client, faq_data):
    response = await client.get("/chat-bot/groups")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "name": "Psychology"},
        {"id": 2, "name": "Technical"},
    ]
    assert all(sorted(item.keys()) == ["id", "name"] for item in response.json())


@pytest.mark.asyncio
async def test_get_all_groups_returns_empty_list_when_source_has_no_groups(client, monkeypatch):
    monkeypatch.setattr(chat_bot_module, "load_faq_data", lambda: {"groups": []})

    response = await client.get("/chat-bot/groups")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all_groups_returns_500_when_data_loading_fails(client, monkeypatch):
    monkeypatch.setattr(
        chat_bot_module,
        "load_faq_data",
        lambda: (_ for _ in ()).throw(FileNotFoundError("chat_bot.json missing")),
    )
    response = await client.get("/chat-bot/groups")
    assert response.status_code == 500
    assert "chat_bot.json missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_all_groups_returns_500_when_group_structure_is_invalid(client, monkeypatch):
    monkeypatch.setattr(chat_bot_module, "load_faq_data", lambda: {"groups": [{"id": 1}]})

    response = await client.get("/chat-bot/groups")

    assert response.status_code == 500
    assert "name" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_all_questions_from_group(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 101, "question": "How to start?"},
        {"id": 102, "question": "How to reduce anxiety?"},
    ]
    assert all(sorted(item.keys()) == ["id", "question"] for item in response.json())


@pytest.mark.asyncio
async def test_get_questions_by_group_applies_limit(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?limit=1")
    assert response.status_code == 200
    assert response.json() == [{"id": 101, "question": "How to start?"}]


@pytest.mark.asyncio
async def test_get_questions_by_group_ignores_non_positive_limit(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?limit=0")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 101, "question": "How to start?"},
        {"id": 102, "question": "How to reduce anxiety?"},
    ]


@pytest.mark.asyncio
async def test_get_questions_by_group_ignores_negative_limit(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?limit=-5")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 101, "question": "How to start?"},
        {"id": 102, "question": "How to reduce anxiety?"},
    ]


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_all_items_when_limit_exceeds_collection_size(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?limit=99")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 101, "question": "How to start?"},
        {"id": 102, "question": "How to reduce anxiety?"},
    ]


@pytest.mark.asyncio
async def test_get_questions_by_group_filters_by_search_case_insensitively(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?search=REDUCE")
    assert response.status_code == 200
    assert response.json() == [{"id": 102, "question": "How to reduce anxiety?"}]


@pytest.mark.asyncio
async def test_get_questions_by_group_keeps_full_list_for_empty_search_string(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?search=")
    assert response.status_code == 200
    assert response.json() == [
        {"id": 101, "question": "How to start?"},
        {"id": 102, "question": "How to reduce anxiety?"},
    ]


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_empty_list_when_search_has_no_matches(client, faq_data):
    response = await client.get("/chat-bot/groups/1/questions?search=missing")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_empty_list_for_group_without_questions(client, monkeypatch):
    monkeypatch.setattr(
        chat_bot_module,
        "load_faq_data",
        lambda: {"groups": [{"id": 1, "name": "Psychology", "questions": []}]},
    )

    response = await client.get("/chat-bot/groups/1/questions")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_404_for_unknown_group(client, faq_data):
    response = await client.get("/chat-bot/groups/999/questions")
    assert response.status_code == 404
    assert response.json()["detail"] == "\u0413\u0440\u0443\u043f\u043f\u0430 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u0430"


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_422_for_invalid_group_id(client):
    response = await client.get("/chat-bot/groups/not-an-int/questions")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_422_for_invalid_limit_type(client):
    response = await client.get("/chat-bot/groups/1/questions?limit=not-an-int")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_500_for_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(chat_bot_module, "load_faq_data", lambda: (_ for _ in ()).throw(RuntimeError("broken json")))
    response = await client.get("/chat-bot/groups/1/questions")
    assert response.status_code == 500
    assert "broken json" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_questions_by_group_returns_500_when_group_has_invalid_question_structure(client, monkeypatch):
    monkeypatch.setattr(
        chat_bot_module,
        "load_faq_data",
        lambda: {
            "groups": [
                {
                    "id": 1,
                    "name": "Psychology",
                    "questions": [{"id": 101}],
                }
            ]
        },
    )

    response = await client.get("/chat-bot/groups/1/questions")

    assert response.status_code == 500
    assert "question" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_answer_by_question_id_returns_full_question(client, faq_data):
    response = await client.get("/chat-bot/questions/102")
    assert response.status_code == 200
    assert response.json() == {
        "id": 102,
        "question": "How to reduce anxiety?",
        "answer": "Use grounding techniques.",
    }


@pytest.mark.asyncio
async def test_get_answer_by_question_id_finds_question_in_another_group(client, faq_data):
    response = await client.get("/chat-bot/questions/201")

    assert response.status_code == 200
    assert response.json() == {
        "id": 201,
        "question": "How to enable notifications?",
        "answer": "Open profile settings.",
    }


@pytest.mark.asyncio
async def test_get_answer_by_question_id_returns_404_for_unknown_question(client, faq_data):
    response = await client.get("/chat-bot/questions/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "\u0412\u043e\u043f\u0440\u043e\u0441 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d"


@pytest.mark.asyncio
async def test_get_answer_by_question_id_returns_422_for_invalid_question_id(client):
    response = await client.get("/chat-bot/questions/not-an-int")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_answer_by_question_id_returns_500_for_unexpected_error(client, monkeypatch):
    monkeypatch.setattr(
        chat_bot_module,
        "load_faq_data",
        lambda: (_ for _ in ()).throw(ValueError("invalid structure")),
    )
    response = await client.get("/chat-bot/questions/101")
    assert response.status_code == 500
    assert "invalid structure" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_answer_by_question_id_raises_response_validation_error_when_payload_breaks_schema(
    client,
    monkeypatch,
):
    monkeypatch.setattr(
        chat_bot_module,
        "load_faq_data",
        lambda: {
            "groups": [
                {
                    "id": 1,
                    "name": "Psychology",
                    "questions": [{"id": 101, "question": "How to start?"}],
                }
            ]
        },
    )

    with pytest.raises(ResponseValidationError):
        await client.get("/chat-bot/questions/101")


@pytest.mark.asyncio
async def test_get_emergency_contacts_returns_expected_static_payload(client):
    response = await client.get("/chat-bot/emergency-contacts")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 4
    assert all(sorted(item.keys()) == ["description", "formatted", "phone"] for item in payload)
    assert payload[0]["phone"] == "8-800-2000-122"
    assert all(item["phone"] in item["formatted"] for item in payload)
    assert all(item["description"] for item in payload)
