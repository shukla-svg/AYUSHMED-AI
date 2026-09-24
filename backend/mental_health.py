def calculate_mental_health_score(answers: list[int]) -> dict:
    """
    Simple screening-support questionnaire.
    Answers should be scored from 0 to 3.
    """

    if len(answers) != 10:
        raise ValueError("Exactly 10 answers are required.")

    if any(answer < 0 or answer > 3 for answer in answers):
        raise ValueError("Each answer must be between 0 and 3.")

    total_score = sum(answers)

    if total_score <= 7:
        level = "Low"
    elif total_score <= 14:
        level = "Moderate"
    elif total_score <= 21:
        level = "High"
    else:
        level = "Very High"

    return {
        "status": "success",
        "score": total_score,
        "maximum_score": 30,
        "risk_level": level,
        "message": (
            "This result is a screening-support assessment "
            "and is not a medical diagnosis."
        )
    }


MENTAL_HEALTH_QUESTIONS = [
    "How often have you felt nervous, anxious, or on edge?",
    "How often have you had little interest or pleasure in doing things?",
    "How often have you felt down, depressed, or hopeless?",
    "How often have you had trouble sleeping?",
    "How often have you felt tired or had low energy?",
    "How often have you had difficulty concentrating?",
    "How often have you felt overwhelmed by daily activities?",
    "How often have you felt socially withdrawn or isolated?",
    "How often have you felt unable to relax?",
    "How often have you felt that your daily activities are becoming difficult?"
]


def get_mental_health_questions() -> list[str]:
    return MENTAL_HEALTH_QUESTIONS