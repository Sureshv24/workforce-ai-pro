from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "datasets" / "attrition_sample.csv"
MODEL_PATH = ROOT / "models" / "attrition_model.joblib"

df = pd.read_csv(DATA_PATH)

target = "attrition"
X = df.drop(columns=[target])
y = df[target]

if y.nunique() < 2:
    raise ValueError("Training data must contain both attrition classes.")

numeric_features = [
    "age",
    "monthly_income",
    "years_at_company",
    "job_satisfaction",
    "work_life_balance",
    "years_since_promotion",
    "distance_from_home",
]
categorical_features = ["overtime"]

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
])

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)
probabilities = model.predict_proba(X_test)[:, 1]

print("Test accuracy:", round(accuracy_score(y_test, predictions), 4))
if y_test.nunique() == 2:
    print("Test ROC-AUC:", round(roc_auc_score(y_test, probabilities), 4))

print("\nClassification report:")
print(classification_report(y_test, predictions, zero_division=0))

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
joblib.dump(model, MODEL_PATH)

print(f"\nModel saved to: {MODEL_PATH}")
print("WARNING: Synthetic-data metrics are not evidence of real-world accuracy.")
