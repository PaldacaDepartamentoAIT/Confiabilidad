from django.test import Client

ALLOWED_ORIGIN = "tauri://localhost"
DISALLOWED_ORIGIN = "https://evil.example.com"
HEALTH = "/api/health/"


def test_cors_allows_tauri_origin() -> None:
    resp = Client().get(HEALTH, headers={"Origin": ALLOWED_ORIGIN})

    assert resp.headers["Access-Control-Allow-Origin"] == ALLOWED_ORIGIN
    assert resp.headers["Access-Control-Allow-Credentials"] == "true"


def test_cors_rejects_unknown_origin() -> None:
    resp = Client().get(HEALTH, headers={"Origin": DISALLOWED_ORIGIN})

    assert not resp.has_header("Access-Control-Allow-Origin")
