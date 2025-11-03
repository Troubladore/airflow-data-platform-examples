#!/usr/bin/env python
"""Test script for AdventureWorksLT Bronze loader - extraction only (no DB write)"""

import sys
from pathlib import Path

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader

def main():
    print("=" * 80)
    print("AdventureWorksLT Bronze Loader Test - Extraction Only")
    print("=" * 80)

    # Initialize loader WITHOUT target database (file storage only)
    loader = AdventureWorksLTBronzeLoader(
        source_host="sql1.eruditis.lab",
        source_database="AdventureWorksLT",
        use_kerberos=True,
        target_db_url=None  # No database, just file storage
    )

    # Load ProductCategory table
    print("\nExtracting SalesLT.ProductCategory from SQL Server...")
    result = loader.load_table("SalesLT.ProductCategory")

    print("\n" + "=" * 80)
    print("Results:")
    print(f"  Table: {result['table']}")
    print(f"  Rows extracted: {result['rows_loaded']}")
    print(f"  Files written:")
    for path in result['paths']:
        print(f"    - {path}")
    print("=" * 80)

    print("\nVerify the files:")
    for path in result['paths']:
        file_path = Path(path)
        if file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  ✓ {path} ({size_kb:.2f} KB)")
        else:
            print(f"  ✗ {path} (not found)")

if __name__ == "__main__":
    main()
