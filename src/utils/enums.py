from enum import Enum


class ViewType(Enum):
    DEFAULT = "default"
    PRIMARY = "primary"


class FieldType(Enum):
    ADDABLE_LIST = "addable_list"
    INPUT = "input"
    TEXT = "text"
    SLIDER = "slider"
    CHOICE = "choice"
