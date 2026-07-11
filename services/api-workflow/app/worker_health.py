from datetime import UTC, datetime, timedelta
from .runtime import database
def main() -> None:
    with database() as connection:
        row = connection.execute("select last_seen_at from worker_heartbeat where worker_name = 'default'").fetchone()
    if row is None or row[0] < datetime.now(UTC) - timedelta(seconds=10):
        raise SystemExit(1)
if __name__ == "__main__":
    main()
