"""
Decision tree on NSCG 2023 + O*NET (issue #39): job satisfaction (very_satisfied = 1).

Same feature sets (A0/A1/A2), outer splits, inner tuning metric, threshold rule and evaluation as the
logistic-regression baseline (nscg_lr_baseline.py), which this script imports from. What differs:
  * no scaling or log transforms (a tree only uses the order of values)
  * tuned on max_depth and min_samples_leaf (leaves are large so predicted probabilities are not noisy)
  * importances (permutation, held-out folds) replace coefficients
"""
import argparse
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import (
    GridSearchCV,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

# shared with the logistic-regression baseline
from nscg_lr_baseline import (  # noqa: F401
    BOOT_SEED, CATEGORY_VARS, COLORS, FEATURE_SETS, FIT_COLS, FIT_PAIRS, N_SPLITS, NUMERIC_LABELS, SEED,
    SETS, FitFeatures, ci_table, load_data, metrics_both, paired_diff, plot_confusion, plot_roc,
)
from rf_baseline import best_f1_threshold, finish_figure, make_boot_indices

ROOT = Path(__file__).resolve().parents[2]


# ----------------------------------------------------------------------------- model
def tree_param_grid(quick=False):
    """Large leaves: ~64k training rows, so min_samples_leaf of 10 would give very noisy probabilities."""
    if quick:
        return {"clf__max_depth": [3, 6], "clf__min_samples_leaf": [50, 250]}
    return {"clf__max_depth": [3, 4, 5, 6, 8, 12, 16],
            "clf__min_samples_leaf": [25, 50, 100, 250, 500, 1000]}


def build_search(spec, param_grid, inner_cv):
    """Imputation lives inside the Pipeline (fit on each training split only). No scaler."""
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True))])
    categorical = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    parts = [("num", numeric, spec["num"]), ("cat", categorical, spec["cat"])]
    if spec["fit"]:
        fit = Pipeline([("fit", FitFeatures(pairs=FIT_PAIRS)),
                        ("imputer", SimpleImputer(strategy="median"))])
        parts.append(("fit", fit, FIT_COLS))
    pipe = Pipeline([
        ("pre", ColumnTransformer(parts)),
        ("clf", DecisionTreeClassifier(class_weight="balanced", random_state=SEED)),
    ])
    return GridSearchCV(pipe, param_grid, scoring="roc_auc", cv=inner_cv, n_jobs=-1, refit=True)


# ----------------------------------------------------------------------------- nested CV
def run_nested_cv(X, y, splits, n_repeats, label, grid, inner_cv, spec):
    """Outer folds score; inner folds tune and set the threshold. Importances use repeat 1 only."""
    y = np.asarray(y)
    cols = X.columns.tolist()
    oof = np.full((n_repeats, len(y)), np.nan)
    pred = np.zeros((n_repeats, len(y)), dtype=int)
    fold_auc, thresholds, chosen, importances = [], [], [], []
    t0 = time.time()
    for i, (train_idx, test_idx) in enumerate(splits):
        r = i // N_SPLITS
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        search = build_search(spec, grid, inner_cv)
        search.fit(X_train, y_train)
        best = search.best_estimator_

        # threshold from inner-fold OOF predictions of the training fold only
        p_inner = cross_val_predict(clone(best), X_train, y_train, cv=inner_cv,
                                    method="predict_proba", n_jobs=-1)[:, 1]
        thr = best_f1_threshold(y_train, p_inner)

        p_test = best.predict_proba(X_test)[:, 1]  # held-out fold touched once
        oof[r, test_idx] = p_test
        pred[r, test_idx] = (p_test >= thr).astype(int)

        fold_auc.append(roc_auc_score(y_test, p_test))
        thresholds.append(thr)
        chosen.append(search.best_params_)
        if r == 0:  # permutation importance on the original columns (a categorical counts as one feature)
            pi = permutation_importance(best, X_test, y_test, scoring="roc_auc",
                                        n_repeats=5, random_state=SEED, n_jobs=-1)
            importances.append(pi.importances_mean)

        if (i + 1) % N_SPLITS == 0:
            print(f"[{label}] repeat {r + 1}/{n_repeats} done, {time.time() - t0:.0f}s elapsed", flush=True)
    assert not np.isnan(oof).any()
    return dict(oof=oof, pred=pred, fold_auc=np.array(fold_auc), thresholds=np.array(thresholds),
                chosen=chosen, importance=pd.Series(np.mean(importances, axis=0), index=cols))


def summarize(results, grid):
    """Console summary: tuned values, grid-edge warnings, thresholds, importances."""
    for name, res in results.items():
        print(f"\n{name}: chosen hyperparameters across {len(res['chosen'])} outer folds")
        print(pd.Series([str(sorted(p.items())) for p in res["chosen"]]).value_counts().to_string())
        for param, values in grid.items():
            edge = {p[param] for p in res["chosen"]} & {min(values), max(values)}
            if edge:
                print(f"  WARNING: {param} reached the edge of its grid {sorted(edge)}")
    print()
    for name, res in results.items():
        t = res["thresholds"]
        print(f"{name}: mean inner-fold F1 threshold = {t.mean():.3f} (SD {t.std():.3f}); "
              f"mean fold AUC = {res['fold_auc'].mean():.4f}")
    print("\nTop permutation importances for A2 (mean drop in held-out ROC-AUC, repeat 1):")
    print(results["A2"]["importance"].sort_values(ascending=False).head(12).round(4).to_string())


# ----------------------------------------------------------------------------- evaluation and outputs
PREFIX = "nscg_dt"


def feature_label(col):
    """Importances are per original column, so labels come from the column name."""
    if col == "occ_group":
        text = "Occupation group"
    else:
        text = NUMERIC_LABELS.get(col, CATEGORY_VARS.get(col, col))
    return f"{text} ({col})"


def plot_importance(importance, out, show):
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    for ax, name in zip(axes, SETS):
        imp = importance[name].sort_values(ascending=False).head(15)[::-1]
        ax.barh([feature_label(c) for c in imp.index], imp.values, color=COLORS[name])
        ax.tick_params(axis="y", labelsize=8)
        ax.set_title(f"Model {name}")
        ax.set_xlabel("Mean drop in ROC-AUC when shuffled")
        ax.grid(True, alpha=0.3)
    fig.suptitle("Permutation importance (top 15 features, repeat 1 held-out folds)")
    finish_figure(fig, out / f"{PREFIX}_permutation_importance.png", show)


def evaluate_and_save(results, y, w, out, n_boot, show):
    """Bootstrap CIs (unweighted and weighted), paired AUC differences, plots and saved tables."""
    n_repeats = results["A0"]["oof"].shape[0]
    boot_idx = make_boot_indices(y, n_boot, BOOT_SEED)  # same people for every set, so comparisons are paired
    point, point_w, boot, boot_w = {}, {}, {}, {}
    for name, res in results.items():
        point[name], point_w[name] = metrics_both(y, w, res["oof"], res["pred"], None)
        pairs = Parallel(n_jobs=-1, batch_size=10)(
            delayed(metrics_both)(y, w, res["oof"], res["pred"], idx) for idx in boot_idx)
        boot[name] = pd.DataFrame([p[0] for p in pairs])
        boot_w[name] = pd.DataFrame([p[1] for p in pairs])
    tab, tab_w = ci_table(point, boot), ci_table(point_w, boot_w)

    for title, t in [("unweighted", tab), ("weighted by WTSURVY (ignores strata/PSU; CIs are approximate)", tab_w)]:
        wide = t.assign(s=t.apply(lambda r: f"{r.value:.3f} [{r.ci_low:.3f}, {r.ci_high:.3f}]", axis=1)) \
                .pivot(index="metric", columns="set", values="s").loc[list(point["A0"])]
        print(f"\n=== Pooled OOF metrics, {title} (mean over repeats; bootstrap 95% CI) ===")
        print(wide.to_string())
    print(f"\nprevalence (PR-AUC floor) = {y.mean():.3f}; "
          f"Brier of a constant-prevalence predictor = {y.mean() * (1 - y.mean()):.3f}")

    diffs = []
    for hi_s, lo_s in [("A1", "A0"), ("A2", "A1")]:
        for wt, (p, b) in {"unweighted": (point, boot), "weighted": (point_w, boot_w)}.items():
            d = paired_diff(b[hi_s], b[lo_s], p[hi_s], p[lo_s],
                            results[hi_s]["fold_auc"], results[lo_s]["fold_auc"])
            diffs.append(dict(comparison=f"{hi_s} - {lo_s}", weighting=wt, **d))
    diffs = pd.DataFrame(diffs)
    print("\n=== Paired bootstrap: ROC-AUC differences ===")
    print(diffs.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    importance = pd.DataFrame({n: r["importance"] for n, r in results.items()})
    importance.index.name = "column"
    chosen = pd.DataFrame([{"set": n, "outer_fold": i, **p}
                           for n, r in results.items() for i, p in enumerate(r["chosen"])])

    cms = plot_confusion(results, y, n_repeats, out, show, prefix=PREFIX)
    plot_roc(results, point, y, n_repeats, out, show, prefix=PREFIX)
    plot_importance(importance, out, show)
    tab.to_csv(out / f"{PREFIX}_point_metrics.csv", index=False)
    tab_w.to_csv(out / f"{PREFIX}_point_metrics_weighted.csv", index=False)
    for name in SETS:
        boot[name].to_csv(out / f"{PREFIX}_bootstrap_{name}.csv", index=False)
        cm = pd.DataFrame(cms[name], index=["true_0", "true_1"], columns=["pred_0", "pred_1"])
        cm.to_csv(out / f"{PREFIX}_confusion_{name}_counts.csv")
        cm.div(cm.sum(axis=1), axis=0).to_csv(out / f"{PREFIX}_confusion_{name}_rownorm.csv")
    diffs.to_csv(out / f"{PREFIX}_paired_auc_diff.csv", index=False)
    importance.to_csv(out / f"{PREFIX}_permutation_importance.csv")
    chosen.to_csv(out / f"{PREFIX}_chosen_params.csv", index=False)
    np.savez(out / f"{PREFIX}_oof.npz", y=y, w=w, **{n: results[n]["oof"] for n in SETS},
             **{f"pred_{n}": results[n]["pred"] for n in SETS})
    print(f"\nsaved tables and figures to {out}")


# ----------------------------------------------------------------------------- single-fold check
def check_one_fold(df, y, quick):
    """Fit each feature set on the first outer training fold and score the held-out fold once."""
    X_sets = {n: df[s["num"] + s["cat"] + (FIT_COLS if s["fit"] else [])]
              .loc[:, lambda d: ~d.columns.duplicated()].copy() for n, s in FEATURE_SETS.items()}
    splits = list(RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=1, random_state=SEED)
                  .split(X_sets["A2"], y))
    train_idx, test_idx = splits[0]
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    grid = tree_param_grid(quick)
    print(f"grid: {grid}\nouter fold 1: train {len(train_idx)}, test {len(test_idx)}\n")
    for name, spec in FEATURE_SETS.items():
        search = build_search(spec, grid, inner_cv)
        search.fit(X_sets[name].iloc[train_idx], y[train_idx])
        best = search.best_estimator_
        p = best.predict_proba(X_sets[name].iloc[test_idx])[:, 1]
        tree = best.named_steps["clf"]
        print(f"{name}: features after preprocessing = {tree.n_features_in_}, best = {search.best_params_}, "
              f"inner AUC = {search.best_score_:.4f}, held-out AUC = {roc_auc_score(y[test_idx], p):.4f}, "
              f"depth = {tree.get_depth()}, leaves = {tree.get_n_leaves()}, "
              f"distinct predicted probabilities = {len(np.unique(p.round(6)))}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="tune and score one outer fold per feature set")
    ap.add_argument("--quick", action="store_true", help="1 repeat and a small grid")
    ap.add_argument("--repeats", type=int, default=5, help="outer CV repeats (default 5)")
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "processed" / "nscg2023_onet_clean.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "nscg")
    ap.add_argument("--show", action="store_true", help="also open plot windows (needs a display)")
    args = ap.parse_args()
    df, y, w = load_data(args.data)
    if args.check:
        check_one_fold(df, y, args.quick)
        return

    n_repeats = 1 if args.quick else args.repeats
    grid = tree_param_grid(args.quick)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    X_sets = {n: df[s["num"] + s["cat"] + (FIT_COLS if s["fit"] else [])]
              .loc[:, lambda d: ~d.columns.duplicated()].copy() for n, s in FEATURE_SETS.items()}
    # same call and seed as the logistic-regression script, so the outer splits are identical
    splits = list(RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=n_repeats, random_state=SEED)
                  .split(X_sets["A2"], y))
    print(f"{len(splits)} outer folds")

    results = {name: run_nested_cv(X_sets[name], y, splits, n_repeats, name, grid, inner_cv, spec)
               for name, spec in FEATURE_SETS.items()}
    summarize(results, grid)
    args.out.mkdir(parents=True, exist_ok=True)
    evaluate_and_save(results, y, w, args.out, 100 if args.quick else 2000, args.show)


if __name__ == "__main__":
    main()
