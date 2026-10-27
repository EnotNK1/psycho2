from src.models.clients import ClientsOrm
from src.repositories.base import BaseRepository
from src.repositories.mappers.mappers import ClientsDataMapper


class ClientsRepository(BaseRepository):
    model = ClientsOrm
    mapper = ClientsDataMapper

    # async def get_all(self):
    #     query = select(self.model)
    #     result = await self.session.execute(query)
    #     return [self.mapper.map_to_domain_entity(model) for model in result.scalars().all()]
