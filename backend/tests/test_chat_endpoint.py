import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import main


class ChatEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_chat_accepts_message_without_history(self):
        with (
            patch.object(main, "FUSION_LOADED", False),
            patch.object(main, "retrieve_knowledge", return_value=[]),
            patch.object(main, "generate_health_response", return_value="Please share duration too."),
        ):
            response = self.client.post("/chat", json={"message": "Mujhe bukhar hai"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertEqual(response.json()["message"], "Please share duration too.")

    def test_assistant_history_cannot_trigger_an_emergency(self):
        with (
            patch.object(main, "FUSION_LOADED", False),
            patch.object(main, "retrieve_knowledge", return_value=[]),
            patch.object(main, "generate_health_response", return_value="Please share duration too."),
        ):
            response = self.client.post(
                "/chat",
                json={
                    "message": "Mujhe halka bukhar hai",
                    "history": [
                        {"role": "assistant", "text": "Do you have chest pain?"},
                    ],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["safety"]["is_emergency"])

    def test_current_emergency_message_bypasses_rag_and_ollama(self):
        with (
            patch.object(main, "retrieve_knowledge", side_effect=AssertionError("RAG must not run")),
            patch.object(main, "generate_health_response", side_effect=AssertionError("Ollama must not run")),
        ):
            response = self.client.post("/chat", json={"message": "I have chest pain"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "urgent")
        self.assertTrue(response.json()["should_stop"])

    def test_invalid_history_role_is_rejected(self):
        response = self.client.post(
            "/chat",
            json={
                "message": "Mujhe cough hai",
                "history": [{"role": "ai", "text": "How long?"}],
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
