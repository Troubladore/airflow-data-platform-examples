from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class Language(SQLModel, table=True):
    """Pagila language table (public.language)."""

    __tablename__ = "language"
    __table_args__ = {"schema": "public"}

    language_id: int = Field(primary_key=True)
    name: str = Field(nullable=False, max_length=20)
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )