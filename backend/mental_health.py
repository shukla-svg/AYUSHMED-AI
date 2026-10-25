def calculate_mental_health_score(answers: list[int]) -> dict:
    """
    Simple screening-support questionnaire.
    Answers should be scored from 0 to 3.
    """

    if not isinstance(answers, list) or len(answers) != 10:
        raise ValueError("Exactly 10 answers are required.")

    if any(
        not isinstance(answer, int)
        or isinstance(answer, bool)
        or answer < 0
        or answer > 3
        for answer in answers
    ):
        raise ValueError("Each answer must be an integer between 0 and 3.")

    total_score = sum(answers)
    needs_urgent_support = answers[-1] > 0

    if needs_urgent_support:
        level = "Urgent support recommended"
    elif total_score <= 7:
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
        "requires_urgent_support": needs_urgent_support,
        "message": (
            "Your responses indicate that immediate support may be needed. "
            "If you may harm yourself or are in immediate danger, contact local "
            "emergency services, a crisis helpline, or a trusted person now."
            if needs_urgent_support
            else "This result is a screening-support assessment and is not a medical diagnosis."
        ),
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
    "How often have you had thoughts that you would be better off dead or of hurting yourself?"
]


def get_mental_health_questions() -> list[str]:
    return MENTAL_HEALTH_QUESTIONS
