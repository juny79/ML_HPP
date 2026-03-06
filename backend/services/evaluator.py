import os
import numpy as np
import pandas as pd


def _rmse(a, b):
    return float(np.sqrt(np.mean((a - b) ** 2)))


def evaluate_submission(filepath, username=None):
    # Look for ground truth relative to project layout
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    gt_path = os.path.abspath(os.path.join(base, '..', 'data', 'ground_truth.csv'))
    if not os.path.exists(gt_path):
        return None

    try:
        pred = pd.read_csv(filepath)
        gt = pd.read_csv(gt_path)

        # Expect both files to have a numeric column named 'value'
        if 'value' in pred.columns and 'value' in gt.columns:
            # Align by index; callers should ensure consistent ordering
            return _rmse(pred['value'].to_numpy(), gt['value'].to_numpy())
    except Exception:
        return None

    return None
