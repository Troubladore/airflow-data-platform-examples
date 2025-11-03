"""
Test Film Bronze Model using TDD approach

Tests that the Film Bronze model properly uses the framework's BronzeMetadata
and correctly represents the Pagila film table structure.
"""

import sys
import pytest
from datetime import datetime
from decimal import Decimal

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import create_engine, Session, select
from sqlalchemy_utils import create_database, drop_database, database_exists
from sqlmodel_framework.base.models import BronzeMetadata

# Import the model we're about to create (this will fail initially - RED phase)
from bronze_datakits_pagila.models.film import FilmBronze


class TestFilmBronzeModel:
    """Test Film Bronze model implementation"""

    def test_film_bronze_inherits_from_framework(self):
        """Film Bronze model should inherit from BronzeMetadata"""
        # Verify FilmBronze inherits from BronzeMetadata
        assert issubclass(FilmBronze, BronzeMetadata)

    def test_film_bronze_has_source_fields(self):
        """Film Bronze model should have all source Pagila fields"""
        # Create an instance to test field presence
        film = FilmBronze(
            # Source fields from Pagila
            film_id=1,
            title="Test Film",
            description="A test film description",
            release_year=2024,
            language_id=1,
            original_language_id=None,
            rental_duration=3,
            rental_rate=4.99,
            length=120,
            replacement_cost=19.99,
            rating="PG",
            last_update=datetime.now(),
            special_features="Deleted Scenes,Behind the Scenes",
            # Bronze metadata fields (required from framework)
            bronze_source_system="pagila_kerberos",
            bronze_source_table="film",
            bronze_source_host="sqlpg.eruditis.lab"
        )

        # Verify source fields
        assert film.film_id == 1
        assert film.title == "Test Film"
        assert film.description == "A test film description"
        assert film.release_year == 2024
        assert film.language_id == 1
        assert film.original_language_id is None
        assert film.rental_duration == 3
        assert film.rental_rate == 4.99
        assert film.length == 120
        assert film.replacement_cost == 19.99
        assert film.rating == "PG"
        assert film.special_features == "Deleted Scenes,Behind the Scenes"
        # fulltext field is EXCLUDED (tsvector, derived field)

    def test_film_bronze_has_metadata_fields(self):
        """Film Bronze model should have all Bronze metadata fields from framework"""
        film = FilmBronze(
            film_id=1,
            title="Test Film",
            language_id=1,
            last_update=datetime.now(),
            bronze_source_system="pagila_kerberos",
            bronze_source_table="film",
            bronze_source_host="sqlpg.eruditis.lab",
            bronze_extraction_method="full_snapshot"
        )

        # Verify framework metadata fields are present
        assert film.bronze_source_system == "pagila_kerberos"
        assert film.bronze_source_table == "film"
        assert film.bronze_source_host == "sqlpg.eruditis.lab"
        assert film.bronze_extraction_method == "full_snapshot"
        assert hasattr(film, 'bronze_load_timestamp')

    def test_film_bronze_table_configuration(self):
        """Film Bronze model should have correct table configuration"""
        # Verify table is configured
        assert FilmBronze.__tablename__ == "bronze_film"
        assert FilmBronze.__table_args__["schema"] == "bronze"

    def test_film_bronze_handles_optional_fields(self):
        """Film Bronze model should handle optional/nullable fields correctly"""
        # Minimal film with only required fields
        film = FilmBronze(
            film_id=2,
            title="Minimal Film",
            language_id=1,
            last_update=datetime.now(),
            bronze_source_system="pagila_kerberos",
            bronze_source_table="film",
            bronze_source_host="sqlpg.eruditis.lab"
        )

        # Optional fields should have appropriate defaults or be None
        assert film.description is None
        assert film.release_year is None
        assert film.original_language_id is None
        assert film.rental_duration == 3  # Default from Pagila
        assert film.rental_rate == 4.99  # Default from Pagila
        assert film.length is None
        assert film.replacement_cost == 19.99  # Default from Pagila
        assert film.rating == "G"  # Default rating
        assert film.special_features is None
        # fulltext field is EXCLUDED from Bronze model

    def test_film_bronze_persistence(self):
        """Film Bronze model should persist to database correctly"""
        # Create a test database (NOT the Pagila database!)
        test_db_url = "postgresql://postgres:postgres@localhost:5433/test_bronze"
        admin_db_url = "postgresql://postgres:postgres@localhost:5433/postgres"

        # Create test database if it doesn't exist
        if not database_exists(test_db_url):
            create_database(test_db_url)

        # Use the test database
        engine = create_engine(test_db_url)

        try:
            # Create the bronze schema
            with engine.begin() as conn:
                conn.exec_driver_sql("DROP SCHEMA IF EXISTS bronze CASCADE")
                conn.exec_driver_sql("CREATE SCHEMA bronze")

            # Create the table
            FilmBronze.metadata.create_all(engine)

            # Create and save a film
            with Session(engine) as session:
                film = FilmBronze(
                    film_id=1,
                    title="Persistence Test Film",
                    description="Testing database persistence",
                    release_year=2024,
                    language_id=1,
                    rental_duration=5,
                    rental_rate=3.99,
                    length=90,
                    replacement_cost=24.99,
                    rating="R",
                    last_update=datetime.now(),
                    special_features="Trailers,Commentary",
                    bronze_source_system="pagila_test",
                    bronze_source_table="film",
                    bronze_source_host="test.host"
                )
                session.add(film)
                session.commit()

                # Retrieve and verify
                retrieved = session.exec(
                    select(FilmBronze).where(FilmBronze.film_id == 1)
                ).first()

                assert retrieved is not None
                assert retrieved.title == "Persistence Test Film"
                assert retrieved.rental_rate == 3.99
                assert retrieved.bronze_source_system == "pagila_test"

        finally:
            # Clean up
            engine.dispose()