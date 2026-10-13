import ast
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[3]
SINGLE_POINT = "apps/core/fingerprints.py"
FORBIDDEN_MODULES = (
    "hashlib",
    "hmac",
    "_hashlib",
    "_sha1",
    "_sha2",
    "_sha256",
    "_sha512",
    "_sha3",
    "_md5",
    "_blake2",
    "django.utils.crypto",
    "django.core.signing",
)
# Lista cerrada de excepciones de RF-010: añadir una es un cambio de la spec.
ALLOWED_USES = {("apps/accounts/password_validation.py", "hashlib.sha1")}


def _is_forbidden(module: str) -> bool:
    return any(module == name or module.startswith(f"{name}.") for name in FORBIDDEN_MODULES)


def forbidden_uses(source: str) -> list[str]:
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    uses: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_forbidden(alias.name):
                    continue
                if alias.asname is None and "." in alias.name:
                    uses.add(alias.name)
                else:
                    aliases[alias.asname or alias.name] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                if _is_forbidden(node.module):
                    uses.add(full_name)
                elif _is_forbidden(full_name):
                    aliases[alias.asname or alias.name] = full_name
    attribute_bases: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in aliases:
                attribute_bases.add(id(node.value))
                uses.add(f"{aliases[node.value.id]}.{node.attr}")
    for node in ast.walk(tree):
        # Un uso sin atributo (por ejemplo, getattr(hashlib, ...)) cuenta como el módulo entero.
        if isinstance(node, ast.Name) and node.id in aliases and id(node) not in attribute_bases:
            uses.add(aliases[node.id])
    return sorted(uses)


def _is_scanned(relative: Path) -> bool:
    if "tests" in relative.parts or relative.name == "conftest.py":
        return False
    if any(part.startswith(".") for part in relative.parts):
        return False
    return relative.as_posix() != SINGLE_POINT


def scan(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if not _is_scanned(relative):
            continue
        uses = [
            use
            for use in forbidden_uses(path.read_text())
            if (relative.as_posix(), use) not in ALLOWED_USES
        ]
        if uses:
            found[relative.as_posix()] = uses
    return found


def _write(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)


@pytest.mark.parametrize(
    ("relative", "source", "use"),
    [
        ("apps/x/a.py", "import hashlib\nhashlib.sha256(b'')\n", "hashlib.sha256"),
        ("apps/x/b.py", "from hmac import new as x\nx(b'k', b'm', 'sha256')\n", "hmac.new"),
        (
            "apps/x/c.py",
            "from django.utils.crypto import salted_hmac\n",
            "django.utils.crypto.salted_hmac",
        ),
        ("apps/x/d.py", "import django.utils.crypto\n", "django.utils.crypto"),
        ("apps/x/migrations/0001_initial.py", "import hmac\nhmac.digest\n", "hmac.digest"),
        ("config/e.py", "import hashlib as h\nh.md5()\n", "hashlib.md5"),
        (
            "apps/accounts/password_validation.py",
            "import hashlib\nhashlib.sha256(b'')\n",
            "hashlib.sha256",
        ),
    ],
)
def test_scan_reports_the_file_and_the_use(
    tmp_path: Path, relative: str, source: str, use: str
) -> None:
    _write(tmp_path, relative, source)

    assert scan(tmp_path) == {relative: [use]}


@pytest.mark.parametrize(
    ("relative", "source", "use"),
    [
        ("apps/x/f.py", "import _hashlib\n_hashlib.new\n", "_hashlib.new"),
        ("apps/x/g.py", "import _sha256\n_sha256.sha256(b'')\n", "_sha256.sha256"),
        (
            "apps/x/h.py",
            "from django.core import signing\nsigning.dumps(1)\n",
            "django.core.signing.dumps",
        ),
        (
            "apps/x/i.py",
            "import django.core.signing\ndjango.core.signing.Signer\n",
            "django.core.signing",
        ),
        ("manage.py", "import hmac\nhmac.new\n", "hmac.new"),
        ("otra/x.py", "from hashlib import md5\n", "hashlib.md5"),
    ],
)
def test_scan_covers_the_whole_backend_and_internal_modules(
    tmp_path: Path, relative: str, source: str, use: str
) -> None:
    _write(tmp_path, relative, source)

    assert scan(tmp_path) == {relative: [use]}


def test_scan_allows_the_framework_password_utilities(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "apps/x/passwords.py",
        "from django.contrib.auth.hashers import make_password\nmake_password('x')\n",
    )

    assert scan(tmp_path) == {}


def test_scan_reports_a_module_used_without_an_attribute(tmp_path: Path) -> None:
    _write(tmp_path, "apps/x/a.py", "import hashlib\ngetattr(hashlib, 'sha256')\n")
    _write(tmp_path, "apps/x/b.py", "from django.utils import crypto\ncrypto.salted_hmac\n")

    assert scan(tmp_path) == {
        "apps/x/a.py": ["hashlib"],
        "apps/x/b.py": ["django.utils.crypto.salted_hmac"],
    }


def test_scan_allows_only_the_listed_exception(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "apps/accounts/password_validation.py",
        "import hashlib\nhashlib.sha1(b'', usedforsecurity=False)\n",
    )

    assert scan(tmp_path) == {}


def test_scan_skips_tests_and_the_single_point(tmp_path: Path) -> None:
    _write(tmp_path, "apps/x/tests/test_a.py", "import hmac\nhmac.new\n")
    _write(tmp_path, "tests/test_b.py", "import hmac\nhmac.new\n")
    _write(tmp_path, "apps/x/conftest.py", "import hmac\nhmac.new\n")
    _write(tmp_path, ".cache/c.py", "import hmac\nhmac.new\n")
    _write(tmp_path, "apps/core/fingerprints.py", "import hmac\nhmac.new\n")
    _write(tmp_path, "apps/x/clean.py", "import secrets\nsecrets.token_urlsafe(8)\n")

    assert scan(tmp_path) == {}


def test_no_fingerprint_is_computed_outside_the_single_point() -> None:
    found = scan(BACKEND_DIR)

    assert found == {}, "Hashes computed outside apps/core/fingerprints.py (RF-010): " + "; ".join(
        f"{path}: {', '.join(uses)}" for path, uses in sorted(found.items())
    )
