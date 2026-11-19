"""
Train the final NSCG + O*NET logistic regression pipelines on ALL rows and save them for the API.

Same recipe as the nested CV in nscg_lr_baseline.py, applied once to the full data:
  * C tuned by 3-fold CV on ROC-AUC (build_search), then refit on every row
  * decision threshold = F1-maximising cut-off on inner-fold OUT-OF-FOLD predictions (never in-sample)

Saved to app/backend/artifacts/:
  nscg_lr_A1.joblib, nscg_lr_A2.joblib   dict(pipeline, threshold, C, columns, n_train, prevalence, ...)
  occupations.json                       one row per NCSES code with its O*NET Work Values + job zone,
                                         so the API can map a picked occupation to model inputs without
                                         the (gitignored) merged CSV

These models have no held-out score of their own; their expected performance is the nested-CV table in
results/nscg/nscg_lr_point_metrics.csv.

Usage:
    python src/models/nscg_lr_final.py
    python src/models/nscg_lr_final.py --data PATH --out DIR
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from nscg_lr_baseline import FEATURE_SETS, FIT_COLS, ONET, build_search, load_data
from rf_baseline import SEED, best_f1_threshold

ROOT = Path(__file__).resolve().parents[2]
APP_MODELS = ["A1", "A2"]  # A2 = app model, A1 = "without fit" comparison
WORK_VALUES = [c for c in ONET if c != "job_zone"]


def build_occupation_table(df):
    """One row per NCSES code. O*NET values are constant within a code, so take the first row."""
    cols = ["ncses_label", *WORK_VALUES, "job_zone"]
    occ = df.groupby("N3OCPR")[cols].first()
    occ["has_work_values"] = occ[WORK_VALUES].notna().all(axis=1)
    occ.insert(1, "occ_group", occ.index.str[:2])
    occ = occ.reset_index().rename(columns={"N3OCPR": "code", "ncses_label": "label"})
    occ = occ.sort_values("label").astype(object).where(occ.notna(), None)
    return occ.to_dict(orient="records")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "processed" / "nscg2023_onet_clean.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "app" / "backend" / "artifacts")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    c_grid = np.logspace(-4, 2, 13)  # same grid as the baseline
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)

    df, y, _ = load_data(args.data)
    trained_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    for name in APP_MODELS:
        spec = FEATURE_SETS[name]
        X = (df[spec["num"] + spec["cat"] + (FIT_COLS if spec["fit"] else [])]
             .loc[:, lambda d: ~d.columns.duplicated()].copy())

        search = build_search(spec, c_grid, inner_cv)
        search.fit(X, y)  # refit=True -> best_estimator_ is trained on all rows
        best = search.best_estimator_
        c = float(search.best_params_["clf__C"])
        if c in (c_grid.min(), c_grid.max()):
            print(f"WARNING: {name} hit the edge of the C grid; consider widening it")

        pred_out_of_fold = cross_val_predict(clone(best), X, y, cv=inner_cv, method="predict_proba",
                                             n_jobs=-1)[:, 1]
        threshold = float(best_f1_threshold(y, pred_out_of_fold))

        bundle = dict(pipeline=best, threshold=threshold, C=c, columns=list(X.columns), n_train=len(y),
                      prevalence=float(y.mean()), sklearn_version=sklearn.__version__, trained_at=trained_at,
                      model=name)
        path = args.out / f"nscg_lr_{name}.joblib"
        joblib.dump(bundle, path, compress=3)

        # the file must load on its own and reproduce the in-memory model
        reloaded = joblib.load(path)
        sample = X.head(1000)
        np.testing.assert_allclose(reloaded["pipeline"].predict_proba(sample),
                                   best.predict_proba(sample), rtol=0, atol=1e-12)
        print(f"{name}: C = {c:.4g}, threshold = {threshold:.3f}, columns = {len(X.columns)}, "
              f"saved {path.name} ({path.stat().st_size / 1024:.0f} KB), reload check OK")

    occupations = build_occupation_table(df)
    (args.out / "occupations.json").write_text(json.dumps(occupations, indent=1))
    n_missing = sum(not o["has_work_values"] for o in occupations)
    print(f"occupations.json: {len(occupations)} occupations, {n_missing} without O*NET Work Values")


if __name__ == "__main__":
    main()
