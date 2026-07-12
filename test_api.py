import unittest
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

class TestDecisionDNAAPI(unittest.TestCase):
    def test_health(self):
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ask_empty_question(self):
        response = client.post("/ask", json={"question": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Question cannot be empty", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
