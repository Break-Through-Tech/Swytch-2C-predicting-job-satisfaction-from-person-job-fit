"""Turns form answers into the one-row DataFrame the pipelines expect, and explains the fit terms.

Anything not answered becomes NaN, which the pipelines impute (training median / most frequent value).
Feature definitions mirror notebooks/nscg/nscg_cleaning.ipynb and load_data() in nscg_lr_baseline.py.
"""
import numpy as np
import pandas as pd

import model_store  # noqa: F401  (puts src/models on sys.path so nscg_features can be imported)
from nscg_features import BINARY, CATEGORICAL, FAC, NUMERIC, ONET
from schema import BOOLEANS, CATEGORICAL as CATEGORICAL_FIELDS, IMPORTANCE, NUMBERS, TELEWORKS

SALARY_FLOOR = 1000  # load_data clips log_salary at log($1,000)
SALARY_TOPCODE_ABOVE = 500_000  # the public file replaces every salary above this with a top-code value
SALARY_TOPCODE_VALUE = 976_934  # the more common of the two top-code values (290 vs 131 rows; other is 827,838)
HOURS_CAP = 96  # NSCG top-codes hours at "96 or more"
NOT_ALLOWED_TELEWORK = {"Not allowed or required to telework", "Telework didn't make sense for job",
                        "Allowed to telework, and didn't"}  # cleaning recodes their telework days to 0


def salary_to_features(salary):
    """One salary answer -> log_salary + the three salary flags the model was trained with.

    Zero has no log (NaN, imputed) and sets salary_zero; salaries under $1,000 are clipped to log($1,000)
    and set salary_low; salaries above $500k look like the file's top-coded rows (salary_topcoded)."""
    if salary is None:
        return dict(log_salary=np.nan, salary_zero=np.nan, salary_low=np.nan, salary_topcoded=np.nan)
    topcoded = salary > SALARY_TOPCODE_ABOVE
    if topcoded:
        salary = SALARY_TOPCODE_VALUE
    log_salary = np.log(max(salary, SALARY_FLOOR)) if salary > 0 else np.nan
    return dict(log_salary=log_salary, salary_zero=float(salary == 0), salary_low=float(0 < salary < SALARY_FLOOR),
                salary_topcoded=float(topcoded))


def hours_to_features(hours):
    if hours is None:
        return dict(HRSWK=np.nan, hours_topcoded=np.nan)
    hours = min(hours, HOURS_CAP)
    return dict(HRSWK=hours, hours_topcoded=float(hours >= HOURS_CAP))


def telework_days(telework, days):
    """TELEFR is 0 unless the person teleworks (matches the cleaning step that recoded the skip to 0)."""
    if telework in NOT_ALLOWED_TELEWORK:
        return 0.0
    if telework in TELEWORKS or days is not None:
        return np.nan if days is None else float(days)
    return np.nan


def build_model_row(req, occupation, columns):
    """req: PredictRequest, occupation: row of occupations.json, columns: the model's training columns."""
    answers = req.model_dump()
    row = {}
    for api_name, (col, *_rest) in NUMBERS.items():
        if api_name not in ("salary", "hours_per_week"):
            row[col] = answers[api_name]
    row.update(salary_to_features(answers["salary"]))
    row.update(hours_to_features(answers["hours_per_week"]))
    row["TELEFR"] = telework_days(answers["telework"], answers["telework_days"])
    row["EMSIZE"] = answers["employer_size"]
    row["OCEDRLP"] = answers["degree_relatedness"]
    for api_name, (col, *_rest) in BOOLEANS.items():
        row[col] = answers[api_name]
    for api_name, (col, *_rest) in CATEGORICAL_FIELDS.items():
        row[col] = answers[api_name]
    for api_name, col, *_rest in IMPORTANCE:
        row[col] = answers["importance"][api_name]

    # from the occupation picker, never asked
    row["occ_group"] = occupation["occ_group"]
    for col in ONET:
        row[col] = occupation[col]

    frame = pd.DataFrame([row])
    numeric = [c for c in NUMERIC + BINARY + ONET + FAC if c in frame]
    frame[numeric] = frame[numeric].astype(float)  # None -> NaN
    for col in CATEGORICAL:
        frame[col] = frame[col].astype(object).where(frame[col].notna(), np.nan)
    return frame[columns]


def fit_details(pipeline, row, occupation):
    """P, J and their z-scores per fit pair, from the fitted FitFeatures step (same numbers the model used)."""
    fit_step = pipeline.named_steps["pre"].named_transformers_["fit"].named_steps["fit"]
    values = row.iloc[0]
    pairs = []
    for work_value, items in fit_step.pairs.items():
        ratings = values[items].to_numpy(float)
        p = None if np.isnan(ratings).all() else float(np.nanmean(ratings))
        j = None if np.isnan(values[work_value]) else float(values[work_value])
        mp, sp, mj, sj = fit_step.stats_[work_value]
        zp = None if p is None else (p - mp) / sp
        zj = None if j is None else (j - mj) / sj
        both = zp is not None and zj is not None
        pairs.append(dict(work_value=work_value, person_items=items, P=p, J=j, P_z=zp, J_z=zj,
                          fit_prod=zp * zj if both else None, fit_gap=abs(zp - zj) if both else None))
    support = values["Support"]
    location = values["FACLOC"]
    return dict(
        available=bool(occupation["has_work_values"]),
        reason=None if occupation["has_work_values"] else
        "O*NET has no Work Values for this occupation, so fit could not be computed; the fit terms were "
        "filled in with typical values from the training data",
        pairs=pairs,
        unpaired={"FACLOC": None if np.isnan(location) else float(location),
                  "Support": None if np.isnan(support) else float(support)})
