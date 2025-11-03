"""
Test Customer Bronze Model using TDD approach

Tests that the Customer Bronze model properly uses the framework's BronzeMetadata
and correctly represents the Pagila customer table structure.
"""

import sys
import pytest
from datetime import datetime, date

# Add framework to path for imports
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import create_engine, Session, select
from sqlalchemy_utils import create_database, drop_database, database_exists
from sqlmodel_framework.base.models import BronzeMetadata

# Import the model we're testing
from bronze_datakits_pagila.models.customer import CustomerBronze


class TestCustomerBronzeModel:
    """Test Customer Bronze model implementation"""

    def test_customer_bronze_inherits_from_framework(self):
        """Customer Bronze model should inherit from BronzeMetadata"""
        assert issubclass(CustomerBronze, BronzeMetadata)

    def test_customer_bronze_has_source_fields(self):
        """Customer Bronze model should have all source Pagila fields"""
        customer = CustomerBronze(
            # Source fields from Pagila
            customer_id=1,
            store_id=1,
            first_name="Alice",
            last_name="Johnson",
            email="alice@example.com",
            address_id=5,
            active=True,
            create_date=date.today(),
            last_update=datetime.now(),
            # Bronze metadata fields (required from framework)
            bronze_source_system="pagila_kerberos",
            bronze_source_table="customer",
            bronze_source_host="sqlpg.eruditis.lab"
        )

        # Verify source fields
        assert customer.customer_id == 1
        assert customer.store_id == 1
        assert customer.first_name == "Alice"
        assert customer.last_name == "Johnson"
        assert customer.email == "alice@example.com"
        assert customer.address_id == 5
        assert customer.active is True
        assert isinstance(customer.create_date, date)
        assert isinstance(customer.last_update, datetime)

    def test_customer_bronze_has_metadata_fields(self):
        """Customer Bronze model should have all Bronze metadata fields from framework"""
        customer = CustomerBronze(
            customer_id=1,
            store_id=1,
            first_name="Bob",
            last_name="Smith",
            address_id=10,
            active=True,
            create_date=date.today(),
            last_update=datetime.now(),
            bronze_source_system="pagila_kerberos",
            bronze_source_table="customer",
            bronze_source_host="sqlpg.eruditis.lab",
            bronze_extraction_method="incremental"
        )

        # Verify framework metadata fields are present
        assert customer.bronze_source_system == "pagila_kerberos"
        assert customer.bronze_source_table == "customer"
        assert customer.bronze_source_host == "sqlpg.eruditis.lab"
        assert customer.bronze_extraction_method == "incremental"
        assert hasattr(customer, 'bronze_load_timestamp')

    def test_customer_bronze_table_configuration(self):
        """Customer Bronze model should have correct table configuration"""
        # Verify table is configured
        assert CustomerBronze.__tablename__ == "bronze_customer"
        assert CustomerBronze.__table_args__["schema"] == "bronze"

    def test_customer_bronze_handles_optional_email(self):
        """Customer Bronze model should handle optional email field"""
        # Customer without email
        customer = CustomerBronze(
            customer_id=2,
            store_id=1,
            first_name="Charlie",
            last_name="Brown",
            address_id=7,
            active=False,
            create_date=date.today(),
            last_update=datetime.now(),
            bronze_source_system="pagila_kerberos",
            bronze_source_table="customer",
            bronze_source_host="sqlpg.eruditis.lab"
        )

        # Email should be None when not provided
        assert customer.email is None
        assert customer.active is False

    def test_customer_bronze_persistence(self):
        """Customer Bronze model should persist to database correctly"""
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
            CustomerBronze.metadata.create_all(engine)

            # Create and save a customer
            with Session(engine) as session:
                customer = CustomerBronze(
                    customer_id=1,
                    store_id=2,
                    first_name="Test",
                    last_name="Customer",
                    email="test@example.com",
                    address_id=42,
                    active=True,
                    create_date=date(2024, 1, 1),
                    last_update=datetime.now(),
                    bronze_source_system="pagila_test",
                    bronze_source_table="customer",
                    bronze_source_host="test.host"
                )
                session.add(customer)
                session.commit()

                # Retrieve and verify
                retrieved = session.exec(
                    select(CustomerBronze).where(CustomerBronze.customer_id == 1)
                ).first()

                assert retrieved is not None
                assert retrieved.first_name == "Test"
                assert retrieved.last_name == "Customer"
                assert retrieved.email == "test@example.com"
                assert retrieved.store_id == 2
                assert retrieved.active is True
                assert retrieved.bronze_source_system == "pagila_test"

        finally:
            # Clean up
            engine.dispose()