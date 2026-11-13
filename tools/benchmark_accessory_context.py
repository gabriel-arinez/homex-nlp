"""Measure repeated accessory-count lookup at controlled input lengths.

Run with PYTHONPATH pointing to the desired package tree; output is JSON.
This benchmark is diagnostic, not a wall-clock pass/fail gate.
"""

import json
import statistics
from time import perf_counter

from homex_nlp.rules import find_accessory_quantity


def benchmark():
    rows = []
    for length in (1_000, 5_000, 10_000, 20_000):
        phrase = "dos USB; "
        text = (phrase * (length // len(phrase) + 1))[:length]
        starts = [i for i in range(len(text)) if text.startswith("USB", i)]
        timings = []
        for _ in range(3):
            started = perf_counter()
            counts = [find_accessory_quantity(text, start, start + 3) for start in starts]
            timings.append(perf_counter() - started)
            assert all(count is not None and count.value == 2 for count in counts)
        rows.append(
            {
                "characters": length,
                "accessory_mentions": len(starts),
                "repetitions": 3,
                "seconds": timings,
                "median_seconds": statistics.median(timings),
            }
        )
    return rows


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
