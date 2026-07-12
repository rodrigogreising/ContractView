from datetime import UTC, datetime, timedelta
from ..application.ports.statements import Statement
from ..application.transaction import transaction as database
def main() -> None:
    with database() as connection:
        row = connection.platform.execute(Statement.WORKER_HEALTH_READ_WORKER_HEARTBEAT_001).fetchone()
    if row is None or row[0] < datetime.now(UTC) - timedelta(seconds=10):
        raise SystemExit(1)
if __name__ == "__main__":
    main()
