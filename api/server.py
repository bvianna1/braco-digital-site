#!/usr/bin/env python3
"""Minimal contact API for Braço Digital, using only Python's standard library."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict, deque
from email.utils import parseaddr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_BODY_BYTES = 16_384
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 600
FIELD_LIMITS = {
    "nome": 100,
    "empresa": 120,
    "email": 254,
    "telefone": 30,
    "processo": 2000,
    "comoFunciona": 3000,
    "website": 200,
}
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def clean_text(value: object, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return CONTROL_CHARS.sub("", value).strip()[:limit]


def number(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    try:
        parsed = float(value)
        return parsed if 0 <= parsed < 1_000_000_000 else 0.0
    except (TypeError, ValueError):
        return 0.0


def validate(payload: object) -> tuple[dict | None, str | None]:
    if not isinstance(payload, dict):
        return None, "JSON inválido."
    data = {key: clean_text(payload.get(key), limit) for key, limit in FIELD_LIMITS.items()}
    for key in ("nome", "empresa", "email", "telefone"):
        data[key] = " ".join(data[key].splitlines()).strip()
    if data["website"]:
        return None, "Solicitação inválida."
    if not data["nome"] or not data["empresa"] or len(data["processo"]) < 10:
        return None, "Preencha os campos obrigatórios."
    if not EMAIL_PATTERN.fullmatch(data["email"]) or parseaddr(data["email"])[1] != data["email"]:
        return None, "Informe um e-mail válido."
    if payload.get("consentimento") not in ("on", True, "true"):
        return None, "O consentimento é obrigatório."
    raw_calc = payload.get("calculadora") if isinstance(payload.get("calculadora"), dict) else {}
    values = {key: number(raw_calc.get(key)) for key in ("pessoas", "custoMensal", "horasSemana")}
    hours_year = values["pessoas"] * values["horasSemana"] * 48
    hourly_cost = values["custoMensal"] / 160
    data["calculadora"] = {
        **values,
        "horasAno": hours_year,
        "custoHora": hourly_cost,
        "custoAno": hours_year * hourly_cost,
    }
    data.pop("website", None)
    return data, None


def email_payload(data: dict, to_email: str, from_email: str) -> dict:
    calc = data["calculadora"]
    body = (
        "Novo pedido de diagnóstico — Braço Digital\n\n"
        f"Nome: {data['nome']}\nEmpresa: {data['empresa']}\n"
        f"E-mail: {data['email']}\nTelefone: {data['telefone'] or 'Não informado'}\n\n"
        f"Tarefa ou processo:\n{data['processo']}\n\n"
        f"Como funciona hoje:\n{data['comoFunciona'] or 'Não informado'}\n\n"
        "Calculadora:\n"
        f"Pessoas: {calc['pessoas']:g}\nCusto mensal por pessoa: R$ {calc['custoMensal']:.2f}\n"
        f"Horas por semana por pessoa: {calc['horasSemana']:g}\n"
        f"Horas por ano: {calc['horasAno']:.2f}\nCusto anual estimado: R$ {calc['custoAno']:.2f}\n"
    )
    return {
        "from": from_email,
        "to": [to_email],
        "reply_to": data["email"],
        "subject": f"Diagnóstico de processo — {data['empresa']}",
        "text": body,
    }


class RateLimiter:
    def __init__(self) -> None:
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, client: str) -> bool:
        now = time.monotonic()
        with self.lock:
            bucket = self.requests[client]
            while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW_SECONDS:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT_REQUESTS:
                return False
            bucket.append(now)
            return True


RATE_LIMITER = RateLimiter()


class Handler(BaseHTTPRequestHandler):
    server_version = "BracoDigitalAPI/1.0"
    sys_version = ""

    def log_message(self, _format: str, *_args: object) -> None:
        # Deliberately omit paths, IPs and form data: only operational status is logged.
        print("contact_api request_processed", flush=True)

    @property
    def allowed_origins(self) -> set[str]:
        configured = os.environ.get(
            "CONTACT_FORM_ALLOWED_ORIGINS",
            "https://bracodigital.com.br,https://www.bracodigital.com.br",
        )
        return {item.strip().rstrip("/") for item in configured.split(",") if item.strip()}

    def send_json(self, status: int, payload: dict, origin: str | None = None) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if origin and origin in self.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"error": "Não encontrado."})

    def do_OPTIONS(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "").rstrip("/")
        if self.path != "/diagnostico" or origin not in self.allowed_origins:
            self.send_json(403, {"error": "Origem não permitida."})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin", "").rstrip("/")
        if self.path != "/diagnostico":
            self.send_json(404, {"error": "Não encontrado."}, origin)
            return
        if origin not in self.allowed_origins:
            self.send_json(403, {"error": "Origem não permitida."})
            return
        if not RATE_LIMITER.allow(self.client_address[0]):
            self.send_json(429, {"error": "Muitas tentativas. Aguarde alguns minutos."}, origin)
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Use application/json."}, origin)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY_BYTES:
            self.send_json(413, {"error": "Solicitação muito grande."}, origin)
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "JSON inválido."}, origin)
            return
        data, error = validate(payload)
        if error or data is None:
            self.send_json(400, {"error": error}, origin)
            return
        api_key = os.environ.get("RESEND_API_KEY", "")
        to_email = os.environ.get("CONTACT_FORM_TO_EMAIL", "")
        from_email = os.environ.get("CONTACT_FORM_FROM_EMAIL", "")
        if not api_key or not to_email or not from_email:
            print("contact_api configuration_error", flush=True)
            self.send_json(503, {"error": "Serviço temporariamente indisponível."}, origin)
            return
        request = urllib.request.Request(
            "https://api.resend.com/emails",
            data=json.dumps(email_payload(data, to_email, from_email)).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status not in (200, 201):
                    raise RuntimeError("Unexpected Resend response")
                response.read()
        except (urllib.error.URLError, TimeoutError, RuntimeError):
            print("contact_api delivery_error", flush=True)
            self.send_json(502, {"error": "Não foi possível enviar agora. Tente novamente."}, origin)
            return
        self.send_json(200, {"ok": True}, origin)


def main() -> None:
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    print(f"contact_api listening port={port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
