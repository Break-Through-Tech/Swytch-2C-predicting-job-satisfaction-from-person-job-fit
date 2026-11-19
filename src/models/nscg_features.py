"""
Shared NSCG + O*NET feature definitions.

Kept free of heavy imports (no matplotlib / seaborn / rf_baseline) so the API can unpickle the saved
pipelines without importing the whole baseline script. joblib records the module path of every custom
class, so `FitFeatures` must live in an importable module like this one, not in a script run as __main__.
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

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
