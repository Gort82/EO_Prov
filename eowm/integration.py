from __future__ import annotations

import random
from typing import Dict, Any

from .repository import CubeRepository, FactVersion


def ingest_synthetic(repo: CubeRepository, seed: int = 42) -> None:
    """
    Toy joiner/systemizer that creates a multi-type EO repository.

    Dimensions: (space, time, provider)
    Facts:
      - "ndvi" numeric, multiple versions
      - "lst" numeric, multiple versions
      - "cloud_mask" numeric-like percentage
      - "metadata" text (not used for numeric watermarking in this prototype)
    """
    rng = random.Random(seed)
    spaces = ["ROI_A", "ROI_B"]
    times = ["2026-01", "2026-02"]
    providers = ["P1", "P2", "P3"]

    for sp in spaces:
        for tm in times:
            for pr in providers:
                dims = (sp, tm, pr)

                # create several versions per fact within a plausible threshold
                base_ndvi = rng.uniform(0.1, 0.9)
                base_lst = rng.uniform(260.0, 320.0)
                base_cloud = rng.uniform(0.0, 0.7)

                for v in range(3):  # versions
                    repo.upsert_fact_version(
                        dims, "ndvi",
                        FactVersion(
                            payload=round(base_ndvi + rng.uniform(-0.01, 0.01), 5),
                            meta={"space": sp, "time": tm, "provider": pr, "fact": "ndvi", "v": v},
                            flags={"carrier_ok": True, "available": True},
                        )
                    )
                    repo.upsert_fact_version(
                        dims, "lst",
                        FactVersion(
                            payload=round(base_lst + rng.uniform(-0.5, 0.5), 3),
                            meta={"space": sp, "time": tm, "provider": pr, "fact": "lst", "v": v},
                            flags={"carrier_ok": True, "available": True},
                        )
                    )
                    repo.upsert_fact_version(
                        dims, "cloud_mask",
                        FactVersion(
                            payload=round(base_cloud + rng.uniform(-0.02, 0.02), 5),
                            meta={"space": sp, "time": tm, "provider": pr, "fact": "cloud_mask", "v": v},
                            flags={"carrier_ok": True, "available": True},
                        )
                    )

                # store some non-numeric payload too
                repo.upsert_fact_version(
                    dims, "metadata",
                    FactVersion(
                        payload=f"EO package {sp}/{tm} from {pr}",
                        meta={"space": sp, "time": tm, "provider": pr, "fact": "metadata"},
                        flags={"carrier_ok": False, "available": True},
                    )
                )
