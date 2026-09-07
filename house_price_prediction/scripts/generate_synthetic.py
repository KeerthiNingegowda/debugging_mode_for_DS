"""Generate a synthetic municipality-style extract for demos and smoke tests.

    uv run python house_price_prediction/scripts/generate_synthetic.py --out datasets/houses_synthetic.csv

Deliberately outside the package: it is test scaffolding, not modelling code.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def make_synthetic(n: int = 3000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    size = rng.normal(1800, 600, n).clip(400, 6000)
    age = rng.integers(0, 120, n).astype(float)
    style = rng.choice(["detached", "semi", "townhouse", "condo"], n)
    beds = rng.integers(1, 6, n).astype(float)
    baths = rng.integers(1, 4, n).astype(float)
    minority = rng.beta(2, 5, n)
    minority_premium = np.sin(3 * minority)  # non-linear, no real-world claim

    # Deliberately non-linear: price per sqft varies by dwelling style
    # (interaction), size has diminishing returns, and age is non-monotone -
    # new builds and heritage stock both command a premium over mid-age stock.
    ppsf = np.select(
        [style == "detached", style == "semi", style == "townhouse"],
        [150.0, 120.0, 105.0],
        default=90.0,
    )
    age_effect = -1_800 * age + 22 * age**2  # dips around ~40 years, recovers
    price = (
        ppsf * size**0.92 * 3.0
        + age_effect
        + 25_000 * beds
        + 18_000 * baths
        + 200_000 * minority_premium
        + rng.normal(0, 40_000, n)
    ).clip(50_000, None)

    df = pd.DataFrame(
        {
            "house_price": price,
            "dwelling_size": size,
            "property_age": age,
            "dwelling_style": style,
            "bedrooms": beds,
            "bathrooms": baths,
            "prop_visible_minorities": minority,
        }
    )
    # inject missingness - the reason the pipeline uses LightGBM
    for col, frac in [("dwelling_size", 0.05), ("property_age", 0.08), ("bathrooms", 0.03)]:
        df.loc[rng.random(n) < frac, col] = np.nan
    return df


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="house_price_prediction/datasets/houses_synthetic.csv")
    ap.add_argument("--rows", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    make_synthetic(args.rows, args.seed).to_csv(out, index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
