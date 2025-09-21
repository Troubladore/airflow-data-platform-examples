import hashlib
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

AUDIT = [
    "br_load_time",
    "br_source_table",
    "br_batch_id",
    "br_is_current",
    "br_record_hash",
]


def ingest_table(table: str, source_url: str, target_url: str, batch_id: str) -> int:
    src = create_engine(source_url)
    tgt = create_engine(target_url)
    df = pd.read_sql(f'SELECT * FROM public."{table}"', src)
    if df.empty:
        return 0
    df["br_load_time"] = datetime.utcnow()
    df["br_source_table"] = f"public.{table}"
    df["br_batch_id"] = batch_id
    df["br_is_current"] = True
    cols = [c for c in df.columns if c not in AUDIT]
    df["br_record_hash"] = (
        df[cols]
        .astype(str)
        .agg("|".join, axis=1)
        .map(lambda s: hashlib.md5(s.encode()).hexdigest())
    )
    df.to_sql(
        name=f"br_{table}",
        con=tgt,
        schema="bronze",
        if_exists="replace",
        index=False,
        method="multi",
    )
    src.dispose()
    tgt.dispose()
    return len(df)
