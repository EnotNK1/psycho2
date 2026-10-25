import uuid
from typing import Optional

from sqlalchemy import and_, select

from src.repositories.base import BaseRepository
from src.models.clients import ClientsOrm
from src.models.users import UsersOrm
from src.models.tests import BordersOrm, ScaleOrm, ScaleResultOrm, TestOrm, TestResultOrm
from src.repositories.mappers.mappers import TestResultDataMapper


class TestResultRepository(BaseRepository):
    model = TestResultOrm
    mapper = TestResultDataMapper

    async def get_psychologist_alert_candidates(
        self, psychologist_id: uuid.UUID, test_ids: tuple[uuid.UUID, ...]
    ) -> list[dict]:
        active_client = select(ClientsOrm.id).where(
            ClientsOrm.client_id == TestResultOrm.user_id,
            ClientsOrm.mentor_id == psychologist_id,
            ClientsOrm.status.is_(True),
        ).exists()
        query = (
            select(
                UsersOrm.id.label("client_id"),
                UsersOrm.username.label("client_name"),
                TestOrm.id.label("test_id"),
                TestOrm.title.label("test_title"),
                TestResultOrm.id.label("test_result_id"),
                TestResultOrm.date.label("date"),
                ScaleOrm.id.label("scale_id"),
                ScaleOrm.min.label("min_score"),
                ScaleOrm.max.label("max_score"),
                ScaleResultOrm.score,
                BordersOrm.title.label("conclusion"),
                BordersOrm.left_border,
                BordersOrm.right_border,
            )
            .select_from(TestResultOrm)
            .join(UsersOrm, UsersOrm.id == TestResultOrm.user_id)
            .join(TestOrm, TestOrm.id == TestResultOrm.test_id)
            .join(ScaleResultOrm, ScaleResultOrm.test_result_id == TestResultOrm.id)
            .join(ScaleOrm, and_(
                ScaleOrm.id == ScaleResultOrm.scale_id,
                ScaleOrm.test_id == TestResultOrm.test_id,
            ))
            .outerjoin(BordersOrm, BordersOrm.scale_id == ScaleOrm.id)
            .where(TestResultOrm.test_id.in_(test_ids), active_client)
            .order_by(TestResultOrm.date.desc(), TestResultOrm.id.desc())
        )
        # Scores are encrypted at rest; selecting the mapped column decrypts them.
        result = await self.session.execute(query)
        return [dict(row) for row in result.mappings().all()]
