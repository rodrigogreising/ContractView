"""Worker composition entrypoint; worker behavior lives in worker_runtime."""

from .integration.composition import compose

compose()

from .worker_runtime.runner import main  # noqa: E402


if __name__ == "__main__":
    main()
