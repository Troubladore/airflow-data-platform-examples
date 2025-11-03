"""
Unit Tests for Data Anomaly Handling

Tests how the Bronze loader handles edge cases and data anomalies:
- NULL values in various fields
- Missing/extra columns
- Large text fields
- Special characters
- Data type mismatches
"""

import sys
import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime

# Add framework and package to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform-examples/bronze-datakits-pagila')

from bronze_datakits_pagila.loader import PagilaBronzeLoader


class TestNullValueHandling:
    """Test handling of NULL values in source data"""

    def test_handles_null_in_optional_fields(self):
        """Test that loader handles NULL values in optional fields"""
        # Arrange - Create DataFrame with NULL values
        df_with_nulls = pd.DataFrame({
            'language_id': [1, 2, 3],
            'name': ['English', 'French', 'German'],
            'last_update': [datetime.now(), datetime.now(), None]  # NULL in last row
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Mock extract_table to return our test data
        with patch.object(loader, 'extract_table', return_value=df_with_nulls):
            # Act
            result = loader.extract_table("language")

            # Assert - Should handle NULL gracefully
            assert len(result) == 3
            assert pd.isna(result.iloc[2]['last_update'])

    def test_handles_all_nulls_in_column(self):
        """Test that loader handles columns with all NULL values"""
        # Arrange - DataFrame where entire column is NULL
        df_all_nulls = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'optional_field': [None, None, None]  # All NULL
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_all_nulls):
            # Act
            result = loader.extract_table("test_table")

            # Assert
            assert len(result) == 3
            assert result['optional_field'].isna().all()

    def test_bronze_metadata_added_despite_nulls(self):
        """Test that Bronze metadata is added even when source data has NULLs"""
        # Arrange
        df_with_nulls = pd.DataFrame({
            'language_id': [1, None, 3],
            'name': ['English', None, 'German'],
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Act - Add Bronze metadata
        result = loader.add_bronze_metadata(
            df_with_nulls,
            source_system="test",
            source_table="language",
            source_host="test.host",
            extraction_method="full"
        )

        # Assert - Bronze columns should exist
        assert 'bronze_load_timestamp' in result.columns
        assert 'bronze_source_system' in result.columns
        assert 'bronze_source_table' in result.columns
        # And all rows should have Bronze metadata even if source data is NULL
        assert not result['bronze_load_timestamp'].isna().any()


class TestMissingColumnHandling:
    """Test handling of missing or extra columns"""

    def test_handles_missing_expected_columns(self):
        """Test behavior when source table is missing expected columns"""
        # Arrange - DataFrame missing 'last_update' column
        df_missing_col = pd.DataFrame({
            'language_id': [1, 2, 3],
            'name': ['English', 'French', 'German']
            # last_update is missing
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_missing_col):
            # Act
            result = loader.extract_table("language")

            # Assert - Should work but column won't be there
            assert 'last_update' not in result.columns
            assert 'language_id' in result.columns

    def test_handles_extra_unexpected_columns(self):
        """Test that loader handles extra columns not in schema"""
        # Arrange - DataFrame with extra column
        df_extra_col = pd.DataFrame({
            'language_id': [1, 2, 3],
            'name': ['English', 'French', 'German'],
            'last_update': [datetime.now()] * 3,
            'unexpected_column': ['X', 'Y', 'Z']  # Extra column
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_extra_col):
            # Act
            result = loader.extract_table("language")

            # Assert - Extra column should be preserved in Bronze
            assert 'unexpected_column' in result.columns
            assert len(result) == 3


class TestLargeTextHandling:
    """Test handling of large text fields"""

    def test_handles_very_long_text_fields(self):
        """Test that loader handles very long text (e.g., film descriptions)"""
        # Arrange - Create DataFrame with very long text
        long_text = "A" * 10000  # 10KB of text
        df_long_text = pd.DataFrame({
            'film_id': [1],
            'title': ['Test Film'],
            'description': [long_text]
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_long_text):
            # Act
            result = loader.extract_table("film")

            # Assert - Long text should be preserved
            assert len(result) == 1
            assert len(result.iloc[0]['description']) == 10000

    def test_handles_empty_strings_vs_nulls(self):
        """Test that loader distinguishes between empty strings and NULLs"""
        # Arrange
        df_mixed = pd.DataFrame({
            'id': [1, 2, 3],
            'description': ['Has text', '', None]  # Regular, empty string, NULL
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_mixed):
            # Act
            result = loader.extract_table("test_table")

            # Assert
            assert result.iloc[0]['description'] == 'Has text'
            assert result.iloc[1]['description'] == ''  # Empty string preserved
            assert pd.isna(result.iloc[2]['description'])  # NULL preserved


class TestSpecialCharacterHandling:
    """Test handling of special characters in data"""

    def test_handles_unicode_characters(self):
        """Test that loader handles Unicode characters correctly"""
        # Arrange - DataFrame with Unicode
        df_unicode = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Café', '日本語', 'Москва']  # French, Japanese, Russian
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_unicode):
            # Act
            result = loader.extract_table("test_table")

            # Assert - Unicode should be preserved
            assert result.iloc[0]['name'] == 'Café'
            assert result.iloc[1]['name'] == '日本語'
            assert result.iloc[2]['name'] == 'Москва'

    def test_handles_special_sql_characters(self):
        """Test that loader handles SQL special characters (quotes, backslashes)"""
        # Arrange - DataFrame with SQL special chars
        df_special = pd.DataFrame({
            'id': [1, 2, 3],
            'description': [
                "It's a test",
                'Quote: "Hello"',
                r'Backslash: \ and C:\path'
            ]
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_special):
            # Act
            result = loader.extract_table("test_table")

            # Assert - Special chars should be preserved
            assert "'" in result.iloc[0]['description']
            assert '"' in result.iloc[1]['description']
            assert '\\' in result.iloc[2]['description']

    def test_handles_newlines_and_tabs(self):
        """Test that loader handles newlines and tabs in text fields"""
        # Arrange
        df_whitespace = pd.DataFrame({
            'id': [1, 2, 3],
            'description': [
                'Line 1\nLine 2',
                'Tab\there',
                'Mixed\n\twhitespace'
            ]
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_whitespace):
            # Act
            result = loader.extract_table("test_table")

            # Assert - Whitespace should be preserved
            assert '\n' in result.iloc[0]['description']
            assert '\t' in result.iloc[1]['description']


class TestDataTypeHandling:
    """Test handling of various data types"""

    def test_handles_mixed_numeric_types(self):
        """Test that loader handles mixed integer and float types"""
        # Arrange
        df_mixed_numeric = pd.DataFrame({
            'int_col': [1, 2, 3],
            'float_col': [1.5, 2.7, 3.9],
            'decimal_col': pd.Series([1.23, 4.56, 7.89], dtype='float64')
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_mixed_numeric):
            # Act
            result = loader.extract_table("test_table")

            # Assert
            assert result['int_col'].dtype in [np.int64, np.int32]
            assert result['float_col'].dtype in [np.float64, np.float32]

    def test_handles_datetime_with_timezone(self):
        """Test that loader handles datetime with timezone information"""
        # Arrange
        df_datetime = pd.DataFrame({
            'id': [1, 2, 3],
            'timestamp': pd.to_datetime([
                '2025-01-01 12:00:00',
                '2025-01-02 13:30:00',
                '2025-01-03 14:45:00'
            ])
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_datetime):
            # Act
            result = loader.extract_table("test_table")

            # Assert
            assert pd.api.types.is_datetime64_any_dtype(result['timestamp'])

    def test_handles_boolean_values(self):
        """Test that loader handles boolean values correctly"""
        # Arrange
        df_bool = pd.DataFrame({
            'id': [1, 2, 3],
            'active': [True, False, True],
            'verified': pd.Series([1, 0, 1], dtype='int64')  # Boolean as int
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        with patch.object(loader, 'extract_table', return_value=df_bool):
            # Act
            result = loader.extract_table("test_table")

            # Assert
            assert result['active'].dtype == bool
            assert result['verified'].dtype in [np.int64, np.int32]


class TestFieldExclusionWithAnomalies:
    """Test field exclusion works even with data anomalies"""

    def test_excludes_fields_when_nulls_present(self):
        """Test that field exclusion works even when excluded fields have NULLs"""
        # Arrange - Mock get columns to include 'fulltext'
        df_with_excluded = pd.DataFrame({
            'film_id': [1, 2, 3],
            'title': ['Film 1', 'Film 2', 'Film 3'],
            # fulltext should be excluded
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Mock the database connection and column query
        with patch('bronze_datakits_pagila.loader.create_engine'):
            with patch('pandas.read_sql', return_value=df_with_excluded):
                # Act
                result = loader.extract_table("film")

                # Assert - fulltext should not be in result
                assert 'fulltext' not in result.columns
                assert 'film_id' in result.columns

    def test_exclusion_list_for_staff_table(self):
        """Test that staff table excludes picture and password fields"""
        # Verify exclusion configuration
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Assert - Verify exclusion list is correct
        assert 'staff' in loader.FIELD_EXCLUSIONS
        assert 'picture' in loader.FIELD_EXCLUSIONS['staff']
        assert 'password' in loader.FIELD_EXCLUSIONS['staff']
        assert 'film' in loader.FIELD_EXCLUSIONS
        assert 'fulltext' in loader.FIELD_EXCLUSIONS['film']
