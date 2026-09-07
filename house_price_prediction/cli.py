"""Training entry point.

    uv run python -m house_price_prediction.cli --data data/houses.csv
"""

from __future__ import annotations

import argparse

import numpy as np

from . import __version__
from .artifacts import write_artifacts
from .config import Config
from .data import load_data, prepare, validate
from .model import base_params, cv_score, fit_final, tune
from .splits import make_splits


def run(cfg: Config, data_path: str) -> None:
    np.random.seed(cfg.seed)

    df = load_data(data_path, cfg)
    validate(df, cfg)
    df = prepare(df, cfg)  # once, globally - see data.prepare

    splits = make_splits(df, cfg)
    study = tune(df, splits, cfg)
    best = base_params(cfg) | study.best_params | {"subsample_freq": 1}
    cv_mape, fold_scores = cv_score(best, df, splits, cfg)
    print(f"[cv] mape={cv_mape:.4f} folds={[round(s, 4) for s in fold_scores]}")

    model = fit_final(best, df, cfg)
    write_artifacts(model, cfg, study.best_params, cv_mape, fold_scores, splits)


def main() -> None:
    ap = argparse.ArgumentParser(prog="house-price-train")
    ap.add_argument("--data", required=True, help="CSV path to the municipality extract")
    ap.add_argument("--date-col", default=None)
    ap.add_argument("--split", default="kfold", choices=["kfold", "expanding"])
    ap.add_argument("--trials", type=int, default=40)
    ap.add_argument("--artifact-dir", default="/tmp/house_price_model")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args()

    run(
        Config(
            split=args.split,
            date_col=args.date_col,
            n_trials=args.trials,
            artifact_dir=args.artifact_dir,
        ),
        args.data,
    )


if __name__ == "__main__":
    main()
