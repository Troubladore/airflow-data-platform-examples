from datetime import datetime
from enum import Enum

# Removed mixin import to avoid table discovery conflicts
from sqlalchemy import TIMESTAMP, Column, text
from sqlmodel import Field, SQLModel


class MPAARating(str, Enum):
    """MPAA film ratings (bronze layer copy)."""

    G = "G"
    PG = "PG"
    PG_13 = "PG-13"
    R = "R"
    NC_17 = "NC-17"


class BronzeFilm(SQLModel, table=True):
    """Bronze layer film table (br__pagila__public.film)."""

    __tablename__ = "film"
    __table_args__ = {"schema": "br__pagila__public"}

    # Source fields (no foreign key constraints in bronze)
    film_id: int = Field(primary_key=True)
    title: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    release_year: int | None = Field(default=None, nullable=True)
    language_id: int = Field(nullable=False)  # No FK constraint
    original_language_id: int | None = Field(
        default=None, nullable=True
    )  # No FK constraint
    rental_duration: int = Field(default=3, nullable=False)
    rental_rate: float = Field(default=4.99, nullable=False)
    length: int | None = Field(default=None, nullable=True)
    replacement_cost: float = Field(default=19.99, nullable=False)
    rating: str | None = Field(default="G", nullable=True)  # Store as string in bronze
    source_last_update: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False)
    )

    # Bronze audit fields:
    br_load_time: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("now()"),
        )
    )
    br_source_table: str = Field(default="public.film", nullable=False)
    br_batch_id: str = Field(nullable=False)
    br_is_current: bool = Field(default=True, nullable=False)
    br_record_hash: str = Field(nullable=False)
