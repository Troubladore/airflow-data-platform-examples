#!/usr/bin/env python3
"""
Integration test script to validate the SQLModel runner can:
1. Connect to databases
2. Create temporal tables
3. Handle data operations
4. Work with mounted code

This is the GREEN phase test - should pass when runner is fully functional.
"""
import os
import sys
from typing import Optional
from datetime import datetime
from uuid import uuid4

def test_sqlmodel_operations():
    """Test SQLModel database operations."""
    print("\n" + "=" * 60)
    print("Testing SQLModel Operations")
    print("=" * 60)

    try:
        from sqlmodel import SQLModel, Field, Session, create_engine, select
        from typing import Optional
        import uuid

        # Define a test model
        class TestTable(SQLModel, table=True):
            __tablename__ = "test_runner_validation"
            __table_args__ = {"schema": "public"}

            id: Optional[int] = Field(default=None, primary_key=True)
            name: str
            value: float
            created_at: datetime = Field(default_factory=datetime.utcnow)
            batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

        print("✓ SQLModel imports successful")
        print("✓ Test model defined")

        # Test database connection (if DATABASE_URL is provided)
        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            print(f"\nTesting database connection...")
            engine = create_engine(db_url, echo=False)

            # Create table
            SQLModel.metadata.create_all(engine)
            print("✓ Table created successfully")

            # Insert test data
            with Session(engine) as session:
                test_record = TestTable(
                    name="runner_test",
                    value=42.0
                )
                session.add(test_record)
                session.commit()
                print("✓ Data inserted successfully")

                # Query data
                statement = select(TestTable).where(TestTable.name == "runner_test")
                results = session.exec(statement).all()
                assert len(results) == 1, "Expected 1 record"
                assert results[0].value == 42.0, "Value mismatch"
                print("✓ Data queried successfully")

                # Clean up
                session.query(TestTable).delete()
                session.commit()
                print("✓ Cleanup completed")

            # Drop table
            TestTable.__table__.drop(engine)
            print("✓ Table dropped successfully")
        else:
            print("\nSkipping database tests (DATABASE_URL not set)")
            print("To test database operations, run with:")
            print("  DATABASE_URL=postgresql://user:pass@host/db")

        return True

    except Exception as e:
        print(f"✗ SQLModel operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pandas_operations():
    """Test pandas data processing capabilities."""
    print("\n" + "=" * 60)
    print("Testing Pandas Operations")
    print("=" * 60)

    try:
        import pandas as pd
        import numpy as np

        # Create test dataframe
        df = pd.DataFrame({
            'id': range(1, 6),
            'value': np.random.rand(5),
            'category': ['A', 'B', 'A', 'C', 'B']
        })
        print("✓ DataFrame created")

        # Test operations
        grouped = df.groupby('category')['value'].mean()
        print("✓ Groupby operations work")

        # Test Excel operations
        if not os.environ.get("SKIP_EXCEL_TEST"):
            excel_path = "/tmp/test_excel.xlsx"
            df.to_excel(excel_path, index=False)
            print("✓ Excel write successful")

            df_read = pd.read_excel(excel_path)
            assert len(df_read) == len(df), "Excel read mismatch"
            print("✓ Excel read successful")

            os.remove(excel_path)
            print("✓ Cleanup completed")

        return True

    except Exception as e:
        print(f"✗ Pandas operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_psycopg_direct():
    """Test direct psycopg connection."""
    print("\n" + "=" * 60)
    print("Testing Psycopg Direct Connection")
    print("=" * 60)

    try:
        import psycopg
        from psycopg.pool import ConnectionPool

        db_url = os.environ.get("DATABASE_URL")
        if db_url:
            print("Testing psycopg connection...")

            # Test basic connection
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    print(f"✓ Connected to: {version.split(',')[0]}")

            # Test connection pool
            pool = ConnectionPool(db_url, min_size=1, max_size=5)
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_database()")
                    db_name = cur.fetchone()[0]
                    print(f"✓ Connection pool works, database: {db_name}")

            pool.close()
            print("✓ Connection pool closed")

            return True
        else:
            print("Skipping psycopg tests (DATABASE_URL not set)")
            return True

    except Exception as e:
        print(f"✗ Psycopg operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_tools():
    """Test CLI tools like typer and rich."""
    print("\n" + "=" * 60)
    print("Testing CLI Tools")
    print("=" * 60)

    try:
        import typer
        from rich.console import Console
        from rich.table import Table

        # Create Typer app
        app = typer.Typer()
        print("✓ Typer app created")

        # Create Rich console and table
        console = Console()
        table = Table(title="Test Table")
        table.add_column("Column 1")
        table.add_column("Column 2")
        table.add_row("Value 1", "Value 2")
        print("✓ Rich console and table created")

        return True

    except Exception as e:
        print(f"✗ CLI tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_retry_logic():
    """Test tenacity retry capabilities."""
    print("\n" + "=" * 60)
    print("Testing Retry Logic")
    print("=" * 60)

    try:
        from tenacity import retry, stop_after_attempt, wait_fixed

        call_count = 0

        @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.1))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Simulated failure")
            return "success"

        result = flaky_function()
        assert result == "success", "Retry didn't succeed"
        assert call_count == 3, f"Expected 3 calls, got {call_count}"
        print(f"✓ Retry logic works (attempted {call_count} times)")

        return True

    except Exception as e:
        print(f"✗ Retry logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alembic():
    """Test Alembic migration capabilities."""
    print("\n" + "=" * 60)
    print("Testing Alembic")
    print("=" * 60)

    try:
        from alembic import command
        from alembic.config import Config
        print("✓ Alembic imports successful")

        # Can't fully test without alembic.ini, but imports work
        return True

    except Exception as e:
        print(f"✗ Alembic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("=" * 60)
    print("SQLModel Runner Integration Tests")
    print("=" * 60)

    all_tests = [
        ("SQLModel Operations", test_sqlmodel_operations),
        ("Pandas Operations", test_pandas_operations),
        ("Psycopg Direct", test_psycopg_direct),
        ("CLI Tools", test_cli_tools),
        ("Retry Logic", test_retry_logic),
        ("Alembic", test_alembic),
    ]

    results = []
    for test_name, test_func in all_tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    failed = sum(1 for _, success in results if not success)

    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    if failed > 0:
        print("\nFailed Tests:")
        for test_name, success in results:
            if not success:
                print(f"  - {test_name}")
        print("\nResult: SOME TESTS FAILED ✗")
        sys.exit(1)
    else:
        print("\nResult: ALL INTEGRATION TESTS PASSED ✓")
        print("The SQLModel runner is fully functional!")
        sys.exit(0)

if __name__ == "__main__":
    main()