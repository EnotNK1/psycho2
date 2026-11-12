import uuid

from src.enums import RoleEnum
from src.exceptions import AccessDeniedHTTPException
from src.schemas.test_alerts import TestAlert
from src.services.base import BaseService


BECK_TEST_ID = uuid.UUID("33d10952-aed7-4a4e-9e5a-dbd01b2f294d")
BECK_TOTAL_SCALE_ID = uuid.UUID("5cd5e9b7-279d-4d19-993e-9debb99b91b1")
DASS_TEST_ID = uuid.UUID("bc9f1204-ea5d-40b0-b367-359bf9b2cc21")
STAI_TEST_ID = uuid.UUID("3a9a3c8d-348e-4f0d-aefd-0feaa960ac25")


class TestAlertService(BaseService):
    async def get_alerts(self, psychologist_id: uuid.UUID) -> list[TestAlert]:
        psychologist = await self.db.users.get_one_or_none(id=psychologist_id)
        if psychologist is None or psychologist.role_id != RoleEnum.PSYCHOLOGIST:
            raise AccessDeniedHTTPException()

        candidates = await self.db.test_result.get_psychologist_alert_candidates(
            psychologist_id, (BECK_TEST_ID, DASS_TEST_ID, STAI_TEST_ID)
        )
        alerts = {}
        for row in candidates:
            score = row["score"]
            if score is None or not row["min_score"] <= score <= row["max_score"]:
                continue
            if row["test_id"] == BECK_TEST_ID:
                matches = row["scale_id"] == BECK_TOTAL_SCALE_ID and 30 <= score <= 63
            else:
                expected = "Высокий" if row["test_id"] == DASS_TEST_ID else "Выше нормы"
                matches = (
                    row["conclusion"] == expected
                    and row["left_border"] is not None
                    and row["right_border"] is not None
                    and row["left_border"] <= score <= row["right_border"]
                )
            if matches and row["test_result_id"] not in alerts:
                alerts[row["test_result_id"]] = TestAlert.model_validate(row)
        return list(alerts.values())
