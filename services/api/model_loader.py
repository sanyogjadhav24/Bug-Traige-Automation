import os, joblib
from loguru import logger
from transformers import AutoTokenizer, AutoModel
import torch

DEFAULT_MODEL_DIR = os.getenv("MODEL_DIR", "ml/models")
HF_MODEL_NAME = os.getenv("HF_MODEL_NAME", "distilbert-base-uncased")

class EmbeddingModel:
    def __init__(self, name: str = HF_MODEL_NAME):
        self.tok = AutoTokenizer.from_pretrained(name)
        self.model = AutoModel.from_pretrained(name)

    def encode(self, text: str):
        inputs = self.tok(text, return_tensors="pt", truncation=True, padding=True, max_length=160)
        with torch.no_grad():
            out = self.model(**inputs).last_hidden_state.mean(dim=1)
        return out.squeeze(0).numpy()

class LoadedModels:
    def __init__(self, model_dir: str = DEFAULT_MODEL_DIR):
        self.model_dir = model_dir
        self.embedding = EmbeddingModel()
        self.category = joblib.load(os.path.join(model_dir, "category_xgb.pkl"))
        self.severity = joblib.load(os.path.join(model_dir, "severity_logreg.pkl"))
        self.assignee = joblib.load(os.path.join(model_dir, "assignee_nb.pkl"))
        self.labelmaps = joblib.load(os.path.join(model_dir, "labelmaps.pkl"))
        self.version = joblib.load(os.path.join(model_dir, "version.pkl"))

    def predict_all(self, text: str):
        emb = self.embedding.encode(text)
        # Category
        cat_proba = self.category.predict_proba([emb])[0]
        cat_idx = int(cat_proba.argmax())
        cat_label = self.labelmaps["category_idx2label"][cat_idx]
        cat_conf = float(cat_proba[cat_idx])
        # Severity
        sev_proba = self.severity.predict_proba([emb])[0]
        sev_idx = int(sev_proba.argmax())
        sev_label = self.labelmaps["severity_idx2label"][sev_idx]
        sev_conf = float(sev_proba[sev_idx])
        # Assignee
        ass_top3_idx = self.assignee.predict_proba([emb])[0].argsort()[-3:][::-1]
        ass_top3 = [self.labelmaps["assignee_idx2label"][int(i)] for i in ass_top3_idx]
        return emb, (cat_label, cat_conf), (sev_label, sev_conf), ass_top3
