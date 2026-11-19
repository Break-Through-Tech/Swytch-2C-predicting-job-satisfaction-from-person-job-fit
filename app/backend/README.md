# Backend API

FastAPI service that serves the saved NSCG + O*NET logistic regression models. The frontend sends assessment
answers and gets back the probability of being **very satisfied** from two models:

- **A2** (the app's main model): demographics + job + O*NET + the person's importance ratings + person-job fit terms
- **A1** (the "without fit" comparison): the same without the ratings and fit terms

## Setup

From the repo root:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r app/backend/requirements.txt
cd app/backend
uvicorn main:app --reload          # http://127.0.0.1:8000, interactive docs at /docs
```

Run the tests from the repo root with `pytest app/backend/tests`. (One test rebuilds respondents from
`data/processed/nscg2023_onet_clean.csv`; it is skipped when that gitignored file is missing.)

CORS allows `http://localhost:5173` and `http://127.0.0.1:5173` (Vite). Set `CORS_ORIGINS` (comma separated)
to change that.

## Saved models

The trained files are small (about 5 KB each), so they are committed in `artifacts/`:

| File | What it is |
|---|---|
| `nscg_lr_A1.joblib`, `nscg_lr_A2.joblib` | dict with the fitted `pipeline`, decision `threshold`, `C`, the training `columns`, `sklearn_version` |
| `occupations.json` | one row per NCSES occupation code with its O*NET Work Values and job zone (the lookup the model needs when someone picks an occupation) |

Current values (trained on all 79,800 employed respondents):

| Model | C | Decision threshold | Columns |
|---|---|---|---|
| A1 | 0.0316 | 0.357 | 35 |
| A2 | 0.0316 | 0.392 | 44 |

To retrain (needs `data/processed/nscg2023_onet_clean.csv`; rebuild it with `notebooks/nscg/nscg_cleaning.ipynb`):

```bash
python src/models/nscg_lr_final.py
```

`scikit-learn` is pinned in `requirements.txt` to the version that wrote the files. The API warns at startup if
the installed version differs.

The expected performance of these models is the nested cross-validation table behind `GET /insights`
(A2 ROC-AUC 0.693 vs A1 0.652). The final models are fit on every row, so they have no held-out score of their own.

## How to read a prediction

- `probability` comes from a model trained with balanced class weights, so it runs higher than the share of
  people who are very satisfied. Show it as a relative score, not a literal chance.
- `predicted_very_satisfied` is `probability >= threshold`. The threshold maximises F1 on out-of-fold predictions.
- Anything the form leaves blank (`null` or missing) is filled in by the model with the training median or most
  common value. Only `occupation_code` is required.
- About 6% of respondents are in occupations with no O*NET Work Values (3 of the 129 occupations, including
  software developers). They still get predictions, but `fit.available` is `false` and the fit terms are imputed.

## Endpoints

### `GET /health`

```json
{"status": "ok",
 "models": {"A1": {"threshold": 0.357, "C": 0.0316, "trained_at": "2026-11-18T23:44:00+00:00", "sklearn_version": "1.9.1"},
            "A2": {"threshold": 0.392, "C": 0.0316, "trained_at": "2026-11-18T23:44:00+00:00", "sklearn_version": "1.9.1"}}}
```

### `GET /schema`

Everything the frontend needs to build the form. `type` is one of `occupation`, `number`, `select`, `boolean`.
Field names with a dot (`importance.salary`) are nested in the `/predict` request.

```json
{"fields": [
  {"name": "occupation_code", "label": "Occupation", "type": "occupation", "group": "Your job", "required": true,
   "options": null, "min": null, "max": null, "default": null, "help": "Pick from GET /occupations; sends the occupation's code"},
  {"name": "salary", "label": "Annual salary (USD)", "type": "number", "group": "Your job", "required": false,
   "options": null, "min": 0, "max": 100000000, "default": null, "help": "Before taxes; 0 if you report none"},
  {"name": "employer_size", "label": "Employer size", "type": "select", "group": "Your job", "required": false,
   "options": [{"value": 1, "label": "10 or fewer employees"}, "..."], "min": null, "max": null, "default": null, "help": null},
  {"name": "importance.salary", "label": "How important is: Salary?", "type": "select", "group": "What you value",
   "required": false, "options": [{"value": 4, "label": "Very important"}, {"value": 3, "label": "Somewhat important"},
   {"value": 2, "label": "Somewhat unimportant"}, {"value": 1, "label": "Not important at all"}],
   "min": null, "max": null, "default": null, "help": null}
]}
```

Groups: `Your job`, `About you`, `Education`, `Benefits`, `Job requirements`, `What you value`.
The importance ratings are the most useful part of the form: the fit terms are built from them.

### `GET /occupations`

129 occupations sorted by label, for the occupation picker.

```json
[{"code": "530860", "label": "Civil engineers, including architectural and sanitary", "occ_group": "53", "has_work_values": true},
 {"code": "110590", "label": "Software developers – applications and systems software", "occ_group": "11", "has_work_values": false}]
```

### `POST /predict`

Request (every field except `occupation_code` is optional):

```json
{"occupation_code": "530860",
 "salary": 85000, "hours_per_week": 40, "weeks_per_year": 52, "tenure_years": 4, "age": 35,
 "employer_size": 4, "degree_relatedness": 1, "telework": "Allowed to telework, and did", "telework_days": 2,
 "sex": "Female", "race_ethnicity": "Asian", "citizenship": "U.S. citizen, native", "marital_status": "Never married",
 "highest_degree": "Bachelor's", "degree_field": "Engineering", "employer_type": "Private for-profit",
 "offers_health_insurance": true, "offers_pension": true, "offers_profit_sharing": false, "offers_paid_leave": true,
 "expertise_natural_sci_eng": true, "expertise_other": false, "expertise_social_sci": false,
 "importance": {"advancement": 3, "benefits": 4, "challenge": 4, "independence": 3, "location": 2,
                "responsibility": 3, "salary": 4, "security": 4, "society": 2}}
```

Importance ratings use 1-4 where **4 = very important**. Allowed values for the select fields are in `/schema`.

How answers become model inputs:

- `occupation_code` supplies `occ_group` (first 2 digits), the six O*NET Work Values and the job zone.
- `salary` becomes `log_salary` plus the `salary_zero`, `salary_low` (under $1,000) and `salary_topcoded` flags.
  Salaries above $500,000 are treated as top-coded, like the survey file (which replaced every such salary with
  976,934 or 827,838; the API uses 976,934, the more common value).
- `hours_per_week` becomes `HRSWK` plus `hours_topcoded` (96 or more).
- `telework_days` is 0 unless `telework` is "Allowed to telework, and did" or "Required to telework".

Response (shortened; `fit.pairs` has 5 entries):

```json
{"occupation": {"code": "530860", "label": "Civil engineers, including architectural and sanitary", "has_work_values": true},
 "A1": {"probability": 0.537, "threshold": 0.357, "predicted_very_satisfied": true},
 "A2": {"probability": 0.521, "threshold": 0.392, "predicted_very_satisfied": true},
 "fit": {
   "available": true, "reason": null,
   "pairs": [{"work_value": "Independence", "person_items": ["FACIND", "FACRESP"],
              "P": 3.0, "J": 5.443, "P_z": -0.842, "J_z": 0.577, "fit_prod": -0.486, "fit_gap": 1.419}],
   "unpaired": {"FACLOC": 2.0, "Support": 4.443}},
 "notes": ["Probabilities come from a model trained with balanced class weights, ...",
           "Fields left blank were filled in with typical values from the training data."]}
```

What `fit` contains, per work value (this is what explains the A2 prediction):

- `P`: the person's importance composite, the mean of the matched ratings in `person_items` (1-4)
- `J`: the occupation's O*NET Work Value (about 1-7)
- `P_z`, `J_z`: both standardized against the training data so they can be compared
- `fit_prod = P_z * J_z`: high when the person cares about it and the job delivers it
- `fit_gap = |P_z - J_z|`: large when the person and the job mismatch
- `unpaired`: the location rating and the Support work value have no counterpart, so they are returned as-is

When `fit.available` is `false`, the occupation has no Work Values: `J`, `J_z`, `fit_prod` and `fit_gap` are `null`,
`reason` says why, and the prediction still comes back.

Errors: invalid input returns **422** with the field name and a message.

```json
{"detail": [{"field": "importance.salary", "message": "Input should be less than or equal to 4"},
            {"field": "sex", "message": "must be one of: ['Female', 'Male']"}]}
```

An unknown `occupation_code` also returns 422 (`field: "occupation_code"`).

### `GET /insights`

Nested cross-validation metrics from `results/nscg/nscg_lr_point_metrics.csv`, with 95% bootstrap intervals.
Models: `A0` (context only), `A1`, `A2`. Metrics: `ROC-AUC`, `PR-AUC`, `Balanced accuracy`, `Brier score`,
`Precision (very satisfied)`, `Recall (very satisfied)`, `F1 (very satisfied)`, `Macro-F1`.

```json
{"A2": {"ROC-AUC": {"value": 0.6928, "ci_low": 0.6891, "ci_high": 0.6965}, "...": "..."}}
```

## Code layout

| File | Role |
|---|---|
| `main.py` | app, CORS, routes |
| `schema.py` | the form fields (single source of truth for `/schema` and validation) |
| `contracts.py` | request and response models |
| `inputs.py` | form answers to model inputs, and the fit explanation |
| `model_store.py` | loads the saved models and occupation table at startup |
