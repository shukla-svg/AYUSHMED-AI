from fastapi import FastAPI
from pydantic import BaseModel

from symptom_rules import CONDITION_RULES


# ==========================================
# AYUSHMED AI - FastAPI Application
# ==========================================

app = FastAPI(
    title="AYUSHMED AI API",
    description="Backend API for AYUSHMED AI",
    version="1.0.0"
)


# ==========================================
# Request Model
# ==========================================

class SymptomRequest(BaseModel):
    symptoms: str


# ==========================================
# Home API
# ==========================================

@app.get("/")
def home():
    return {
        "message": "AYUSHMED AI Backend is running!"
    }


# ==========================================
# Health Check API
# ==========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# ==========================================
# Symptom Processing
# ==========================================

def analyze_symptom_text(symptoms: str):

    symptoms = symptoms.lower()

    detected = []

    if "fever" in symptoms:
        detected.append("fever")

    if "headache" in symptoms:
        detected.append("headache")

    if "cough" in symptoms:
        detected.append("cough")

    if "cold" in symptoms:
        detected.append("cold")

    if "weakness" in symptoms:
        detected.append("weakness")

    if "sore throat" in symptoms:
        detected.append("sore throat")

    if "body pain" in symptoms:
        detected.append("body pain")

    return detected


# ==========================================
# Score Based Condition Matching
# ==========================================

def calculate_condition_scores(detected_symptoms):

    results = []

    for condition, data in CONDITION_RULES.items():

        required_symptoms = data["symptoms"]

        matched_symptoms = [
            symptom
            for symptom in required_symptoms
            if symptom in detected_symptoms
        ]

        total_symptoms = len(required_symptoms)
        matched_count = len(matched_symptoms)

        score = (matched_count / total_symptoms) * 100

        results.append({
            "condition": condition,
            "matched_symptoms": matched_symptoms,
            "score": round(score, 2)
        })

    results.sort(
        key=lambda result: result["score"],
        reverse=True
    )

    return results


# ==========================================
# Symptom Analyzer API
# ==========================================

@app.post("/analyze-symptoms")
def analyze_symptoms(request: SymptomRequest):

    detected_symptoms = analyze_symptom_text(
        request.symptoms
    )

    condition_results = calculate_condition_scores(
        detected_symptoms
    )

    return {
        "input": request.symptoms,
        "detected_symptoms": detected_symptoms,
        "condition_results": condition_results,
        "disclaimer": (
            "This is an informational assessment, "
            "not a medical diagnosis."
        ),
        "status": "success"
    }