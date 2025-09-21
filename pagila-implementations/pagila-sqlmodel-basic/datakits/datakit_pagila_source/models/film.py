from datetime import datetime
from enum import Enum

from sqlalchemy import (
    SMALLINT,
    TIMESTAMP,
    Column,
    ForeignKey,
    Numeric,
    text,
)
from sqlalchemy import Enum as SQLEnum
from sqlmodel import Field, SQLModel


class MPAARating(str, Enum):
    """MPAA film ratings."""

    G = "G"
    PG = "PG"
    PG_13 = "PG-13"
    R = "R"
    NC_17 = "NC-17"


class Film(SQLModel, table=True):
    """Pagila film table (public.film)."""

    __tablename__ = "film"
    __table_args__ = {"schema": "public"}

    film_id: int = Field(primary_key=True)
    title: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    release_year: int | None = Field(default=None, nullable=True)
    language_id: int = Field(
        sa_column=Column(ForeignKey("public.language.language_id"), nullable=False)
    )
    original_language_id: int | None = Field(
        sa_column=Column(ForeignKey("public.language.language_id"), nullable=True),
        default=None,
    )
    rental_duration: int = Field(
        sa_column=Column(SMALLINT, nullable=False, server_default=text("3"))
    )
    rental_rate: float = Field(
        sa_column=Column(
            Numeric(4, 2), nullable=False, server_default=text("4.99")
        )
    )
    length: int | None = Field(sa_column=Column(SMALLINT, nullable=True), default=None)
    replacement_cost: float = Field(
        sa_column=Column(
            Numeric(5, 2), nullable=False, server_default=text("19.99")
        )
    )
    rating: MPAARating | None = Field(
        sa_column=Column(
            SQLEnum(MPAARating, name="mpaa_rating"),
            nullable=True,
            server_default=text("'G'::mpaa_rating"),
        )
    )
    last_update: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
