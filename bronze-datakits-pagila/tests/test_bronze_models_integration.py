"""
Integration Test for All Bronze Models

Tests that all Bronze models work together correctly with the framework,
can be created in the same database, and handle relationships properly.
"""

import sys
import pytest
from datetime import datetime, date

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import create_engine, Session, select, SQLModel
from sqlalchemy_utils import create_database, drop_database, database_exists
from sqlmodel_framework.base.models import BronzeMetadata

# Import all Bronze models
from bronze_datakits_pagila.models import FilmBronze, ActorBronze, CustomerBronze


class TestBronzeModelsIntegration:
    """Test all Bronze models working together"""

    @pytest.fixture(scope="class")
    def test_engine(self):
        """Create a test database engine for all integration tests"""
        test_db_url = "postgresql://postgres:postgres@localhost:5433/test_bronze_integration"

        # Create test database if it doesn't exist
        if database_exists(test_db_url):
            drop_database(test_db_url)
        create_database(test_db_url)

        # Create engine
        engine = create_engine(test_db_url)

        # Create bronze schema
        with engine.begin() as conn:
            conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS bronze")

        # Create all tables
        SQLModel.metadata.create_all(engine)

        yield engine

        # Cleanup
        engine.dispose()
        drop_database(test_db_url)

    def test_all_models_inherit_from_bronze_metadata(self):
        """All Bronze models should inherit from BronzeMetadata"""
        assert issubclass(FilmBronze, BronzeMetadata)
        assert issubclass(ActorBronze, BronzeMetadata)
        assert issubclass(CustomerBronze, BronzeMetadata)

    def test_all_models_have_consistent_schema(self):
        """All Bronze models should use the same schema"""
        assert FilmBronze.__table_args__["schema"] == "bronze"
        assert ActorBronze.__table_args__["schema"] == "bronze"
        assert CustomerBronze.__table_args__["schema"] == "bronze"

    def test_create_all_models_in_same_session(self, test_engine):
        """Should be able to create all model instances in the same session"""
        with Session(test_engine) as session:
            # Create instances of each model
            film = FilmBronze(
                film_id=1,
                title="Integration Test Film",
                language_id=1,
                last_update=datetime.now(),
                bronze_source_system="integration_test",
                bronze_source_table="film",
                bronze_source_host="test.host"
            )

            actor = ActorBronze(
                actor_id=1,
                first_name="Integration",
                last_name="Actor",
                last_update=datetime.now(),
                bronze_source_system="integration_test",
                bronze_source_table="actor",
                bronze_source_host="test.host"
            )

            customer = CustomerBronze(
                customer_id=1,
                store_id=1,
                first_name="Integration",
                last_name="Customer",
                address_id=1,
                active=True,
                create_date=date.today(),
                last_update=datetime.now(),
                bronze_source_system="integration_test",
                bronze_source_table="customer",
                bronze_source_host="test.host"
            )

            # Add all to session
            session.add(film)
            session.add(actor)
            session.add(customer)
            session.commit()

            # Verify all were saved
            assert session.exec(select(FilmBronze).where(FilmBronze.film_id == 1)).first() is not None
            assert session.exec(select(ActorBronze).where(ActorBronze.actor_id == 1)).first() is not None
            assert session.exec(select(CustomerBronze).where(CustomerBronze.customer_id == 1)).first() is not None

    def test_bronze_metadata_consistency(self, test_engine):
        """Bronze metadata should be consistent across all models"""
        source_system = "pagila_batch_001"
        source_host = "sqlpg.eruditis.lab"
        extraction_method = "full_snapshot"

        with Session(test_engine) as session:
            # Create instances with same Bronze metadata
            film = FilmBronze(
                film_id=2,
                title="Batch Test Film",
                language_id=1,
                last_update=datetime.now(),
                bronze_source_system=source_system,
                bronze_source_table="film",
                bronze_source_host=source_host,
                bronze_extraction_method=extraction_method
            )

            actor = ActorBronze(
                actor_id=2,
                first_name="Batch",
                last_name="Actor",
                last_update=datetime.now(),
                bronze_source_system=source_system,
                bronze_source_table="actor",
                bronze_source_host=source_host,
                bronze_extraction_method=extraction_method
            )

            customer = CustomerBronze(
                customer_id=2,
                store_id=1,
                first_name="Batch",
                last_name="Customer",
                address_id=2,
                active=True,
                create_date=date.today(),
                last_update=datetime.now(),
                bronze_source_system=source_system,
                bronze_source_table="customer",
                bronze_source_host=source_host,
                bronze_extraction_method=extraction_method
            )

            session.add_all([film, actor, customer])
            session.commit()

            # Query all records with the same source system
            films = session.exec(
                select(FilmBronze).where(FilmBronze.bronze_source_system == source_system)
            ).all()
            actors = session.exec(
                select(ActorBronze).where(ActorBronze.bronze_source_system == source_system)
            ).all()
            customers = session.exec(
                select(CustomerBronze).where(CustomerBronze.bronze_source_system == source_system)
            ).all()

            # Verify consistency
            assert len(films) == 1
            assert len(actors) == 1
            assert len(customers) == 1

            assert films[0].bronze_source_host == source_host
            assert actors[0].bronze_source_host == source_host
            assert customers[0].bronze_source_host == source_host

            assert films[0].bronze_extraction_method == extraction_method
            assert actors[0].bronze_extraction_method == extraction_method
            assert customers[0].bronze_extraction_method == extraction_method

    def test_bulk_insert_performance(self, test_engine):
        """Test that bulk inserts work efficiently with Bronze models"""
        with Session(test_engine) as session:
            # Create multiple records
            films = [
                FilmBronze(
                    film_id=100 + i,
                    title=f"Bulk Film {i}",
                    language_id=1,
                    rental_rate=4.99 + (i * 0.5),
                    last_update=datetime.now(),
                    bronze_source_system="bulk_test",
                    bronze_source_table="film",
                    bronze_source_host="bulk.host"
                )
                for i in range(10)
            ]

            actors = [
                ActorBronze(
                    actor_id=100 + i,
                    first_name=f"Actor{i}",
                    last_name=f"Surname{i}",
                    last_update=datetime.now(),
                    bronze_source_system="bulk_test",
                    bronze_source_table="actor",
                    bronze_source_host="bulk.host"
                )
                for i in range(10)
            ]

            # Bulk insert
            session.add_all(films + actors)
            session.commit()

            # Verify all were inserted
            film_count = session.exec(
                select(FilmBronze).where(FilmBronze.bronze_source_system == "bulk_test")
            ).all()
            actor_count = session.exec(
                select(ActorBronze).where(ActorBronze.bronze_source_system == "bulk_test")
            ).all()

            assert len(film_count) == 10
            assert len(actor_count) == 10

    def test_timestamp_fields_auto_populate(self, test_engine):
        """Test that bronze_load_timestamp auto-populates correctly"""
        with Session(test_engine) as session:
            # Create without explicitly setting bronze_load_timestamp
            film = FilmBronze(
                film_id=999,
                title="Timestamp Test",
                language_id=1,
                last_update=datetime.now(),
                bronze_source_system="timestamp_test",
                bronze_source_table="film",
                bronze_source_host="test.host"
            )

            session.add(film)
            session.commit()
            session.refresh(film)

            # Verify timestamp was auto-populated
            assert film.bronze_load_timestamp is not None
            assert isinstance(film.bronze_load_timestamp, datetime)
            # Should be recent (within last minute)
            time_diff = datetime.now() - film.bronze_load_timestamp.replace(tzinfo=None)
            assert time_diff.total_seconds() < 60