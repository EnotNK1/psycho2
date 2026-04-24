from src.repositories.base import BaseRepository
from src.models.mood_tracker import MoodTrackerOrm
from src.repositories.mappers.mappers import MoodTrackerDataMapper, UserTasksDataMapper, OntologyEntryDataMapper
from src.models.ontology import OntologyEntryOrm


class OntologyEntryRepository(BaseRepository):
    model = OntologyEntryOrm
    mapper = OntologyEntryDataMapper
