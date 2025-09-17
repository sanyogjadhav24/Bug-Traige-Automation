from fastapi import FastAPI
from services.api.schemas import PredictIn, PredictOut, HealthOut
from services.api.model_loader import LoadedModels
from services.api.utils import gating_thresholds
from services.api.explain import similar_cases
from services.api.jira_client import create_issue, update_issue
from loguru import logger
import os

app = FastAPI(title="Bug Triage Inference API", version="1.0.0")

_models = None
_emb_matrix = None
_emb_ids = []


@app.on_event("startup")
def _load():
    global _models, _emb_matrix, _emb_ids
    _models = LoadedModels()
    try:
        import joblib, numpy as np
        hist = joblib.load(os.path.join("ml", "models", "history_embeddings.pkl"))
        _emb_matrix = hist["embeddings"].astype(float)
        _emb_ids = hist["ids"]
        logger.info(f"Loaded {_emb_matrix.shape[0]} historical embeddings for explain.")
    except Exception:
        logger.info("No historical embeddings; explanations will be minimal.")


@app.get("/health", response_model=HealthOut)
def health():
    return {"status": "ok", "model_version": _models.version}


@app.post("/predict", response_model=PredictOut)
def predict(req: PredictIn):
    text = (req.summary or "") + "\n" + (req.description or "")
    emb, (cat, cat_conf), (sev, sev_conf), ass_top3 = _models.predict_all(text)
    auto_thr, cmt_thr = gating_thresholds()

    comment = (
        f"AI triage → category: {cat} ({cat_conf:.2f}), "
        f"severity: {sev} ({sev_conf:.2f}), "
        f"assignee: {ass_top3[0]}"
    )

    issue_key = None
    if cat_conf >= auto_thr:
        # Create a new Jira issue automatically
        issue_key = create_issue(
            summary=req.summary,
            description=req.description,
            category=cat,
            severity=sev,
            assignee=ass_top3[0]
        )
    elif cat_conf >= cmt_thr:
        # Just add comment to a default issue
        update_issue("DEM-1", fields={}, comment=f"[Suggestion] {comment}")

    ex = similar_cases(emb, _emb_matrix, _emb_ids, top_k=5)

    return {
        "category": cat, "category_conf": cat_conf,
        "severity": sev, "severity_conf": sev_conf,
        "assignee_top1": ass_top3[0], "assignee_top3": ass_top3,
        "explanations": {"similar_cases": ex} if ex else None,
        "jira_issue_key": issue_key,
        "model_version": _models.version
    }
