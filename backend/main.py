
# ============================================================
# IMPORTS
# ============================================================

import os
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# AI MODULES
from ai.safety_layer import build_safety_context
from ai.response_builder import build_health_response
from ai.rag.retriever import retrieve_knowledge
from ai.ollama_service import generate_health_response

# SYMPTOM ANALYSIS
from symptom_rules import (
    extract_symptoms,
    analyze_rule_based_symptoms,
)

# MENTAL HEALTH
from mental_health import (
    calculate_mental_health_score,
    get_mental_health_questions,
)

# DATABASE
from database import Base, engine, get_db
from database_models import User


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
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============================================================
# PASSWORD SECURITY
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

Base.metadata.create_all(bind=engine)


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
    print("Available symptoms:", len(available_symptoms))

except Exception as e:

    FUSION_LOADED = False

    run_fusion_prediction = None
    get_fusion_info = None
    available_symptoms = []

    print("WARNING: Fusion model could not be loaded.")
    print("Error:", e)


# ============================================================
# REQUEST MODELS
# ============================================================

class SymptomRequest(BaseModel):
    symptoms: str = Field(max_length=3000)


class ChatHistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=1500)


class ChatRequest(BaseModel):
    message: str = Field(max_length=1500)
    history: list[ChatHistoryItem] = Field(
        default_factory=list,
        max_length=12,
    )


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
            "Natural AI Chatbot",
            "Fusion Disease Screening",
            "RAG Knowledge Retrieval",
            "Ollama LLM",
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
        "symptom_features": len(available_symptoms),
    }


# ============================================================
# FUSION PREDICTION HELPER
# ============================================================

def predict_disease(matched_symptoms: list[str]):

    if not FUSION_LOADED:
        raise RuntimeError("Fusion model is not loaded.")

    if not matched_symptoms:
        return []

    try:
        predictions = run_fusion_prediction(
            matched_symptoms,
            top_k=3,
        )

        return predictions

    except Exception as error:

        print("WARNING: Fusion prediction failed:", error)
        return []


# ============================================================
# DISEASE PREDICTION ENDPOINT
# ============================================================

@app.post("/predict-disease")
def predict_disease_endpoint(request: SymptomRequest):

    if not request.symptoms.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms.",
        )

    safety = build_safety_context(request.symptoms)

    if safety.get("is_emergency"):

        return {
            "status": "urgent",
            "model": "safety_layer",
            "input": request.symptoms,
            "matched_symptoms": [],
            "top_predictions": [],
            "safety": safety,
            "health_response": build_health_response(
                request.symptoms,
                [],
                {},
                safety,
            ),
            "disclaimer": (
                "This system does not provide medical diagnosis "
                "or replace professional medical care."
            ),
        }

    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms,
    )

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
                "This system provides informational screening "
                "support and is not a medical diagnosis."
            ),
        }

    if FUSION_LOADED:

        predictions = predict_disease(matched_symptoms)

        if predictions:

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
                    "screening-support result, not a medical diagnosis."
                ),
            }

    rule_result = analyze_rule_based_symptoms(
        matched_symptoms
    )

    return {
        "status": rule_result["status"],
        "input": request.symptoms,
        "matched_symptoms": rule_result["matched_symptoms"],
        "possible_categories": rule_result["possible_categories"],
        "disclaimer": rule_result["disclaimer"],
    }


# ============================================================
# NATURAL CONVERSATIONAL AI CHATBOT
# ============================================================

@app.post("/chat")
def chat_endpoint(request: ChatRequest):

    message = request.message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please provide a message.",
        )

    # --------------------------------------------------------
    # CONVERSATION HISTORY
    # --------------------------------------------------------

    history_text = []

    for item in request.history:

        if item.role == "user":
            text = item.text.strip()

            if text:
                history_text.append(text)

    combined_input = "\n".join(
        [*history_text, message]
    )

    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    safety = build_safety_context(message)

    if safety.get("is_emergency"):

        health_response = build_health_response(
            message,
            [],
            {},
            safety,
        )

        return {
            "status": "urgent",
            "model": "safety_layer",
            "message": health_response,
            "safety": safety,
            "should_stop": True,
            "disclaimer": (
                "This system does not provide medical diagnosis "
                "or replace professional medical care."
            ),
        }

    # --------------------------------------------------------
    # SYMPTOM EXTRACTION
    # --------------------------------------------------------

    matched_symptoms = extract_symptoms(
        combined_input,
        available_symptoms,
    )

    # --------------------------------------------------------
    # FUSION PREDICTION
    # --------------------------------------------------------

    predictions = []

    if FUSION_LOADED and matched_symptoms:

        predictions = predict_disease(
            matched_symptoms
        )

    top_prediction = (
        predictions[0]
        if predictions
        else None
    )

    # --------------------------------------------------------
    # LOCAL RAG
    # --------------------------------------------------------

    rag_context = retrieve_knowledge(
        combined_input,
        top_k=3,
    )

    # --------------------------------------------------------
    # APPLICATION CONTEXT
    # --------------------------------------------------------

    application_data = {
        "prediction": (
            {
                "condition": top_prediction.get("disease"),
                "confidence": top_prediction.get("confidence"),
            }
            if top_prediction
            else None
        ),
        "matched_symptoms": matched_symptoms,
        "safety": safety,
        "rag_context": rag_context,
    }

    # --------------------------------------------------------
    # OLLAMA RESPONSE
    # --------------------------------------------------------

    try:

        health_response = generate_health_response(
            combined_input,
            application_data,
        )

    except Exception as error:

        print("Ollama response error:", error)

        raise HTTPException(
            status_code=503,
            detail=(
                "Local AI service is currently unavailable. "
                "Please check whether Ollama is running."
            ),
        )

    # --------------------------------------------------------
    # FINAL CHAT RESPONSE
    # --------------------------------------------------------

    return {
        "status": "success",
        "model": "chat+fusion+rag+ollama",
        "message": health_response,
        "matched_symptoms": matched_symptoms,
        "top_predictions": predictions[:3],
        "rag_context": rag_context,
        "safety": safety,
        "should_stop": False,
        "disclaimer": (
            "This is an AI-based informational "
            "screening-support response, not a medical diagnosis."
        ),
    }


# ============================================================
# SYMPTOM ANALYSIS ENDPOINT
# ============================================================

@app.post("/analyze-symptoms")
def analyze_symptoms(request: SymptomRequest):

    if not request.symptoms.strip():

        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms.",
        )

    safety = build_safety_context(
        request.symptoms
    )

    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms,
    )

    if safety.get("is_emergency"):

        health_response = build_health_response(
            request.symptoms,
            matched_symptoms,
            {},
            safety,
        )

        return {
            "status": "urgent",
            "model": "safety_layer",
            "input": request.symptoms,
            "matched_symptoms": matched_symptoms,
            "condition": None,
            "confidence": None,
            "top_predictions": [],
            "safety": safety,
            "health_response": health_response,
            "disclaimer": (
                "This system does not provide medical diagnosis "
                "or replace professional medical care."
            ),
        }

    if FUSION_LOADED and matched_symptoms:

        predictions = predict_disease(
            matched_symptoms
        )

        if predictions:

            top_prediction = predictions[0]

            condition = top_prediction.get("disease")
            confidence = top_prediction.get("confidence")

            rag_context = retrieve_knowledge(
                request.symptoms,
                top_k=3,
            )

            application_data = {
                "prediction": {
                    "condition": condition,
                    "confidence": confidence,
                },
                "matched_symptoms": matched_symptoms,
                "safety": safety,
                "rag_context": rag_context,
            }

            health_response = generate_health_response(
                request.symptoms,
                application_data,
            )

            return {
                "status": "success",
                "model": "fusion+rag+ollama",
                "input": request.symptoms,
                "matched_symptoms": matched_symptoms,
                "condition": condition,
                "confidence": confidence,
                "top_predictions": predictions,
                "fusion": {
                    "old_model_weight": 0.2,
                    "pretrained_model_weight": 0.8,
                },
                "rag_context": rag_context,
                "safety": safety,
                "health_response": health_response,
                "disclaimer": (
                    "This is an AI-based informational "
                    "screening-support result, not a medical diagnosis."
                ),
            }

    rule_result = analyze_rule_based_symptoms(
        matched_symptoms
    )

    health_response = build_health_response(
        request.symptoms,
        matched_symptoms,
        {},
        safety,
    )

    return {
        "status": rule_result["status"],
        "input": request.symptoms,
        "matched_symptoms": rule_result["matched_symptoms"],
        "possible_categories": rule_result["possible_categories"],
        "safety": safety,
        "health_response": health_response,
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
    request: MentalHealthRequest,
):

    try:

        result = calculate_mental_health_score(
            request.answers
        )

        return result

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# USER REGISTRATION
# ============================================================

@app.post("/register")
def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    email = request.email.strip().lower()

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="Email already registered.",
        )

    hashed_password = pwd_context.hash(
        request.password
    )

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
    db: Session = Depends(get_db),
):

    email = request.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not pwd_context.verify(
        request.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
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
