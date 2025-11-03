"""
Test Actor Bronze Model using TDD approach

Tests that the Actor Bronze model properly uses the framework's BronzeMetadata
and correctly represents the Pagila actor table structure.
"""

import sys
import pytest
from datetime import datetime

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import create_engine, Session, select
from sqlalchemy_utils import create_database, drop_database, database_exists
from sqlmodel_framework.base.models import BronzeMetadata

# Import the model we're testing
from bronze_datakits_pagila.models.actor import ActorBronze


class TestActorBronzeModel:
    """Test Actor Bronze model implementation"""

    def test_actor_bronze_inherits_from_framework(self):
        """Actor Bronze model should inherit from BronzeMetadata"""
        assert issubclass(ActorBronze, BronzeMetadata)

    def test_actor_bronze_has_source_fields(self):
        """Actor Bronze model should have all source Pagila fields"""
        actor = ActorBronze(
            # Source fields from Pagila
            actor_id=1,
            first_name="John",
            last_name="Doe",
            last_update=datetime.now(),
            # Bronze metadata fields (required from framework)
            bronze_source_system="pagila_kerberos",
            bronze_source_table="actor",
            bronze_source_host="sqlpg.eruditis.lab"
        )

        # Verify source fields
        assert actor.actor_id == 1
        assert actor.first_name == "John"
        assert actor.last_name == "Doe"
        assert isinstance(actor.last_update, datetime)

    def test_actor_bronze_has_metadata_fields(self):
        """Actor Bronze model should have all Bronze metadata fields from framework"""
        actor = ActorBronze(
            actor_id=1,
            first_name="Jane",
            last_name="Smith",
            last_update=datetime.now(),
            bronze_source_system="pagila_kerberos",
            bronze_source_table="actor",
            bronze_source_host="sqlpg.eruditis.lab",
            bronze_extraction_method="full_snapshot"
        )

        # Verify framework metadata fields are present
        assert actor.bronze_source_system == "pagila_kerberos"
        assert actor.bronze_source_table == "actor"
        assert actor.bronze_source_host == "sqlpg.eruditis.lab"
        assert actor.bronze_extraction_method == "full_snapshot"
        assert hasattr(actor, 'bronze_load_timestamp')

    def test_actor_bronze_table_configuration(self):
        """Actor Bronze model should have correct table configuration"""
        # Verify table is configured
        assert ActorBronze.__tablename__ == "bronze_actor"
        assert ActorBronze.__table_args__["schema"] == "bronze"

    def test_actor_bronze_persistence(self):
        """Actor Bronze model should persist to database correctly"""
        # Create a test database (NOT the Pagila database!)
        test_db_url = "postgresql://postgres:postgres@localhost:5433/test_bronze"

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
            ActorBronze.metadata.create_all(engine)

            # Create and save an actor
            with Session(engine) as session:
                actor = ActorBronze(
                    actor_id=1,
                    first_name="Test",
                    last_name="Actor",
                    last_update=datetime.now(),
                    bronze_source_system="pagila_test",
                    bronze_source_table="actor",
                    bronze_source_host="test.host"
                )
                session.add(actor)
                session.commit()

                # Retrieve and verify
                retrieved = session.exec(
                    select(ActorBronze).where(ActorBronze.actor_id == 1)
                ).first()

                assert retrieved is not None
                assert retrieved.first_name == "Test"
                assert retrieved.last_name == "Actor"
                assert retrieved.bronze_source_system == "pagila_test"

        finally:
            # Clean up
            engine.dispose()