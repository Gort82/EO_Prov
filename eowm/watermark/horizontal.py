from __future__ import annotations

from typing import List, Tuple, Optional

from ..repository import CubeRepository
from .crypto import prng_u64
from .embedding import NumericEmbedConfig, embed_bit, extract_bit


def carrier_for_mark(ks: str, mark_index: int, epoch: int, ncarriers: int) -> int:
    """
    Deterministic carrier addressing. This function is the core of "self-recalibration":
    as epoch changes, the carrier index changes, effectively relocating marks.

    This is a practical instantiation of horizontal synchronization:
    stage A carriers (epoch 0) differ from stage B carriers (epoch t).
    """
    if ncarriers <= 0:
        raise ValueError("ncarriers must be > 0")
    seed = prng_u64(ks, str(mark_index), str(epoch))
    return seed % ncarriers


def relocate_epoch(
    repo: CubeRepository,
    ks: str,
    epoch: int,
    wbits: int,
    cfg: Optional[NumericEmbedConfig] = None,
) -> None:
    """
    Apply horizontal synchronization for `epoch` by moving marks from epoch-1 carriers
    to epoch carriers.

    Implementation strategy (deterministic, no log):
      1) Extract bits from epoch-1 carrier set
      2) Embed them into epoch carrier set

    This mimics operational-phase resynchronization while keeping detectability at any time.
    """
    if epoch <= 0:
        return  # nothing to relocate

    if cfg is None:
        cfg = NumericEmbedConfig()

    carriers: List[Tuple[Tuple[str, ...], str, int]] = []
    for dims, fact_id, vidx, fv in repo.iter_fact_versions():
        if fv.flags.get("available", True) and fv.flags.get("carrier_ok", False) and fv.is_numeric():
            carriers.append((dims, fact_id, vidx))
    if not carriers:
        raise RuntimeError("No eligible numeric carriers found.")

    # read bits from previous epoch placement
    bits_prev: List[int] = []
    for j in range(wbits):
        idx_prev = carrier_for_mark(ks, j, epoch - 1, len(carriers))
        dims, fact_id, vidx = carriers[idx_prev]
        fv = repo.cells[dims].facts[fact_id].versions[vidx]
        bits_prev.append(extract_bit(float(fv.payload), cfg))

    # write bits to new placement
    for j, bit in enumerate(bits_prev):
        idx_new = carrier_for_mark(ks, j, epoch, len(carriers))
        dims, fact_id, vidx = carriers[idx_new]
        fv = repo.cells[dims].facts[fact_id].versions[vidx]
        fv.payload, _ = embed_bit(float(fv.payload), bit, cfg)
