from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional

from ..repository import CubeRepository, FactVersion
from .crypto import watermark_bits, vpk, prng_u64
from .embedding import NumericEmbedConfig, embed_bit, extract_bit
from .horizontal import carrier_for_mark


@dataclass
class EmbedResult:
    watermark: List[int]
    epoch: int
    embedded: int
    skipped: int


def embed_watermark(
    repo: CubeRepository,
    ks: str,
    provenance: str,
    wbits: int = 128,
    epoch: int = 0,
    cfg: Optional[NumericEmbedConfig] = None,
) -> List[int]:
    """
    Vertical embedding at a given epoch.

    Carrier selection uses the same deterministic function used by extraction at the same epoch,
    so embed/extract align (vertical synchronization).
    """
    if cfg is None:
        cfg = NumericEmbedConfig()

    W = watermark_bits(ks, provenance, wbits)

    # Collect all eligible numeric carriers to allow deterministic addressing.
    carriers: List[Tuple[Tuple[str, ...], str, int]] = []
    for dims, fact_id, vidx, fv in repo.iter_fact_versions():
        if fv.flags.get("available", True) and fv.flags.get("carrier_ok", False) and fv.is_numeric():
            carriers.append((dims, fact_id, vidx))

    if not carriers:
        raise RuntimeError("No eligible numeric carriers found.")

    # Embed each mark into a deterministic carrier for this epoch.
    for j, bit in enumerate(W):
        idx = carrier_for_mark(ks, j, epoch, len(carriers))
        dims, fact_id, vidx = carriers[idx]
        fv = repo.cells[dims].facts[fact_id].versions[vidx]
        y, _ = embed_bit(float(fv.payload), bit, cfg)
        fv.payload = y

    return W


def expected_bits(ks: str, provenance: str, wbits: int) -> List[int]:
    return watermark_bits(ks, provenance, wbits)


def extract_watermark(
    repo: CubeRepository,
    ks: str,
    provenance: str,
    wbits: int = 128,
    epoch: int = 0,
    cfg: Optional[NumericEmbedConfig] = None,
) -> List[int]:
    """
    Vertical extraction at a given epoch. It must match the same deterministic carrier addressing
    used by embed (and by horizontal relocation schedule for later epochs).
    """
    if cfg is None:
        cfg = NumericEmbedConfig()

    carriers: List[Tuple[Tuple[str, ...], str, int]] = []
    for dims, fact_id, vidx, fv in repo.iter_fact_versions():
        if fv.flags.get("available", True) and fv.flags.get("carrier_ok", False) and fv.is_numeric():
            carriers.append((dims, fact_id, vidx))

    if not carriers:
        raise RuntimeError("No eligible numeric carriers found.")

    Wp: List[int] = []
    for j in range(wbits):
        idx = carrier_for_mark(ks, j, epoch, len(carriers))
        dims, fact_id, vidx = carriers[idx]
        fv = repo.cells[dims].facts[fact_id].versions[vidx]
        Wp.append(extract_bit(float(fv.payload), cfg))
    return Wp
