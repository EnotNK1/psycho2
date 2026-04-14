import pytest

from src.api.chat_bot import router as chat_bot_router


@pytest.fixture
async def client(api_client_factory):
    async for async_client, _ in api_client_factory(chat_bot_router):
        yield async_client


@pytest.mark.asyncio
async def test_chat_bot_groups_smoke(client):
    response = await client.get("/chat-bot/groups")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


@pytest.mark.asyncio
async def test_chat_bot_question_smoke(client):
    response = await client.get("/chat-bot/questions/101")

    assert response.status_code == 200
    body = response.json()
    assert {"id", "question", "answer"} <= set(body.keys())


@pytest.mark.asyncio
async def test_chat_bot_emergency_contacts_smoke(client):
    response = await client.get("/chat-bot/emergency-contacts")

    assert response.status_code == 200
    assert len(response.json()) >= 1
