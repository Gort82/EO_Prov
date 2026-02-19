from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import math


@dataclass
class NumericEmbedConfig:
    """
    Bit-level embedding in numeric carriers.

    We quantize floats to a fixed-point integer (scale),
    flip a chosen bit position, then de-quantize.
    """
    scale: int = 10_000  # fixed-point multiplier
    bit_pos: int = 1     # 0 = LSB, 1 = second LSB, etc.
    clamp_min: float | None = None
    clamp_max: float | None = None


def _quantize(x: float, scale: int) -> int:
    return int(round(x * scale))


def _dequantize(q: int, scale: int) -> float:
    return q / scale


def embed_bit(x: float, bit: int, cfg: NumericEmbedConfig) -> Tuple[float, int]:
    """
    Embed a single bit into x by setting bit position cfg.bit_pos of quantized value.
    Returns: (watermarked_value, original_bit_at_pos)
    """
    q = _quantize(float(x), cfg.scale)
    mask = 1 << cfg.bit_pos
    orig = 1 if (q & mask) else 0
    if bit not in (0, 1):
        raise ValueError("bit must be 0 or 1")
    if bit == 1:
        q2 = q | mask
    else:
        q2 = q & ~mask

    y = _dequantize(q2, cfg.scale)

    if cfg.clamp_min is not None:
        y = max(cfg.clamp_min, y)
    if cfg.clamp_max is not None:
        y = min(cfg.clamp_max, y)

    return y, orig


def extract_bit(x: float, cfg: NumericEmbedConfig) -> int:
    q = _quantize(float(x), cfg.scale)
    mask = 1 << cfg.bit_pos
    return 1 if (q & mask) else 0
