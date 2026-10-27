import uuid
from src.database import Base
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column


class ClientsOrm(Base):
    __tablename__ = "clients"
    __table_args__ = (
        UniqueConstraint("client_id", "mentor_id", name="uq_clients_pair"),
        Index("ix_clients_lookup", "mentor_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    mentor_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    text: Mapped[str]
    status: Mapped[bool]
