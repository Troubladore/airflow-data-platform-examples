"""
Performance Tests for Large Table Handling

Tests performance characteristics for large tables, particularly payment (16k rows).
These tests verify:
- Processing time stays under acceptable limits
- Memory usage remains reasonable
- No memory leaks during extraction
"""

import sys
import time
import pytest
from unittest.mock import patch
import pandas as pd
import numpy as np
from datetime import datetime
import gc

# Add framework and package to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform-examples/bronze-datakits-pagila')

from bronze_datakits_pagila.loader import PagilaBronzeLoader


class TestPaymentTablePerformance:
    """Performance tests for payment table (16k rows)"""

    def test_payment_table_extraction_completes_quickly(self):
        """Test that payment table (16k rows) extracts in under 10 seconds"""
        # Arrange - Create mock payment data (16,049 rows)
        num_rows = 16049
        mock_payment_data = pd.DataFrame({
            'payment_id': range(1, num_rows + 1),
            'customer_id': np.random.randint(1, 600, num_rows),
            'staff_id': np.random.randint(1, 3, num_rows),
            'rental_id': range(1, num_rows + 1),
            'amount': np.random.uniform(0.99, 9.99, num_rows),
            'payment_date': [datetime.now()] * num_rows,
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Mock pandas.read_sql to return our mock data
        with patch('pandas.read_sql', return_value=mock_payment_data):
            with patch('bronze_datakits_pagila.loader.create_engine'):
                # Act - Measure time
                start_time = time.time()
                result = loader.extract_table("payment")
                elapsed_time = time.time() - start_time

                # Assert - Should complete in under 10 seconds
                assert elapsed_time < 10, f"Payment extraction took {elapsed_time:.2f}s, expected < 10s"
                assert len(result) == num_rows

    def test_bronze_metadata_addition_is_fast(self):
        """Test that adding Bronze metadata to 16k rows is fast"""
        # Arrange - Create mock payment data
        num_rows = 16049
        mock_data = pd.DataFrame({
            'payment_id': range(1, num_rows + 1),
            'amount': np.random.uniform(0.99, 9.99, num_rows),
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Act - Measure time to add metadata
        start_time = time.time()
        result = loader.add_bronze_metadata(
            mock_data,
            source_system="pagila",
            source_table="payment",
            source_host="test",
            extraction_method="full"
        )
        elapsed_time = time.time() - start_time

        # Assert - Should be very fast (under 1 second)
        assert elapsed_time < 1.0, f"Metadata addition took {elapsed_time:.2f}s, expected < 1s"
        assert len(result) == num_rows
        assert 'bronze_load_timestamp' in result.columns


class TestMemoryUsage:
    """Test memory usage for large table operations"""

    def test_extraction_does_not_leak_memory(self):
        """Test that multiple extractions don't accumulate memory"""
        # Arrange
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Create mock data
        mock_data = pd.DataFrame({
            'id': range(1000),
            'data': ['x' * 1000] * 1000  # 1MB of data
        })

        with patch('pandas.read_sql', return_value=mock_data):
            with patch('bronze_datakits_pagila.loader.create_engine') as mock_engine:
                # Setup mock engine with dispose
                engine_instance = patch.object(mock_engine.return_value, 'dispose')
                engine_instance.start()

                # Act - Extract multiple times
                for _ in range(5):
                    loader.extract_table("test_table")
                    gc.collect()  # Force garbage collection

                # Assert - dispose should be called each time
                assert mock_engine.return_value.dispose.call_count == 5

    def test_handles_16k_rows_without_memory_error(self):
        """Test that loader can handle 16k rows without running out of memory"""
        # Arrange - Create 16k rows with realistic data size
        num_rows = 16049
        mock_large_data = pd.DataFrame({
            'payment_id': range(1, num_rows + 1),
            'customer_id': np.random.randint(1, 600, num_rows),
            'staff_id': np.random.randint(1, 3, num_rows),
            'rental_id': range(1, num_rows + 1),
            'amount': np.random.uniform(0.99, 9.99, num_rows),
            'payment_date': [datetime.now()] * num_rows,
        })

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Act - This should not raise MemoryError
        with patch('pandas.read_sql', return_value=mock_large_data):
            with patch('bronze_datakits_pagila.loader.create_engine'):
                try:
                    result = loader.extract_table("payment")
                    # Assert
                    assert len(result) == num_rows
                except MemoryError:
                    pytest.fail("MemoryError raised for 16k rows")


class TestConcurrentExtractions:
    """Test performance with concurrent extractions"""

    def test_multiple_small_table_extractions_are_efficient(self):
        """Test that extracting multiple small tables is efficient"""
        # Arrange
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Mock data for small tables
        small_tables = {
            'language': pd.DataFrame({'language_id': range(1, 7), 'name': ['Lang' + str(i) for i in range(1, 7)]}),
            'category': pd.DataFrame({'category_id': range(1, 17), 'name': ['Cat' + str(i) for i in range(1, 17)]}),
            'country': pd.DataFrame({'country_id': range(1, 110), 'country': ['Country' + str(i) for i in range(1, 110)]}),
        }

        with patch('pandas.read_sql') as mock_read:
            with patch('bronze_datakits_pagila.loader.create_engine'):
                # Setup mock to return appropriate data
                def side_effect(query, engine):
                    for table_name, data in small_tables.items():
                        if table_name in query:
                            return data
                    return pd.DataFrame()

                mock_read.side_effect = side_effect

                # Act - Extract all small tables
                start_time = time.time()
                results = []
                for table_name in small_tables.keys():
                    results.append(loader.extract_table(table_name))
                elapsed_time = time.time() - start_time

                # Assert - Should complete quickly (under 5 seconds for 3 tables)
                assert elapsed_time < 5.0
                assert len(results) == 3


class TestDataFrameOperations:
    """Test DataFrame operations performance"""

    def test_iterrows_performance_for_load_operation(self):
        """Test that iterrows on 16k rows completes in reasonable time"""
        # Note: This tests the pattern used in load_table method
        # Arrange - Create 16k row DataFrame
        num_rows = 16049
        df = pd.DataFrame({
            'payment_id': range(1, num_rows + 1),
            'amount': np.random.uniform(0.99, 9.99, num_rows),
        })

        # Act - Measure iterrows time
        start_time = time.time()
        row_count = 0
        for _, row in df.iterrows():
            row_count += 1
            # Simulate what load_table does (convert to dict)
            row_dict = row.to_dict()
        elapsed_time = time.time() - start_time

        # Assert - Should complete (though may be slow)
        # iterrows is known to be slow, but should complete
        assert row_count == num_rows
        # Warning if it takes > 30 seconds
        if elapsed_time > 30:
            pytest.warn(UserWarning(f"iterrows on {num_rows} rows took {elapsed_time:.2f}s - consider using to_dict('records')"))

    def test_to_dict_records_is_faster_alternative(self):
        """Test that to_dict('records') is a faster alternative to iterrows"""
        # Arrange - Create 16k row DataFrame
        num_rows = 16049
        df = pd.DataFrame({
            'payment_id': range(1, num_rows + 1),
            'amount': np.random.uniform(0.99, 9.99, num_rows),
        })

        # Act - Measure to_dict('records') time
        start_time = time.time()
        records = df.to_dict('records')
        elapsed_time = time.time() - start_time

        # Assert - Should be very fast (under 1 second)
        assert elapsed_time < 1.0
        assert len(records) == num_rows


class TestScalability:
    """Test scalability characteristics"""

    def test_scales_linearly_with_row_count(self):
        """Test that processing time scales linearly with row count"""
        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        # Test with different row counts
        row_counts = [1000, 5000, 10000]
        times = []

        for num_rows in row_counts:
            mock_data = pd.DataFrame({
                'id': range(num_rows),
                'value': np.random.random(num_rows)
            })

            start_time = time.time()
            result = loader.add_bronze_metadata(
                mock_data,
                source_system="test",
                source_table="test",
                source_host="test",
                extraction_method="full"
            )
            elapsed = time.time() - start_time
            times.append(elapsed)

        # Assert - Time should grow roughly linearly
        # Time for 10k rows should be less than 10x time for 1k rows
        assert times[2] < times[0] * 10, "Performance degradation worse than linear"

    def test_handles_maximum_expected_table_size(self):
        """Test that loader can handle maximum expected table size"""
        # From specs: payment table is largest at 16,049 rows
        # Test with slightly more to ensure headroom
        max_rows = 20000

        loader = PagilaBronzeLoader(
            source_host="sqlpg.eruditis.lab",
            source_database="pagila",
            use_kerberos=False
        )

        mock_data = pd.DataFrame({
            'id': range(max_rows),
            'value': np.random.random(max_rows)
        })

        # Act - Should complete without error
        with patch('pandas.read_sql', return_value=mock_data):
            with patch('bronze_datakits_pagila.loader.create_engine'):
                try:
                    result = loader.extract_table("test_large_table")
                    assert len(result) == max_rows
                except Exception as e:
                    pytest.fail(f"Failed to handle {max_rows} rows: {e}")
