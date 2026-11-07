"""
L2 logistic regression on NSCG 2023 + O*NET (issue #39): job satisfaction (very_satisfied = 1).

Feature sets (nested):
  A0  respondent + job context (incl. 2-digit occupation group)
  A1  A0 + O*NET Work Values + job zone
  A2  A1 + the respondent's FAC* importance ratings + person-job fit terms (FAC composite x Work Value)

Protocol (same as the GSS baselines, issues #26 / #27):
  * Pipeline: in-fold median imputation + missing flags -> standardize numerics / one-hot categoricals -> LR
  * class_weight="balanced"; C tuned by inner 3-fold CV on ROC-AUC
  * Outer RepeatedStratifiedKFold(5 x 5, seed 42), same splits for every feature set
  * Threshold maximises F1 on INNER-fold out-of-fold predictions only
  * Stratified bootstrap (2,000) 95% CIs, pooled-OOF confusion matrices, paired bootstrap on AUC differences
  * Fit is unweighted; metrics are reported unweighted (primary) and weighted by WTSURVY

Usage:
    python src/models/nscg_lr_baseline.py                 # full run
    python src/models/nscg_lr_baseline.py --quick         # smoke test
    python src/models/nscg_lr_baseline.py --data PATH --out DIR --show
"""
import argparse
import hashlib
import time
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from joblib import Parallel, delayed
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
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
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# reuse the shared evaluation helpers from the random-forest baseline
from rf_baseline import N_SPLITS, SEED, best_f1_threshold, finish_figure, make_boot_indices

# ----------------------------------------------------------------------------- config
ROOT = Path(__file__).resolve().parents[2]
BOOT_SEED = 2024
TARGET = "very_satisfied"
WEIGHT = "WTSURVY"

NUMERIC = ["AGE", "HRSWK", "WKSWK", "tenure_years", "log_salary", "TELEFR", "EMSIZE", "OCEDRLP"]
BINARY = ["JOBINS", "JOBPENS", "JOBPROFT", "JOBVAC", "MGRNAT", "MGROTH", "MGRSOC",
          "salary_zero", "salary_low", "salary_topcoded", "hours_topcoded"]
CATEGORICAL = ["SEX_2023", "RACETHM", "CTZN", "MARSTA", "DGRDG", "NDGMEMG", "NEDTP", "TELEC", "occ_group"]
ONET = ["Achievement", "Independence", "Recognition", "Relationships", "Support", "Working Conditions", "job_zone"]
FAC = ["FACADV", "FACBEN", "FACCHAL", "FACIND", "FACLOC", "FACRESP", "FACSAL", "FACSEC", "FACSOC"]

# person composite (mean of matched FAC items) <-> O*NET Work Value; FACLOC and Support stay unpaired
FIT_PAIRS = {
    "Achievement": ["FACCHAL"],
    "Independence": ["FACIND", "FACRESP"],
    "Recognition": ["FACADV"],
    "Relationships": ["FACSOC"],
    "Working Conditions": ["FACSAL", "FACBEN", "FACSEC"],
}
FIT_COLS = FAC + list(FIT_PAIRS)

FEATURE_SETS = {
    "A0": dict(num=NUMERIC + BINARY, cat=CATEGORICAL, fit=False),
    "A1": dict(num=NUMERIC + BINARY + ONET, cat=CATEGORICAL, fit=False),
    "A2": dict(num=NUMERIC + BINARY + ONET + FAC, cat=CATEGORICAL, fit=True),
}
SETS = list(FEATURE_SETS)
COLORS = {"A0": "blue", "A1": "orange", "A2": "green"}


# ----------------------------------------------------------------------------- data
def load_data(path):
    df = pd.read_csv(path, dtype=str)
    for c in NUMERIC + ONET + FAC + [WEIGHT]:
        df[c] = pd.to_numeric(df[c])
    for c in BINARY + [TARGET]:
        df[c] = df[c].map({"True": 1, "False": 0, "1": 1, "0": 0, "1.0": 1, "0.0": 0}).astype(float)
    assert df[TARGET].notna().all(), "target has missing values"
    # row-wise clip (nothing learned from data): 212 implausibly low salaries would inflate the SD
    df["log_salary"] = df["log_salary"].clip(lower=np.log(1000))
    df["occ_group"] = df["N3OCPR"].str[:2]

    # leakage guard: no satisfaction items among the features
    used = set().union(*[set(s["num"]) | set(s["cat"]) for s in FEATURE_SETS.values()]) | set(FIT_COLS)
    leaks = [c for c in used if c == "JOBSATIS" or c.startswith("SAT")]
    assert not leaks, f"leakage columns in features: {leaks}"

    y = df[TARGET].astype(int).to_numpy()
    w = df[WEIGHT].to_numpy()
    print(f"n = {len(y)}, very satisfied = {y.sum()} ({y.mean():.1%} unweighted, "
          f"{np.average(y, weights=w):.1%} weighted)")
    return df, y, w


# ----------------------------------------------------------------------------- model
class FitFeatures(BaseEstimator, TransformerMixin):
    """Person-job fit terms. For each (job value J, person composite P = mean of matched FAC items):
    z(P) * z(J) and |z(P) - z(J)|. Means and SDs come from the training rows only; NaN propagates."""

    def __init__(self, pairs=None):
        self.pairs = pairs

    def _parts(self, X):
        X = pd.DataFrame(X)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return {job: (np.nanmean(X[facs].to_numpy(float), axis=1), X[job].to_numpy(float))
                    for job, facs in self.pairs.items()}

    def fit(self, X, y=None):
        self.stats_ = {}
        for job, (p, j) in self._parts(X).items():
            self.stats_[job] = (np.nanmean(p), np.nanstd(p) or 1.0, np.nanmean(j), np.nanstd(j) or 1.0)
        return self

    def transform(self, X):
        out = []
        for job, (p, j) in self._parts(X).items():
            mp, sp, mj, sj = self.stats_[job]
            zp, zj = (p - mp) / sp, (j - mj) / sj
            out += [zp * zj, np.abs(zp - zj)]
        return np.column_stack(out)

    def get_feature_names_out(self, input_features=None):
        return np.array([f"{kind}_{job}" for job in self.pairs for kind in ("fit_prod", "fit_gap")])


def build_search(spec, c_grid, inner_cv):
    """Imputers and the scaler live inside the Pipeline, so they are fit on each training split only."""
    numeric = Pipeline([("imputer", SimpleImputer(strategy="median", add_indicator=True)),
                        ("scaler", StandardScaler())])
    categorical = Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                            ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    parts = [("num", numeric, spec["num"]), ("cat", categorical, spec["cat"])]
    if spec["fit"]:
        fit = Pipeline([("fit", FitFeatures(pairs=FIT_PAIRS)),
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler())])
        parts.append(("fit", fit, FIT_COLS))
    pipe = Pipeline([
        ("pre", ColumnTransformer(parts)),
        ("clf", LogisticRegression(penalty="l2", class_weight="balanced", solver="lbfgs", max_iter=2000)),
    ])
    return GridSearchCV(pipe, {"clf__C": c_grid}, scoring="roc_auc", cv=inner_cv, n_jobs=-1, refit=True)


def run_nested_cv(X, y, splits, n_repeats, label, c_grid, inner_cv, spec):
    y = np.asarray(y)
    oof = np.full((n_repeats, len(y)), np.nan)
    pred = np.zeros((n_repeats, len(y)), dtype=int)
    fold_auc, thresholds, chosen_c, coefs = [], [], [], []
    t0 = time.time()
    for i, (train_idx, test_idx) in enumerate(splits):
        r = i // N_SPLITS
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        search = build_search(spec, c_grid, inner_cv)
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
        chosen_c.append(search.best_params_["clf__C"])
        coefs.append(pd.Series(best.named_steps["clf"].coef_[0],
                               index=best.named_steps["pre"].get_feature_names_out()))
        if (i + 1) % N_SPLITS == 0:
            print(f"[{label}] repeat {r + 1}/{n_repeats} done, {time.time() - t0:.0f}s elapsed", flush=True)
    assert not np.isnan(oof).any()
    return dict(oof=oof, pred=pred, fold_auc=np.array(fold_auc), thresholds=np.array(thresholds),
                chosen_c=np.array(chosen_c), coefs=pd.DataFrame(coefs))


# ----------------------------------------------------------------------------- metrics
def metrics_one(y_true, p, hard, w=None):
    kw = dict(sample_weight=w)
    return {
        "ROC-AUC": roc_auc_score(y_true, p, **kw),
        "PR-AUC": average_precision_score(y_true, p, **kw),
        "Balanced accuracy": balanced_accuracy_score(y_true, hard, **kw),
        "Brier score": brier_score_loss(y_true, p, **kw),
        "Precision (very satisfied)": precision_score(y_true, hard, zero_division=0, **kw),
        "Recall (very satisfied)": recall_score(y_true, hard, zero_division=0, **kw),
        "F1 (very satisfied)": f1_score(y_true, hard, zero_division=0, **kw),
        "Macro-F1": f1_score(y_true, hard, average="macro", zero_division=0, **kw),
    }


def metrics_pooled(y_true, oof, pred, w=None, idx=None):
    """Metrics on the pooled OOF predictions of each repeat (every person scored once), averaged over repeats."""
    if idx is None:
        idx = np.arange(len(y_true))
    ww = None if w is None else w[idx]
    rows = [metrics_one(y_true[idx], oof[r, idx], pred[r, idx], ww) for r in range(oof.shape[0])]
    return pd.DataFrame(rows).mean().to_dict()


def metrics_both(y, w, oof, pred, idx):
    return metrics_pooled(y, oof, pred, None, idx), metrics_pooled(y, oof, pred, w, idx)


def ci_table(point, boot):
    rows = []
    for name in point:
        for m, v in point[name].items():
            lo, hi = np.percentile(boot[name][m], [2.5, 97.5])
            rows.append(dict(set=name, metric=m, value=v, ci_low=lo, ci_high=hi))
    return pd.DataFrame(rows)


def paired_diff(boot_hi, boot_lo, p_hi, p_lo, fold_hi, fold_lo):
    d = boot_hi["ROC-AUC"].to_numpy() - boot_lo["ROC-AUC"].to_numpy()
    lo, hi = np.percentile(d, [2.5, 97.5])
    fd = fold_hi - fold_lo
    return dict(auc_diff=p_hi["ROC-AUC"] - p_lo["ROC-AUC"], ci_low=lo, ci_high=hi,
                bootstrap_p=min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())),
                folds_favoring_larger=int((fd > 0).sum()), n_folds=len(fd), mean_fold_diff=fd.mean())


# ----------------------------------------------------------------------------- feature labels
# Plain-language names for plots/tables (descriptions from the NSCG codebook and nscg_cleaning.ipynb).
NUMERIC_LABELS = {
    "AGE": "Age (years)", "HRSWK": "Hours worked per week", "WKSWK": "Weeks worked per year",
    "tenure_years": "Years in current job", "log_salary": "Salary (log)",
    "TELEFR": "Telework days per week (0-4)", "EMSIZE": "Employer size (1 = small ... 8 = large)",
    "OCEDRLP": "Job less related to degree (1 = closely ... 3 = not related)",
    "JOBINS": "Offers health insurance", "JOBPENS": "Offers pension/retirement plan",
    "JOBPROFT": "Offers profit sharing", "JOBVAC": "Offers paid vacation/sick days",
    "MGRNAT": "Job needs expertise: eng/CS/math/natural sci", "MGROTH": "Job needs expertise: other fields",
    "MGRSOC": "Job needs expertise: social sciences",
    "salary_zero": "Reported salary of 0", "salary_low": "Implausibly low salary (<$1,000)",
    "salary_topcoded": "Salary top-coded", "hours_topcoded": "Hours top-coded (96)",
    "job_zone": "O*NET job zone (preparation needed)",
    "FACADV": "Rates advancement important", "FACBEN": "Rates benefits important",
    "FACCHAL": "Rates intellectual challenge important", "FACIND": "Rates independence important",
    "FACLOC": "Rates job location important", "FACRESP": "Rates level of responsibility important",
    "FACSAL": "Rates salary important", "FACSEC": "Rates job security important",
    "FACSOC": "Rates contribution to society important",
}
for _wv in ["Achievement", "Independence", "Recognition", "Relationships", "Support", "Working Conditions"]:
    NUMERIC_LABELS[_wv] = f"O*NET work value: {_wv}"

CATEGORY_VARS = {
    "SEX_2023": "Sex", "RACETHM": "Race/ethnicity", "CTZN": "Citizenship", "MARSTA": "Marital status",
    "DGRDG": "Highest degree", "NDGMEMG": "Degree field", "NEDTP": "Employer type", "TELEC": "Telework",
}
TELEC_LABELS = {
    "Allowed to telework, and did": "Allowed and teleworked",
    "Allowed to telework, and didn't": "Allowed but not teleworking",
    "Not allowed or required to telework": "Telework not allowed",
    "Telework didn't make sense for job": "Telework doesn't suit the job",
    "Required to telework": "Required to telework",
}
OCC_GROUPS = {
    "11": "Computer & information science", "12": "Math, statistics & data science",
    "18": "Postsecondary teachers: math/CS", "21": "Agricultural & food scientists", "22": "Life scientists",
    "23": "Conservation scientists & foresters", "28": "Postsecondary teachers: life sciences",
    "31": "Chemists", "32": "Environmental & earth scientists", "33": "Physicists",
    "34": "Other physical scientists", "38": "Postsecondary teachers: physical sciences",
    "41": "Economists", "42": "Political scientists", "43": "Psychologists",
    "44": "Anthropologists & sociologists", "45": "Other social scientists",
    "48": "Postsecondary teachers: social sciences", "51": "Aerospace engineers", "52": "Chemical engineers",
    "53": "Civil engineers", "54": "Electrical & computer engineers", "55": "Industrial engineers",
    "56": "Mechanical engineers", "57": "Other engineers", "58": "Postsecondary teachers: engineering",
    "61": "Health occupations (nurses, pharmacists, therapists...)",
    "62": "Managers (engineering, health, IT, science)", "63": "Secondary teachers: STEM & social sci",
    "64": "Technicians & programmers", "65": "Architects & actuaries", "71": "Executives & other managers",
    "72": "Management-related (finance, HR, purchasing...)", "73": "K-12 teachers (non-STEM focus)",
    "74": "Postsecondary teachers: other fields", "75": "Counselors & social service",
    "76": "Sales", "77": "Writers, artists & media", "78": "Admin support, lawyers & service",
}


def describe_feature(name):
    """'cat__TELEC_Allowed to telework, and didn't' -> "Allowed but not teleworking (cat__TELEC_...)"."""
    kind, _, rest = name.partition("__")
    if kind == "fit":
        _, what, job = rest.split("_", 2)  # e.g. "fit_prod_Working Conditions"
        text = (f"Fit: person x job match, {job}" if what == "prod"
                else f"Fit: gap between person and job, {job}")
    elif kind == "num" and rest.startswith("missingindicator_"):
        col = rest[len("missingindicator_"):]
        text = f"Missing flag: {NUMERIC_LABELS.get(col, col)}"
    elif kind == "num":
        text = NUMERIC_LABELS.get(rest, rest)
    elif kind == "cat":
        var = next((v for v in list(CATEGORY_VARS) + ["occ_group"] if rest.startswith(v + "_")), None)
        val = rest[len(var) + 1:] if var else rest
        if var == "occ_group":
            text = f"Occupation: {OCC_GROUPS.get(val, 'group ' + val)} [{val}]"
        elif var == "TELEC":
            text = TELEC_LABELS.get(val, val)
        elif var:
            text = f"{CATEGORY_VARS[var]}: {val}"
        else:
            text = rest
    else:
        text = rest
    return f"{text} ({name})"


# ----------------------------------------------------------------------------- plots
def plot_confusion(results, y, n_repeats, out, show):
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    cms = {}
    for ax, name in zip(axes, SETS):
        cm = np.mean([confusion_matrix(y, results[name]["pred"][r], labels=[0, 1])
                      for r in range(n_repeats)], axis=0)
        cms[name] = cm
        cm_row = cm / cm.sum(axis=1, keepdims=True)
        annot = np.array([[f"{cm_row[i, j]:.1%}" for j in range(2)] for i in range(2)])
        labels = ["Not very satisfied (0)", "Very satisfied (1)"]
        sns.heatmap(cm_row, annot=annot, fmt="", cmap="Blues", cbar=False, ax=ax, vmin=0, vmax=1,
                    xticklabels=labels, yticklabels=labels)
        ax.set_xlabel("Predicted Label")
        ax.set_ylabel("True Label")
        ax.set_title(f"OOF Confusion Matrix (Model {name}, % of true class)")
    finish_figure(fig, out / "nscg_lr_confusion_matrices.png", show)
    return cms


def plot_roc(results, point, y, n_repeats, out, show):
    fig = plt.figure(figsize=(7, 6))
    for name in SETS:
        for r in range(n_repeats):
            fpr, tpr, _ = roc_curve(y, results[name]["oof"][r])
            plt.plot(fpr, tpr, color=COLORS[name], alpha=0.35, lw=1,
                     label=f"Model {name} (AUC = {point[name]['ROC-AUC']:.3f})" if r == 0 else None)
    plt.plot([0, 1], [0, 1], "k--", label="Random Chance (AUC = 0.50)")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("Out-of-Fold ROC: Context (A0) vs. + O*NET (A1) vs. + Fit (A2)")
    plt.legend(loc="lower right")
    plt.grid(True, alpha=0.3)
    finish_figure(fig, out / "nscg_lr_roc_curves.png", show)


def plot_coefficients(coef_table, out, show):
    t = coef_table[coef_table["set"] == "A2"].copy()
    t = t.reindex(t["mean_coef"].abs().sort_values(ascending=False).index).head(20)[::-1]
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.barh(t["label"], t["mean_coef"], xerr=t["sd_coef"], color=COLORS["A2"], alpha=0.8)
    ax.tick_params(axis="y", labelsize=8)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("Mean coefficient across outer folds (log-odds per 1 SD; bars = fold SD)")
    ax.set_title("Top 20 logistic regression coefficients (Model A2)")
    ax.grid(True, alpha=0.3)
    finish_figure(fig, out / "nscg_lr_coefficients.png", show)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quick", action="store_true", help="1 repeat, 100 bootstraps, 4-point C grid")
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "processed" / "nscg2023_onet_clean.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "results" / "nscg")
    ap.add_argument("--show", action="store_true", help="also open plot windows (needs a display)")
    args = ap.parse_args()

    n_repeats = 1 if args.quick else 5
    n_boot = 100 if args.quick else 2000
    c_grid = np.logspace(-4, 2, 4) if args.quick else np.logspace(-4, 2, 13)
    inner_cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=SEED)
    args.out.mkdir(parents=True, exist_ok=True)

    df, y, w = load_data(args.data)
    X_sets = {name: df[spec["num"] + spec["cat"] + (FIT_COLS if spec["fit"] else [])]
              .loc[:, lambda d: ~d.columns.duplicated()].copy()
              for name, spec in FEATURE_SETS.items()}

    rskf = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=n_repeats, random_state=SEED)
    splits = list(rskf.split(X_sets["A2"], y))
    fingerprint = hashlib.md5(b"".join(te.tobytes() for _, te in splits)).hexdigest()[:10]
    print(f"{len(splits)} outer folds, split fingerprint = {fingerprint}")

    results = {name: run_nested_cv(X_sets[name], y, splits, n_repeats, name, c_grid, inner_cv, spec)
               for name, spec in FEATURE_SETS.items()}

    chosen = pd.DataFrame({n: results[n]["chosen_c"] for n in SETS})
    chosen.index.name = "outer_fold"
    for name in SETS:
        print(f"\n{name}: chosen C across the {len(splits)} outer folds")
        print(chosen[name].value_counts().sort_index().to_string())
        if chosen[name].isin([c_grid.min(), c_grid.max()]).any():
            print(f"  WARNING: {name} hit the edge of the C grid; consider widening it")

    # bootstrap: same resampled people for every set (paired); unweighted and weighted metrics
    boot_idx = make_boot_indices(y, n_boot, BOOT_SEED)
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
    for name in SETS:
        t = results[name]["thresholds"]
        print(f"{name}: mean inner-fold F1 threshold = {t.mean():.3f} (SD {t.std():.3f})")

    # paired bootstrap AUC differences
    diffs = []
    for hi_s, lo_s in [("A1", "A0"), ("A2", "A1")]:
        for wt, (p, b) in {"unweighted": (point, boot), "weighted": (point_w, boot_w)}.items():
            d = paired_diff(b[hi_s], b[lo_s], p[hi_s], p[lo_s],
                            results[hi_s]["fold_auc"], results[lo_s]["fold_auc"])
            diffs.append(dict(comparison=f"{hi_s} - {lo_s}", weighting=wt, **d))
    diffs = pd.DataFrame(diffs)
    print("\n=== Paired bootstrap: ROC-AUC differences ===")
    print(diffs.to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # coefficients (mean / SD over outer folds); odds ratio is per 1 SD of the standardized feature
    coef_rows = []
    for name in SETS:
        c = results[name]["coefs"]
        coef_rows.append(pd.DataFrame({"set": name, "feature": c.columns, "mean_coef": c.mean().to_numpy(),
                                       "sd_coef": c.std().to_numpy(), "odds_ratio": np.exp(c.mean().to_numpy())}))
    coef_table = pd.concat(coef_rows, ignore_index=True)
    coef_table.insert(2, "label", coef_table["feature"].map(describe_feature))
    a2 = coef_table[coef_table["set"] == "A2"]
    print("\nA2 fit-term coefficients:")
    print(a2[a2["feature"].str.contains("fit_")].to_string(index=False, float_format=lambda v: f"{v:.4f}"))

    # outputs
    cms = plot_confusion(results, y, n_repeats, args.out, args.show)
    plot_roc(results, point, y, n_repeats, args.out, args.show)
    plot_coefficients(coef_table, args.out, args.show)
    tab.to_csv(args.out / "nscg_lr_point_metrics.csv", index=False)
    tab_w.to_csv(args.out / "nscg_lr_point_metrics_weighted.csv", index=False)
    for name in SETS:
        boot[name].to_csv(args.out / f"nscg_lr_bootstrap_{name}.csv", index=False)
        cm = pd.DataFrame(cms[name], index=["true_0", "true_1"], columns=["pred_0", "pred_1"])
        cm.to_csv(args.out / f"nscg_lr_confusion_{name}_counts.csv")
        (cm.div(cm.sum(axis=1), axis=0)).to_csv(args.out / f"nscg_lr_confusion_{name}_rownorm.csv")
    diffs.to_csv(args.out / "nscg_lr_paired_auc_diff.csv", index=False)
    coef_table.to_csv(args.out / "nscg_lr_coefficients.csv", index=False)
    chosen.to_csv(args.out / "nscg_lr_chosen_C.csv")
    np.savez(args.out / "nscg_lr_oof.npz", y=y, w=w, **{n: results[n]["oof"] for n in SETS},
             **{f"pred_{n}": results[n]["pred"] for n in SETS})
    print(f"\nsaved tables and figures to {args.out}")


if __name__ == "__main__":
    main()
