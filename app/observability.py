import time
from collections.abc import Iterator
from contextlib import contextmanager


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
