import json
import os
import tempfile
import unittest
from unittest.mock import patch

import server


class RateLimiterTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.state_file = os.path.join(self._tmp.name, "rate-limit.json")
        self.environment = patch.dict(
            os.environ, {"RATE_LIMIT_STATE_FILE": self.state_file}
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_rate_limit_blocks_after_limit(self):
        rl = server.RateLimiter()
        for _ in range(5):
            self.assertTrue(rl.allow("client"))
        self.assertFalse(rl.allow("client"))

    def test_rate_limit_releases_after_window(self):
        with patch("server.time.time", return_value=1_000.0):
            rl = server.RateLimiter()
            for _ in range(5):
                self.assertTrue(rl.allow("client"))
            self.assertFalse(rl.allow("client"))
        with patch("server.time.time", return_value=1_601.0):
            self.assertTrue(rl.allow("client"))

    def test_rate_limit_persists_state_to_file(self):
        rl = server.RateLimiter()
        self.assertTrue(rl.allow("client"))
        with open(self.state_file, encoding="utf-8") as state_file:
            state = json.load(state_file)
        self.assertIn("client", state["clients"])

    def test_rate_limit_reloads_state_from_file(self):
        state = {"clients": {"client": [999.0] * 4}, "saved_at": 999.0}
        with open(self.state_file, "w", encoding="utf-8") as state_file:
            json.dump(state, state_file)
        with patch("server.time.time", return_value=1_000.0):
            rl = server.RateLimiter()
            self.assertTrue(rl.allow("client"))
            self.assertFalse(rl.allow("client"))


class ContactApiTests(unittest.TestCase):
    def valid_payload(self):
        return {
            "nome": "Bruno",
            "empresa": "Empresa teste",
            "email": "bruno@example.com",
            "telefone": "",
            "processo": "Conferir pagamentos toda semana",
            "comoFunciona": "Planilha e sistema",
            "website": "",
            "consentimento": "on",
            "calculadora": {"pessoas": 2, "custoMensal": 4000, "horasSemana": 5},
        }

    def test_validation_recalculates_results_server_side(self):
        data, error = server.validate(self.valid_payload())
        self.assertIsNone(error)
        self.assertEqual(data["calculadora"]["horasAno"], 480)
        self.assertEqual(data["calculadora"]["custoAno"], 12000)

    def test_honeypot_is_rejected(self):
        payload = self.valid_payload()
        payload["website"] = "spam.example"
        data, error = server.validate(payload)
        self.assertIsNone(data)
        self.assertEqual(error, "Solicitação inválida.")

    def test_missing_consent_is_rejected(self):
        payload = self.valid_payload()
        payload.pop("consentimento")
        self.assertIsNotNone(server.validate(payload)[1])

    def test_email_payload_uses_reply_to(self):
        data, _ = server.validate(self.valid_payload())
        message = server.email_payload(data, "lead@example.com", "Site <site@example.com>")
        self.assertEqual(message["reply_to"], "bruno@example.com")
        self.assertEqual(message["to"], ["lead@example.com"])

    def test_single_line_fields_are_sanitized(self):
        payload = self.valid_payload()
        payload["empresa"] = "Empresa\nAssunto injetado"
        data, error = server.validate(payload)
        self.assertIsNone(error)
        self.assertEqual(data["empresa"], "Empresa Assunto injetado")

    @patch("server.subprocess.run")
    def test_resend_request_shape_without_network(self, run):
        data, _ = server.validate(self.valid_payload())
        message = server.email_payload(data, "lead@example.com", "Site <site@example.com>")
        run.return_value.returncode = 0
        ok = server.send_email(message, "test")
        self.assertTrue(ok)
        cmd = run.call_args.args[0]
        self.assertIn("https://api.resend.com/emails", cmd)
        self.assertIn("--header", cmd)
        self.assertIn("Authorization: Bearer test", cmd)
        sent = run.call_args.kwargs["input"]
        self.assertIn(b"lead@example.com", sent)
        # o nome do lead não deve vazar no header de autorização
        auth_header = next(a for a in cmd if a.startswith("Authorization:"))
        self.assertNotIn("Bruno", auth_header)

    @patch("server.subprocess.run")
    def test_resend_https_delivery_is_mocked(self, run):
        run.return_value.returncode = 0
        data, _ = server.validate(self.valid_payload())
        message = server.email_payload(data, "lead@example.com", "Site <site@example.com>")
        ok = server.send_email(message, "test")
        self.assertTrue(ok)
        self.assertEqual(run.call_count, 1)
        sent = run.call_args.kwargs["input"]
        self.assertEqual(json.loads(sent)["to"], ["lead@example.com"])
        self.assertFalse(run.call_args.kwargs["check"])

    @patch("server.subprocess.run")
    def test_resend_delivery_failure_returns_false(self, run):
        run.return_value.returncode = 22  # curl error code for HTTP >= 400
        data, _ = server.validate(self.valid_payload())
        message = server.email_payload(data, "lead@example.com", "Site <site@example.com>")
        self.assertFalse(server.send_email(message, "test"))


if __name__ == "__main__":
    unittest.main()
