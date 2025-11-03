"""Bronze model for AdventureWorksLT ProductCategory table"""

from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid
import sys

# Add framework to path
sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel_framework.base.models import BronzeMetadata


class ProductCategoryBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer model for SalesLT.ProductCategory table"""
    __tablename__ = "bronze_product_category"
    __table_args__ = {"schema": "bronze"}

    # Primary key from source
    productcategoryid: int = Field(primary_key=True, description="Product category ID from source")

    # Business fields
    parentproductcategoryid: Optional[int] = Field(
        default=None,
        description="Parent category ID for hierarchical structure"
    )
    name: str = Field(description="Category name")
    rowguid: uuid.UUID = Field(description="GUID from source system")
    modifieddate: datetime = Field(description="Last modified timestamp from source")

    # Bronze metadata fields inherited from BronzeMetadata:
    # - bronze_load_timestamp
    # - bronze_source_system
    # - bronze_source_table
    # - bronze_source_host
    # - bronze_extraction_method
