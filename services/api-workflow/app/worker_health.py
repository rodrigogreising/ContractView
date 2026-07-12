"""Worker-health composition entrypoint."""

from .integration.composition import compose

compose()

from .worker_runtime.health import main  # noqa: E402


if __name__ == "__main__":
    main()
