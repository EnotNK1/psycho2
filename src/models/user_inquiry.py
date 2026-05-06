from sqlalchemy import Table, Column, ForeignKey
from src.database import Base

user_inquiry = Table(
    "user_inquiry",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("inquiry_id", ForeignKey("inquiry.id"), primary_key=True)
)