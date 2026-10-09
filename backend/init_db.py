"""Idempotent startup initialization: preserve existing data on every restart."""
import time
import psycopg
from database import connect


def initialize():
    for attempt in range(1, 16):
        try:
            with connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS missions (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(100) NOT NULL CHECK (length(trim(title)) > 0),
                        sector VARCHAR(40) NOT NULL CHECK (length(trim(sector)) > 0),
                        category VARCHAR(20) NOT NULL
                            CHECK (category IN ('Exploration', 'Engineering', 'Science')),
                        reward INTEGER NOT NULL CHECK (reward BETWEEN 10 AND 500),
                        status VARCHAR(20) NOT NULL DEFAULT 'available'
                            CHECK (status IN ('available', 'completed')),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        completed_at TIMESTAMPTZ
                    )
                """)
                # A separate marker stops demo data from returning after a user deletes it.
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS app_meta (
                        key TEXT PRIMARY KEY
                    )
                """)
                marker = conn.execute(
                    "INSERT INTO app_meta (key) VALUES ('demo_seeded') "
                    "ON CONFLICT DO NOTHING RETURNING key"
                ).fetchone()
                if marker:
                    for title, sector, category, reward in [
                        ('Map the lava tubes', 'Olympus Mons', 'Exploration', 150),
                        ('Repair the solar array', 'Habitat Alpha', 'Engineering', 100),
                        ('Analyze ancient ice', 'Jezero Crater', 'Science', 200),
                    ]:
                        conn.execute(
                            "INSERT INTO missions (title, sector, category, reward) "
                            "VALUES (%s, %s, %s, %s)",
                            (title, sector, category, reward),
                        )
            print('Database ready.', flush=True)
            return
        except psycopg.OperationalError:
            if attempt == 15:
                raise RuntimeError('Database unavailable after startup retries.') from None
            print(f'Waiting for database ({attempt}/15)...', flush=True)
            time.sleep(2)


if __name__ == '__main__':
    initialize()
