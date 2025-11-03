"""
Unit Tests for Error Handling in Bronze Loader

Tests error scenarios including:
- Kerberos authentication failures
- Database connection failures
- Invalid table names
- Data extraction errors
- Load failures
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import psycopg2
from sqlalchemy.exc import OperationalError, DatabaseError
import subprocess

# Add framework and package to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform-examples/bronze-datakits-pagila')

from bronze_datakits_pagila.loader import PagilaBronzeLoader


class TestKerberosFailures:
    """Test Kerberos authentication failure scenarios"""

    def test_loader_handles_missing_kerberos_ticket(self):
        """Test that loader handles missing Kerberos ticket gracefully"""
        # Arrange - Mock klist to return error (no ticket)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=1, stdout="", stderr="No credentials cache found")

            # Act - Create loader with Kerberos
            loader = PagilaBronzeLoader(
                source_host="sqlpg.eruditis.lab",
                source_database="pagila",
                use_kerberos=True
            )

            # Assert - _get_kerberos_username should return None
            username = loader._get_kerberos_username()
            assert username is None

    def test_loader_handles_expired_kerberos_ticket(self):
        """Test that loader detects expired Kerberos tickets"""
        # Arrange - Mock klist with expired ticket output
        with patch('subprocess.run') as mock_run:
            # klist returns 0 but no valid principal
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Ticket cache: FILE:/tmp/krb5cc_1000\n",
                stderr=""
            )

            # Act
            loader = PagilaBronzeLoader(
                source_host="sqlpg.eruditis.lab",
                source_database="pagila",
                use_kerberos=True
            )

            # Assert - Should return None when no principal found
            username = loader._get_kerberos_username()
            assert username is None

    def test_loader_extracts_username_from_valid_ticket(self):
        """Test that loader correctly extracts username from valid Kerberos ticket"""
        # Arrange - Mock klist with valid ticket
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="Default principal: emaynard@ERUDITIS.LAB\n",
                stderr=""
            )

            # Act
            loader = PagilaBronzeLoader(
                source_host="sqlpg.eruditis.lab",
                source_database="pagila",
                use_kerberos=True
            )
            username = loader._get_kerberos_username()

            # Assert
            assert username == "emaynard"

    def test_loader_handles_klist_command_not_found(self):
        """Test that loader handles missing klist command"""
        # Arrange - Mock klist to raise FileNotFoundError
        with patch('subprocess.run', side_effect=FileNotFoundError("klist not found")):
            # Act
            loader = PagilaBronzeLoader(
                source_host="sqlpg.eruditis.lab",
                source_database="pagila",
                use_kerberos=True
            )
            username = loader._get_kerberos_username()

            # Assert - Should return None gracefully
            assert username is None


class TestDatabaseConnectionFailures:
    """Test database connection failure scenarios"""

    def test_extract_handles_connection_refused(self):
        """Test that extract_table handles connection refused errors"""
        # Arrange - Mock create_engine to raise connection error
        with patch('bronze_datakits_pagila.loader.create_engine') as mock_engine:
            mock_engine.side_effect = OperationalError(
                "Connection refused",
                params=None,
                orig=Exception("Connection refused")
            )

            loader = PagilaBronzeLoader(
                source_host="invalid.host.lab",
                source_database="pagila",
                use_kerberos=False
            )

            # Act & Assert - Should raise OperationalError
            with pytest.raises(OperationalError):
                loader.extract_table("language")

    def test_extract_handles_authentication_failure(self):
        """Test that extract_table handles authentication failures"""
        # Arrange - Mock pandas.read_sql to raise auth error
        with patch('pandas.read_sql') as mock_read:
            mock_read.side_effect = OperationalError(
                "GSSAPI authentication failed",
                params=None,
                orig=Exception("GSSAPI error")
            )

            with patch('bronze_datakits_pagila.loader.create_engine'):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="pagila",
                    use_kerberos=True
                )

                # Act & Assert
                with pytest.raises(OperationalError, match="GSSAPI"):
                    loader.extract_table("language")

    def test_extract_handles_database_not_found(self):
        """Test that extract_table handles non-existent database"""
        # Arrange - Mock read_sql to raise error
        with patch('pandas.read_sql') as mock_read:
            mock_read.side_effect = DatabaseError(
                "database \"nonexistent\" does not exist",
                params=None,
                orig=Exception("database error")
            )

            with patch('bronze_datakits_pagila.loader.create_engine'):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="nonexistent",
                    use_kerberos=False
                )

                # Act & Assert
                with pytest.raises(DatabaseError):
                    loader.extract_table("language")

    def test_extract_handles_network_timeout(self):
        """Test that extract_table handles network timeouts"""
        # Arrange - Mock connection to timeout
        with patch('bronze_datakits_pagila.loader.create_engine') as mock_create:
            mock_create.side_effect = OperationalError(
                "timeout expired",
                params=None,
                orig=Exception("timeout")
            )

            loader = PagilaBronzeLoader(
                source_host="sqlpg.eruditis.lab",
                source_database="pagila",
                use_kerberos=False
            )

            # Act & Assert
            with pytest.raises(OperationalError, match="timeout"):
                loader.extract_table("language")


class TestInvalidTableHandling:
    """Test handling of invalid table names and missing models"""

    def test_load_table_raises_on_invalid_table_name(self):
        """Test that load_table raises ValueError for invalid table names"""
        # Arrange
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Mock extract_table to return a dataframe
        with patch.object(loader, 'extract_table') as mock_extract:
            mock_extract.return_value = Mock()

            with patch.object(loader, 'add_bronze_metadata') as mock_metadata:
                mock_metadata.return_value = Mock()

                # Act & Assert - Should raise ValueError for unmapped table
                with pytest.raises(ValueError, match="No model found"):
                    loader.load_table("invalid_table_name")

    def test_extract_handles_nonexistent_table(self):
        """Test that extract_table handles table that doesn't exist in database"""
        # Arrange - Mock read_sql to raise error for non-existent table
        with patch('pandas.read_sql') as mock_read:
            mock_read.side_effect = DatabaseError(
                "relation \"nonexistent_table\" does not exist",
                params=None,
                orig=Exception("table error")
            )

            with patch('bronze_datakits_pagila.loader.create_engine'):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="pagila",
                    use_kerberos=False
                )

                # Act & Assert
                with pytest.raises(DatabaseError, match="does not exist"):
                    loader.extract_table("nonexistent_table")


class TestDataExtractionErrors:
    """Test data extraction error scenarios"""

    def test_extract_handles_query_timeout(self):
        """Test that extract handles query timeout on large table"""
        # Arrange - Mock read_sql to raise timeout
        with patch('pandas.read_sql') as mock_read:
            mock_read.side_effect = OperationalError(
                "canceling statement due to statement timeout",
                params=None,
                orig=Exception("timeout")
            )

            with patch('bronze_datakits_pagila.loader.create_engine'):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="pagila",
                    use_kerberos=False
                )

                # Act & Assert
                with pytest.raises(OperationalError, match="timeout"):
                    loader.extract_table("payment")

    def test_extract_handles_out_of_memory(self):
        """Test that extract handles out of memory errors on huge tables"""
        # Arrange - Mock read_sql to raise MemoryError
        with patch('pandas.read_sql') as mock_read:
            mock_read.side_effect = MemoryError("Cannot allocate memory")

            with patch('bronze_datakits_pagila.loader.create_engine'):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="pagila",
                    use_kerberos=False
                )

                # Act & Assert
                with pytest.raises(MemoryError):
                    loader.extract_table("payment")

    def test_extract_disposes_engine_on_error(self):
        """Test that extract_table properly disposes engine even on error"""
        # Arrange - Mock engine and connection
        with patch('bronze_datakits_pagila.loader.create_engine') as mock_create:
            mock_engine = Mock()
            mock_create.return_value = mock_engine

            # Make read_sql raise an error
            with patch('pandas.read_sql', side_effect=Exception("Query failed")):
                loader = PagilaBronzeLoader(
                    source_host="sqlpg.eruditis.lab",
                    source_database="pagila",
                    use_kerberos=False
                )

                # Act & Assert
                with pytest.raises(Exception):
                    loader.extract_table("language")

                # Verify dispose was called in finally block
                mock_engine.dispose.assert_called_once()


class TestLoadFailures:
    """Test load operation failure scenarios"""

    def test_load_handles_target_database_connection_failure(self):
        """Test that load_table handles target database connection failures"""
        # Arrange
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False,
            target_db_url="postgresql://invalid:5433/bronze"
        )

        # Mock successful extract
        with patch.object(loader, 'extract_table') as mock_extract:
            mock_extract.return_value = Mock()

            with patch.object(loader, 'add_bronze_metadata') as mock_metadata:
                mock_metadata.return_value = Mock()

                # Mock create_engine for target to fail
                with patch('bronze_datakits_pagila.loader.create_engine') as mock_create:
                    mock_create.side_effect = OperationalError(
                        "could not connect to server",
                        params=None,
                        orig=Exception("connection error")
                    )

                    # Act & Assert
                    with pytest.raises(OperationalError):
                        loader.load_table("language")

    def test_load_disposes_target_engine_on_error(self):
        """Test that load_table disposes target engine even on error"""
        # Arrange
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False,
            target_db_url="postgresql://postgres:postgres@localhost:5433/bronze"
        )

        # Mock successful extract and metadata
        with patch.object(loader, 'extract_table'):
            with patch.object(loader, 'add_bronze_metadata'):
                with patch('bronze_datakits_pagila.loader.create_engine') as mock_create:
                    mock_engine = Mock()
                    mock_create.return_value = mock_engine

                    # Mock Session to raise error
                    with patch('bronze_datakits_pagila.loader.Session', side_effect=Exception("Session error")):
                        # Mock write_bronze to avoid errors
                        with patch.object(loader, 'write_bronze'):
                            # Act & Assert
                            with pytest.raises(Exception):
                                loader.load_table("language")

                            # Verify dispose was called
                            mock_engine.dispose.assert_called_once()
