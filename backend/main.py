from typing import Optional

import joblib
import numpy as np

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from symptom_rules import (
    extract_symptoms,
    analyze_rule_based_symptoms,
)


# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(
    title="AYUSHMED AI",
    description=(
        "AI-powered symptom screening support API. "
        "This system does not provide medical diagnosis."
    ),
    version="1.0.0",
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Load ML Models
# ==========================================

MODEL_DIR = "model"

try:
    logistic_model = joblib.load(
        f"{MODEL_DIR}/logistic_model.pkl"
    )

    nb_model = joblib.load(
        f"{MODEL_DIR}/nb_model.pkl"
    )

    available_symptoms = joblib.load(
        f"{MODEL_DIR}/symptoms.pkl"
    )

    ensemble_info = joblib.load(
        f"{MODEL_DIR}/ensemble_info.pkl"
    )

    MODELS_LOADED = True

    print("ML models loaded successfully!")
    print("Symptoms loaded:", len(available_symptoms))

except Exception as e:
    MODELS_LOADED = False

    logistic_model = None
    nb_model = None
    available_symptoms = []
    ensemble_info = {}

    print("WARNING: ML models could not be loaded.")
    print("Error:", e)


# ==========================================
# Request Models
# ==========================================

class SymptomRequest(BaseModel):
    symptoms: str


class HealthRequest(BaseModel):
    symptoms: Optional[str] = ""


# ==========================================
# Root Endpoint
# ==========================================

@app.get("/")
def root():
    return {
        "message": "AYUSHMED AI Backend is running!",
        "ml_model_loaded": MODELS_LOADED,
    }


# ==========================================
# Health Check
# ==========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "ml_model_loaded": MODELS_LOADED,
        "symptom_features": len(available_symptoms),
    }


# ==========================================
# ML Prediction Function
# ==========================================

def predict_disease(matched_symptoms: list[str]):

    # Create empty feature vector
    feature_vector = np.zeros(
        len(available_symptoms),
        dtype=np.float32
    )

    # Set matched symptoms to 1
    symptom_index = {
        symptom: index
        for index, symptom in enumerate(available_symptoms)
    }

    for symptom in matched_symptoms:

        if symptom in symptom_index:
            index = symptom_index[symptom]
            feature_vector[index] = 1

    # Reshape for model
    X = feature_vector.reshape(1, -1)

    # Get probabilities from both models
    logistic_prob = logistic_model.predict_proba(X)[0]
    nb_prob = nb_model.predict_proba(X)[0]

    # Ensemble weights
    logistic_weight = ensemble_info.get(
        "logistic_weight",
        0.60
    )

    nb_weight = ensemble_info.get(
        "nb_weight",
        0.40
    )

    # Combine probabilities
    ensemble_prob = (
        logistic_weight * logistic_prob
        + nb_weight * nb_prob
    )

    # Top predictions
    top_indices = np.argsort(
        ensemble_prob
    )[::-1][:3]

    predictions = []

    for index in top_indices:

        disease = logistic_model.classes_[index]

        confidence = float(
            ensemble_prob[index] * 100
        )

        predictions.append(
            {
                "disease": str(disease),
                "confidence": round(
                    confidence,
                    2
                ),
            }
        )

    return predictions


# ==========================================
# ML Disease Prediction Endpoint
# ==========================================

@app.post("/predict-disease")
def predict_disease_endpoint(request: SymptomRequest):

    if not MODELS_LOADED:
        raise HTTPException(
            status_code=500,
            detail="ML models are not loaded."
        )

    if not request.symptoms.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms."
        )

    # Extract dataset symptoms
    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms
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
                "This system provides informational "
                "screening support and is not a medical diagnosis."
            ),
        }

    # Predict
    predictions = predict_disease(
        matched_symptoms
    )

    return {
        "status": "success",
        "input": request.symptoms,
        "matched_symptoms": matched_symptoms,
        "top_prediction": predictions[0],
        "top_predictions": predictions,
        "disclaimer": (
            "This is an AI-based informational "
            "screening-support result, not a medical diagnosis."
        ),
    }


# ==========================================
# Existing Symptom Analysis Endpoint
# ==========================================

@app.post("/analyze-symptoms")
def analyze_symptoms(request: SymptomRequest):

    if not request.symptoms.strip():
        raise HTTPException(
            status_code=400,
            detail="Please provide symptoms."
        )

    # Match symptoms
    matched_symptoms = extract_symptoms(
        request.symptoms,
        available_symptoms
    )

    # If ML models are available
    if MODELS_LOADED and matched_symptoms:

        predictions = predict_disease(
            matched_symptoms
        )

        return {
            "status": "success",
            "input": request.symptoms,
            "matched_symptoms": matched_symptoms,
            "condition": predictions[0]["disease"],
            "confidence": predictions[0]["confidence"],
            "top_predictions": predictions,
            "disclaimer": (
                "This is an AI-based informational "
                "screening-support result, not a medical diagnosis."
            ),
        }

    # Rule-based fallback
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