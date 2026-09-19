import re


def normalize_text(text: str) -> str:
    """
    Normalize symptom text for matching.
    """
    text = str(text).lower().strip()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_symptom(symptom: str) -> str:
    """
    Normalize a dataset symptom name.
    """
    return normalize_text(symptom)


def extract_symptoms(user_text: str, available_symptoms: list[str]) -> list[str]:
    """
    Match symptoms written by the user against the
    symptom names available in the dataset.
    """

    normalized_input = normalize_text(user_text)

    matched = []

    # Longest symptoms first
    sorted_symptoms = sorted(
        available_symptoms,
        key=lambda x: len(normalize_symptom(x)),
        reverse=True
    )

    for symptom in sorted_symptoms:
        normalized_symptom = normalize_symptom(symptom)

        if not normalized_symptom:
            continue

        # Exact phrase match inside user input
        if normalized_symptom in normalized_input:
            matched.append(symptom)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(matched))


def analyze_rule_based_symptoms(symptoms: list[str]) -> dict:
    """
    Simple rule-based fallback.
    This is NOT a medical diagnosis.
    """

    normalized = [normalize_symptom(s) for s in symptoms]

    conditions = []

    # Respiratory-related symptoms
    respiratory = {
        "cough",
        "breathing difficulty",
        "shortness of breath",
        "chest pain",
        "sore throat",
    }

    # Fever/infection-related symptoms
    infection = {
        "fever",
        "high fever",
        "chills",
        "fatigue",
    }

    # Head-related symptoms
    headache_group = {
        "headache",
        "dizziness",
        "nausea",
    }

    if any(symptom in normalized for symptom in respiratory):
        conditions.append("Respiratory symptoms")

    if any(symptom in normalized for symptom in infection):
        conditions.append("Possible infection-related symptoms")

    if any(symptom in normalized for symptom in headache_group):
        conditions.append("Headache-related symptoms")

    return {
        "matched_symptoms": symptoms,
        "possible_categories": conditions,
        "status": "success",
        "disclaimer": (
            "This is an informational screening-support result "
            "and not a medical diagnosis."
        ),
    }