import csv
import io
import json
from datetime import datetime, timezone
from pathlib import Path
import os
import uuid
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/datasets", tags=["Dataset Management"])

ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "ml" / "datasets"
SAMPLE_DATASET = DATASET_DIR / "attrition_sample.csv"
METADATA_FILE = DATASET_DIR / "dataset_metadata.json"

FEATURE_COLUMNS = [
    "age",
    "monthly_income",
    "years_at_company",
    "job_satisfaction",
    "work_life_balance",
    "overtime",
    "years_since_promotion",
    "distance_from_home",
]
REQUIRED_COLUMNS = FEATURE_COLUMNS + ["attrition"]
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


def require_hr(user: User):
    if user.role not in ("ADMIN", "HR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or HR permission required",
        )


def load_metadata():
    if not METADATA_FILE.exists():
        return []
    try:
        content = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        return content if isinstance(content, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_metadata(items):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    temporary = METADATA_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(items, indent=2),
        encoding="utf-8",
    )
    temporary.replace(METADATA_FILE)


def dataset_summary(path: Path, dataset_id: str, uploaded_at=None):
    try:
        df = pd.read_csv(path)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="CSV could not be read.",
        ) from None

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]

    return {
        "id": dataset_id,
        "name": path.name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "missing_required_columns": missing,
        "valid": not missing and len(df) > 0,
        "uploaded_at": uploaded_at,
        "size_bytes": path.stat().st_size,
        "is_sample": path.name == SAMPLE_DATASET.name,
    }


@router.get("/")
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    items = []
    if SAMPLE_DATASET.is_file():
        items.append(
            dataset_summary(
                SAMPLE_DATASET,
                "sample",
                uploaded_at=None,
            )
        )

    for metadata in load_metadata():
        filename = metadata.get("filename", "")
        path = (DATASET_DIR / filename).resolve()

        if (
            path.parent != DATASET_DIR.resolve()
            or not path.is_file()
            or path == SAMPLE_DATASET
        ):
            continue

        items.append(
            dataset_summary(
                path,
                metadata.get("id", filename),
                metadata.get("uploaded_at"),
            )
        )

    return {"items": items, "total": len(items)}


@router.post("/validate")
async def validate_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    if not file.filename or Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=415, detail="Upload a CSV file.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="CSV file must be 10 MB or smaller.",
        )

    try:
        text = content.decode("utf-8-sig")
        df = pd.read_csv(io.StringIO(text))
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="CSV is invalid or could not be decoded as UTF-8.",
        ) from None
    finally:
        await file.close()

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    issues = []

    if df.empty:
        issues.append("Dataset contains no data rows.")

    if missing:
        issues.append("Missing required columns: " + ", ".join(missing))

    if "attrition" in df.columns and not df.empty:
        labels = set(df["attrition"].dropna().astype(str).str.strip())
        if not labels.issubset({"0", "1"}):
            issues.append("attrition must contain only 0 and 1.")
        elif labels != {"0", "1"}:
            issues.append("Training data must contain both attrition classes.")

    for column in FEATURE_COLUMNS:
        if column not in df.columns:
            continue
        if column != "overtime":
            values = pd.to_numeric(df[column], errors="coerce")
            if values.isna().any():
                issues.append(f"{column} contains missing or non-numeric values.")
        else:
            overtime = set(
                df[column].dropna().astype(str).str.strip().str.lower()
            )
            if not overtime.issubset({"yes", "no"}):
                issues.append("overtime must contain Yes or No values.")

    return {
        "filename": Path(file.filename).name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(df.columns),
        "missing_required_columns": missing,
        "valid": len(issues) == 0,
        "issues": issues,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_hr(current_user)

    if not file.filename or Path(file.filename).suffix.lower() != ".csv":
        raise HTTPException(status_code=415, detail="Upload a CSV file.")

    original_name = Path(file.filename).name
    if not original_name or original_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid filename.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="CSV file must be 10 MB or smaller.",
        )

    try:
        df = pd.read_csv(io.BytesIO(content), encoding="utf-8-sig")
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="CSV is invalid or could not be decoded as UTF-8.",
        ) from None

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Required columns are missing.", "missing": missing},
        )

    if df.empty:
        raise HTTPException(status_code=422, detail="Dataset contains no data rows.")

    if df["attrition"].isna().any():
        raise HTTPException(status_code=422, detail="attrition cannot be empty.")

    labels = set(df["attrition"].astype(str).str.strip())
    if not labels.issubset({"0", "1"}) or labels != {"0", "1"}:
        raise HTTPException(
            status_code=422,
            detail="attrition must contain both classes: 0 and 1.",
        )

    for column in FEATURE_COLUMNS:
        if column == "overtime":
            values = set(df[column].dropna().astype(str).str.strip().str.lower())
            if df[column].isna().any() or not values.issubset({"yes", "no"}):
                raise HTTPException(
                    status_code=422,
                    detail="overtime must contain only Yes or No values.",
                )
        else:
            values = pd.to_numeric(df[column], errors="coerce")
            if values.isna().any():
                raise HTTPException(
                    status_code=422,
                    detail=f"{column} must contain numeric values without blanks.",
                )
            df[column] = values

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    dataset_id = uuid.uuid4().hex
    filename = f"uploaded_{dataset_id}.csv"
    destination = DATASET_DIR / filename

    # Save normalized CSV content under a generated name, not the user's filename.
    df.to_csv(destination, index=False)

    metadata = load_metadata()
    metadata.append({
        "id": dataset_id,
        "filename": filename,
        "original_name": original_name,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": current_user.id,
    })

    try:
        save_metadata(metadata)
    except Exception:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Dataset was not registered. Please try again.",
        ) from None

    return dataset_summary(
        destination,
        dataset_id,
        uploaded_at=metadata[-1]["uploaded_at"],
    )


@router.post("/{dataset_id}/train")
def train_dataset_model(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Train and evaluate the attrition model using a registered CSV dataset."""
    require_hr(current_user)

    DATASET_DIR.mkdir(parents=True, exist_ok=True)

    # Resolve the requested ID only against the built-in sample or metadata.
    if dataset_id in {"sample", SAMPLE_DATASET.stem, SAMPLE_DATASET.name}:
        dataset_path = SAMPLE_DATASET
    else:
        metadata = load_metadata()
        selected = next(
            (item for item in metadata if str(item.get("id")) == dataset_id),
            None,
        )

        if selected is None:
            raise HTTPException(status_code=404, detail="Dataset not found.")

        filename = selected.get("filename")
        if not filename or Path(filename).name != filename:
            raise HTTPException(status_code=400, detail="Invalid dataset metadata.")

        dataset_path = (DATASET_DIR / filename).resolve()
        if dataset_path.parent != DATASET_DIR.resolve():
            raise HTTPException(status_code=400, detail="Invalid dataset path.")

    if not dataset_path.is_file():
        raise HTTPException(status_code=404, detail="Dataset file not found.")

    try:
        df = pd.read_csv(dataset_path)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail="Could not read the selected CSV dataset.",
        ) from None

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Required columns are missing.", "missing": missing},
        )

    if df.empty:
        raise HTTPException(status_code=422, detail="Dataset contains no rows.")

    # Keep only model features and target; reject malformed labels.
    df = df[REQUIRED_COLUMNS].copy()
    labels = df["attrition"].astype(str).str.strip()
    if not labels.isin(["0", "1"]).all() or labels.nunique() != 2:
        raise HTTPException(
            status_code=422,
            detail="attrition must contain both classes: 0 and 1.",
        )

    y = labels.astype(int)
    if y.value_counts().min() < 2:
        raise HTTPException(
            status_code=422,
            detail="At least two rows per attrition class are required for training.",
        )

    X = df[FEATURE_COLUMNS].copy()

    numeric_features = [column for column in FEATURE_COLUMNS if column != "overtime"]
    categorical_features = ["overtime"]

    for column in numeric_features:
        X[column] = pd.to_numeric(X[column], errors="coerce")

    X["overtime"] = X["overtime"].astype("string").str.strip().str.lower()
    X["overtime"] = X["overtime"].map({
        "yes": "Yes",
        "no": "No",
    })

    # Reject entirely empty numeric columns and missing categorical values;
    # the pipeline imputes occasional missing values in otherwise usable columns.
    for column in numeric_features:
        if X[column].notna().sum() == 0:
            raise HTTPException(
                status_code=422,
                detail=f"{column} has no usable numeric values.",
            )

    if X["overtime"].notna().sum() == 0:
        raise HTTPException(
            status_code=422,
            detail="overtime must contain Yes or No values.",
        )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]),
                numeric_features,
            ),
            (
                "categorical",
                Pipeline(steps=[
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore")),
                ]),
                categorical_features,
            ),
        ]
    )

    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced")),
    ])

    try:
        X_train, X_eval, y_train, y_eval = train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y,
        )
        model.fit(X_train, y_train)

        predictions = model.predict(X_eval)
        probabilities = model.predict_proba(X_eval)[:, 1]
        accuracy = float(accuracy_score(y_eval, predictions))
        auc = float(roc_auc_score(y_eval, probabilities))
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Training or evaluation failed: {type(exc).__name__}. "
                   "Check that the dataset has enough valid rows and both classes.",
        ) from None

    # Resolve the prediction loader before replacing the current model.
    from app.api.v1.predictions import get_attrition_model

    model_dir = ROOT / "ml" / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "attrition_model.joblib"
    temp_path = model_dir / f"attrition_model_{uuid.uuid4().hex}.tmp"

    try:
        # Write to a temporary file first so an existing model is not
        # overwritten unless serialization succeeds.
        joblib.dump(model, temp_path)
        os.replace(temp_path, model_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save the trained model.",
        ) from None

    # Refresh the prediction endpoint's cached model after the replacement.
    get_attrition_model.cache_clear()

    return {
        "message": "Model trained and evaluated successfully.",
        "dataset_id": dataset_id,
        "dataset_filename": dataset_path.name,
        "training_rows": int(len(X_train)),
        "evaluation_rows": int(len(X_eval)),
        "accuracy": accuracy,
        "roc_auc": auc,
        "model_file": model_path.name,
    }
