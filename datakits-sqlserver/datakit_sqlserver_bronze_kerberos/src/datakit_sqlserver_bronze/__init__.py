"""
SQL Server Bronze Datakit with Kerberos Authentication

This datakit implements Bronze layer ingestion from SQL Server using NT Authentication.
It follows the medallion architecture pattern and integrates with the sqlmodel-framework.
"""

from .cli import app as cli
from .connector import SQLServerKerberosConnector
from .ingestion import BronzeIngestionPipeline

__version__ = "0.1.0"

__all__ = [
    "cli",
    "SQLServerKerberosConnector",
    "BronzeIngestionPipeline",
]