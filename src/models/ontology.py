import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from src.database import Base
import uuid


class OntologyEntryOrm(Base):
    __tablename__ = "ontology_entry"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    type: Mapped[str]
    created_at: Mapped[datetime.datetime]
    destination_id: Mapped[uuid.UUID]
    link_to_picture: Mapped[str] = mapped_column(nullable=True)
    user_id: Mapped[uuid.UUID]

