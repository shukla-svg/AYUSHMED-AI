import unittest

from ai.ollama_service import _fallback_response, _is_usable_response
from ai.rag.retriever import retrieve_knowledge
from ai.safety_layer import build_safety_context
from mental_health import calculate_mental_health_score


class SafetyAndServiceTests(unittest.TestCase):
    def test_hinglish_breathing_red_flag_is_urgent(self):
        safety = build_safety_context("Mujhe saans lene mein bahut dikkat ho rahi hai")

        self.assertTrue(safety["is_emergency"])
        self.assertIn("severe breathing difficulty", safety["red_flags"])

    def test_self_harm_message_is_urgent(self):
        safety = build_safety_context("I want to hurt myself")

        self.assertTrue(safety["is_emergency"])
        self.assertIn("self-harm or suicide risk", safety["red_flags"])

    def test_rag_returns_relevant_local_reference(self):
        results = retrieve_knowledge("I have a cough and sore throat")

        self.assertTrue(results)
        self.assertIn(results[0]["condition"], {"Common Cold", "Cough", "Sore Throat"})

    def test_unsafe_model_medication_response_is_rejected(self):
        self.assertFalse(_is_usable_response("Take paracetamol 500 mg twice a day."))

    def test_fallback_does_not_treat_screening_as_diagnosis(self):
        response = _fallback_response(
            {
                "prediction": {"condition": "Flu", "confidence": "not-a-number"},
                "safety": {"is_emergency": False},
            }
        )

        self.assertIn("confirmed diagnosis nahi hai", response)

    def test_mental_health_self_harm_answer_requests_urgent_support(self):
        result = calculate_mental_health_score([0] * 9 + [1])

        self.assertTrue(result["requires_urgent_support"])
        self.assertEqual(result["risk_level"], "Urgent support recommended")

    def test_mental_health_rejects_boolean_answers(self):
        with self.assertRaises(ValueError):
            calculate_mental_health_score([0] * 9 + [True])


if __name__ == "__main__":
    unittest.main()
