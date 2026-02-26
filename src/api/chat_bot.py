from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import json
from pathlib import Path

router = APIRouter(prefix="/chat-bot", tags=["Чат бот"])


# Модели данных
class QuestionSchema(BaseModel):
    id: int
    question: str
    answer: str


class GroupSchema(BaseModel):
    id: int
    name: str
    questions: List[QuestionSchema]


class GroupsListSchema(BaseModel):
    groups: List[GroupSchema]


class EmergencyContactSchema(BaseModel):
    phone: str
    description: str
    formatted: str  # Полная строка с номером и описанием


# Загрузка данных из JSON файла
def load_faq_data():
    with open("src/services/info/chat_bot.json", encoding="utf-8") as file:
        return json.load(file)


@router.get("/groups", response_model=List[dict])
async def get_all_groups():
    try:
        data = load_faq_data()
        groups = [
            {"id": group["id"], "name": group["name"]}
            for group in data["groups"]
        ]
        return groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке групп: {str(e)}")


@router.get("/groups/{group_id}/questions", response_model=List[dict])
async def get_questions_by_group(
        group_id: int,
        limit: Optional[int] = Query(None, description="Ограничить количество вопросов"),
        search: Optional[str] = Query(None, description="Поиск по тексту вопроса")
):
    try:
        data = load_faq_data()

        group = next(
            (g for g in data["groups"] if g["id"] == group_id),
            None
        )

        if not group:
            raise HTTPException(status_code=404, detail="Группа не найдена")

        questions = group["questions"]

        if search:
            search_lower = search.lower()
            questions = [
                q for q in questions
                if search_lower in q["question"].lower()
            ]

        if limit and limit > 0:
            questions = questions[:limit]

        result = [
            {"id": q["id"], "question": q["question"]}
            for q in questions
        ]

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке вопросов: {str(e)}")


@router.get("/questions/{question_id}", response_model=QuestionSchema)
async def get_answer_by_question_id(question_id: int):
    try:
        data = load_faq_data()

        for group in data["groups"]:
            for question in group["questions"]:
                if question["id"] == question_id:
                    return question

        raise HTTPException(status_code=404, detail="Вопрос не найден")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке ответа: {str(e)}")


@router.get("/emergency-contacts", response_model=List[EmergencyContactSchema])
async def get_emergency_contacts():
    try:
        emergency_contacts = [
            {
                "phone": "8-800-2000-122",
                "description": "Единый общероссийский телефон доверия для детей, подростков и их родителей (круглосуточно, анонимно)",
                "formatted": "8-800-2000-122 — Единый общероссийский телефон доверия для детей, подростков и их родителей (круглосуточно, анонимно)"
            },
            {
                "phone": "8-800-333-44-34",
                "description": "Кризисная линия доверия (психологическая помощь в жизненных проблемах)",
                "formatted": "8-800-333-44-34 — Кризисная линия доверия (психологическая помощь в жизненных проблемах)"
            },
            {
                "phone": "8-495-989-50-50",
                "description": "Горячая линия центра экстренной психологической помощи МЧС России",
                "formatted": "8-495-989-50-50 — Горячая линия центра экстренной психологической помощи МЧС России"
            },
            {
                "phone": "8-800-7000-600",
                "description": "Горячая линия для женщин, пострадавших от домашнего насилия",
                "formatted": "8-800-7000-600 — Горячая линия для женщин, пострадавших от домашнего насилия"
            }
        ]

        return emergency_contacts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке контактов: {str(e)}")
