#!/usr/bin/env python
"""Test script for AdventureWorksLT Bronze loader using config.yaml"""

import sys
import subprocess
from pathlib import Path
import yaml

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from bronze_datakits_adventureworkslt.loader import AdventureWorksLTBronzeLoader


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


def get_kerberos_username():
    """Extract username from Kerberos ticket"""
    try:
        result = subprocess.run(['klist'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if 'Default principal:' in line:
                    principal = line.split(':')[1].strip()
                    username = principal.split('@')[0]
                    return username
    except Exception:
        pass
    return None


def build_target_url(config):
    """Build PostgreSQL connection URL from config"""
    target = config['target']

    if target.get('use_kerberos', True):
        username = get_kerberos_username()
        if not username:
            print("ERROR: No Kerberos ticket found. Run 'kinit' first.")
            sys.exit(1)
        # Use psycopg2 with Kerberos
        return f"postgresql+psycopg2://{username}@{target['host']}:{target['port']}/{target['database']}?gssencmode=require"
    else:
        user = target.get('user')
        password = target.get('password')
        if password:
            return f"postgresql://{user}:{password}@{target['host']}:{target['port']}/{target['database']}"
        else:
            return f"postgresql://{user}@{target['host']}:{target['port']}/{target['database']}"


def main():
    print("=" * 80)
    print("AdventureWorksLT Bronze Loader Test")
    print("=" * 80)

    # Load configuration
    config = load_config()
    source = config['source']
    target = config['target']
    storage = config['storage']

    print(f"\nSource: {source['database']} on {source['host']}")
    print(f"Target: {target['database']} on {target['host']}")
    print(f"Tables to extract: {len(source['tables'])}")

    # Build target database URL
    target_url = build_target_url(config)

    # Initialize loader
    loader = AdventureWorksLTBronzeLoader(
        source_host=source['host'],
        source_database=source['database'],
        use_kerberos=source.get('use_kerberos', True),
        bronze_path=Path(storage['bronze_path']),
        target_db_url=target_url
    )

    # Load each table
    results = []
    for table_name in source['tables']:
        print(f"\n{'=' * 80}")
        print(f"Extracting: {table_name}")
        print('=' * 80)

        try:
            result = loader.load_table(table_name)
            results.append(result)

            print(f"\n✓ Successfully loaded {result['rows_loaded']} rows")
            print(f"  Files written:")
            for path in result['paths']:
                print(f"    - {path}")

        except Exception as e:
            print(f"\n✗ ERROR loading {table_name}: {e}")
            continue

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total_rows = sum(r['rows_loaded'] for r in results)
    print(f"Tables processed: {len(results)}/{len(source['tables'])}")
    print(f"Total rows loaded: {total_rows}")
    print("\nCheck your data:")
    print(f"  Database: {target['database']} on {target['host']}")
    print(f"  Schema: {target['schema']}")
    print(f"  Files: {storage['bronze_path']}")


if __name__ == "__main__":
    main()
