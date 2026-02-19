from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple, Optional


DimensionTuple = Tuple[str, ...]


@dataclass
class FactVersion:
    """
    A single version of a fact. In the paper, multiple versions of a fact
    (within a distortion threshold) are used for correction and watermarking.

    For simplicity we store:
      - payload: typed value (numeric, text, vector-like dict, etc.)
      - meta: stable attributes used for VPK derivation
      - flags: availability for watermark synchronization
    """
    payload: Any
    meta: Dict[str, Any]
    flags: Dict[str, Any]

    def is_numeric(self) -> bool:
        return isinstance(self.payload, (int, float))

    def clone(self) -> "FactVersion":
        return FactVersion(payload=self.payload, meta=dict(self.meta), flags=dict(self.flags))


@dataclass
class Fact:
    fact_id: str
    versions: List[FactVersion]


@dataclass
class Cell:
    """
    A cell in the multidimensional cube, identified by a dimension tuple
    (e.g., (space_id, time_id, provider_id, ...)).
    """
    dims: DimensionTuple
    facts: Dict[str, Fact]  # fact_id -> Fact


class CubeRepository:
    """
    In-memory prototype of a multidimensional repository.

    This is intentionally simple: a dict from dimension tuple -> Cell.
    """
    def __init__(self) -> None:
        self.cells: Dict[DimensionTuple, Cell] = {}

    def upsert_fact_version(self, dims: DimensionTuple, fact_id: str, fv: FactVersion) -> None:
        cell = self.cells.get(dims)
        if cell is None:
            cell = Cell(dims=dims, facts={})
            self.cells[dims] = cell
        fact = cell.facts.get(fact_id)
        if fact is None:
            fact = Fact(fact_id=fact_id, versions=[])
            cell.facts[fact_id] = fact
        fact.versions.append(fv)

    def iter_fact_versions(self):
        for dims, cell in self.cells.items():
            for fact_id, fact in cell.facts.items():
                for vidx, fv in enumerate(fact.versions):
                    yield dims, fact_id, vidx, fv

    def to_dict(self) -> Dict[str, Any]:
        # JSON needs string keys; encode dimension tuples as joined strings.
        out: Dict[str, Any] = {"cells": {}}
        for dims, cell in self.cells.items():
            k = "|".join(dims)
            out["cells"][k] = {
                "dims": list(dims),
                "facts": {
                    fid: {
                        "fact_id": fid,
                        "versions": [asdict(v) for v in f.versions],
                    } for fid, f in cell.facts.items()
                }
            }
        return out

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CubeRepository":
        repo = cls()
        for _, cell in d.get("cells", {}).items():
            dims = tuple(cell["dims"])
            for fid, f in cell["facts"].items():
                for v in f["versions"]:
                    repo.upsert_fact_version(
                        dims=dims,
                        fact_id=fid,
                        fv=FactVersion(payload=v["payload"], meta=v["meta"], flags=v["flags"]),
                    )
        return repo

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, path: str) -> "CubeRepository":
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        return cls.from_dict(d)
