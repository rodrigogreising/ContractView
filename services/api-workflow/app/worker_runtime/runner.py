import signal
import time
from datetime import UTC, datetime
from ..ingestion import process_next_job

from ..application.ports.statements import Statement
from ..application.transaction import transaction as database
running = True
def stop(*_: object) -> None:
    global running
    running = False
def heartbeat() -> None:
    with database() as connection:
        connection.platform.execute(Statement.WORKER_WRITE_WORKER_HEARTBEAT_001, (datetime.now(UTC),))
        connection.commit()
def main() -> None:
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while running:
        heartbeat()
        if not process_next_job():
            time.sleep(0.5)
if __name__ == "__main__":
    main()
