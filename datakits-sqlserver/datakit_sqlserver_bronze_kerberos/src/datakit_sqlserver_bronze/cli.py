"""
CLI for SQL Server Bronze Datakit with Kerberos Authentication
"""
import os
import sys
import json
from pathlib import Path
from typing import Optional, List
import logging

import typer
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler
from dotenv import load_dotenv

from .connector import SQLServerConfig, SQLServerKerberosConnector
from .ingestion import BronzeIngestionPipeline

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)

# CLI setup
app = typer.Typer(
    name="datakit-sqlserver",
    help="SQL Server Bronze Ingestion with Kerberos Authentication",
    add_completion=False,
)
console = Console()

# Load environment variables
load_dotenv()


def get_config_from_env() -> SQLServerConfig:
    """Build configuration from environment variables."""
    return SQLServerConfig(
        server=os.getenv("MSSQL_SERVER", "localhost"),
        port=int(os.getenv("MSSQL_PORT", "1433")),
        database=os.getenv("MSSQL_DATABASE", "master"),
        auth_type=os.getenv("MSSQL_AUTH_TYPE", "kerberos"),
        username=os.getenv("MSSQL_USERNAME"),
        password=os.getenv("MSSQL_PASSWORD"),
        driver=os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
        trust_server_certificate=os.getenv("MSSQL_TRUST_CERT", "false").lower() == "true",
        application_name=os.getenv("MSSQL_APP_NAME", "DataKit-Bronze-CLI"),
    )


@app.command()
def test_connection(
    server: Optional[str] = typer.Option(None, "--server", "-s", help="SQL Server hostname"),
    database: Optional[str] = typer.Option(None, "--database", "-d", help="Database name"),
    auth_type: str = typer.Option("kerberos", "--auth", "-a", help="Auth type: kerberos, sql, azure_ad"),
    username: Optional[str] = typer.Option(None, "--username", "-u", help="Username for SQL auth"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password for SQL auth"),
):
    """Test connection to SQL Server with Kerberos authentication."""
    console.print("[bold blue]Testing SQL Server connection...[/bold blue]")

    # Build config
    config = get_config_from_env()
    if server:
        config.server = server
    if database:
        config.database = database
    if auth_type:
        config.auth_type = auth_type
    if username:
        config.username = username
    if password:
        config.password = password

    # Test connection
    connector = SQLServerKerberosConnector(config)
    success, message = connector.test_connection()

    if success:
        console.print(f"[green]✓ {message}[/green]")
        raise typer.Exit(0)
    else:
        console.print(f"[red]✗ {message}[/red]")
        raise typer.Exit(1)


@app.command()
def discover(
    schema: str = typer.Option("dbo", "--schema", help="Database schema"),
    pattern: Optional[str] = typer.Option(None, "--pattern", help="Table name pattern (regex)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    limit: int = typer.Option(100, "--limit", help="Maximum tables to show"),
):
    """Discover available tables in SQL Server database."""
    console.print(f"[bold blue]Discovering tables in schema: {schema}[/bold blue]")

    config = get_config_from_env()
    pipeline = BronzeIngestionPipeline(config)

    try:
        tables = pipeline.discover_tables(schema=schema, pattern=pattern)

        # Display results
        if tables:
            table_display = Table(title=f"Discovered {len(tables)} Tables")
            table_display.add_column("Schema", style="cyan")
            table_display.add_column("Table", style="green")
            table_display.add_column("Rows", style="yellow")
            table_display.add_column("Columns", style="blue")

            for i, tm in enumerate(tables[:limit]):
                table_display.add_row(
                    tm["schema"],
                    tm["table"],
                    f"{tm['row_count']:,}",
                    str(len(tm["columns"])),
                )

            console.print(table_display)

            if len(tables) > limit:
                console.print(f"[yellow]... and {len(tables) - limit} more tables[/yellow]")

            # Save to file if requested
            if output:
                with open(output, "w") as f:
                    json.dump(tables, f, indent=2, default=str)
                console.print(f"[green]✓ Saved metadata to {output}[/green]")
        else:
            console.print("[yellow]No tables found matching criteria[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ingest_table(
    source_table: str = typer.Argument(..., help="Source table name"),
    source_schema: str = typer.Option("dbo", "--source-schema", help="Source schema"),
    target_table: Optional[str] = typer.Option(None, "--target-table", help="Target table name"),
    target_schema: str = typer.Option("bronze", "--target-schema", help="Target schema"),
    batch_size: int = typer.Option(10000, "--batch-size", help="Batch size for reading"),
):
    """Ingest a single table to Bronze layer."""
    console.print(f"[bold green]Ingesting {source_schema}.{source_table}[/bold green]")

    config = get_config_from_env()
    pipeline = BronzeIngestionPipeline(config)

    try:
        rows = pipeline.ingest_table(
            source_table=source_table,
            source_schema=source_schema,
            target_table=target_table,
            target_schema=target_schema,
            batch_size=batch_size,
        )

        console.print(f"[green]✓ Successfully ingested {rows:,} rows[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ingest_tables(
    tables: List[str] = typer.Argument(..., help="List of table names to ingest"),
    source_schema: str = typer.Option("dbo", "--source-schema", help="Source schema"),
    target_schema: str = typer.Option("bronze", "--target-schema", help="Target schema"),
    batch_size: int = typer.Option(10000, "--batch-size", help="Batch size for reading"),
    continue_on_error: bool = typer.Option(True, "--continue-on-error", help="Continue if table fails"),
    metadata_output: Optional[str] = typer.Option(None, "--metadata", "-m", help="Save metadata to file"),
):
    """Ingest multiple tables to Bronze layer."""
    console.print(f"[bold blue]Ingesting {len(tables)} tables[/bold blue]")

    config = get_config_from_env()
    pipeline = BronzeIngestionPipeline(config)

    try:
        summary = pipeline.ingest_multiple_tables(
            tables=tables,
            source_schema=source_schema,
            target_schema=target_schema,
            batch_size=batch_size,
            continue_on_error=continue_on_error,
        )

        # Display summary
        console.print("\n[bold]Ingestion Summary:[/bold]")
        console.print(f"  Total tables: {len(summary['tables_processed'])}")
        console.print(f"  Total rows: {summary['total_rows']:,}")
        console.print(f"  Duration: {summary['duration_seconds']:.2f} seconds")

        if summary['errors']:
            console.print(f"  [red]Errors: {len(summary['errors'])}[/red]")
            for error in summary['errors']:
                console.print(f"    - {error['table']}: {error['error']}")

        # Save metadata
        if metadata_output:
            with open(metadata_output, "w") as f:
                json.dump(summary, f, indent=2)
            console.print(f"\n[green]✓ Metadata saved to {metadata_output}[/green]")

        if summary['success']:
            console.print("\n[green]✓ Ingestion completed successfully[/green]")
        else:
            console.print("\n[yellow]⚠ Ingestion completed with errors[/yellow]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def ingest_all(
    source_schema: str = typer.Option("dbo", "--source-schema", help="Source schema"),
    target_schema: str = typer.Option("bronze", "--target-schema", help="Target schema"),
    include_pattern: Optional[str] = typer.Option(None, "--include", help="Include pattern (regex)"),
    exclude_pattern: Optional[str] = typer.Option(None, "--exclude", help="Exclude pattern (regex)"),
    batch_size: int = typer.Option(10000, "--batch-size", help="Batch size for reading"),
    metadata_output: Optional[str] = typer.Option(None, "--metadata", "-m", help="Save metadata to file"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be ingested without doing it"),
):
    """Discover and ingest all matching tables to Bronze layer."""
    console.print("[bold blue]Starting full Bronze ingestion pipeline[/bold blue]")

    config = get_config_from_env()
    pipeline = BronzeIngestionPipeline(config)

    try:
        if dry_run:
            # Just show what would be ingested
            tables = pipeline.discover_tables(
                schema=source_schema,
                pattern=include_pattern,
            )

            console.print(f"\n[yellow]DRY RUN: Would ingest {len(tables)} tables[/yellow]")
            for tm in tables[:10]:
                console.print(f"  - {tm['schema']}.{tm['table']} ({tm['row_count']:,} rows)")

            if len(tables) > 10:
                console.print(f"  ... and {len(tables) - 10} more tables")

        else:
            # Perform actual ingestion
            summary = pipeline.ingest_all_tables(
                source_schema=source_schema,
                target_schema=target_schema,
                pattern=include_pattern,
                exclude_pattern=exclude_pattern,
                batch_size=batch_size,
            )

            # Display summary
            console.print("\n[bold]Ingestion Summary:[/bold]")
            console.print(f"  Total tables: {len(summary['tables_processed'])}")
            console.print(f"  Total rows: {summary['total_rows']:,}")
            console.print(f"  Duration: {summary['duration_seconds']:.2f} seconds")

            if summary['errors']:
                console.print(f"  [red]Errors: {len(summary['errors'])}[/red]")

            # Save metadata
            if metadata_output:
                with open(metadata_output, "w") as f:
                    json.dump(summary, f, indent=2)
                console.print(f"\n[green]✓ Metadata saved to {metadata_output}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate_env():
    """Validate environment configuration for Kerberos authentication."""
    console.print("[bold blue]Validating environment configuration...[/bold blue]")

    checks = []

    # Check Kerberos ticket cache
    krb5ccname = os.environ.get("KRB5CCNAME", "/krb5/cache/krb5cc")
    if os.path.exists(krb5ccname):
        checks.append(("✓", f"Kerberos ticket cache found: {krb5ccname}", "green"))
    else:
        checks.append(("✗", f"Kerberos ticket cache not found: {krb5ccname}", "red"))

    # Check SQL Server environment variables
    if os.getenv("MSSQL_SERVER"):
        checks.append(("✓", f"SQL Server configured: {os.getenv('MSSQL_SERVER')}", "green"))
    else:
        checks.append(("⚠", "MSSQL_SERVER not set", "yellow"))

    if os.getenv("MSSQL_DATABASE"):
        checks.append(("✓", f"Database configured: {os.getenv('MSSQL_DATABASE')}", "green"))
    else:
        checks.append(("⚠", "MSSQL_DATABASE not set (using 'master')", "yellow"))

    # Check authentication type
    auth_type = os.getenv("MSSQL_AUTH_TYPE", "kerberos")
    checks.append(("ℹ", f"Authentication type: {auth_type}", "blue"))

    # Display results
    for icon, message, color in checks:
        console.print(f"[{color}]{icon} {message}[/{color}]")

    # Test actual connection if possible
    console.print("\n[bold]Testing connection...[/bold]")
    try:
        config = get_config_from_env()
        connector = SQLServerKerberosConnector(config)
        success, message = connector.test_connection()
        if success:
            console.print(f"[green]✓ Connection successful[/green]")
        else:
            console.print(f"[red]✗ Connection failed: {message}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Connection test failed: {e}[/red]")


if __name__ == "__main__":
    app()