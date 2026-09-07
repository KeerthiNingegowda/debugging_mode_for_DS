"""Loading, validation, and frame preparation."""

from __future__ import annotations

import pandas as pd

from .config import CATEGORICAL, TARGET, Config


def load_data(path: str, cfg: Config) -> pd.DataFrame:
    """Read a municipality snapshot extract."""
    return pd.read_csv(path)


def validate(df: pd.DataFrame, cfg: Config) -> None:
    """Fail loudly on anything that would silently corrupt the model or MAPE."""
    required = [TARGET, *cfg.features] + ([cfg.date_col] if cfg.date_col else [])
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

    if df[TARGET].isna().any():
        raise ValueError("target contains nulls")
    if (df[TARGET] <= 0).any():
        raise ValueError("target contains non-positive prices (MAPE is undefined)")

    for col in ["property_age", "bedrooms", "bathrooms", "dwelling_size"]:
        if (df[col].dropna() < 0).any():
            raise ValueError(f"{col} has negative values")

    p = df["prop_visible_minorities"].dropna()
    if not p.between(0, 1).all():
        raise ValueError("prop_visible_minorities must be a proportion in [0, 1]")

    print(f"[validate] ok: {len(df)} rows, {df[cfg.features].isna().mean().mean():.1%} mean missingness")


def prepare(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Cast categoricals ONCE, globally.

    Call this exactly once, before make_splits. Casting per fold gives
    LightGBM inconsistent category codes across folds.
    """
    df = df.copy()
    for col in CATEGORICAL:
        if col in cfg.features:
            df[col] = df[col].astype("category")
    if cfg.date_col:
        df[cfg.date_col] = pd.to_datetime(df[cfg.date_col])
        df = df.sort_values(cfg.date_col).reset_index(drop=True)
    return df


def train_filter(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Training-time filter. Applied to training rows ONLY.

    Never apply this to a validation fold: the model must be scored on the
    population it will actually see at inference time.
    """
    return df[(df[TARGET] <= cfg.price_max) & (df[TARGET] >= cfg.price_min)]
