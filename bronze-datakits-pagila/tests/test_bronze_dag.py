"""
Test Bronze DAG for Pagila Orchestration

Tests the structure and configuration of the Bronze Pagila ingestion DAG.
"""

import sys
import os
from pathlib import Path

# Add dags to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'dags'))


def test_dag_loads_without_errors():
    """Test that DAG can be imported without errors"""
    try:
        from bronze_pagila_ingestion import dag
        assert dag is not None
        assert dag.dag_id == 'bronze_pagila_ingestion'
    except ImportError as e:
        assert False, f"DAG failed to import: {e}"


def test_dag_has_kerberos_check():
    """Test that DAG has Kerberos check task"""
    from bronze_pagila_ingestion import dag

    task_ids = [task.task_id for task in dag.tasks]
    assert 'check_kerberos' in task_ids, f"Expected 'check_kerberos' task, found: {task_ids}"


def test_dag_has_all_15_table_tasks():
    """Test that DAG has all 15 table tasks"""
    from bronze_pagila_ingestion import dag

    task_ids = [task.task_id for task in dag.tasks]

    # Expected tables based on loader.py
    expected_tables = [
        'actor', 'address', 'category', 'city', 'country',
        'customer', 'film', 'film_actor', 'film_category',
        'inventory', 'language', 'payment', 'rental', 'staff', 'store'
    ]

    for table in expected_tables:
        # Tasks are in groups, so the IDs will be like "small_tables.load_language"
        matching_tasks = [tid for tid in task_ids if f'load_{table}' in tid]
        assert len(matching_tasks) > 0, f"No task found for table '{table}'"


def test_dag_has_task_groups():
    """Test that DAG has task groups for organizing tables"""
    from bronze_pagila_ingestion import dag

    # Get task IDs to check group structure
    task_ids = [task.task_id for task in dag.tasks]

    # Check for task groups
    assert any('small_tables' in tid for tid in task_ids), "Missing small_tables group"
    assert any('medium_tables' in tid for tid in task_ids), "Missing medium_tables group"
    assert any('large_tables' in tid for tid in task_ids), "Missing large_tables group"
    assert any('huge_tables' in tid for tid in task_ids), "Missing huge_tables group"


def test_dag_configuration():
    """Test that DAG has correct configuration"""
    from bronze_pagila_ingestion import dag

    # Check basic configuration
    assert dag.description == 'Bronze layer ingestion from Pagila'
    assert dag.schedule is None  # Manual trigger initially
    assert dag.catchup is False
    assert dag.max_active_runs == 1

    # Check tags
    assert 'bronze' in dag.tags
    assert 'pagila' in dag.tags

    # Check default args
    assert dag.default_args['owner'] == 'data-platform'
    assert dag.default_args['retries'] == 2


def test_dag_task_dependencies():
    """Test that DAG has correct task dependencies"""
    from bronze_pagila_ingestion import dag

    # Get Kerberos check task
    kerberos_task = None
    for task in dag.tasks:
        if task.task_id == 'check_kerberos':
            kerberos_task = task
            break

    assert kerberos_task is not None, "Kerberos check task not found"

    # Check that kerberos check has downstream dependencies
    assert len(kerberos_task.downstream_task_ids) > 0, "Kerberos check has no downstream tasks"

    # Check that table loading tasks have upstream dependencies
    table_tasks = [t for t in dag.tasks if 'load_' in t.task_id]
    for task in table_tasks:
        assert len(task.upstream_task_ids) > 0, f"Task {task.task_id} has no upstream dependencies"