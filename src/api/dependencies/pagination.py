from typing import Annotated
from fastapi import Depends, Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: Annotated[int | None, Query(default=1, gt=0)]
    per_page: Annotated[int | None, Query(default=None, gt=0, lt=30)]


PaginationDep = Annotated[PaginationParams, Depends()]
