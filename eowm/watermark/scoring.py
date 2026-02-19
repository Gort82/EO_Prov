from __future__ import annotations

from typing import List


def hamming_similarity(a: List[int], b: List[int]) -> float:
    if len(a) != len(b):
        raise ValueError("Bitstrings must have same length")
    if not a:
        return 1.0
    eq = sum(1 for i in range(len(a)) if a[i] == b[i])
    return eq / len(a)
