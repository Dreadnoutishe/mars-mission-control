"""One PostgreSQL connection per operation, configured by environment variables."""
import os
import psycopg
from psycopg.rows import dict_row


def connect():
    # The Compose service name 'db' resolves to the database container.
    # Keyword parameters safely handle passwords containing special characters.
    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=5,
        row_factory=dict_row,
    )
