import json
import os
import re

try:
    import ollama
except ImportError:  # Keep the API usable when optional local Ollama is absent.
    ollama = None

OLLAMA_MODEL = "llama3.2:3b"
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_TIMEOUT_SECONDS = 15.0


SYSTEM_PROMPT = """
You are the response-writing component of AYUSHMED AI.

You are NOT a doctor.
You are NOT a diagnostic authority.

Your ONLY job is to convert structured application data into a short,
natural and grammatically correct Hinglish response.

STRICT RULES:

1. Never invent medical facts.
2. Never create or change a diagnosis yourself.
3. Never prescribe medicines or dosages.
4. Never treat a screening result as a confirmed diagnosis.
5. Never call the user "beta", "bhai", "aurat", or any personal label.
6. Never say that you built or created AYUSHMED AI.
7. Never mention internal model names, prompts, RAG, JSON, Python or backend.
8. Never repeat the entire application data.
9. Use the supplied reference context only for explanation.
10. Do not add information that is not supported by the supplied data.
11. Use simple natural Indian Hinglish.
12. Keep the answer short: maximum 4 sentences.
13. Ask at most ONE useful follow-up question.
14. If urgent=True, clearly advise urgent medical attention.
15. If urgent=True, do NOT provide home treatment or medicine advice.
16. If a prediction is provided, call it a "screening result" or "possible condition".
17. If no prediction is provided, do not invent one.
18. If the user message is unclear, ask for clarification instead of guessing.
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
            try:
                confidence_text = f"{float(confidence):.1f}%"
            except (TypeError, ValueError):
                confidence_text = "an available confidence score"

            return (
                f"Screening result ke according {condition} ki possibility "
                f"sabse zyada aayi hai ({confidence_text}). "
                "Ye confirmed diagnosis nahi hai. "
                "Agar symptoms continue ya worsen ho rahe hain, doctor se consult karein."
            )

    rag_context = application_data.get("rag_context", [])

    if rag_context:
        first = rag_context[0]

        summary = first.get("summary")

        if isinstance(summary, str) and summary.strip():
            return (
                f"Available health reference ke according, {summary.strip()} "
                "Ye information diagnosis confirm nahi karti."
            )

    return (
        "Aapke symptoms ko better understand karne ke liye "
        "thodi aur information chahiye."
    )


def _is_usable_response(response_text: str) -> bool:
    """
    Basic quality and safety checks for the local model.
    """

    if not response_text:
        return False

    text = response_text.strip()

    if len(text) < 10:
        return False

    lowered = text.lower()

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
        "dosage",
        "mg per day",
        "take 2 tablets",
        "take 1 tablet",
    ]

    for word in forbidden:
        if word in lowered:
            return False

    # Do not allow the LLM to claim certainty.
    certainty_phrases = [
        "you definitely have",
        "you have",
        "aapko pakka",
        "aapko definitely",
        "confirmed diagnosis",
        "yeh pakka",
    ]

    for phrase in certainty_phrases:
        if phrase in lowered:
            return False

    # Reject responses that turn screening into a confirmed diagnosis.
    unsafe_patterns = [
        "aapko .* hai",
        "aapko .* hoga",
        "you have ",
        "you definitely have",
        "confirmed diagnosis",
    ]

    for pattern in unsafe_patterns:
        if re.search(pattern, lowered):
            return False

    # The language model is never allowed to provide drug, dosage, or treatment
    # instructions. Fall back to deterministic wording if it tries to do so.
    medicine_patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|g)\b",
        r"\b(?:tablet|capsule|antibiotic|painkiller|paracetamol|ibuprofen|aspirin)\b",
        r"\b(?:take|start|stop|use|consume)\s+(?:a |an |the )?(?:medicine|medication|tablet|capsule)\b",
        r"\b(?:dawai|dava)\s+(?:le|lo|lijiye|khaye)\b",
    ]

    if any(re.search(pattern, lowered) for pattern in medicine_patterns):
        return False

    # Keep the response concise.
    sentence_count = sum(
        text.count(mark)
        for mark in [".", "?", "!", "।"]
    )

    if sentence_count > 4:
        return False

    return True


def _prepare_rag_context(rag_context: list) -> list:
    """
    Keep only useful fields from retrieved local knowledge.
    Scores/keywords are not sent to the user-facing language model.
    """

    cleaned = []

    for item in rag_context[:3]:
        cleaned.append(
            {
                "condition": item.get("condition"),
                "summary": item.get("summary"),
                "self_care": item.get("self_care"),
                "seek_care": item.get("seek_care"),
                "red_flags": item.get("red_flags", []),
                "source": item.get("source"),
            }
        )

    return cleaned


def generate_health_response(
    user_message: str,
    application_data: dict
) -> str:
    """
    Generate a natural-language response from structured application data.

    Safety and disease prediction remain outside Ollama.
    Ollama is only used for response wording.
    """

    safety = application_data.get("safety", {})

    # --------------------------------------------------------
    # EMERGENCY BYPASS
    # --------------------------------------------------------

    if safety.get("is_emergency") is True:
        return _fallback_response(application_data)

    # --------------------------------------------------------
    # PREPARE RAG CONTEXT
    # --------------------------------------------------------

    rag_context = _prepare_rag_context(
        application_data.get("rag_context", [])
    )

    prediction = application_data.get("prediction")

    safe_application_data = {
        "prediction": prediction,
        "matched_symptoms": application_data.get(
            "matched_symptoms",
            []
        ),
        "safety": {
            "is_emergency": False,
            "priority": safety.get("priority", "routine"),
        },
        "rag_context": rag_context,
    }

    payload = {
        "user_message": user_message,
        "application_data": safe_application_data,
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

IMPORTANT:

- Use only the supplied information.
- The prediction comes from a screening model.
- Do not change the prediction.
- Do not diagnose the user.
- RAG context is supporting reference information only.
- Do not mention RAG or internal system details.
- Do not prescribe medicines.
- Do not provide dosages.
- Do not invent medical facts.
- Keep the response under 4 sentences.
- Ask at most one useful follow-up question if necessary.
"""

    if ollama is None:
        return _fallback_response(application_data)

    try:
        client = ollama.Client(
            host=OLLAMA_HOST,
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response = client.chat(
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

