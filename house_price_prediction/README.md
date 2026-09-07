# house_price_prediction

Training and backtesting package for a house-price model built on a snapshotted
municipality extract. LightGBM, MAPE, Optuna (TPE) tuning, versioned artifacts.

Install from the repo root:

```bash
uv sync
```

---

## Expected data

One row per property. `load_data` reads a CSV with these columns:

| Column | Type | Notes |
|---|---|---|
| `house_price` | float | target; must be non-null and **strictly positive** (MAPE divides by it) |
| `dwelling_size` | float | NaN allowed |
| `property_age` | float | NaN allowed, must be >= 0 |
| `dwelling_style` | str | cast to pandas `category` by `prepare` |
| `bedrooms` | float | NaN allowed, >= 0 |
| `bathrooms` | float | NaN allowed, >= 0 |
| `prop_visible_minorities` | float | must lie in [0, 1] |

A date column is optional and only needed for `split="expanding"`.

---

## Development API

Import surface for building on, extending, or evaluating the pipeline.

### `house_price_prediction`

| Name | Purpose |
|---|---|
| `__version__` | package version; stamped into every artifact directory |
| `Config` | all run settings (see below) |
| `TARGET`, `FEATURES`, `CATEGORICAL` | schema constants |

`Config` fields: `seed`, `n_splits`, `n_trials`, `price_max`, `price_min`,
`split` (`"kfold"` \| `"expanding"`), `date_col`, `artifact_dir`, `features`.

### `.data`

| Function | Contract |
|---|---|
| `load_data(path, cfg) -> DataFrame` | reads the CSV. Nothing else — no cleaning, no filtering |
| `validate(df, cfg) -> None` | **raises** `ValueError` on missing columns, null or non-positive prices, negative numerics, or an out-of-range proportion. Fail-loud by design |
| `prepare(df, cfg) -> DataFrame` | casts categoricals, sorts by `date_col` if set. **Call exactly once, before splitting** — casting per fold gives LightGBM inconsistent category codes |
| `train_filter(df, cfg) -> DataFrame` | applies the $3M cap and $1k floor. **Training rows only** — never apply to a validation fold |

### `.splits`

`make_splits(df, cfg) -> list[(train_idx, valid_idx)]` — seeded `KFold`, or
`TimeSeriesSplit` when `cfg.split == "expanding"` (requires `cfg.date_col`).

### `.model`

| Function | Contract |
|---|---|
| `base_params(cfg) -> dict` | fixed LightGBM params: MAPE objective, seeded and deterministic |
| `cv_score(params, df, splits, cfg) -> (mean_mape, fold_mapes)` | the backtest. Applies `train_filter` per fold to training rows only and asserts the validation fold is untouched |
| `tune(df, splits, cfg) -> optuna.Study` | TPE search over 7 params, seeded sampler, minimizing the same CV MAPE that is reported |
| `fit_final(best_params, df, cfg) -> LGBMRegressor` | refits on all filtered rows |

### `.metrics`

`mape(y_true, y_pred) -> float`. Used as the tuning objective, the LightGBM
objective, and the reported metric — no train/report mismatch.

### `.benchmark` / `.candidates`

`candidates(cfg) -> dict[str, estimator]` and `benchmark(df, cfg) -> DataFrame`
score LightGBM, XGBoost, HistGradientBoosting, and a median-imputed Ridge
baseline on identical folds. See **Model choice** below.

### `.artifacts`

`run_dir(cfg) -> Path` and `write_artifacts(model, cfg, best, cv_mape, fold_scores, splits) -> Path`.

---

## Command line

```bash
# generate a synthetic extract (demo / smoke test only)
uv run python house_price_prediction/scripts/generate_synthetic.py

# train
uv run house-price-train --data house_price_prediction/datasets/houses_synthetic.csv

# compare candidate model families
uv run house-price-benchmark --data house_price_prediction/datasets/houses_synthetic.csv
```

Both accept `--split`, `--date-col`, `--artifact-dir`; `house-price-train` also
takes `--trials` and `--version`.

---

## Inference API

**There is no `predict` module.** Inference today is: load the pickle, run the
same `prepare`, call `.predict`. That is the whole contract:

```python
import joblib, pandas as pd
from house_price_prediction import Config
from house_price_prediction.data import prepare

cfg = Config()
model = joblib.load("/tmp/house_price_model/0.1.0-<sha>/model.joblib")

df = prepare(pd.read_csv("new_properties.csv"), cfg)
preds = model.predict(df[cfg.features])
```

Four things that matter at inference time:

- **Run `prepare`, not `validate`.** `validate` asserts on `house_price`, which
  scoring data does not have.
- **Use `np.nan` for missing numerics, never `None`.** `None` makes the column
  `object` dtype and LightGBM raises `pandas dtypes must be int, float or bool`.
  Genuine NaNs are fine and are handled natively.
- **`dwelling_style` must be `category` dtype** (which `prepare` does). LightGBM
  stores the training category *values* in the booster and remaps by value, so a
  scoring frame containing only a subset of styles predicts correctly — verified.
  A style never seen in training is treated as unknown, not as a new level.
- **Column order comes from `cfg.features`.** Index with it rather than passing
  the frame whole.

`run.json` in the artifact directory records the package version, git SHA,
config, best params, feature list, and CV scores — check the feature list there
matches your `Config` before scoring with an older model.

### Known gap

There is no versioned load-and-score entry point, no schema check on scoring
input, and no guard that the model's `run.json` feature list matches the caller's
`Config`. If this model is going to be served, that wrapper should exist rather
than each caller re-implementing the four rules above.

---

## Artifacts

Every run writes to `<artifact_dir>/<__version__>-<short git sha>/`:

| File | Contents |
|---|---|
| `model.joblib` | fitted LightGBM regressor |
| `run.json` | version, git SHA, config, best params, CV + fold MAPE, library versions |
| `splits.npz` | validation indices per fold, so a backtest can be reproduced exactly |
| `model_comparison.csv` | benchmark table (written by `house-price-benchmark`) |
| `model_choice.json` | benchmark winner, the model actually trained, and the caveats |

Reproducibility comes from seeding numpy, the Optuna TPE sampler, and LightGBM
(`random_state` + `deterministic` + `force_row_wise`), and from persisting the
split indices.

---

## Backtesting

The municipality data is a **snapshot with no time axis**, so the default is
seeded K-fold. If your real extract carries a sale or snapshot date, use it:

```bash
uv run house-price-train --data extract.csv --split expanding --date-col sale_date
```

Random K-fold on dated sales leaks future comparables into training and will
flatter the MAPE.

---

## Model choice

Measured on the synthetic extract, identical folds, identical filter and metric:

| model | cv_mape | std |
|---|---|---|
| hist_gbm | 0.0750 | 0.0035 |
| lightgbm | 0.0757 | 0.0028 |
| xgboost | 0.0805 | 0.0028 |
| ridge_imputed | 0.0865 | 0.0034 |

LightGBM ties the best model at roughly 6x the speed; it does not clearly win on
accuracy. Three caveats, also recorded in `model_choice.json`:

1. These numbers come from **synthetic data**. Re-run `house-price-benchmark` on
   the real extract before citing them.
2. Only LightGBM optimizes MAPE directly — XGBoost has no native MAPE objective,
   so it and HistGB optimize MAE. This biases toward LightGBM.
3. All candidates run at library defaults, which handicaps the boosters relative
   to the effectively hyperparameter-free Ridge.

---

## A note on `prop_visible_minorities`

It is included as specified, but using a neighbourhood racial-composition
variable in an automated valuation model is a fair-housing / disparate-impact
exposure. It is listed in `FEATURES` in `config.py` so removing it is a one-line
change; re-run the benchmark afterwards to see what it costs.
