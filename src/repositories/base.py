import uuid

from sqlalchemy import select, insert, delete, update
from sqlalchemy.exc import NoResultFound, IntegrityError
from pydantic import BaseModel
from asyncpg.exceptions import UniqueViolationError
from fastapi import HTTPException
import logging

from src.exceptions import (
    ObjectNotFoundException,
    ObjectAlreadyExistsException,
    SeveralObjectsFoundException,
)
from src.repositories.mappers.base import DataMapper
from datetime import date, datetime

class BaseRepository:
    model = None
    mapper = None

    def __init__(self, session):
        self.session = session


    async def get_filtered(self, *filter, **filtered_by):
        query = select(self.model).filter(*filter).filter_by(**filtered_by)
        result = await self.session.execute(query)

        return [
            self.mapper.map_to_domain_entity(model) for model in result.scalars().all()
        ]

    async def get_all(self, *args, **kwargs):
        return await self.get_filtered()

    async def get_one_or_none(self, **filter_by):
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)

        model = result.scalars().one_or_none()
        if model is None:
            return None
        return self.mapper.map_to_domain_entity(model)

    async def get_one(self, **filter_by) -> BaseModel:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        try:
            model = result.scalar_one()
        except NoResultFound:
            raise ObjectNotFoundException
        return self.mapper.map_to_domain_entity(model)

    async def add(self, data: BaseModel):
        try:
            add_data_stmt = (
                insert(self.model).values(**data.model_dump()).returning(self.model)
            )
            result = await self.session.execute(add_data_stmt)
            model = result.scalars().one()
            return self.mapper.map_to_domain_entity(model)
        except IntegrityError as ex:
            logging.exception(f"Не удалось добавить данные в БД, входные данные={data}")
            if isinstance(ex.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsException from ex
            else:
                logging.exception(
                    f"Незнакомая ошибка: не удалось добавить данные в БД, входные данные={data}"
                )
                raise ex

    async def add_bulk(self, data: list[BaseModel]):
        data_stmt = insert(self.model).values([item.model_dump() for item in data])
        await self.session.execute(data_stmt)

    async def edit(self, data: BaseModel, exclude_unset: bool = False, **filter_by):
        query = select(self.model).filter_by(**filter_by)

        result = await self.session.execute(query)
        items = result.scalars().all()

        if len(items) == 0:
            raise ObjectNotFoundException
        elif len(items) > 1:
            raise SeveralObjectsFoundException

        edit_stmt = (
            update(self.model)
            .filter_by(**filter_by)
            .values(**data.model_dump(exclude_unset=exclude_unset))
        )
        await self.session.execute(edit_stmt)

    async def delete(self, **filter_by):
        delete_stmt = delete(self.model).filter_by(**filter_by)
        await self.session.execute(delete_stmt)


