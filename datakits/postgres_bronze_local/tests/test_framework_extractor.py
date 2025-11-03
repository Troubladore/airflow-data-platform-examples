"""
Test for refactored LocalPagilaBronzeExtractor using framework classes.

This test verifies that our refactored local extractor correctly uses
the sqlmodel-framework base classes without Kerberos.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add framework source to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')


class TestLocalPagilaBronzeExtractorWithFramework:
    """Test the refactored local extractor using framework base classes"""

    def test_extractor_inherits_from_framework_pipeline(self):
        """Test that LocalPagilaBronzeExtractor extends BronzeIngestionPipeline"""
        # This test should FAIL initially (RED phase)
        from src.extract import LocalPagilaBronzeExtractor
        from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

        # Verify inheritance
        assert issubclass(LocalPagilaBronzeExtractor, BronzeIngestionPipeline)

    def test_local_extractor_uses_framework_without_kerberos(self):
        """Test that local extractor uses PostgresConnector without Kerberos"""
        # This test should FAIL initially (RED phase)
        from src.extract import LocalPagilaBronzeExtractor
        from sqlmodel_framework.base.connectors import PostgresConnector

        # Create mock connector
        mock_connector = Mock(spec=PostgresConnector)
        bronze_path = Path('/tmp/bronze')

        # Create extractor with framework connector
        extractor = LocalPagilaBronzeExtractor(
            connector=mock_connector,
            bronze_path=bronze_path
        )

        # Verify connector is stored and no Kerberos config
        assert extractor.connector == mock_connector
        assert extractor.bronze_path == bronze_path

    def test_extract_table_with_host_override(self):
        """Test that extract_table supports host override for different environments"""
        # This test should FAIL initially (RED phase)
        from src.extract import LocalPagilaBronzeExtractor
        from sqlmodel_framework.base.connectors import PostgresConnector, PostgresConfig

        # Create mock connector with context manager
        mock_connector = Mock(spec=PostgresConnector)
        mock_connection = MagicMock()
        # Properly mock the context manager
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_connection
        mock_context.__exit__.return_value = None
        mock_connector.connection_context.return_value = mock_context
        mock_connector.config = Mock(spec=PostgresConfig)
        mock_connector.config.host = 'localhost'

        # Create extractor
        extractor = LocalPagilaBronzeExtractor(
            connector=mock_connector,
            bronze_path=Path('/tmp/bronze')
        )

        # Mock the framework methods
        sample_df = pd.DataFrame({'id': [1, 2], 'name': ['Test1', 'Test2']})

        with patch('pandas.read_sql', return_value=sample_df):
            with patch.object(extractor, 'add_bronze_metadata', return_value=sample_df) as mock_add_metadata:
                with patch.object(extractor, 'write_bronze', return_value={
                    'parquet': '/tmp/bronze/pagila/film/film.parquet',
                    'json': '/tmp/bronze/pagila/film/film.json'
                }) as mock_write_bronze:
                    # Extract table with host override
                    result = extractor.extract_table('film', host_override='docker-host')

        # Verify connection context was used
        mock_connector.connection_context.assert_called_once()

        # Verify framework methods were called with correct metadata
        mock_add_metadata.assert_called_once()
        # Check that host_override was used in metadata
        call_kwargs = mock_add_metadata.call_args[1]
        assert call_kwargs['source_host'] == 'docker-host'

        # Verify result
        assert result['success'] is True
        assert result['rows_extracted'] == 2

    def test_main_function_uses_local_config(self):
        """Test that main() uses PostgresConfig without Kerberos"""
        # This test should FAIL initially (RED phase)
        from src.extract import main
        from sqlmodel_framework.base.connectors import PostgresConfig, PostgresConnector

        with patch('src.extract.PostgresConfig') as mock_config_class:
            with patch('src.extract.PostgresConnector') as mock_connector_class:
                with patch('src.extract.LocalPagilaBronzeExtractor') as mock_extractor_class:
                    # Mock the extractor instance
                    mock_extractor = Mock()
                    mock_extractor.test_connectivity.return_value = {
                        'success': True,
                        'tables_found': ['film', 'actor'],
                        'is_pagila': True
                    }
                    mock_extractor.extract_table.return_value = {
                        'success': True,
                        'rows_extracted': 10
                    }
                    mock_extractor_class.return_value = mock_extractor

                    # Run main (should exit with 0)
                    with patch('sys.exit'):
                        main()

        # Verify PostgresConfig was created WITHOUT Kerberos
        mock_config_class.assert_called_once()
        config_call = mock_config_class.call_args
        # Check that use_kerberos is False or not present
        assert config_call[1].get('use_kerberos', False) is False

    def test_no_kerberos_code_exists(self):
        """Test that no Kerberos-specific code exists in local extractor"""
        # This test should FAIL initially (RED phase)
        from src import extract

        # These Kerberos-related methods should NOT exist
        if hasattr(extract, 'LocalPagilaBronzeExtractor'):
            extractor_class = extract.LocalPagilaBronzeExtractor
            assert not hasattr(extractor_class, 'test_kerberos_ticket')
            assert not hasattr(extractor_class, '_get_kerberos_username')

        # Only the framework-based class should exist
        assert hasattr(extract, 'LocalPagilaBronzeExtractor')