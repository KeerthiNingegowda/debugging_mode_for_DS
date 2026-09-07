"""Candidate models for the selection benchmark.

All four are evaluated on the same folds, with the same training-time filter
and the same MAPE, so the choice of LightGBM is an empirical result rather
than an assertion.

- lightgbm / xgboost / hist_gbm: handle NaN natively, no imputation needed.
- ridge_imputed: median-imputed + one-hot linear floor. If a booster cannot
  beat this, the extra complexity is not paying for itself.

Two caveats on fairness, both of which flatter LightGBM:

1. Only LightGBM optimizes the reported metric. XGBoost has no native MAPE
   objective, so it and HistGB optimize MAE instead.
2. Every candidate runs at library defaults. Ridge at defaults is close to
   Ridge tuned; a booster at defaults is not (tuning moved LightGBM from
   0.1315 to 0.1266 on an earlier data version), so the boosters are
   handicapped relative to what tuning would give them.

Both are accepted deliberately to keep the comparison one screen of code.
"""

from __future__ import annotations

import lightgbm as lgb
import xgboost as xgb
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import CATEGORICAL, Config


def _ridge(cfg: Config) -> Pipeline:
    numeric = [c for c in cfg.features if c not in CATEGORICAL]
    categorical = [c for c in cfg.features if c in CATEGORICAL]
    pre = ColumnTransformer(
        [
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
        ]
    )
    return make_pipeline(pre, Ridge(alpha=1.0, random_state=cfg.seed))


def candidates(cfg: Config) -> dict:
    """Default-configured candidates - no tuning, so the comparison is fair."""
    return {
        "lightgbm": lgb.LGBMRegressor(
            objective="mape", random_state=cfg.seed, verbosity=-1,
            deterministic=True, force_row_wise=True,
        ),
        "xgboost": xgb.XGBRegressor(
            objective="reg:absoluteerror", random_state=cfg.seed,
            enable_categorical=True, tree_method="hist",
        ),
        "hist_gbm": HistGradientBoostingRegressor(
            loss="absolute_error", random_state=cfg.seed,
            categorical_features="from_dtype",
        ),
        "ridge_imputed": _ridge(cfg),
    }
