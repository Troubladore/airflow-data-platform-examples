"""
Bronze Layer Ingestion Pipeline for SQL Server
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .connector import SQLServerKerberosConnector, SQLServerConfig

logger = logging.getLogger(__name__)
console = Console()


class IngestionMetadata:
    """Track metadata for Bronze ingestion."""

    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = None
        self.tables_processed = []
        self.total_rows = 0
        self.errors = []

    def add_table(self, table_name: str, row_count: int, status: str = "success"):
        """Add table processing metadata."""
        self.tables_processed.append({
            "table": table_name,
            "row_count": row_count,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })
        if status == "success":
            self.total_rows += row_count

    def add_error(self, table_name: str, error: str):
        """Add error metadata."""
        self.errors.append({
            "table": table_name,
            "error": str(error),
            "timestamp": datetime.now().isoformat(),
        })

    def finalize(self):
        """Finalize metadata."""
        self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": (
                (self.end_time - self.start_time).total_seconds()
                if self.end_time
                else None
            ),
            "tables_processed": self.tables_processed,
            "total_rows": self.total_rows,
            "errors": self.errors,
            "success": len(self.errors) == 0,
        }


class BronzeIngestionPipeline:
    """
    Pipeline for ingesting data from SQL Server to Bronze layer.

    This pipeline:
    1. Connects to SQL Server using Kerberos authentication
    2. Discovers tables for ingestion
    3. Extracts data in batches
    4. Writes to Bronze layer with metadata
    5. Tracks lineage and audit information
    """

    def __init__(self, config: SQLServerConfig):
        self.config = config
        self.connector = SQLServerKerberosConnector(config)
        self.metadata = IngestionMetadata()

    def discover_tables(
        self,
        schema: str = "dbo",
        pattern: Optional[str] = None,
        exclude_system: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Discover tables available for ingestion.

        Args:
            schema: Database schema to search
            pattern: Optional pattern to filter tables
            exclude_system: Exclude system tables

        Returns:
            List of table metadata
        """
        console.print(f"[bold blue]Discovering tables in schema: {schema}[/bold blue]")

        tables = self.connector.list_tables(schema=schema)

        # Filter tables
        if pattern:
            import re
            regex = re.compile(pattern, re.IGNORECASE)
            tables = [t for t in tables if regex.search(t)]

        if exclude_system:
            # Exclude common system tables
            system_patterns = ["sys", "INFORMATION_SCHEMA", "tempdb", "msdb"]
            tables = [
                t for t in tables
                if not any(sp in t for sp in system_patterns)
            ]

        # Get metadata for each table
        table_metadata = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Getting metadata for {len(tables)} tables...",
                total=len(tables),
            )

            for table in tables:
                try:
                    metadata = self.connector.get_table_metadata(table, schema)
                    table_metadata.append(metadata)
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(f"Failed to get metadata for {table}: {e}")

        return table_metadata

    def ingest_table(
        self,
        source_table: str,
        source_schema: str = "dbo",
        target_table: Optional[str] = None,
        target_schema: str = "bronze",
        batch_size: int = 10000,
    ) -> int:
        """
        Ingest a single table to Bronze layer.

        Args:
            source_table: Source table name
            source_schema: Source schema
            target_table: Target table name (defaults to source name)
            target_schema: Target schema (bronze)
            batch_size: Batch size for reading

        Returns:
            Number of rows ingested
        """
        if not target_table:
            target_table = f"{source_schema}_{source_table}"

        console.print(
            f"[bold green]Ingesting {source_schema}.{source_table} "
            f"-> {target_schema}.{target_table}[/bold green]"
        )

        try:
            # Read source data
            df = self.connector.read_table(
                source_table,
                schema=source_schema,
                batch_size=batch_size,
            )

            if df.empty:
                console.print(f"[yellow]No data found in {source_table}[/yellow]")
                self.metadata.add_table(source_table, 0, "empty")
                return 0

            # Add Bronze metadata columns
            df["_bronze_loaded_at"] = datetime.now()
            df["_bronze_source_system"] = "sqlserver"
            df["_bronze_source_schema"] = source_schema
            df["_bronze_source_table"] = source_table

            # Write to Bronze
            rows_written = self.connector.write_to_bronze(
                df,
                target_table=target_table,
                target_schema=target_schema,
                if_exists="replace",  # Or "append" based on requirements
            )

            self.metadata.add_table(source_table, rows_written, "success")
            console.print(
                f"[green]✓ Successfully ingested {rows_written} rows[/green]"
            )

            return rows_written

        except Exception as e:
            error_msg = f"Failed to ingest {source_table}: {str(e)}"
            logger.error(error_msg)
            self.metadata.add_error(source_table, str(e))
            console.print(f"[red]✗ {error_msg}[/red]")
            raise

    def ingest_multiple_tables(
        self,
        tables: List[str],
        source_schema: str = "dbo",
        target_schema: str = "bronze",
        batch_size: int = 10000,
        continue_on_error: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest multiple tables to Bronze layer.

        Args:
            tables: List of table names to ingest
            source_schema: Source schema
            target_schema: Target schema
            batch_size: Batch size for reading
            continue_on_error: Continue if a table fails

        Returns:
            Ingestion summary
        """
        console.print(
            f"[bold blue]Starting Bronze ingestion for {len(tables)} tables[/bold blue]"
        )

        for table in tables:
            try:
                self.ingest_table(
                    source_table=table,
                    source_schema=source_schema,
                    target_schema=target_schema,
                    batch_size=batch_size,
                )
            except Exception as e:
                if not continue_on_error:
                    raise
                console.print(f"[red]Skipping {table} due to error[/red]")

        self.metadata.finalize()
        return self.metadata.to_dict()

    def ingest_all_tables(
        self,
        source_schema: str = "dbo",
        target_schema: str = "bronze",
        pattern: Optional[str] = None,
        exclude_pattern: Optional[str] = None,
        batch_size: int = 10000,
    ) -> Dict[str, Any]:
        """
        Discover and ingest all tables matching criteria.

        Args:
            source_schema: Source schema
            target_schema: Target schema
            pattern: Include pattern for table names
            exclude_pattern: Exclude pattern for table names
            batch_size: Batch size for reading

        Returns:
            Ingestion summary
        """
        # Discover tables
        table_metadata = self.discover_tables(
            schema=source_schema,
            pattern=pattern,
            exclude_system=True,
        )

        # Filter by exclude pattern if provided
        if exclude_pattern:
            import re
            exclude_regex = re.compile(exclude_pattern, re.IGNORECASE)
            table_metadata = [
                t for t in table_metadata
                if not exclude_regex.search(t["table"])
            ]

        # Display discovered tables
        table_display = Table(title=f"Tables to Ingest ({len(table_metadata)})")
        table_display.add_column("Schema", style="cyan")
        table_display.add_column("Table", style="green")
        table_display.add_column("Rows", style="yellow")
        table_display.add_column("Columns", style="blue")

        for tm in table_metadata:
            table_display.add_row(
                tm["schema"],
                tm["table"],
                str(tm["row_count"]),
                str(len(tm["columns"])),
            )

        console.print(table_display)

        # Ingest tables
        tables = [tm["table"] for tm in table_metadata]
        return self.ingest_multiple_tables(
            tables=tables,
            source_schema=source_schema,
            target_schema=target_schema,
            batch_size=batch_size,
        )

    def save_metadata(self, output_path: Path) -> None:
        """Save ingestion metadata to file."""
        metadata = self.metadata.to_dict()
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2)
        console.print(f"[green]Metadata saved to {output_path}[/green]")