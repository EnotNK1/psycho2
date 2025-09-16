from enum import Enum

class RoleEnum(int, Enum):
    USER = 1  # Клиент
    MANAGER = 2  # Менеджер
    PSYСHOLOGIST = 3 #Психолог
    ADMIN = 0  # Администратор

class DailyTaskType(int, Enum):
    THEORY = 1
    MOOD_TRACKER_AND_FREE_DIARY = 2
    TEST = 3
    OTHER = 4