from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from datasets import Dataset, load_dataset


DATASET_ID = "ManikaSaini/zomato-restaurant-recommendation"


def _norm_str(s: Any) -> Optional[str]:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        s = str(s)
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    return re.sub(r"\s+", " ", s)


def _norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _split_cuisines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    else:
        s = _norm_str(value)
        if not s:
            return []
        items = re.split(r"[,/|;]+", s)
    out: list[str] = []
    for item in items:
        s = _norm_str(item)
        if not s:
            continue
        out.append(s.lower())
    # de-dupe preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for c in out:
        if c in seen:
            continue
        seen.add(c)
        deduped.append(c)
    return deduped


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = _norm_str(value)
    if not s:
        return None
    
    # Remove commas used as thousands separators
    s = s.replace(",", "")
    
    m = re.search(r"(\d+(\.\d+)?)", s)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _parse_cost(value: Any) -> Optional[float]:
    # Keep numeric if present; cost-level mapping happens in Phase 2.
    return _parse_float(value)


def _parse_rating(value: Any) -> Optional[float]:
    r = _parse_float(value)
    if r is None:
        return None
    # Clamp to 0..5 (common rating range)
    return max(0.0, min(5.0, r))


@dataclass(frozen=True)
class FieldMap:
    id: Optional[str]
    name: Optional[str]
    location: Optional[str]
    cuisines: Optional[str]
    cost: Optional[str]
    rating: Optional[str]


def _pick_field(columns: list[str], candidates: list[str]) -> Optional[str]:
    normed = {_norm_key(c): c for c in columns}
    for cand in candidates:
        key = _norm_key(cand)
        if key in normed:
            return normed[key]
    return None


def infer_field_map(columns: list[str]) -> FieldMap:
    return FieldMap(
        id=_pick_field(columns, ["id", "restaurant_id", "res_id", "rid"]),
        name=_pick_field(columns, ["name", "restaurant_name", "restaurantname", "rest_name"]),
        location=_pick_field(columns, ["location", "city", "locality", "area"]),
        cuisines=_pick_field(columns, ["cuisines", "cuisine", "cuisine_type"]),
        cost=_pick_field(columns, ["cost", "average_cost_for_two", "avg_cost_for_two", "price", "costfortwo", "approx_cost(for two people)"]),
        rating=_pick_field(columns, ["rating", "aggregate_rating", "user_rating", "rating_value", "rate"]),
    )


def load_source_dataset(dataset_id: str = DATASET_ID) -> Dataset:
    ds_dict = load_dataset(dataset_id)
    # Prefer 'train' split if present; otherwise take the first split.
    if "train" in ds_dict:
        return ds_dict["train"]
    return next(iter(ds_dict.values()))


def normalize_dataset(ds: Dataset, fmap: FieldMap) -> tuple[Dataset, dict[str, Any]]:
    cols = ds.column_names

    def norm_row(row: dict[str, Any]) -> dict[str, Any]:
        raw_id = row.get(fmap.id) if fmap.id else None
        raw_name = row.get(fmap.name) if fmap.name else None
        raw_loc = row.get(fmap.location) if fmap.location else None
        raw_cuis = row.get(fmap.cuisines) if fmap.cuisines else None
        raw_cost = row.get(fmap.cost) if fmap.cost else None
        raw_rating = row.get(fmap.rating) if fmap.rating else None

        name = _norm_str(raw_name)
        location = _norm_str(raw_loc)
        cuisines = _split_cuisines(raw_cuis)
        cost = _parse_cost(raw_cost)
        rating = _parse_rating(raw_rating)

        # Provide a stable id: use source id if present, else derive from name+location.
        source_id = _norm_str(raw_id)
        if not source_id:
            base = f"{(name or 'unknown').lower()}|{(location or 'unknown').lower()}"
            source_id = re.sub(r"[^a-z0-9|]+", "-", base).strip("-")

        return {
            "id": source_id,
            "name": name,
            "location": location,
            "cuisines": cuisines,
            "cost": cost,
            "rating": rating,
        }

    normalized = ds.map(norm_row, remove_columns=cols, load_from_cache_file=False)

    meta = {
        "dataset_id": DATASET_ID,
        "source_columns": cols,
        "field_map": fmap.__dict__,
    }
    return normalized, meta


def write_artifacts(ds: Dataset, meta: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / "zomato_clean.parquet"
    manifest_path = out_dir / "manifest.json"

    ds.to_parquet(str(parquet_path))

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "row_count": ds.num_rows,
        "columns": ds.column_names,
        **meta,
        "artifacts": {
            "parquet": str(parquet_path),
            "manifest": str(manifest_path),
        },
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest

