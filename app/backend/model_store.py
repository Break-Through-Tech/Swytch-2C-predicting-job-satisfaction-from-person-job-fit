"""Loads the saved models and lookup tables once at startup."""
import csv
import json
import os
import sys
import warnings
from pathlib import Path

import joblib
import sklearn

ROOT = Path(__file__).resolve().parents[2]

# the pickled pipelines reference nscg_features.FitFeatures, which lives in src/models
sys.path.insert(0, str(ROOT / "src" / "models"))

ARTIFACTS = Path(os.environ.get("ARTIFACTS_DIR", Path(__file__).resolve().parent / "artifacts"))
INSIGHTS_CSV = Path(os.environ.get("INSIGHTS_CSV", ROOT / "results" / "nscg" / "nscg_lr_point_metrics.csv"))
MODEL_NAMES = ["A1", "A2"]


class ModelStore:
    def __init__(self):
        self.models = {name: joblib.load(ARTIFACTS / f"nscg_lr_{name}.joblib") for name in MODEL_NAMES}
        for name, bundle in self.models.items():
            if bundle["sklearn_version"] != sklearn.__version__:
                warnings.warn(f"model {name} was saved with scikit-learn {bundle['sklearn_version']}, "
                              f"but {sklearn.__version__} is installed; retrain or reinstall the pinned version")
        occupations = json.loads((ARTIFACTS / "occupations.json").read_text())
        self.occupations = occupations
        self.occupation_by_code = {o["code"]: o for o in occupations}

    def insights(self):
        """{model: {metric: {value, ci_low, ci_high}}} from the nested-CV results table."""
        out = {}
        with open(INSIGHTS_CSV, newline="") as f:
            for row in csv.DictReader(f):
                out.setdefault(row["set"], {})[row["metric"]] = {
                    "value": float(row["value"]), "ci_low": float(row["ci_low"]), "ci_high": float(row["ci_high"])}
        return out
