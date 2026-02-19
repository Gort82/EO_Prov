"""
EO Watermarking CLI (reference implementation)

Usage:
  python -m eowm demo --epochs 3
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from .demo import run_demo
from .repository import CubeRepository
from .integration import ingest_synthetic
from .watermark.vertical import embed_watermark, extract_watermark
from .watermark.horizontal import relocate_epoch
from .watermark.scoring import hamming_similarity


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="eowm", description="EO self-recalibrated watermarking (prototype).")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="Run an end-to-end demo.")
    d.add_argument("--epochs", type=int, default=3, help="Number of epochs to simulate.")
    d.add_argument("--ks", type=str, default="demo-secret-key", help="Secret key (KS).")
    d.add_argument("--provenance", type=str, default="provider=A;roi=R1;time=2026-01;pipeline=v1",
                   help="Provenance string to encode.")
    d.add_argument("--wbits", type=int, default=128, help="Watermark size in bits.")
    d.add_argument("--tau", type=float, default=0.85, help="Similarity threshold for acceptance.")

    ing = sub.add_parser("ingest", help="Ingest synthetic EO data into a new repository JSON file.")
    ing.add_argument("--out", type=str, required=True, help="Output path for repository JSON.")
    ing.add_argument("--seed", type=int, default=42)

    emb = sub.add_parser("embed", help="Embed a watermark at a given epoch into a repository JSON.")
    emb.add_argument("--repo", type=str, required=True)
    emb.add_argument("--out", type=str, required=True)
    emb.add_argument("--ks", type=str, required=True)
    emb.add_argument("--provenance", type=str, required=True)
    emb.add_argument("--epoch", type=int, default=0)
    emb.add_argument("--wbits", type=int, default=128)

    ext = sub.add_parser("extract", help="Extract a watermark at a given epoch from a repository JSON.")
    ext.add_argument("--repo", type=str, required=True)
    ext.add_argument("--ks", type=str, required=True)
    ext.add_argument("--provenance", type=str, required=True)
    ext.add_argument("--epoch", type=int, default=0)
    ext.add_argument("--wbits", type=int, default=128)

    rel = sub.add_parser("relocate", help="Apply horizontal synchronization for an epoch.")
    rel.add_argument("--repo", type=str, required=True)
    rel.add_argument("--out", type=str, required=True)
    rel.add_argument("--ks", type=str, required=True)
    rel.add_argument("--epoch", type=int, required=True)
    rel.add_argument("--wbits", type=int, default=128)

    tam = sub.add_parser("tamper", help="Simulate tampering on a repository JSON.")
    tam.add_argument("--repo", type=str, required=True)
    tam.add_argument("--out", type=str, required=True)
    tam.add_argument("--rate", type=float, default=0.15, help="Fraction of numeric carriers to modify.")
    tam.add_argument("--seed", type=int, default=7)

    return p


def main() -> None:
    p = _build_parser()
    args = p.parse_args()

    if args.cmd == "demo":
        run_demo(epochs=args.epochs, ks=args.ks, provenance=args.provenance, wbits=args.wbits, tau=args.tau)
        return

    if args.cmd == "ingest":
        repo = CubeRepository()
        ingest_synthetic(repo, seed=args.seed)
        repo.to_json(args.out)
        print(f"Wrote synthetic repository to {args.out}")
        return

    if args.cmd == "embed":
        repo = CubeRepository.from_json(args.repo)
        wm = embed_watermark(repo, ks=args.ks, provenance=args.provenance, wbits=args.wbits, epoch=args.epoch)
        repo.to_json(args.out)
        print(json.dumps({"embedded_bits": len(wm), "epoch": args.epoch}, indent=2))
        return

    if args.cmd == "relocate":
        repo = CubeRepository.from_json(args.repo)
        relocate_epoch(repo, ks=args.ks, epoch=args.epoch, wbits=args.wbits)
        repo.to_json(args.out)
        print(json.dumps({"relocated_epoch": args.epoch}, indent=2))
        return

    if args.cmd == "extract":
        repo = CubeRepository.from_json(args.repo)
        w_expected = extract_watermark.expected_bits(ks=args.ks, provenance=args.provenance, wbits=args.wbits)
        w_got = extract_watermark(repo, ks=args.ks, provenance=args.provenance, wbits=args.wbits, epoch=args.epoch)
        sim = hamming_similarity(w_expected, w_got)
        print(json.dumps({"epoch": args.epoch, "similarity": sim, "accept": sim >= 0.85}, indent=2))
        return

    if args.cmd == "tamper":
        from .tamper import tamper_repository
        repo = CubeRepository.from_json(args.repo)
        tamper_repository(repo, rate=args.rate, seed=args.seed)
        repo.to_json(args.out)
        print(json.dumps({"tampered": True, "rate": args.rate}, indent=2))
        return


if __name__ == "__main__":
    main()
