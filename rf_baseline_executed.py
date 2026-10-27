"""
Random forest baseline on feature sets A0 and A1 (issue #23): job dissatisfaction (satjob in {3, 4}).

  * Pipeline: in-fold imputation -> one-hot (nominal) / unscaled numeric -> RandomForest
  * class_weight="balanced_subsample", min_samples_leaf >= 10
  * Nested CV: outer RepeatedStratifiedKFold(5 x 5, seed 42), inner StratifiedKFold(3) tuned on ROC-AUC
  * Threshold for the dissatisfied class: maximises F1 on INNER-fold out-of-fold predictions only
  * Stratified bootstrap (2,000) 95% CIs, pooled-OOF confusion matrices, paired bootstrap on A1 - A0 AUC

Usage (run from anywhere):
    python rf_baseline_notebook.py                 # full run (~12 min on 2 cores)
    python rf_baseline_notebook.py --quick         # smoke test (~30 s)
    python rf_baseline_notebook.py --data PATH --out DIR --show
"""
import argparse
import hashlib
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no GUI needed; figures are saved to files (use --show to open windows)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from joblib import Parallel, delayed
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import (
    GridSearchCV,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ----------------------------------------------------------------------------- config
ROOT = Path(__file__).resolve().parent
N_SPLITS = 5
SEED = 42          # outer splits, inner CV, forest and permutation importance
BOOT_SEED = 2024

# identical feature lists to the logistic-regression notebook
BASE_FEATURES_A0 = [
    "age", "hrs1", "weekswrk", "childs", "realrinc",
    "educ", "wrkstat", "wrkslf", "sex",
    "race", "hispanic", "born", "marital", "region", "union1",
]
FEATURES_A1 = BASE_FEATURES_A0 + ["prestg10"]

# Every column in the CSV is float64, so select_dtypes would find no categoricals:
# the unordered category codes are listed by hand to get one-hot encoding.
NOMINAL_COLS = ["wrkstat", "wrkslf", "sex", "race", "hispanic", "born", "marital", "region", "union1"]


# ----------------------------------------------------------------------------- data
def load_data(path):
    dfraw = pd.read_csv(path)
    # (satjob >= 3) is False for NaN, so rows without a satjob answer would silently become "satisfied".
    # Keep only respondents with a valid answer (a no-op if the file is already filtered).
    print(f"rows with missing satjob: {dfraw['satjob'].isna().sum()} of {len(dfraw)}")
    dfraw = dfraw[dfraw["satjob"].notna()].reset_index(drop=True)
    y = (dfraw["satjob"] >= 3).astype(int).to_numpy()  # 1 = dissatisfied (satjob 3-4)
    print(f"n = {len(y)}, dissatisfied = {y.sum()} ({y.mean():.1%}), "
        f"majority-class accuracy = {1 - y.mean():.1%}")
    return dfraw, y


# ----------------------------------------------------------------------------- model
def build_search(cols, n_trees, param_grid, inner_cv):
    """Preprocessing + random forest + inner 3-fold tuning on ROC-AUC.
    Imputers live inside the Pipeline, so they are fit on each training fold only; there is no scaler."""
    nom = [c for c in cols if c in NOMINAL_COLS]
    num = [c for c in cols if c not in NOMINAL_COLS]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
    ])
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, num),
        ("cat", categorical_transformer, nom),
    ])
    rf_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=n_trees,
            class_weight="balanced_subsample",
            n_jobs=1,
            random_state=SEED,
        )),
    ])
    return GridSearchCV(rf_pipeline, param_grid, scoring="roc_auc", cv=inner_cv, n_jobs=-1, refit=True)


def best_f1_threshold(y_true, p):
    prec, rec, thr = precision_recall_curve(y_true, p)
    f1 = 2 * prec[:-1] * rec[:-1] / np.clip(prec[:-1] + rec[:-1], 1e-12, None)
    return float(thr[np.argmax(f1)])


def run_nested_cv(X, y, splits, n_repeats, label, n_trees, param_grid, inner_cv):
    """Outer folds score; inner folds tune and set the threshold."""
    y = np.asarray(y)
    cols = X.columns.tolist()
    oof = np.full((n_repeats, len(y)), np.nan)       # one full out-of-fold probability vector per repeat
    pred = np.zeros((n_repeats, len(y)), dtype=int)  # hard labels at the inner-fold threshold
    fold_auc, thresholds, chosen, importances = [], [], [], []
    t0 = time.time()
    for i, (train_idx, test_idx) in enumerate(splits):
        r = i // N_SPLITS
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # inner 3-fold CV picks the hyperparameters (ROC-AUC) using the training fold only
        search = build_search(cols, n_trees, param_grid, inner_cv)
        search.fit(X_train, y_train)
        best = search.best_estimator_

        # threshold: maximise F1 on the inner-fold out-of-fold predictions of the training fold only
        p_inner = cross_val_predict(clone(best), X_train, y_train, cv=inner_cv,
                                    method="predict_proba", n_jobs=-1)[:, 1]
        thr = best_f1_threshold(y_train, p_inner)

        # the held-out fold is touched once: probabilities, then the fixed threshold
        p_test = best.predict_proba(X_test)[:, 1]
        oof[r, test_idx] = p_test
        pred[r, test_idx] = (p_test >= thr).astype(int)

        fold_auc.append(roc_auc_score(y_test, p_test))
        thresholds.append(thr)
        chosen.append(search.best_params_)
        if r == 0:  # permutation importance on held-out folds of the first repeat
            pi = permutation_importance(best, X_test, y_test, scoring="roc_auc",
                                        n_repeats=5, random_state=SEED, n_jobs=-1)
            importances.append(pi.importances_mean)

        if (i + 1) % N_SPLITS == 0:
            print(f"[{label}] repeat {r + 1}/{n_repeats} done, {time.time() - t0:.0f}s elapsed", flush=True)
    assert not np.isnan(oof).any()
    return dict(oof=oof, pred=pred, fold_auc=np.array(fold_auc), thresholds=np.array(thresholds),
                chosen=chosen, importance=pd.Series(np.mean(importances, axis=0), index=cols))


# ----------------------------------------------------------------------------- metrics
def metrics_one(y_true, p, hard):
    return {
        "ROC-AUC": roc_auc_score(y_true, p),
        "PR-AUC": average_precision_score(y_true, p),
        "Balanced accuracy": balanced_accuracy_score(y_true, hard),
        "Brier score": brier_score_loss(y_true, p),
        "Precision (dissatisfied)": precision_score(y_true, hard, zero_division=0),
        "Recall (dissatisfied)": recall_score(y_true, hard, zero_division=0),
        "F1 (dissatisfied)": f1_score(y_true, hard, zero_division=0),
        "Macro-F1": f1_score(y_true, hard, average="macro", zero_division=0),
    }


def metrics_pooled(y_true, oof, pred, idx=None):
    """Each metric is computed on the pooled out-of-fold predictions of one repeat
    (every person scored once), then averaged over the repeats."""
    if idx is None:
        idx = np.arange(len(y_true))
    rows = [metrics_one(y_true[idx], oof[r, idx], pred[r, idx]) for r in range(oof.shape[0])]
    return pd.DataFrame(rows).mean().to_dict()


def make_boot_indices(y, n_boot, seed):
    """Stratified bootstrap of people, shared by A0 and A1 so the AUC comparison is paired."""
    rng = np.random.default_rng(seed)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    return np.stack([
        np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])
        for _ in range(n_boot)
    ])


# ----------------------------------------------------------------------------- plots
def finish_figure(fig, path, show):
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    if show:
        plt.show()
    plt.close(fig)


def plot_confusion(results, y, n_repeats, out, show):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    cms = {}
    for ax, name in zip(axes, ["A0", "A1"]):
        cm = np.mean([confusion_matrix(y, results[name]["pred"][r], labels=[0, 1])
                    for r in range(n_repeats)], axis=0)
        cms[name] = cm
        cm_row = cm / cm.sum(axis=1, keepdims=True)
        annot = np.array([[f"{cm[i, j]:.0f}\n({cm_row[i, j]:.1%})" for j in range(2)] for i in range(2)])
        sns.heatmap(cm, annot=annot, fmt="", cmap="Blues", cbar=False, ax=ax,
                    xticklabels=["Satisfied (0)", "Dissatisfied (1)"],
                    yticklabels=["Satisfied (0)", "Dissatisfied (1)"])
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(f"OOF Confusion Matrix (Model {name}, inner-fold threshold)")
    finish_figure(fig, out / "rf_confusion_matrices.png", show)
    return cms


def plot_roc(results, point, y, n_repeats, colors, out, show):
    fig = plt.figure(figsize=(7, 6))
    for name in ["A0", "A1"]:
        for r in range(n_repeats):
            fpr, tpr, _ = roc_curve(y, results[name]["oof"][r])
            plt.plot(fpr, tpr, color=colors[name], alpha=0.35, lw=1,
                    label=f"Model {name} (AUC = {point[name]['ROC-AUC']:.3f})" if r == 0 else None)
    plt.plot([0, 1], [0, 1], "k--", label="Random Chance (AUC = 0.50)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Out-of-Fold ROC Curves: Baseline Controls (A0) vs. + Prestige (A1)")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    finish_figure(fig, out / "rf_roc_curves.png", show)


def plot_importance(results, colors, out, show):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, name in zip(axes, ["A0", "A1"]):
        imp = results[name]["importance"].sort_values(ascending=False).head(15)[::-1]
        ax.barh(imp.index, imp.values, color=colors[name])
        ax.set_title(f"Permutation importance (Model {name}, repeat 1 held-out folds)")
        ax.set_xlabel("Mean drop in ROC-AUC when shuffled")
        ax.grid(True, alpha=0.3)
    finish_figure(fig, out / "rf_permutation_importance.png", show)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="1 repeat, 60 trees, 100 bootstraps, small grid")
    ap.add_argument("--data", type=Path, default=ROOT / "gss2024_onet_cleaned.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "rf")
    ap.add_argument("--show", action="store_true", help="also open plot windows (needs a display)")
    args = ap.parse_args()

    n_repeats = 1 if args.quick else 5
    n_trees = 60 if args.quick else 300
    n_boot = 100 if args.quick else 2000
    param_grid = {
        # min_samples_leaf >= 10 (issue #23); 60 and 80 added because an earlier run picked 40, the top of its grid
        "classifier__min_samples_leaf": [10, 20] if args.quick else [10, 20, 40, 60, 80],
        "classifier__max_features": ["sqrt"] if args.quick else ["sqrt", 0.5],
    }
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    args.out.mkdir(parents=True, exist_ok=True)

    dfraw, y = load_data(args.data)
    # no log transform of realrinc: it is monotone, so it cannot change a tree's splits
    X_sets = {"A0": dfraw[BASE_FEATURES_A0].copy(), "A1": dfraw[FEATURES_A1].copy()}
    print("nominal:", NOMINAL_COLS)
    print("numeric:", [c for c in FEATURES_A1 if c not in NOMINAL_COLS])

    # same call as the logistic-regression notebook; splits depend only on y and the seed
    rskf = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=n_repeats, random_state=SEED)
    splits = list(rskf.split(X_sets["A1"], y))
    fingerprint = hashlib.md5(b"".join(te.tobytes() for _, te in splits)).hexdigest()[:10]
    print(f"{len(splits)} outer folds, split fingerprint = {fingerprint}")

    results = {}
    for name, X_set in X_sets.items():
        results[name] = run_nested_cv(X_set, y, splits, n_repeats, name, n_trees, param_grid, inner_cv)
    for name in results:
        print(f"\n{name}: chosen hyperparameters across the {len(splits)} outer folds")
        print(pd.Series([str(p) for p in results[name]["chosen"]]).value_counts().to_string())

    # metrics with stratified-bootstrap 95% CIs
    boot_idx = make_boot_indices(y, n_boot, BOOT_SEED)
    boot, point = {}, {}
    for name, res in results.items():
        point[name] = metrics_pooled(y, res["oof"], res["pred"])
        boot[name] = pd.DataFrame(Parallel(n_jobs=-1, batch_size=20)(
            delayed(metrics_pooled)(y, res["oof"], res["pred"], idx) for idx in boot_idx
        ))
    table = pd.DataFrame({
        name: {m: f"{point[name][m]:.3f} [{np.percentile(boot[name][m], 2.5):.3f}, "
                f"{np.percentile(boot[name][m], 97.5):.3f}]" for m in point[name]}
        for name in results
    })
    print("\n=== Pooled OOF metrics (mean over repeats; bootstrap 95% CI) ===")
    print(table.to_string())
    print(f"\nprevalence (PR-AUC floor) = {y.mean():.3f}; "
          f"Brier of a constant-prevalence predictor = {y.mean() * (1 - y.mean()):.3f}")
    for name in results:
        t = results[name]["thresholds"]
        print(f"{name}: mean inner-fold F1 threshold = {t.mean():.3f} (SD {t.std():.3f})")

    # paired bootstrap of the ROC-AUC difference (A1 - A0), same resampled people for both models
    d_auc = boot["A1"]["ROC-AUC"].to_numpy() - boot["A0"]["ROC-AUC"].to_numpy()
    auc_diff = point["A1"]["ROC-AUC"] - point["A0"]["ROC-AUC"]
    ci_low, ci_high = np.percentile(d_auc, [2.5, 97.5])
    p_two = min(1.0, 2 * min((d_auc <= 0).mean(), (d_auc >= 0).mean()))
    fold_diff = results["A1"]["fold_auc"] - results["A0"]["fold_auc"]
    print("\n=== Paired bootstrap: AUC(A1) - AUC(A0) ===")
    print(f"ROC-AUC A0: {point['A0']['ROC-AUC']:.4f}   A1: {point['A1']['ROC-AUC']:.4f}")
    print(f"ROC-AUC Difference (A1 - A0): {auc_diff:.4f}")
    print(f"95% Bootstrap Confidence Interval: [{ci_low:.4f}, {ci_high:.4f}]   (two-sided bootstrap p = {p_two:.3f})")
    print(f"A1 beat A0 in {(fold_diff > 0).sum()} of {len(fold_diff)} outer folds "
        f"(mean fold difference {fold_diff.mean():+.4f}, SD {fold_diff.std(ddof=1):.4f})")

    # plots (saved as PNGs)
    colors = {"A0": "blue", "A1": "orange"}
    cms = plot_confusion(results, y, n_repeats, args.out, args.show)
    plot_roc(results, point, y, n_repeats, colors, args.out, args.show)
    plot_importance(results, colors, args.out, args.show)

    # save results
    pd.DataFrame(point).T.to_csv(args.out / "rf_point_metrics.csv")
    for name in boot:
        boot[name].to_csv(args.out / f"rf_bootstrap_{name}.csv", index=False)
        pd.DataFrame(cms[name]).to_csv(args.out / f"confusion_{name}_counts.csv")
    pd.Series({"auc_diff_A1_minus_A0": auc_diff, "ci_low": ci_low, "ci_high": ci_high,
            "bootstrap_p": p_two}).to_csv(args.out / "rf_paired_auc_diff.csv", header=["value"])
    np.savez(args.out / "rf_oof.npz", y=y, A0=results["A0"]["oof"], A1=results["A1"]["oof"],
            pred_A0=results["A0"]["pred"], pred_A1=results["A1"]["pred"])
    print(f"\nsaved tables and figures to {args.out}")


if __name__ == "__main__":
    main()
