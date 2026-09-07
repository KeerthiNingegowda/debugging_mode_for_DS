"""Single source of truth for schema and run settings."""

from __future__ import annotations

from dataclasses import dataclass, field

TARGET = "house_price"
CATEGORICAL = ["dwelling_style"]
FEATURES = [
    "dwelling_size",
    "property_age",
    "dwelling_style",
    "bedrooms",
    "bathrooms",
    "prop_visible_minorities",  # fair-housing exposure: drop here to exclude
]


@dataclass
class Config:
    seed: int = 42
    n_splits: int = 5
    n_trials: int = 40
    price_max: float = 3_000_000.0  # training-time filter only
    price_min: float = 1_000.0      # guards MAPE against $0/$1 transfers
    split: str = "kfold"            # "kfold" | "expanding"
    date_col: str | None = None     # required when split == "expanding"
    artifact_dir: str = "/tmp/house_price_model"
    features: list[str] = field(default_factory=lambda: list(FEATURES))
