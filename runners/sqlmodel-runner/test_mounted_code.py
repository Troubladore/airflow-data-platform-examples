#!/usr/bin/env python3
"""
Test script to verify code can be mounted and executed in the runner container.
This simulates how datakit code will be mounted at runtime.
"""
import os
import sys
from sqlmodel import SQLModel, Field, Session, create_engine
from typing import Optional
from datetime import datetime


class TestModel(SQLModel, table=True):
    """Test model to verify SQLModel works correctly."""
    __tablename__ = "test_mount"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    value: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


def main():
    """Main function to test mounted code execution."""
    print("=" * 60)
    print("Mounted Code Execution Test")
    print("=" * 60)

    # Verify environment
    print(f"\nPython version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")

    # Test SQLModel
    print("\n✓ SQLModel imported successfully")
    print(f"✓ Test model defined: {TestModel.__tablename__}")

    # Test other imports
    try:
        import pandas as pd
        import psycopg
        from psycopg_pool import ConnectionPool
        import typer
        from rich import print as rprint

        print("✓ All required packages imported successfully")

        # Test pandas
        df = pd.DataFrame({'a': [1, 2, 3], 'b': [4, 5, 6]})
        print(f"✓ Pandas DataFrame created with shape: {df.shape}")

        # Test Rich
        rprint("[green]✓ Rich console works![/green]")

        print("\n" + "=" * 60)
        print("RESULT: All mounted code tests PASSED ✓")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())