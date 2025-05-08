from enum import Enum

class RoleEnum(int, Enum):
    USER = 1  # Клиент
    MANAGER = 2  # Менеджер
    PSYСHOLOGIST = 3 #Психолог
    ADMIN = 0  # Администратор