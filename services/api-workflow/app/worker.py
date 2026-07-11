import signal
import time
from datetime import UTC, datetime
from .runtime import database
from .ingestion import process_next_job

running = True
def stop(*_: object) -> None:
    global running
    running = False
def heartbeat() -> None:
    with database() as connection:
        connection.execute("insert into worker_heartbeat(worker_name, last_seen_at) values ('default', %s) on conflict (worker_name) do update set last_seen_at = excluded.last_seen_at", (datetime.now(UTC),))
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
