import time
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def timer(metrics: dict, key: str) -> Iterator[None]:
    start = time.perf_counter()

    try:
        yield
    finally:
        metrics[key] = round(
            time.perf_counter() - start,
            6,
        )
