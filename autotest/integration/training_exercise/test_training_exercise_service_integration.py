import pytest
from sqlalchemy import select

from autotest.factories.training_exercise import USER_ID
from src.models.training_exercises import (
    TrainingCompletedExerciseOrm,
    TrainingExerciseOrm,
    TrainingQuestionOrm,
    TrainingVariantOrm,
)
from src.models.users import UsersOrm
from src.services.training_exercise import TrainingExerciseService
from src.services.fixtures.training_exercise import TRAINING_EXERCISES


EXERCISE_ID = __import__("uuid").UUID(TRAINING_EXERCISES[0]["id"])


def build_user_orm(*, user_id=USER_ID):
    return UsersOrm(
        id=user_id,
        email="training-service@example.com",
        username="trainer-service",
        hashed_password="hashed",
        city="Tomsk",
        company=None,
        online=None,
        gender="male",
        birth_date=__import__("datetime").date(1999, 1, 1),
        phone_number="+70000000002",
        description=None,
        role_id=1,
        is_active=True,
        department=None,
        job_title=None,
        face_to_face=None,
    )


@pytest.mark.asyncio
async def test_training_exercise_service_seed_persists_real_hierarchy(
    integration_db,
    integration_session_factory,
):
    await TrainingExerciseService(integration_db).seed_exercises()

    async with integration_session_factory() as session:
        exercises = (await session.execute(select(TrainingExerciseOrm))).scalars().all()
        questions = (await session.execute(select(TrainingQuestionOrm))).scalars().all()
        variants = (await session.execute(select(TrainingVariantOrm))).scalars().all()

    assert len(exercises) >= 3
    assert len(questions) > 0
    assert len(variants) > 0
    assert any(exercise.id == EXERCISE_ID for exercise in exercises)


@pytest.mark.asyncio
async def test_training_exercise_service_get_all_marks_completed_from_real_db(
    integration_db,
    integration_session_factory,
):
    await TrainingExerciseService(integration_db).seed_exercises()

    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()
        session.add(
            TrainingCompletedExerciseOrm(
                training_exercise_id=EXERCISE_ID,
                user_id=USER_ID,
            )
        )
        await session.commit()

    result = await TrainingExerciseService(integration_db).get_all_exercises(USER_ID)

    completed_item = next(item for item in result if item.id == EXERCISE_ID)
    assert completed_item.is_completed is True


@pytest.mark.asyncio
async def test_training_exercise_service_complete_is_idempotent_integration(
    integration_db,
    integration_session_factory,
):
    await TrainingExerciseService(integration_db).seed_exercises()

    async with integration_session_factory() as session:
        session.add(build_user_orm())
        await session.commit()

    await TrainingExerciseService(integration_db).complete_exercise(EXERCISE_ID, USER_ID)
    await TrainingExerciseService(integration_db).complete_exercise(EXERCISE_ID, USER_ID)

    async with integration_session_factory() as session:
        rows = (
            await session.execute(
                select(TrainingCompletedExerciseOrm).filter_by(
                    training_exercise_id=EXERCISE_ID,
                    user_id=USER_ID,
                )
            )
        ).scalars().all()

    assert len(rows) == 1


@pytest.mark.asyncio
async def test_training_exercise_service_get_exercise_by_id_raises_for_missing_entity(integration_db):
    with pytest.raises(ValueError, match="Exercise not found"):
        await TrainingExerciseService(integration_db).get_exercise_by_id(EXERCISE_ID, USER_ID)
