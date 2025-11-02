#!/usr/bin/env python3
"""
Test script to validate all required imports work in the SQLModel runner image.
Following TDD approach - this script should fail initially and pass when Dockerfile is correct.
"""
import sys
import traceback
from typing import List, Tuple

def test_import(module_name: str, attribute: str = None) -> Tuple[bool, str]:
    """
    Test if a module can be imported successfully.

    Args:
        module_name: Name of the module to import
        attribute: Optional attribute to check within the module

    Returns:
        Tuple of (success, error_message)
    """
    try:
        module = __import__(module_name)
        if attribute:
            # Navigate through nested module path
            components = module_name.split('.')
            for comp in components[1:]:
                module = getattr(module, comp)
            # Check for the attribute
            getattr(module, attribute)
        return True, ""
    except ImportError as e:
        return False, f"ImportError: {e}"
    except AttributeError as e:
        return False, f"AttributeError: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"

def test_kerberos_libraries() -> Tuple[bool, str]:
    """Test if Kerberos libraries are available at system level."""
    import subprocess
    try:
        result = subprocess.run(['which', 'kinit'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "kinit not found in PATH"

        result = subprocess.run(['which', 'klist'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "klist not found in PATH"

        # Check if krb5.conf exists
        import os
        if not os.path.exists('/etc/krb5.conf'):
            return False, "/etc/krb5.conf not found"

        return True, ""
    except Exception as e:
        return False, f"Error checking Kerberos: {e}"

def test_postgresql_client() -> Tuple[bool, str]:
    """Test if PostgreSQL client is available."""
    import subprocess
    try:
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        if result.returncode != 0:
            return False, "psql not found in PATH"
        return True, ""
    except Exception as e:
        return False, f"Error checking PostgreSQL client: {e}"

def main():
    """Run all import tests and report results."""
    print("=" * 60)
    print("SQLModel Runner Import Validation")
    print("=" * 60)

    # Define all required imports
    required_imports = [
        # Core Framework
        ("sqlmodel", "SQLModel"),
        ("sqlmodel", "Field"),
        ("sqlmodel", "Session"),
        ("pydantic", "BaseModel"),
        ("pydantic_settings", "BaseSettings"),

        # Database Drivers
        ("psycopg", "connect"),
        ("psycopg_pool", "ConnectionPool"),  # Note: underscore not dot
        ("pymssql", None),  # SQL Server driver

        # Data Processing
        ("pandas", "DataFrame"),
        ("numpy", "array"),
        ("openpyxl", None),

        # Utilities
        ("dotenv", "load_dotenv"),
        ("typer", "Typer"),
        ("rich", "print"),
        ("rich.console", "Console"),
        ("rich.table", "Table"),
        ("tenacity", "retry"),

        # Database Migrations
        ("alembic.command", None),
        ("alembic.config", "Config"),

        # Monitoring/Logging
        ("structlog", "get_logger"),
        ("prometheus_client", "Counter"),
        ("prometheus_client", "Histogram"),
    ]

    failed_tests = []
    passed_tests = []

    print("\nTesting Python Package Imports:")
    print("-" * 40)

    for module_info in required_imports:
        if len(module_info) == 2:
            module_name, attribute = module_info
        else:
            module_name = module_info[0]
            attribute = None

        success, error = test_import(module_name, attribute)

        if success:
            status = "✓ PASS"
            passed_tests.append(module_name)
        else:
            status = "✗ FAIL"
            failed_tests.append((module_name, error))

        display_name = f"{module_name}"
        if attribute:
            display_name += f".{attribute}"

        print(f"{status}: {display_name:40}")
        if not success:
            print(f"       {error}")

    print("\nTesting System Libraries:")
    print("-" * 40)

    # Test Kerberos
    success, error = test_kerberos_libraries()
    if success:
        print("✓ PASS: Kerberos libraries")
        passed_tests.append("kerberos")
    else:
        print("✗ FAIL: Kerberos libraries")
        print(f"       {error}")
        failed_tests.append(("kerberos", error))

    # Test PostgreSQL client
    success, error = test_postgresql_client()
    if success:
        print("✓ PASS: PostgreSQL client")
        passed_tests.append("postgresql-client")
    else:
        print("✗ FAIL: PostgreSQL client")
        print(f"       {error}")
        failed_tests.append(("postgresql-client", error))

    # Test environment variables
    print("\nTesting Environment Variables:")
    print("-" * 40)

    import os
    required_env_vars = [
        ("PYTHONPATH", "/app/src:/app/lib"),
        ("KRB5_CONFIG", "/etc/krb5.conf"),
        ("KRB5CCNAME", "/var/krb5/cache/ccache")
    ]

    for var_name, expected_value in required_env_vars:
        actual_value = os.environ.get(var_name)
        if actual_value == expected_value:
            print(f"✓ PASS: {var_name} = {actual_value}")
            passed_tests.append(f"env:{var_name}")
        else:
            print(f"✗ FAIL: {var_name}")
            print(f"       Expected: {expected_value}")
            print(f"       Actual: {actual_value}")
            failed_tests.append((f"env:{var_name}", f"Expected {expected_value}, got {actual_value}"))

    # Test mount points
    print("\nTesting Mount Points:")
    print("-" * 40)

    required_dirs = [
        "/app/src",
        "/app/config",
        "/app/lib",
        "/var/krb5/cache"
    ]

    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"✓ PASS: {dir_path} exists")
            passed_tests.append(f"dir:{dir_path}")
        else:
            print(f"✗ FAIL: {dir_path} not found")
            failed_tests.append((f"dir:{dir_path}", "Directory not found"))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {len(passed_tests)}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed Tests:")
        for test_name, error in failed_tests:
            print(f"  - {test_name}: {error}")
        print("\nResult: FAIL ✗")
        sys.exit(1)
    else:
        print("\nResult: ALL TESTS PASSED ✓")
        print("The SQLModel runner image is correctly configured!")
        sys.exit(0)

if __name__ == "__main__":
    main()