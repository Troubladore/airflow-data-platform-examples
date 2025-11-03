"""
Payment Bronze Model using framework BronzeMetadata
"""

import sys
from datetime import datetime
from typing import Optional
from decimal import Decimal

sys.path.insert(0, '/home/emaynard/repos/airflow-data-platform/sqlmodel-framework/src')

from sqlmodel import SQLModel, Field
from sqlmodel_framework.base.models import BronzeMetadata


class PaymentBronze(BronzeMetadata, SQLModel, table=True):
    """Bronze layer for Pagila payment table"""

    __tablename__ = "bronze_payment"
    __table_args__ = {"schema": "bronze"}

    payment_id: int = Field(primary_key=True)
    customer_id: int
    staff_id: int
    rental_id: Optional[int] = Field(default=None)
    amount: Decimal = Field(max_digits=5, decimal_places=2)
    payment_date: datetime