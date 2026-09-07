"""Backtest splits."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, TimeSeriesSplit

from .config import Config


def make_splits(df: pd.DataFrame, cfg: Config) -> list[tuple[np.ndarray, np.ndarray]]:
    if cfg.split == "expanding":
        if not cfg.date_col:
            raise ValueError("split='expanding' requires date_col")
        splitter = TimeSeriesSplit(n_splits=cfg.n_splits)
    elif cfg.split == "kfold":
        # No time axis in the municipality snapshot, so random K-fold it is.
        splitter = KFold(n_splits=cfg.n_splits, shuffle=True, random_state=cfg.seed)
    else:
        raise ValueError(f"unknown split: {cfg.split}")
    return list(splitter.split(df))
