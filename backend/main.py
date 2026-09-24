import os
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from symptom_rules import (
    extract_symptoms,
    analyze_rule_based_symptoms,
)

from mental_health import (
    calculate_mental_health_score,
    get_mental_health_questions,
)

from database import Base, engine, get_db
from database_models import User


# ============================================================
# FUSION MODEL
# ============================================================

try:
    from predict_fusion import (
        predict_fusion as run_fusion_prediction,
        get_fusion_info,
        available_symptoms,
    )

    FUSION_LOADED = True

    print("Fusion model loaded successfully!")
    print(
        "Available symptoms:",
        len(available_symptoms)
    )

except Exception as e:
    FUSION_LOADED = False

    run_fusion_prediction = None
    get_fusion_info = None
    available_symptoms = []

    print(
        "WARNING: Fusion model could not be loaded."
    )
    print("Error:", e)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AYUSHMED AI",
    description=(
        "AI-powered health screening support API. "
        "This system does not provide medical diagnosis."
    ),
    version="2.0.0",
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class SymptomRequest(BaseModel):
    symptoms: str


class HealthRequest(BaseModel):
    symptoms: Optional[str] = ""


class MentalHealthRequest(BaseModel):
    answers: list[int]


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    fusion_info = {}

    if FUSION_LOADED and get_fusion_info:
        fusion_info = get_fusion_info()

    return {
        "status": "success",
        "message": "AYUSHMED AI Backend is running!",
        "fusion_model_loaded": FUSION_LOADED,
        "model": fusion_info,
        "features": [
            "Disease Symptom Assessment",
            "Mental Health Assessment",
            "User Registration",
            "User Login",
        ],
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "fusion_model_loaded": FUSION_LOADED,
        "symptom_features": len(
            available_symptoms
        ),
    }


# ============================================================
# FUSION PREDICTION
# ============================================================

def predict_disease(
    matched_symptoms: list[str]
):
    """
    Final AYUSHMED AI prediction.

    Fusion configuration:

        Old model       = 20%
        Pretrained      = 80%

    Old model internally:

        Logistic        = 60%
        Naive Bayes     = 40%
    """

    if not FUSION_LOADED:
        raise RuntimeError(
            "Fusion model is not loaded."
        )

    if not matched_symptoms:
        return []

    predictions = run_fusion_prediction(
        matched_symptoms,
        top_k=3
    )

    return predictions


# ============================================================
# DISEASE PREDICTION ENDPOINT
# ============================================================

@app.post("/predict-disease")
def predict_disease_endpoint(
    request: SymptomRequest
):

    if not request.symptoms.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms."
        )

    # --------------------------------------------------------
    # EXTRACT DATASET SYMPTOMS
    # --------------------------------------------------------

    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms
    )

    # --------------------------------------------------------
    # NO MATCH
    # --------------------------------------------------------

    if not matched_symptoms:

        return {
            "status": "no_match",
            "message": (
                "No matching symptoms were found "
                "in the trained dataset."
            ),
            "input": request.symptoms,
            "matched_symptoms": [],
            "predictions": [],
            "disclaimer": (
                "This system provides informational "
                "screening support and is not a "
                "medical diagnosis."
            ),
        }

    # --------------------------------------------------------
    # FUSION PREDICTION
    # --------------------------------------------------------

    if FUSION_LOADED:

        predictions = predict_disease(
            matched_symptoms
        )

        return {
            "status": "success",
            "model": "fusion",
            "input": request.symptoms,
            "matched_symptoms": matched_symptoms,
            "top_prediction": predictions[0],
            "top_predictions": predictions,
            "fusion": {
                "old_model_weight": 0.2,
                "pretrained_model_weight": 0.8,
            },
            "disclaimer": (
                "This is an AI-based informational "
                "screening-support result, not a "
                "medical diagnosis."
            ),
        }

    # --------------------------------------------------------
    # RULE-BASED FALLBACK
    # --------------------------------------------------------

    rule_result = analyze_rule_based_symptoms(
        matched_symptoms
    )

    return {
        "status": rule_result["status"],
        "input": request.symptoms,
        "matched_symptoms": (
            rule_result["matched_symptoms"]
        ),
        "possible_categories": (
            rule_result["possible_categories"]
        ),
        "disclaimer": rule_result["disclaimer"],
    }


# ============================================================
# SYMPTOM ANALYSIS ENDPOINT
# ============================================================

@app.post("/analyze-symptoms")
def analyze_symptoms(
    request: SymptomRequest
):

    if not request.symptoms.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms."
        )

    # --------------------------------------------------------
    # MATCH SYMPTOMS
    # --------------------------------------------------------

    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms
    )

    # --------------------------------------------------------
    # FUSION MODEL
    # --------------------------------------------------------

    if FUSION_LOADED and matched_symptoms:

        predictions = predict_disease(
            matched_symptoms
        )

        return {
            "status": "success",
            "model": "fusion",
            "input": request.symptoms,
            "matched_symptoms": matched_symptoms,
            "condition": predictions[0][
                "disease"
            ],
            "confidence": predictions[0][
                "confidence"
            ],
            "top_predictions": predictions,
            "fusion": {
                "old_model_weight": 0.2,
                "pretrained_model_weight": 0.8,
            },
            "disclaimer": (
                "This is an AI-based informational "
                "screening-support result, not a "
                "medical diagnosis."
            ),
        }

    # --------------------------------------------------------
    # RULE-BASED FALLBACK
    # --------------------------------------------------------

    rule_result = analyze_rule_based_symptoms(
        matched_symptoms
    )

    return {
        "status": rule_result["status"],
        "input": request.symptoms,
        "matched_symptoms": (
            rule_result["matched_symptoms"]
        ),
        "possible_categories": (
            rule_result["possible_categories"]
        ),
        "disclaimer": rule_result["disclaimer"],
    }


# ============================================================
# MENTAL HEALTH QUESTIONS
# ============================================================

@app.get("/mental-health/questions")
def mental_health_questions():

    return {
        "status": "success",
        "questions": get_mental_health_questions(),
        "answer_scale": {
            "0": "Not at all",
            "1": "Several days",
            "2": "More than half the days",
            "3": "Nearly every day",
        },
    }


# ============================================================
# MENTAL HEALTH ASSESSMENT
# ============================================================

@app.post("/mental-health-assessment")
def mental_health_assessment(
    request: MentalHealthRequest
):

    try:

        result = calculate_mental_health_score(
            request.answers
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


# ============================================================
# USER REGISTRATION
# ============================================================

@app.post("/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):

    # Normalize email
    email = request.email.strip().lower()

    # Check existing user
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="Email already registered."
        )

    # Hash password
    hashed_password = pwd_context.hash(
        request.password
    )

    # Create user
    user = User(
        name=request.name.strip(),
        email=email,
        password_hash=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "message": "Registration successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }


# ============================================================
# USER LOGIN
# ============================================================

@app.post("/login")
def login_user(
    request: LoginRequest,
    db: Session = Depends(get_db)
):

    email = request.email.strip().lower()

    # Find user
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    # Verify password
    if not pwd_context.verify(
        request.password,
        user.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    return {
        "status": "success",
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }