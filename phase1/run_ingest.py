from __future__ import annotations

import os
from pathlib import Path

# Ensure HF caches live inside the workspace (Cursor sandbox may block ~/.*).
# Must be set BEFORE importing datasets/huggingface modules.
_workspace_cache = Path(__file__).resolve().parent / "artifacts" / ".hf_cache"
_workspace_cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_CACHE_HOME", str(_workspace_cache / "xdg"))
os.environ.setdefault("HF_HOME", str(_workspace_cache / "hf_home"))
os.environ.setdefault("HF_DATASETS_CACHE", str(_workspace_cache / "datasets"))
os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(_workspace_cache / "hub"))

from .ingest import infer_field_map, load_source_dataset, normalize_dataset, write_artifacts


def main() -> None:
    ds = load_source_dataset()
    fmap = infer_field_map(ds.column_names)
    normalized, meta = normalize_dataset(ds, fmap)

    out_dir = Path(__file__).resolve().parent / "artifacts"
    manifest = write_artifacts(normalized, meta, out_dir)

    print("Phase 1 ingestion complete")
    print(f"- rows: {manifest['row_count']}")
    print(f"- parquet: {manifest['artifacts']['parquet']}")
    print(f"- manifest: {manifest['artifacts']['manifest']}")
    print(f"- field_map: {manifest['field_map']}")


if __name__ == "__main__":
    main()

