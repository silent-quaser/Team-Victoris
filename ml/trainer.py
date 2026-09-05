"""
GridGuard — XGBoost Failure Probability Trainer

Trains a component failure probability model on synthetic scenario data.

Pipeline:
    1. Load synthetic data (component_states + observations + scenarios)
    2. Build feature matrix X, binary target y
    3. Train/validation/test split (70/15/15)
    4. Train XGBoost classifier
    5. Evaluate: confusion matrix, ROC-AUC, accuracy, precision, recall
    6. Feature importance
    7. Save trained model to ml/models/failure_model.json

The trained model predicts P(component is failed) given:
    asset properties + electrical state + environmental conditions + observations

Usage:
    python -m ml.trainer                   # train from synthetic data
    from ml.trainer import train, evaluate

NOTE: Model output is a PROBABILITY, not a hard decision.
The decision "REPAIR T3 vs INSPECT T3 vs DEFER" is made by
P3's decision engine using VOI + criticality + resources.
"""
from __future__ import annotations
import json
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "failure_model.json"
METRICS_PATH = MODEL_DIR / "training_metrics.json"


def _ensure_xgboost() -> Any:
    try:
        import xgboost as xgb
        return xgb
    except ImportError:
        raise ImportError(
            "XGBoost is required for the ML model. "
            "Install with: pip install xgboost"
        )


def _ensure_sklearn() -> Any:
    try:
        import sklearn
        return sklearn
    except ImportError:
        raise ImportError("scikit-learn is required. pip install scikit-learn")


def train(
    synthetic_dir: Optional[Path] = None,
    model_path: Optional[Path] = None,
    test_size: float = 0.15,
    val_size: float = 0.15,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
    seed: int = 42,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Train the XGBoost failure probability model.

    Returns a metrics dict including AUC, accuracy, and feature importance.
    """
    xgb = _ensure_xgboost()
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import (
        roc_auc_score, accuracy_score, precision_score,
        recall_score, f1_score, confusion_matrix,
    )

    from ml.features import load_synthetic_data, build_feature_matrix

    # 1. Load data
    if verbose:
        print("[trainer] Loading synthetic scenario data ...")
    df = load_synthetic_data(synthetic_dir)
    if df is None:
        raise FileNotFoundError(
            "Synthetic data not found. Run scenario generator first:\n"
            "  python -c \"from scenario.generator import run_generation; run_generation()\""
        )

    X, y = build_feature_matrix(df)
    if verbose:
        print(f"[trainer] Dataset: {len(X):,} samples, {X.shape[1]} features")
        print(f"[trainer] Failure rate: {y.mean():.3f} ({y.sum():,} positives)")

    # 2. Split
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=seed, stratify=y
    )
    val_frac = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_frac, random_state=seed, stratify=y_temp
    )

    if verbose:
        print(f"[trainer] Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")

    # 3. Class weight for imbalanced data
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / max(pos_count, 1)

    # 4. Train XGBoost
    params = {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "learning_rate": learning_rate,
        "scale_pos_weight": scale_pos_weight,
        "eval_metric": "auc",
        "random_state": seed,
        "tree_method": "hist",
        "n_jobs": -1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "gamma": 0.1,
    }
    if verbose:
        print(f"[trainer] Training XGBoost (n_estimators={n_estimators}, depth={max_depth}) ...")

    model = xgb.XGBClassifier(**params)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

    # 5. Evaluate
    y_prob_test = model.predict_proba(X_test)[:, 1]
    y_pred_test = (y_prob_test >= 0.5).astype(int)

    auc = roc_auc_score(y_test, y_prob_test)
    acc = accuracy_score(y_test, y_pred_test)
    prec = precision_score(y_test, y_pred_test, zero_division=0)
    rec = recall_score(y_test, y_pred_test, zero_division=0)
    f1 = f1_score(y_test, y_pred_test, zero_division=0)
    cm = confusion_matrix(y_test, y_pred_test).tolist()

    # Feature importance
    feat_imp = dict(zip(X.columns.tolist(), model.feature_importances_.tolist()))
    feat_imp_sorted = dict(sorted(feat_imp.items(), key=lambda x: x[1], reverse=True))

    metrics = {
        "n_train": int(len(X_train)),
        "n_val": int(len(X_val)),
        "n_test": int(len(X_test)),
        "failure_rate": float(y.mean()),
        "roc_auc": round(auc, 4),
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": cm,
        "feature_importance": {k: round(v, 4) for k, v in feat_imp_sorted.items()},
        "model_params": params,
    }

    if verbose:
        print(f"\n[trainer] -- Test Set Metrics --------------------------")
        print(f"  ROC-AUC:   {auc:.4f}")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Precision: {prec:.4f}")
        print(f"  Recall:    {rec:.4f}")
        print(f"  F1-Score:  {f1:.4f}")
        print(f"\n[trainer] Top features by importance:")
        for feat, imp in list(feat_imp_sorted.items())[:5]:
            print(f"    {feat:<30s} {imp:.4f}")

    # 6. Save model
    save_path = model_path or MODEL_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(save_path))
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    if verbose:
        print(f"\n[trainer] Model saved: {save_path}")
        print(f"[trainer] Metrics saved: {METRICS_PATH}")

    return metrics


def evaluate(model_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and print stored training metrics."""
    path = METRICS_PATH
    if path.exists():
        with open(path) as f:
            return json.load(f)
    raise FileNotFoundError(f"No metrics found at {path}. Train the model first.")


if __name__ == "__main__":
    train()
