# EO Data Provenance Protection via Self‑Recalibrated Watermarking (Reference Implementation)

This repository contains a **reference implementation** of the framework described in:

> Pérez Gort, M. L., & Cortesi, A. (2026). *Earth observation data provenance protection through self‑recalibrated watermarking*. **GeoInformatica**, 30(1), 6. https://doi.org/10.1007/s10707-026-00566-2

## What this implements

The paper proposes a watermarking scheme that:
- embeds a robust provenance watermark **inside EO data stored in a multi‑type repository**,
- supports **vertical synchronization** (standard embed/extract),
- adds **horizontal synchronization (self‑recalibration)**: marks can be deterministically **relocated** across eligible carriers during the operational phase,
- preserves database operability and avoids breaking downstream analytics by embedding only in distortion‑tolerant carriers.

This repo provides a practical, end‑to‑end prototype with:
- a **multidimensional repository** keyed by dimensions (e.g., space, time) and storing *facts* with multiple *versions*,
- **VPK‑like keying** and key‑dependent pseudo‑random carrier selection,
- mark embedding in numeric carriers using configurable **bit‑level** perturbation,
- deterministic **horizontal relocation** driven by a per‑epoch schedule (no server‑side log required),
- watermark extraction, similarity scoring, and a simple tamper signal.

> Note: This is a research‑grade prototype intended for experimentation. Real deployments will typically connect the repository layer to real EO storage/DBs and add richer normalization/linking.

## Quickstart

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the demo
```bash
python -m eowm demo --epochs 3
```

You should see:
- ingest of synthetic multi‑type EO facts,
- watermark embed at epoch 0,
- horizontal relocation at later epochs,
- successful extraction and similarity score,
- then a tampering simulation and detection.

### 3) CLI overview
```bash
python -m eowm --help
python -m eowm demo --help
python -m eowm ingest --help
python -m eowm embed --help
python -m eowm extract --help
python -m eowm tamper --help
```

## Concepts mapped to code

- **Repository / cube**: `eowm/repository.py`
- **Normalization + linking (toy joiner/systemizer)**: `eowm/integration.py`
- **Vertical synchronization (embed/extract)**: `eowm/watermark/vertical.py`
- **Horizontal synchronization (relocation / recalibration)**: `eowm/watermark/horizontal.py`
- **VPK + hashing + PRNG**: `eowm/watermark/crypto.py`
- **Distortion-tolerant numeric embedding (LSB/bit position)**: `eowm/watermark/embedding.py`
- **Scoring (Hamming similarity) + decision**: `eowm/watermark/scoring.py`

## Design notes

- **Carrier selection** is key‑dependent and data‑dependent. We derive a per‑carrier seed from:
  - a **virtual primary key** (VPK) built from stable attributes of the fact/version,
  - combined with the secret key `KS`.
- **Horizontal relocation** is deterministic per epoch:
  - the carrier that holds each mark is recomputed from `(KS, watermark_index, epoch, dimension_tuple, fact_id)`,
  - so extraction at a given epoch finds the same carriers without needing historical state.
- The default embedder perturbs only a single bit in a numeric value (configurable), with guardrails to avoid breaking simple analytics.

## Security & reproducibility

This code is meant to be *readable and hackable*. It does **not** attempt to be production‑hardened.
If you use it beyond experiments, review:
- key management, threat model alignment, and auditing,
- repository constraints, schema, and normalization fidelity,
- embedding distortion budgets per data type and per application.

## License

MIT (see `LICENSE`).
