"""Empirical model selection.

    uv run python -m house_price_prediction.benchmark --data <csv>

Scores every candidate on the identical backtest folds and writes the table
next to the model artifacts, so the LightGBM choice is evidenced.
"""

from __future__ import annotations

import argparse
import json
import time

import numpy as np
import pandas as pd

from .artifacts import run_dir
from .candidates import candidates
from .config import TARGET, Config
from .data import load_data, prepare, train_filter, validate
from .metrics import mape
from .splits import make_splits


def score_model(model, df: pd.DataFrame, splits, cfg: Config) -> tuple[float, float, float]:
    scores, t0 = [], time.perf_counter()
    for tr_idx, va_idx in splits:
        tr = train_filter(df.iloc[tr_idx], cfg)  # training rows only
        va = df.iloc[va_idx]
        model.fit(tr[cfg.features], tr[TARGET])
        scores.append(mape(va[TARGET].to_numpy(), model.predict(va[cfg.features])))
    return float(np.mean(scores)), float(np.std(scores)), time.perf_counter() - t0


def benchmark(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    splits = make_splits(df, cfg)
    rows = []
    for name, model in candidates(cfg).items():
        mean, std, secs = score_model(model, df, splits, cfg)
        print(f"[bench] {name:<14} mape={mean:.4f} (+/-{std:.4f})  {secs:.1f}s")
        rows.append({"model": name, "cv_mape": mean, "cv_mape_std": std, "fit_seconds": secs})
    return pd.DataFrame(rows).sort_values("cv_mape").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(prog="house-price-benchmark")
    ap.add_argument("--data", required=True)
    ap.add_argument("--date-col", default=None)
    ap.add_argument("--split", default="kfold", choices=["kfold", "expanding"])
    ap.add_argument("--artifact-dir", default="/tmp/house_price_model")
    args = ap.parse_args()

    cfg = Config(split=args.split, date_col=args.date_col, artifact_dir=args.artifact_dir)
    np.random.seed(cfg.seed)

    df = load_data(args.data, cfg)
    validate(df, cfg)
    df = prepare(df, cfg)

    table = benchmark(df, cfg)
    out = run_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "model_comparison.csv", index=False)
    (out / "model_choice.json").write_text(
        json.dumps(
            {
                # The benchmark ranks candidates; the trained artifact is
                # whatever cli.py fits (LightGBM). Keys are named so the two
                # can never be confused when auditing an artifact directory.
                "benchmark_winner": table.iloc[0]["model"],
                "trained_model": "lightgbm",
                "caveats": [
                    ("Only LightGBM optimizes MAPE directly; XGBoost and HistGB optimize"
                     " MAE (no native MAPE objective). This biases toward LightGBM."),
                    ("All candidates run at defaults. Ridge is near-optimal untuned; the"
                     " boosters are not, so they are structurally handicapped here."),
                    ("Re-run on the real municipality extract before treating this as"
                     " evidence about your data."),
                ],
                "results": table.to_dict("records"),
            },
            indent=2,
        )
    )
    print(f"\nbest: {table.iloc[0]['model']} (mape={table.iloc[0]['cv_mape']:.4f})")
    print(f"[artifacts] {out / 'model_comparison.csv'}")


if __name__ == "__main__":
    main()
