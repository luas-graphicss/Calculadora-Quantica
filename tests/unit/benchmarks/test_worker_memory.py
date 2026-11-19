import os

from benchmarks.harness.worker_memory import (
    own_peak_rss_bytes,
    require_children_listing,
    worker_peak_rss_bytes,
)

MEBIBYTE = 1024**2


def test_own_peak_is_the_high_water_mark_of_this_process() -> None:
    before = own_peak_rss_bytes()
    held = bytearray(32 * MEBIBYTE)
    held[::4096] = b"\x01" * len(held[::4096])

    assert own_peak_rss_bytes() >= before
    assert own_peak_rss_bytes() >= len(held)


def test_a_process_without_calculation_workers_reports_no_worker_peak() -> None:
    require_children_listing(os.getpid())

    assert worker_peak_rss_bytes(os.getpid()) == 0
