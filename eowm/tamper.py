from __future__ import annotations

import random
from typing import Tuple, List

from .repository import CubeRepository


def tamper_repository(repo: CubeRepository, rate: float = 0.15, seed: int = 7) -> None:
    """
    Simple attacker model: randomly modify a fraction of numeric carriers.
    """
    rng = random.Random(seed)
    numeric_refs: List[Tuple[Tuple[str, ...], str, int]] = []

    for dims, fact_id, vidx, fv in repo.iter_fact_versions():
        if fv.is_numeric() and fv.flags.get("carrier_ok", False):
            numeric_refs.append((dims, fact_id, vidx))

    rng.shuffle(numeric_refs)
    k = int(round(rate * len(numeric_refs)))
    for i in range(k):
        dims, fact_id, vidx = numeric_refs[i]
        fv = repo.cells[dims].facts[fact_id].versions[vidx]
        # add a small perturbation (could flip embedded bits)
        fv.payload = float(fv.payload) + rng.uniform(-0.02, 0.02)
