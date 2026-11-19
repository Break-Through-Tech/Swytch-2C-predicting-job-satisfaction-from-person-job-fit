"""FastAPI backend: serves the saved NSCG logistic regression models.

Run from this folder:  uvicorn main:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from contracts import PredictRequest, PredictResponse
from inputs import build_model_row, fit_details
from model_store import ModelStore
from schema import FIELDS

DEFAULT_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"  # Vite dev server
NOTES = [
    "Probabilities come from a model trained with balanced class weights, so they run higher than the "
    "share of people who are very satisfied. Treat them as a relative score, not a literal chance.",
    "Fields left blank were filled in with typical values from the training data.",
]


@asynccontextmanager
async def lifespan(app):
    app.state.store = ModelStore()
    yield


app = FastAPI(title="Swytch job satisfaction API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", DEFAULT_ORIGINS).split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError):
    """422 with {"detail": [{"field": "importance.salary", "message": "..."}]}."""
    detail = [{"field": ".".join(str(p) for p in e["loc"] if p != "body"),
               "message": e["msg"].removeprefix("Value error, ")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": detail})


@app.get("/health")
def health():
    models = app.state.store.models
    return {"status": "ok",
            "models": {name: {"threshold": b["threshold"], "C": b["C"], "trained_at": b["trained_at"],
                              "sklearn_version": b["sklearn_version"]} for name, b in models.items()}}


@app.get("/schema")
def schema():
    return {"fields": FIELDS}


@app.get("/occupations")
def occupations():
    return [{"code": o["code"], "label": o["label"], "occ_group": o["occ_group"],
             "has_work_values": o["has_work_values"]} for o in app.state.store.occupations]


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    store = app.state.store
    occupation = store.occupation_by_code.get(req.occupation_code)
    if occupation is None:
        raise HTTPException(422, detail=[{"field": "occupation_code",
                                          "message": f"unknown occupation code '{req.occupation_code}'; "
                                                     "use a code from GET /occupations"}])

    result = {}
    for name, bundle in store.models.items():
        row = build_model_row(req, occupation, bundle["columns"])
        probability = float(bundle["pipeline"].predict_proba(row)[0, 1])
        result[name] = dict(probability=probability, threshold=bundle["threshold"],
                            predicted_very_satisfied=probability >= bundle["threshold"])
        if name == "A2":
            fit = fit_details(bundle["pipeline"], row, occupation)

    notes = list(NOTES)
    if not fit["available"]:
        notes.append(fit["reason"])
    return {"occupation": {"code": occupation["code"], "label": occupation["label"],
                           "has_work_values": occupation["has_work_values"]},
            **result, "fit": fit, "notes": notes}


@app.get("/insights")
def insights():
    return app.state.store.insights()
