"""Model params, backtesting, and hyperparameter tuning."""

from __future__ import annotations

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from .config import TARGET, Config
from .data import train_filter
from .metrics import mape


def base_params(cfg: Config) -> dict:
    return {
        "objective": "mape",
        "metric": "mape",
        "verbosity": -1,
        "random_state": cfg.seed,
        "deterministic": True,
        "force_row_wise": True,
        "n_estimators": 2000,
    }


def cv_score(params: dict, df: pd.DataFrame, splits, cfg: Config) -> tuple[float, list[float]]:
    """Backtest. The >3M filter is applied per fold, to training rows only."""
    scores = []
    for tr_idx, va_idx in splits:
        tr = train_filter(df.iloc[tr_idx], cfg)
        va = df.iloc[va_idx]
        assert len(va) == len(va_idx), "validation fold must never be filtered"
        model = lgb.LGBMRegressor(**params)
        model.fit(
            tr[cfg.features],
            tr[TARGET],
            eval_X=va[cfg.features],
            eval_y=va[TARGET],
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )
        scores.append(mape(va[TARGET].to_numpy(), model.predict(va[cfg.features])))
    return float(np.mean(scores)), scores


def tune(df: pd.DataFrame, splits, cfg: Config) -> optuna.Study:
    """TPE (Bayesian) search - deliberately not grid search."""

    def objective(trial: optuna.Trial) -> float:
        params = base_params(cfg) | {
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 8, 128, log=True),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 100),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "subsample_freq": 1,
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
        }
        return cv_score(params, df, splits, cfg)[0]

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=cfg.seed),
    )
    study.optimize(objective, n_trials=cfg.n_trials)
    return study


def fit_final(best_params: dict, df: pd.DataFrame, cfg: Config) -> lgb.LGBMRegressor:
    model = lgb.LGBMRegressor(**best_params)
    train = train_filter(df, cfg)
    model.fit(train[cfg.features], train[TARGET])
    return model
