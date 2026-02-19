from __future__ import annotations

import hashlib
from typing import Iterable, List


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def xor_bytes(a: bytes, b: bytes) -> bytes:
    n = min(len(a), len(b))
    return bytes([a[i] ^ b[i] for i in range(n)])


def bits_from_digest(d: bytes, nbits: int) -> List[int]:
    out: List[int] = []
    for byte in d:
        for j in range(8):
            out.append((byte >> (7 - j)) & 1)
            if len(out) >= nbits:
                return out
    # If nbits > len(d)*8, extend by hashing again (counter mode)
    counter = 1
    cur = d
    while len(out) < nbits:
        cur = sha256_bytes(cur + counter.to_bytes(4, "big"))
        counter += 1
        for byte in cur:
            for j in range(8):
                out.append((byte >> (7 - j)) & 1)
                if len(out) >= nbits:
                    return out
    return out


def watermark_bits(ks: str, provenance: str, wbits: int) -> List[int]:
    """
    Deterministically derive watermark bits from (KS, provenance).
    This matches the paper's idea that provenance is encoded and synchronized with KS.
    """
    seed = sha256_bytes((ks + "|" + provenance).encode("utf-8"))
    return bits_from_digest(seed, wbits)


def vpk(meta: dict) -> str:
    """
    Virtual Primary Key-like construction from stable meta fields.
    In practice, choose fields stable under benign updates.

    Here we sort items to produce a stable string.
    """
    items = sorted((str(k), str(v)) for k, v in meta.items())
    s = "|".join([f"{k}={v}" for k, v in items])
    return sha256_hex(s.encode("utf-8"))


def prng_u64(*parts: str) -> int:
    """
    Deterministic PRNG seed expansion: hash concatenated parts to 64-bit int.
    """
    h = sha256_bytes("|".join(parts).encode("utf-8"))
    return int.from_bytes(h[:8], "big")
