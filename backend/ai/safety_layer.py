import re
from typing import Dict, List


# High-priority symptoms/signs that should trigger urgent-care guidance.
RED_FLAG_PATTERNS = {
    "chest pain": [
        r"\bchest pain\b",
        r"\bseene mein dard\b",
        r"\bseene me dard\b",
        r"\bchest mein pain\b",
        r"\bchest me pain\b",
    ],
    "severe breathing difficulty": [
        r"\bsevere breathing\b",
        r"\bbreathing difficulty\b",
        r"\bbreathing problem\b",
        r"\bsaans lene mein dikkat\b",
        r"\bsaans lene me dikkat\b",
        r"\bsaans nahi aa\b",
        r"\bsaans nahin aa\b",
    ],
    "loss of consciousness": [
        r"\bunconscious\b",
        r"\bpassed out\b",
        r"\bbehosh\b",
        r"\bbehoshi\b",
    ],
    "severe confusion": [
        r"\bsevere confusion\b",
        r"\bconfused\b",
        r"\bbahut confusion\b",
        r"\bhadd se zyada confusion\b",
    ],
    "seizure": [
        r"\bseizure\b",
        r"\bfit aa\b",
        r"\bfits aa\b",
        r"\bdaura\b",
    ],
    "severe bleeding": [
        r"\bsevere bleeding\b",
        r"\bheavy bleeding\b",
        r"\bbahut zyada bleeding\b",
        r"\bzyada khoon\b",
        r"\bkhoon bahut nikal\b",
    ],
    "stroke warning signs": [
        r"\bface droop\b",
        r"\bface tedha\b",
        r"\bface ek taraf\b",
        r"\bspeech difficulty\b",
        r"\bbolne mein dikkat\b",
        r"\bbolne me dikkat\b",
        r"\bachanak haath pair kamzor\b",
        r"\bachanak weakness\b",
    ],
}


def normalize_text(text: str) -> str:
    """Normalize user text for simple red-flag matching."""
    if not isinstance(text, str):
        return ""

    text = text.lower()
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def detect_red_flags(user_text: str) -> List[str]:
    """
    Detect high-priority emergency warning signs.

    This is a safety screen, not a diagnosis.
    """
    text = normalize_text(user_text)

    detected = []

    for flag_name, patterns in RED_FLAG_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                detected.append(flag_name)
                break

    return detected


def build_safety_context(user_text: str) -> Dict:
    """
    Build structured safety information for the rest of the application.
    """

    detected_flags = detect_red_flags(user_text)

    if detected_flags:
        return {
            "is_emergency": True,
            "red_flags": detected_flags,
            "priority": "urgent",
            "message": (
                "Aapke message mein kuch warning signs detect hue hain. "
                "Agar symptoms severe hain, rapidly worsen ho rahe hain, "
                "ya aapko emergency feel ho rahi hai, to local emergency "
                "medical service ya nearest emergency department se "
                "turant help lein."
            ),
        }

    return {
        "is_emergency": False,
        "red_flags": [],
        "priority": "routine",
        "message": (
            "Koi high-priority emergency warning sign automatically "
            "detect nahi hua. Yeh emergency ko rule out nahi karta."
        ),
    }
