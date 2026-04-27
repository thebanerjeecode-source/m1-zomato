from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ranker import rank_with_llm
from .schemas import Phase2Shortlist


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 3 LLM ranking + explanations")
    parser.add_argument("--shortlist", required=True, help="Path to Phase 2 shortlist JSON")
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--out", default="phase3/artifacts/llm_ranked.json")
    args = parser.parse_args()

    shortlist_path = Path(args.shortlist)
    data = json.loads(shortlist_path.read_text(encoding="utf-8"))
    shortlist = Phase2Shortlist.model_validate(data)

    result = rank_with_llm(shortlist, source_path=str(shortlist_path), top_n=args.top_n)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")

    print("Phase 3 ranking complete")
    print(f"- out: {out_path}")
    print(f"- used_llm: {result.used_llm}")
    if result.model:
        print(f"- model: {result.model}")
    if result.warnings:
        print("- warnings:")
        for w in result.warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    main()

