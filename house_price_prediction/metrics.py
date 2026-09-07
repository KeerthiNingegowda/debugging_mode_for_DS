"""Evaluation metric."""

from __future__ import annotations

import numpy as np


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs((y_true - y_pred) / y_true)))
