"""
Test for refactored PagilaBronzeExtractor using framework classes.

This test verifies that our refactored extractor correctly uses
the sqlmodel-framework base classes.
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


class TestPagilaBronzeExtractorWithFramework:
    """Test the refactored extractor using framework base classes"""

    def test_extractor_inherits_from_framework_pipeline(self):
        """Test that PagilaBronzeExtractor extends BronzeIngestionPipeline"""
        # This test should FAIL initially (RED phase)
        from src.extract import PagilaBronzeExtractor
        from sqlmodel_framework.base.loaders import BronzeIngestionPipeline

        # Verify inheritance
        assert issubclass(PagilaBronzeExtractor, BronzeIngestionPipeline)

    def test_extractor_uses_framework_connector(self):
        """Test that extractor uses PostgresConnector from framework"""
        # This test should FAIL initially (RED phase)
        from src.extract import PagilaBronzeExtractor
        from sqlmodel_framework.base.connectors import PostgresConnector

        # Create mock connector
        mock_connector = Mock(spec=PostgresConnector)
        bronze_path = Path('/tmp/bronze')

        # Create extractor with framework connector
        extractor = PagilaBronzeExtractor(
            connector=mock_connector,
            bronze_path=bronze_path
        )

        # Verify connector is stored
        assert extractor.connector == mock_connector
        assert extractor.bronze_path == bronze_path

    def test_test_connectivity_uses_framework_methods(self):
        """Test that connectivity test uses framework connector methods"""
        # This test should FAIL initially (RED phase)
        from src.extract import PagilaBronzeExtractor
        from sqlmodel_framework.base.connectors import PostgresConnector

        # Create mock connector
        mock_connector = Mock(spec=PostgresConnector)
        mock_connector.test_connection.return_value = True
        mock_connector.get_tables.return_value = ['film', 'actor', 'customer', 'rental']

        # Create extractor
        extractor = PagilaBronzeExtractor(
            connector=mock_connector,
            bronze_path=Path('/tmp/bronze')
        )

        # Test connectivity
        result = extractor.test_connectivity()

        # Verify framework methods were called
        mock_connector.test_connection.assert_called_once()
        mock_connector.get_tables.assert_called_once_with(schema='public')

        # Verify result structure
        assert result['success'] is True
        assert 'tables_found' in result
        assert result['is_pagila'] is True

    def test_extract_table_uses_framework_context_manager(self):
        """Test that extract_table uses framework connection context"""
        # This test should FAIL initially (RED phase)
        from src.extract import PagilaBronzeExtractor
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
        mock_connector.config.host = 'test-host'

        # Create extractor
        extractor = PagilaBronzeExtractor(
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
                    # Extract table
                    result = extractor.extract_table('film', limit=10)

        # Verify connection context was used
        mock_connector.connection_context.assert_called_once()

        # Verify framework methods were called
        mock_add_metadata.assert_called_once()
        mock_write_bronze.assert_called_once()

        # Verify result
        assert result['success'] is True
        assert result['rows_extracted'] == 2

    def test_main_function_creates_framework_config(self):
        """Test that main() uses PostgresConfig from framework"""
        # This test should FAIL initially (RED phase)
        from src.extract import main
        from sqlmodel_framework.base.connectors import PostgresConfig, PostgresConnector

        with patch('src.extract.PostgresConfig') as mock_config_class:
            with patch('src.extract.PostgresConnector') as mock_connector_class:
                with patch('src.extract.PagilaBronzeExtractor') as mock_extractor_class:
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

        # Verify PostgresConfig was created with correct params
        mock_config_class.assert_called_once_with(
            host='sqlpg.eruditis.lab',
            port=5432,
            database='pagila',
            use_kerberos=True,
            gssencmode='require'
        )

        # Verify PostgresConnector was created with config
        mock_connector_class.assert_called_once()

    def test_no_custom_connection_code_exists(self):
        """Test that old custom connection code has been removed"""
        # This test should FAIL initially (RED phase)
        # It checks that we've removed the old implementation
        from src import extract

        # These should NOT exist in the refactored code
        assert not hasattr(extract, 'PostgresBronzeExtractor')
        assert not hasattr(extract, '_get_default_config')
        assert not hasattr(extract, 'test_kerberos_ticket')
        assert not hasattr(extract, 'get_connection')

        # Only the new class should exist
        assert hasattr(extract, 'PagilaBronzeExtractor')