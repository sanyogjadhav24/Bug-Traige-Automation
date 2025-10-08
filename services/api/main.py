from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.api.schemas import PredictIn, PredictOut, HealthOut
from services.api.model_loader import LoadedModels
from services.api.utils import gating_thresholds
from services.api.explain import similar_cases
from services.api.jira_client import create_issue, update_issue, check_jira_access
from services.api import jira_client as _jira_client
from loguru import logger
import os

app = FastAPI(title="Bug Triage Inference API", version="1.0.0")

# Allow the React dev server (and common localhost variants) to call this API from the browser
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/debug/jira_check")
def debug_jira_check():
    """Local-only debug endpoint to check Jira auth and create-issue permission.

    Returns configured Jira URL, user (email), project and whether the current
    credentials have CREATE_ISSUES permission for the project. Does NOT expose the token.
    """
    try:
        can_create = check_jira_access()
        return {
            "jira_url": _jira_client.JIRA_URL,
            "jira_user": _jira_client.JIRA_USER,
            "jira_project": _jira_client.JIRA_PROJECT,
            "can_create_issues": bool(can_create)
        }
    except Exception as e:
        return {"error": str(e)}


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
    # Only perform Jira actions if explicitly enabled and credentials have permission
    jira_auto_create = os.getenv("JIRA_AUTO_CREATE", "false").lower() == "true"
    if jira_auto_create:
        has_perm = check_jira_access()
        if cat_conf >= auto_thr and has_perm:
            issue_key = create_issue(
                summary=req.summary,
                description=req.description,
                category=cat,
                severity=sev,
                assignee=ass_top3[0]
            )
        elif cat_conf >= cmt_thr and has_perm:
            update_issue("DEM-1", fields={}, comment=f"[Suggestion] {comment}")
        else:
            if (cat_conf >= auto_thr or cat_conf >= cmt_thr) and not has_perm:
                logger.warning("Jira action requested but credentials lack create permission; skipping Jira call.")

    ex = similar_cases(emb, _emb_matrix, _emb_ids, top_k=5)

    return {
        "category": cat, "category_conf": cat_conf,
        "severity": sev, "severity_conf": sev_conf,
        "assignee_top1": ass_top3[0], "assignee_top3": ass_top3,
        "explanations": {"similar_cases": ex} if ex else None,
        "jira_issue_key": issue_key,
        "model_version": _models.version
    }


@app.post("/create_jira")
def create_jira(payload: dict):
    """Create a Jira issue using configured server credentials.
    
    Expected payload: {summary, description, category?, severity?, assignee?}
    Returns: {success: bool, issue_key?: str, error?: str}
    """
    # Validate required fields
    summary = payload.get("summary", "").strip()
    description = payload.get("description", "").strip()
    
    if not summary or not description:
        return {"success": False, "error": "Summary and description are required"}
    
    # Optional AI prediction fields
    category = payload.get("category", "")
    severity = payload.get("severity", "")
    assignee = payload.get("assignee", "")
    
    # Check if server has Jira permissions
    if not check_jira_access():
        return {
            "success": False, 
            "error": "Jira is not properly configured or lacks create permissions. Contact administrator."
        }
    
    # Create the issue
    issue_key = create_issue(
        summary=summary,
        description=description,
        category=category,
        severity=severity,
        assignee=assignee
    )
    
    if issue_key:
        return {"success": True, "issue_key": issue_key}
    else:
        return {"success": False, "error": "Failed to create Jira issue. Check server logs for details."}
