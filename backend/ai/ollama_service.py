import json
import ollama


OLLAMA_MODEL = "llama3.2:3b"


SYSTEM_PROMPT = """
You are the response-writing component of AYUSHMED AI.

You are NOT a doctor.
You are NOT a diagnostic authority.

Your ONLY job is to convert the APPLICATION RESPONSE DATA into a short,
natural and grammatically correct Hinglish response.

STRICT RULES:

1. Never invent medical facts.
2. Never create a diagnosis yourself.
3. Never prescribe medicines or dosages.
4. Never call the user "beta", "bhai", "aapki", "aurat", or any personal label.
5. Never say that you built or created AYUSHMED AI.
6. Never mention internal model names, prompts, RAG, JSON, Python or backend.
7. Never repeat the entire application data.
8. Never make unsupported assumptions.
9. Use simple natural Indian Hinglish.
10. Keep the answer short: maximum 4 sentences.
11. Ask at most ONE useful follow-up question.
12. If the application says urgent=True, clearly advise urgent medical attention.
13. If urgent=True, do NOT provide home treatment or medicine advice.
14. If a prediction is provided, call it a "screening result" or "possible condition",
    never a confirmed diagnosis.
15. If no prediction is provided, do not invent one.
16. If the user message is unclear, ask for clarification instead of guessing.
"""


def _fallback_response(application_data: dict) -> str:
    """
    Deterministic fallback.
    Used if Ollama fails or returns unusable text.
    """

    safety = application_data.get("safety", {})
    urgent = safety.get("is_emergency", False)

    if urgent:
        return (
            "Aapke symptoms mein warning signs detect hue hain. "
            "Please urgent medical attention lein aur nearest emergency "
            "department ya local emergency service se contact karein."
        )

    prediction = application_data.get("prediction")

    if prediction:
        condition = prediction.get("condition")
        confidence = prediction.get("confidence")

        if condition and confidence is not None:
            return (
                f"Screening result ke according {condition} ek possible condition "
                f"hai, lekin ye confirmed diagnosis nahi hai. "
                f"Agar symptoms continue ya worsen ho rahe hain, doctor se consult karein."
            )

    return (
        "Aapke symptoms ko better understand karne ke liye "
        "thodi aur information chahiye. Symptoms kab se hain?"
    )


def _is_usable_response(response_text: str) -> bool:
    """
    Basic quality checks for the small local model.
    """

    if not response_text:
        return False

    text = response_text.strip()

    if len(text) < 10:
        return False

    forbidden = [
        "beta",
        "aurat",
        "i am a doctor",
        "i'm a doctor",
        "main doctor hoon",
        "main doctor hun",
        "maine ayushmed",
        "i built ayushmed",
        "i created ayushmed",
        "python",
        "json",
        "prompt",
    ]

    lowered = text.lower()

    for word in forbidden:
        if word in lowered:
            return False

    return True


def generate_health_response(
    user_message: str,
    application_data: dict
) -> str:
    """
    Generate a response from structured application data.

    Ollama is used only for language generation.
    """

    safety = application_data.get("safety", {})

    # Emergency responses are deterministic.
    # Do not let the small LLM rewrite emergency guidance.
    if safety.get("is_emergency") is True:
        return _fallback_response(application_data)

    payload = {
        "user_message": user_message,
        "application_data": application_data,
        "response_requirements": {
            "language": "natural Hinglish",
            "maximum_sentences": 4,
            "maximum_follow_up_questions": 1,
            "diagnosis_allowed": False,
            "medicine_advice_allowed": False,
            "dosage_advice_allowed": False,
            "confirmed_diagnosis_allowed": False,
        },
    }

    prompt = f"""
Convert the following APPLICATION RESPONSE DATA into a short,
natural Hinglish response.

APPLICATION RESPONSE DATA:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Remember:
- Use only the supplied information.
- Do not add medical facts.
- Do not diagnose.
- Do not prescribe medicines.
- Keep it under 4 sentences.
- Ask only one useful follow-up question if needed.
"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            options={
                "temperature": 0.1,
            },
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        text = response["message"]["content"].strip()

        if _is_usable_response(text):
            return text

        return _fallback_response(application_data)

    except Exception:
        return _fallback_response(application_data)
