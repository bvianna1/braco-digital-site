#!/usr/bin/env python3
"""Minimal contact API for Braço Digital, using only Python's standard library."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from email.utils import parseaddr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    import fcntl
except ImportError:  # pragma: no cover - fcntl is unavailable on Windows
    fcntl = None

MAX_BODY_BYTES = 16_384
RATE_LIMIT_REQUESTS = 5
RATE_LIMIT_WINDOW_SECONDS = 600
RATE_LIMIT_STATE_FILE = "/var/lib/braco-digital-api/rate-limit.json"
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


def send_email(payload: dict, api_key: str) -> bool:
    """Envia o e-mail via Resend usando curl.

    O Resend bloqueia urllib.request/Python com Cloudflare 403 (error code
    1010), então a chamada é feita por curl via subprocess.
    """
    cmd = [
        "curl", "--silent", "--show-error", "--fail-with-body",
        "--max-time", "15",
        "https://api.resend.com/emails",
        "--request", "POST",
        "--header", f"Authorization: Bearer {api_key}",
        "--header", "Content-Type: application/json",
        "--data-binary", "@-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            check=False,
        )
        return proc.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


class RateLimiter:
    def __init__(self) -> None:
        self.state_file = os.environ.get("RATE_LIMIT_STATE_FILE", RATE_LIMIT_STATE_FILE)
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()
        self._state_dirty = False
        with self.lock, self._file_lock():
            self._load_state(time.time())

    @contextmanager
    def _file_lock(self):
        """1 réplica Dokploy; lock de arquivo protege contra processos concorrentes."""
        lock_file = None
        try:
            if fcntl is not None:
                lock_file = open(f"{self.state_file}.lock", "a+", encoding="utf-8")
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        except OSError:
            print("contact_api rate_limit_lock_error", flush=True)
        try:
            yield
        finally:
            if lock_file is not None:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                finally:
                    lock_file.close()

    def _load_state(self, now: float) -> None:
        try:
            with open(self.state_file, encoding="utf-8") as state_file:
                state = json.load(state_file)
            clients = state["clients"]
            if not isinstance(clients, dict):
                raise ValueError("invalid clients")
            loaded: dict[str, deque[float]] = defaultdict(deque)
            cutoff = now - RATE_LIMIT_WINDOW_SECONDS
            for client, timestamps in clients.items():
                if not isinstance(client, str) or not isinstance(timestamps, list):
                    raise ValueError("invalid bucket")
                loaded[client].extend(sorted(
                    timestamp for timestamp in timestamps
                    if isinstance(timestamp, (int, float))
                    and not isinstance(timestamp, bool)
                    and cutoff < timestamp <= now
                ))
            self.requests = loaded
        except FileNotFoundError:
            print("contact_api rate_limit_state_missing", flush=True)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            self.requests = defaultdict(deque)
            print("contact_api rate_limit_state_invalid", flush=True)

    def _save_state(self, now: float) -> bool:
        directory = os.path.dirname(self.state_file) or "."
        temporary_path = None
        state = {
            "clients": {client: list(bucket) for client, bucket in self.requests.items() if bucket},
            "saved_at": now,
        }
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=directory, delete=False
            ) as temporary:
                temporary_path = temporary.name
                json.dump(state, temporary, separators=(",", ":"))
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, self.state_file)
            return True
        except OSError:
            print("contact_api rate_limit_state_write_error", flush=True)
            return False
        finally:
            if temporary_path and os.path.exists(temporary_path):
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass

    def allow(self, client: str) -> bool:
        now = time.time()
        with self.lock, self._file_lock():
            if not self._state_dirty:
                self._load_state(now)
            bucket = self.requests[client]
            while bucket and bucket[0] <= now - RATE_LIMIT_WINDOW_SECONDS:
                bucket.popleft()
            if len(bucket) >= RATE_LIMIT_REQUESTS:
                return False
            bucket.append(now)
            self._state_dirty = not self._save_state(now)
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
        # curl via subprocess: o Resend bloqueia urllib.request/Python com
        # Cloudflare 403 (error code 1010). Usar curl mantém a entrega estável.
        payload = email_payload(data, to_email, from_email)
        if not send_email(payload, api_key):
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
