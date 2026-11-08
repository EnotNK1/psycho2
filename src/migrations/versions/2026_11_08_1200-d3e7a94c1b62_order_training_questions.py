"""add stable ordering to training exercise questions

Revision ID: d3e7a94c1b62
Revises: c8d4e1f2a7b9
Create Date: 2026-11-08 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d3e7a94c1b62"
down_revision: Union[str, Sequence[str], None] = "c8d4e1f2a7b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


QUESTION_ORDER = (
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "Ты серьёзно?! Я столько времени потратил, а ты даже не предупредил. Это просто свинство. Всё, не звони мне сегодня, мне нужно остыть.",
        1,
    ),
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "Я опоздала на встречу с подругой на двадцать минут. Она ждала меня в кафе, хотя у неё сегодня важный звонок должен был быть. Я знаю, как она не любит ждать. И ведь я обещала, что приду вовремя. Настроение просто упало ниже некуда",
        2,
    ),
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "Сзади шаги, кто-то быстро приближается в темноте. Дыхание перехватило. Руки дрожат, телефон выскальзывает. Надо бежать. Сейчас же.",
        3,
    ),
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "Всё как-то бессмысленно сегодня... Даже вставать не хочется. Просто оставь меня в покое, пожалуйста. Побуду одна.",
        4,
    ),
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "Я зашёл в столовую и взял обед. Когда я откусил котлету, я почувствовал во рту что-то странное — мягкое, скользкое и с привкусом тухлятины. Я выплюнул это в салфетку и увидел кусок сырого, серого фарша. Меня буквально передёрнуло, к горлу подкатила тошнота.",
        5,
    ),
    (
        "03bb5961-0983-44a9-b14b-4c3b3b7314df",
        "ОБОЖАЮ! Всё прошло идеально! 😍 Так легко на душе, будто крылья выросли. Срочно хочу увидеться и отпраздновать!",
        6,
    ),
    (
        "ebf39484-222a-43e6-9a70-75ff11b8a9cf",
        "Ваш руководитель указал на ошибку в отчёте на общем совещании.",
        1,
    ),
    (
        "ebf39484-222a-43e6-9a70-75ff11b8a9cf",
        "Вы написали близкому другу важное сообщение вчера вечером, но ответа до сих пор нет.",
        2,
    ),
    (
        "ebf39484-222a-43e6-9a70-75ff11b8a9cf",
        "Листая ленту, вы видите фото знакомого с новой работы и квартиры.",
        3,
    ),
    (
        "1a406e72-efac-4cc8-9144-19b367a1547b",
        "Если я ошибусь, это просто ужасно",
        1,
    ),
    (
        "1a406e72-efac-4cc8-9144-19b367a1547b",
        "Я должен(а) всегда быть продуктивным(ой)!",
        2,
    ),
)


def upgrade() -> None:
    op.add_column(
        "training_question",
        sa.Column("position", sa.Integer(), nullable=False, server_default="1000000"),
    )

    connection = op.get_bind()
    for exercise_id, question_text, position in QUESTION_ORDER:
        connection.execute(
            sa.text(
                "UPDATE training_question "
                "SET position = :position "
                "WHERE training_exercise_id = :exercise_id AND text = :question_text"
            ),
            {
                "position": position,
                "exercise_id": exercise_id,
                "question_text": question_text,
            },
        )

    op.alter_column("training_question", "position", server_default=None)


def downgrade() -> None:
    op.drop_column("training_question", "position")
