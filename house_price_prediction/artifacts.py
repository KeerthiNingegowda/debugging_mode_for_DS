"""Versioned artifact writing.

Every run lands in <artifact_dir>/<package version>-<git sha>/ so a model on
disk is always traceable to the code that produced it.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from . import __version__
from .config import Config


def git_sha(short: bool = False) -> str:
    cmd = ["git", "rev-parse"] + (["--short"] if short else []) + ["HEAD"]
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:  # noqa: BLE001 - git absent or not a repo is fine here
        return "unknown"


def run_dir(cfg: Config) -> Path:
    return Path(cfg.artifact_dir) / f"{__version__}-{git_sha(short=True)}"


def write_artifacts(model, cfg: Config, best: dict, cv_mape: float, fold_scores: list[float], splits) -> Path:
    out = run_dir(cfg)
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "model.joblib")
    (out / "run.json").write_text(
        json.dumps(
            {
                "package_version": __version__,
                "git_sha": git_sha(),
                "config": asdict(cfg),
                "best_params": best,
                "cv_mape": cv_mape,
                "fold_mape": fold_scores,
                "features": cfg.features,
                "python": sys.version.split()[0],
                "versions": {
                    "lightgbm": lgb.__version__,
                    "optuna": optuna.__version__,
                    "pandas": pd.__version__,
                    "numpy": np.__version__,
                },
            },
            indent=2,
        )
    )
    np.savez(out / "splits.npz", **{f"fold{i}_valid": v for i, (_, v) in enumerate(splits)})
    print(f"[artifacts] written to {out}")
    return out
