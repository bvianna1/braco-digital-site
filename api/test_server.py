import json
import unittest
from unittest.mock import patch

import server


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

    def test_resend_request_shape_without_network(self):
        data, _ = server.validate(self.valid_payload())
        message = server.email_payload(data, "lead@example.com", "Site <site@example.com>")
        request = server.urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(message).encode(),
            headers={"Authorization": "Bearer test", "Content-Type": "application/json"},
            method="POST",
        )
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertNotIn("Bruno", str(request.headers))

    @patch("server.urllib.request.urlopen")
    def test_resend_https_delivery_is_mocked(self, urlopen):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *_args): return None
            def read(self): return b'{"id":"mock"}'

        urlopen.return_value = Response()
        data, _ = server.validate(self.valid_payload())
        request = server.urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(server.email_payload(data, "lead@example.com", "Site <site@example.com>")).encode(),
            headers={"Authorization": "Bearer test", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            self.assertEqual(response.status, 200)
        sent_request = urlopen.call_args.args[0]
        self.assertEqual(sent_request.get_method(), "POST")
        self.assertEqual(sent_request.full_url, "https://api.resend.com/emails")


if __name__ == "__main__":
    unittest.main()
