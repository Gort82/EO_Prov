from __future__ import annotations

import random
from typing import List

from .repository import CubeRepository
from .integration import ingest_synthetic
from .watermark.vertical import embed_watermark, extract_watermark, expected_bits
from .watermark.horizontal import relocate_epoch
from .watermark.scoring import hamming_similarity
from .tamper import tamper_repository


def run_demo(epochs: int, ks: str, provenance: str, wbits: int = 128, tau: float = 0.85) -> None:
    repo = CubeRepository()
    ingest_synthetic(repo, seed=42)

    print("== Embed (epoch 0)")
    W = embed_watermark(repo, ks=ks, provenance=provenance, wbits=wbits, epoch=0)
    print(f"Embedded {len(W)} bits.")

    for e in range(1, epochs):
        print(f"== Horizontal resynchronization (epoch {e})")
        relocate_epoch(repo, ks=ks, epoch=e, wbits=wbits)

        Wexp = expected_bits(ks, provenance, wbits)
        Wgot = extract_watermark(repo, ks=ks, provenance=provenance, wbits=wbits, epoch=e)
        sim = hamming_similarity(Wexp, Wgot)
        print(f"Extracted at epoch {e}: similarity={sim:.3f} accept={sim >= tau}")

    print("== Tamper simulation")
    tamper_repository(repo, rate=0.20, seed=7)

    e = max(0, epochs - 1)
    Wexp = expected_bits(ks, provenance, wbits)
    Wgot = extract_watermark(repo, ks=ks, provenance=provenance, wbits=wbits, epoch=e)
    sim = hamming_similarity(Wexp, Wgot)
    print(f"After tampering @epoch {e}: similarity={sim:.3f} accept={sim >= tau}")
