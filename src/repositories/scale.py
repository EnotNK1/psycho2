from src.models import ScaleOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import ScaleDataMapper


class ScalesRepository(BaseRepository):
    model = ScaleOrm
    mapper = ScaleDataMapper

    async def get_filtered(self, *filters, **filtered_by):
        from sqlalchemy import select

        result = await self.session.execute(
            select(self.model)
            .filter(*filters)
            .filter_by(**filtered_by)
            .order_by(self.model.position, self.model.id)
        )
        return [
            self.mapper.map_to_domain_entity(item) for item in result.scalars().all()
        ]
