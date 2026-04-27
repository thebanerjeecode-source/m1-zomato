from __future__ import annotations

import argparse
import json
from pathlib import Path

from .retrieval import build_shortlist
from .schemas import BudgetLevel, Preferences


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 2 deterministic shortlist builder")
    parser.add_argument("--dataset", default="phase1/artifacts/zomato_clean.parquet")
    parser.add_argument("--location", required=True)
    parser.add_argument("--location-match", default="contains", choices=["contains", "exact"])
    parser.add_argument("--budget", default="medium", choices=[b.value for b in BudgetLevel])
    parser.add_argument("--cuisine", required=True)
    parser.add_argument("--min-rating", type=float, default=0.0)
    parser.add_argument("--top-k", type=int, default=25)
    parser.add_argument("--out", default="phase2/artifacts/shortlist.json")
    args = parser.parse_args()

    prefs = Preferences(
        location=args.location,
        location_match=args.location_match,
        budget=BudgetLevel(args.budget),
        cuisine=args.cuisine,
        min_rating=args.min_rating,
        top_k=args.top_k,
    )

    resp = build_shortlist(Path(args.dataset), prefs)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(resp.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    print("Phase 2 shortlist complete")
    print(f"- out: {out_path}")
    print(f"- items: {len(resp.shortlist)}")
    if resp.warnings:
        print("- warnings:")
        for w in resp.warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    main()

