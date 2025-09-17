

from sqlalchemy.orm import mapped_column, Mapped

from src.database import Base


class EmojiOrm(Base):
    __tablename__ = "emojis"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str]


