import typer

from .ingest import ingest_table

app = typer.Typer()


@app.command()
def ingest(table: str, source_url: str, target_url: str, batch_id: str):
    rows = ingest_table(table, source_url, target_url, batch_id)
    print({"table": table, "rows": rows})
