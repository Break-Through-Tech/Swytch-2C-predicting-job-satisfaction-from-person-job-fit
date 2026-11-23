"""
Paired HistGradientBoosting vs logistic regression comparison on NSCG 2023 + O*NET (very_satisfied = 1).

Companion to notebooks/models/HistGradientBoosting_NSCG.ipynb. Both models are scored on exactly the same:
  * stratified 80/20 split (random_state 42) and test rows
  * 5 inner CV folds (tuning for LR, out-of-fold predictions for the F1 threshold)
  * 1,000 stratified bootstrap resamples of the test people
so the bootstrap CIs are on the HGB - LR difference itself (a paired comparison), unlike comparing HGB's single-split
numbers with the LR / DT nested-CV tables.

HGB is refit with the hyperparameters the notebook chose (results/nscg/nscg_hgb_chosen_params.csv), so run the
notebook first. LR is tuned here with the same C grid and pipeline as nscg_lr_baseline.py. The HGB pipeline below
mirrors build_pipeline() in the notebook; the refit should reproduce the notebook's test ROC-AUC.

Writes results/nscg/nscg_hgb_vs_lr_paired.csv.

Usage:
    python src/models/nscg_hgb_vs_lr.py
    python src/models/nscg_hgb_vs_lr.py --data PATH --out DIR
"""
import argparse
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from nscg_features import FEATURE_SETS, FIT_COLS, FIT_PAIRS, FitFeatures
from nscg_lr_baseline import BOOT_SEED, build_search, load_data, metrics_one
from rf_baseline import SEED, best_f1_threshold, make_boot_indices

ROOT = Path(__file__).resolve().parents[2]
COMPARED = ["ROC-AUC", "PR-AUC", "Brier score", "F1 (very satisfied)", "Balanced accuracy"]


def feature_frame(df, spec):
    cols = spec["num"] + spec["cat"] + (FIT_COLS if spec["fit"] else [])
    return df[list(dict.fromkeys(cols))].copy()


def hgb_pipeline(spec, params):
    """Same pipeline as the notebook: native NaN handling, ordinal-coded categoricals flagged for native splits."""
    parts = [("num", "passthrough", spec["num"]),
             ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=np.nan,
                                    encoded_missing_value=np.nan), spec["cat"])]
    is_cat = [False] * len(spec["num"]) + [True] * len(spec["cat"])
    if spec["fit"]:
        parts.append(("fit", FitFeatures(pairs=FIT_PAIRS), FIT_COLS))
        is_cat += [False] * (2 * len(FIT_PAIRS))
    hgb = HistGradientBoostingClassifier(
        categorical_features=is_cat, class_weight="balanced", early_stopping=True, n_iter_no_change=15,
        validation_fraction=0.1, max_iter=500, random_state=SEED,
        learning_rate=params["learning_rate"], max_depth=int(params["max_depth"]),
        min_samples_leaf=int(params["min_samples_leaf"]), l2_regularization=params["l2_regularization"])
    return Pipeline([("pre", ColumnTransformer(parts)), ("clf", hgb)])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "processed" / "nscg2023_onet_clean.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "nscg")
    args = ap.parse_args()
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    df, y, _ = load_data(args.data)
    chosen = pd.read_csv(args.out / "nscg_hgb_chosen_params.csv").set_index("set")
    train_idx, test_idx = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42, stratify=y)
    y_train, y_test = y[train_idx], y[test_idx]
    inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)

    preds = {}
    for name, spec in FEATURE_SETS.items():
        X = feature_frame(df, spec)
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        hgb = hgb_pipeline(spec, chosen.loc[name]).fit(X_train, y_train)
        search = build_search(spec, np.logspace(-4, 2, 13), inner_cv).fit(X_train, y_train)
        for label, model in [("HGB", hgb), ("LR", search.best_estimator_)]:
            # F1 threshold from training out-of-fold predictions only, so the test rows are touched once
            p_inner = cross_val_predict(clone(model), X_train, y_train, cv=inner_cv,
                                        method="predict_proba", n_jobs=-1)[:, 1]
            thr = best_f1_threshold(y_train, p_inner)
            p = model.predict_proba(X_test)[:, 1]
            preds[(label, name)] = dict(p=p, hard=(p >= thr).astype(int))
        print(f"{name}: test ROC-AUC HGB {roc_auc_score(y_test, preds[('HGB', name)]['p']):.4f}, "
              f"LR {roc_auc_score(y_test, preds[('LR', name)]['p']):.4f} (LR C = {search.best_params_['clf__C']:.4g})",
              flush=True)

    boot_idx = make_boot_indices(y_test, 1000, BOOT_SEED)  # same resamples as the notebook
    draws = {k: pd.DataFrame(Parallel(n_jobs=-1)(
        delayed(metrics_one)(y_test[i], v["p"][i], v["hard"][i]) for i in boot_idx)) for k, v in preds.items()}
    points = {k: metrics_one(y_test, v["p"], v["hard"]) for k, v in preds.items()}

    rows = []
    for name in FEATURE_SETS:
        for m in COMPARED:
            d = draws[("HGB", name)][m].to_numpy() - draws[("LR", name)][m].to_numpy()
            lo, hi = np.percentile(d, [2.5, 97.5])
            rows.append(dict(set=name, metric=m, LR=points[("LR", name)][m], HGB=points[("HGB", name)][m],
                             HGB_minus_LR=points[("HGB", name)][m] - points[("LR", name)][m], ci_low=lo, ci_high=hi,
                             bootstrap_p=min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))))
    table = pd.DataFrame(rows)
    print("\nPaired HGB - LR on the same test rows (bootstrap 95% CI on the difference; Brier: lower is better)")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    args.out.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out / "nscg_hgb_vs_lr_paired.csv", index=False)
    print(f"\nsaved {args.out / 'nscg_hgb_vs_lr_paired.csv'}")


if __name__ == "__main__":
    main()
