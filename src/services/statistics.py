import uuid
from typing import Dict, Any, List
from uuid import UUID
from sqlalchemy import func, select
from src.services.base import BaseService
from src.exceptions import MyAppException, ObjectNotFoundException
from venv import logger


class StatisticsService(BaseService):
    async def get_user_activity_statistics(self, user_id: UUID) -> Dict[str, Any]:
        try:
            statistics = {
                "user_id": str(user_id),
                "exercises": await self._get_exercise_statistics(user_id),
                "tests": await self._get_test_statistics(user_id),
                "mood_trackers_count": await self._get_mood_tracker_count(user_id),
                "education_blocks_count": await self._get_education_progress_count(user_id)
            }

            statistics["total_activities"] = (
                    statistics["exercises"]["total_exercises"] +
                    statistics["tests"]["total_tests"] +
                    statistics["mood_trackers_count"] +
                    statistics["education_blocks_count"]
            )

            return statistics

        except Exception as e:
            logger.error(f"Ошибка получения статистики пользователя {user_id}: {str(e)}")
            raise MyAppException()

    async def _get_exercise_statistics(self, user_id: UUID) -> Dict[str, Any]:
        try:
            exercise_results = await self.db.CompletedExerciseOrm.get_filtered(user_id=user_id)

            if not exercise_results:
                return {
                    "total_exercises": 0,
                    "by_exercise": {}
                }

            exercise_counts = {}
            for result in exercise_results:
                exercise_id = str(result.exercise_id)
                exercise_counts[exercise_id] = exercise_counts.get(exercise_id, 0) + 1

            exercise_details = {}
            exercise_ids = list(exercise_counts.keys())

            if exercise_ids:
                exercises = await self.db.exercises.get_by_ids(exercise_ids)
                exercise_map = {str(exercise.id): exercise for exercise in exercises}

                for exercise_id, count in exercise_counts.items():
                    exercise = exercise_map.get(exercise_id)
                    exercise_name = exercise.title if exercise else f"Упражнение_{exercise_id}"
                    exercise_details[exercise_name] = count

            return {
                "total_exercises": len(exercise_results),
                "by_exercise": exercise_details
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики упражнений: {str(e)}")
            return {
                "total_exercises": 0,
                "by_exercise": {}
            }

    async def _get_test_statistics(self, user_id: UUID) -> Dict[str, Any]:
        try:
            test_results = await self.db.test_result.get_filtered(user_id=user_id)

            if not test_results:
                return {
                    "total_tests": 0,
                    "by_test": {}
                }

            test_counts = {}
            for result in test_results:
                test_id = str(result.test_id)
                test_counts[test_id] = test_counts.get(test_id, 0) + 1

            test_details = {}
            test_ids = list(test_counts.keys())

            if test_ids:
                tests = await self.db.tests.get_by_ids(test_ids)
                test_map = {str(test.id): test for test in tests}

                for test_id, count in test_counts.items():
                    test = test_map.get(test_id)
                    test_name = test.title if test else f"Тест_{test_id}"
                    test_details[test_name] = count

            return {
                "total_tests": len(test_results),
                "by_test": test_details
            }

        except Exception as e:
            logger.error(f"Ошибка получения статистики тестов: {str(e)}")
            return {
                "total_tests": 0,
                "by_test": {}
            }

    async def _get_mood_tracker_count(self, user_id: UUID) -> int:
        try:
            mood_trackers = await self.db.mood_tracker.get_filtered(user_id=user_id)
            return len(mood_trackers) if mood_trackers else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества трекеров настроения: {str(e)}")
            return 0

    async def _get_education_progress_count(self, user_id: UUID) -> int:
        try:
            progress_entries = await self.db.education_progress.get_filtered(user_id=user_id)
            return len(progress_entries) if progress_entries else 0
        except Exception as e:
            logger.error(f"Ошибка получения прогресса обучения: {str(e)}")
            return 0

    async def get_multiple_users_statistics(self, user_ids: List[UUID]) -> Dict[str, Any]:
        try:
            result = {}
            for user_id in user_ids:
                result[str(user_id)] = await self.get_user_activity_statistics(user_id)

            return result

        except Exception as e:
            logger.error(f"Ошибка получения статистики для нескольких пользователей: {str(e)}")
            raise MyAppException()