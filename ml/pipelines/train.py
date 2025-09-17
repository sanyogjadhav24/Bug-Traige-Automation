import argparse, os, joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from xgboost import XGBClassifier
from transformers import AutoTokenizer, AutoModel
import torch
from ml.features.text import clean_text

HF_MODEL = "distilbert-base-uncased"

def embed_batch(texts, tok, model, max_len=160):
    all_vecs = []
    for i in range(0, len(texts), 16):
        batch = texts[i:i+16]
        inputs = tok(batch, return_tensors="pt", truncation=True, padding=True, max_length=max_len)
        with torch.no_grad():
            out = model(**inputs).last_hidden_state.mean(dim=1).cpu().numpy()
        all_vecs.append(out)
    return np.vstack(all_vecs)

def main(data_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    df = pd.read_csv(data_path)
    df["text"] = (df["summary"].fillna("") + "\n" + df["description"].fillna("")).map(clean_text)
    df = df[(df["text"].str.len() > 10) & df["category"].notna() & df["severity"].notna() & df["assignee"].notna()].copy()

    tok = AutoTokenizer.from_pretrained(HF_MODEL)
    model = AutoModel.from_pretrained(HF_MODEL)

    X = embed_batch(df["text"].tolist(), tok, model)
    le_cat = LabelEncoder().fit(df["category"])
    le_sev = LabelEncoder().fit(df["severity"])
    le_ass = LabelEncoder().fit(df["assignee"])

    y_cat = le_cat.transform(df["category"])
    y_sev = le_sev.transform(df["severity"])
    y_ass = le_ass.transform(df["assignee"])

    X_train, X_test, ycat_tr, ycat_te, ysev_tr, ysev_te, yass_tr, yass_te = train_test_split(
        X, y_cat, y_sev, y_ass, test_size=0.2, random_state=42, stratify=y_cat
    )

    cat_clf = XGBClassifier(n_estimators=300, max_depth=8, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, objective="multi:softprob", tree_method="hist")
    cat_clf.fit(X_train, ycat_tr)

    sev_clf = LogisticRegression(max_iter=1000, multi_class="multinomial")
    sev_clf.fit(X_train, ysev_tr)

    scaler = MinMaxScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)
    ass_clf = GaussianNB()
    ass_clf.fit(X_train_sc, yass_tr)

    joblib.dump(cat_clf, os.path.join(out_dir, "category_xgb.pkl"))
    joblib.dump(sev_clf, os.path.join(out_dir, "severity_logreg.pkl"))
    joblib.dump(ass_clf, os.path.join(out_dir, "assignee_nb.pkl"))
    labelmaps = {
        "category_idx2label": {int(i): l for i,l in enumerate(le_cat.classes_)},
        "severity_idx2label": {int(i): l for i,l in enumerate(le_sev.classes_)},
        "assignee_idx2label": {int(i): l for i,l in enumerate(le_ass.classes_)},
        "assignee_scaler_min": scaler.min_.tolist(),
        "assignee_scaler_scale": scaler.scale_.tolist(),
    }
    joblib.dump(labelmaps, os.path.join(out_dir, "labelmaps.pkl"))
    joblib.dump("v1.0.0", os.path.join(out_dir, "version.pkl"))

    hist = {"embeddings": X_test[:100], "ids": df["bug_id"].astype(str).tolist()[:100]}
    joblib.dump(hist, os.path.join(out_dir, "history_embeddings.pkl"))

    from sklearn.metrics import classification_report
    print("CATEGORY\n", classification_report(ycat_te, cat_clf.predict(X_test)))
    print("SEVERITY\n", classification_report(ysev_te, sev_clf.predict(X_test)))
    print("ASSIGNEE (top-1 proxy)\n", classification_report(yass_te, ass_clf.predict(X_test_sc)))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_path", required=True)
    ap.add_argument("--out_dir", default="ml/models")
    args = ap.parse_args()
    main(args.data_path, args.out_dir)
