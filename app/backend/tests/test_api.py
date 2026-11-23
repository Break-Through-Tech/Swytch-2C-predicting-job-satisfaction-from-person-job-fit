import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from inputs import build_model_row, salary_to_features
from main import app
from nscg_features import CATEGORICAL
from schema import CATEGORICAL as CATEGORICAL_FIELDS, IMPORTANCE

warnings.filterwarnings("ignore")

CLEAN_CSV = Path(__file__).resolve().parents[3] / "data" / "processed" / "nscg2023_onet_clean.csv"
CIVIL_ENGINEERS = "530860"

SAMPLE = {
    "occupation_code": CIVIL_ENGINEERS, "salary": 85000, "hours_per_week": 40, "age": 35, "tenure_years": 4,
    "importance": {"advancement": 3, "benefits": 4, "challenge": 4, "independence": 3, "location": 2,
                   "responsibility": 3, "salary": 4, "security": 4, "society": 2},
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert set(body["models"]) == {"A1", "A2"}


def test_schema_options_match_the_trained_encoder(client):
    names = {f["name"] for f in client.get("/schema").json()["fields"]}
    assert "occupation_code" in names and "importance.salary" in names
    encoder = app.state.store.models["A2"]["pipeline"].named_steps["pre"].named_transformers_["cat"] \
        .named_steps["onehot"]
    trained = dict(zip(CATEGORICAL, encoder.categories_))
    for _api_name, (column, _label, options) in CATEGORICAL_FIELDS.items():
        assert {o["value"] for o in options} == set(trained[column]), column


def test_occupations(client):
    occupations = client.get("/occupations").json()
    assert len(occupations) == 129
    labels = [o["label"] for o in occupations]
    assert labels == sorted(labels)
    assert any(not o["has_work_values"] for o in occupations)


def test_predict_known_input(client):
    r = client.post("/predict", json=SAMPLE)
    assert r.status_code == 200
    body = r.json()
    assert body["A2"]["probability"] == pytest.approx(0.5212117, abs=1e-6)
    assert body["A1"]["probability"] == pytest.approx(0.5371163, abs=1e-6)
    assert body["A2"]["predicted_very_satisfied"] is True
    assert body["fit"]["available"] is True
    assert [p["work_value"] for p in body["fit"]["pairs"]] == [
        "Achievement", "Independence", "Recognition", "Relationships", "Working Conditions"]
    independence = body["fit"]["pairs"][1]
    assert independence["person_items"] == ["FACIND", "FACRESP"] and independence["P"] == 3.0


def test_predict_only_occupation_required(client):
    assert client.post("/predict", json={"occupation_code": CIVIL_ENGINEERS}).status_code == 200


@pytest.mark.parametrize("change", [
    {"importance": {"salary": 7}},
    {"salary": -5},
    {"hours_per_week": 120},
    {"sex": "unknown"},
    {"occupation_code": "not-a-code"},
    {"made_up_field": 1},
])
def test_predict_rejects_invalid_input(client, change):
    r = client.post("/predict", json={**SAMPLE, **change})
    assert r.status_code == 422
    assert r.json()["detail"][0]["field"] and r.json()["detail"][0]["message"]


def test_predict_without_work_values_still_predicts(client):
    code = next(o["code"] for o in client.get("/occupations").json() if not o["has_work_values"])
    r = client.post("/predict", json={**SAMPLE, "occupation_code": code})
    assert r.status_code == 200
    body = r.json()
    assert body["fit"]["available"] is False and body["fit"]["reason"]
    assert body["fit"]["pairs"][0]["J"] is None
    assert 0 <= body["A2"]["probability"] <= 1


def test_insights(client):
    insights = client.get("/insights").json()
    assert insights["A2"]["ROC-AUC"]["value"] == pytest.approx(0.693, abs=1e-3)


def test_cors_allows_local_frontend(client):
    r = client.options("/predict", headers={"Origin": "http://localhost:5173",
                                            "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_salary_features():
    zero = salary_to_features(0)
    assert zero["salary_zero"] == 1 and np.isnan(zero["log_salary"])
    low = salary_to_features(500)
    assert low["salary_low"] == 1 and low["log_salary"] == pytest.approx(np.log(1000))
    top = salary_to_features(650_000)
    assert top["salary_topcoded"] == 1 and top["log_salary"] == pytest.approx(np.log(976_934))
    normal = salary_to_features(85_000)
    assert (normal["salary_zero"], normal["salary_low"], normal["salary_topcoded"]) == (0, 0, 0)


@pytest.mark.skipif(not CLEAN_CSV.exists(), reason="cleaned NSCG data is gitignored; rebuild it to run this")
def test_form_answers_reproduce_training_rows():
    """Rebuild respondents' form answers from the cleaned data and check we get their training features back."""
    df = pd.read_csv(CLEAN_CSV, dtype=str)
    df = df[(df.salary_topcoded == "False") & (df.hours_topcoded == "False")].head(300)
    store = app.state.store
    columns = store.models["A2"]["columns"]
    expected_all = pd.read_csv(CLEAN_CSV, dtype=str).loc[df.index]

    def num(value):
        return None if pd.isna(value) else float(value)

    def flag(value):
        return None if pd.isna(value) else value in ("True", "1", "1.0")

    from contracts import PredictRequest
    for idx, r in df.iterrows():
        req = PredictRequest(
            occupation_code=r.N3OCPR, salary=num(r.SALARY), hours_per_week=num(r.HRSWK), weeks_per_year=num(r.WKSWK),
            tenure_years=num(r.tenure_years), age=num(r.AGE),
            employer_size=None if pd.isna(r.EMSIZE) else int(r.EMSIZE),
            degree_relatedness=None if pd.isna(r.OCEDRLP) else int(r.OCEDRLP),
            telework_days=None if pd.isna(r.TELEFR) else int(float(r.TELEFR)),
            sex=r.SEX_2023 if pd.notna(r.SEX_2023) else None,
            race_ethnicity=r.RACETHM if pd.notna(r.RACETHM) else None,
            citizenship=r.CTZN if pd.notna(r.CTZN) else None,
            marital_status=r.MARSTA if pd.notna(r.MARSTA) else None,
            highest_degree=r.DGRDG if pd.notna(r.DGRDG) else None,
            degree_field=r.NDGMEMG if pd.notna(r.NDGMEMG) else None,
            employer_type=r.NEDTP if pd.notna(r.NEDTP) else None,
            telework=r.TELEC if pd.notna(r.TELEC) else None,
            offers_health_insurance=flag(r.JOBINS), offers_pension=flag(r.JOBPENS),
            offers_profit_sharing=flag(r.JOBPROFT), offers_paid_leave=flag(r.JOBVAC),
            expertise_natural_sci_eng=flag(r.MGRNAT), expertise_other=flag(r.MGROTH),
            expertise_social_sci=flag(r.MGRSOC),
            importance={api: num(r[col]) and int(float(r[col])) for api, col, *_ in IMPORTANCE})
        got = build_model_row(req, store.occupation_by_code[r.N3OCPR], columns).iloc[0]
        want = expected_all.loc[idx]
        assert got["occ_group"] == want.N3OCPR[:2]
        for col in columns:
            if col == "occ_group":
                continue
            if col in CATEGORICAL:
                assert (got[col] == want[col]) or (pd.isna(got[col]) and pd.isna(want[col])), (idx, col)
                continue
            truth = {"True": 1.0, "False": 0.0}.get(want[col], want[col])
            truth = np.nan if pd.isna(truth) else float(truth)
            if col == "log_salary":  # training clips implausibly low salaries at log($1,000)
                truth = max(truth, np.log(1000))
            assert got[col] == pytest.approx(truth, nan_ok=True), (idx, col)
