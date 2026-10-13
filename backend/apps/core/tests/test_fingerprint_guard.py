import ast
import re
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[3]
SINGLE_POINT = "apps/core/fingerprints.py"
FORBIDDEN_MODULES = (
    "hashlib",
    "hmac",
    "crypt",
    "_hashlib",
    "_sha1",
    "_sha2",
    "_sha3",
    "_md5",
    "_blake2",
    "_crypt",
    "django.utils.crypto",
    "django.core.signing",
    "django.contrib.auth.tokens",
)
# Bibliotecas criptográficas conocidas y su módulo de import: solo se vigilan si el proyecto las
# declara como dependencia (D-08, S-07). Ampliar la tabla es un cambio de la spec.
KNOWN_CRYPTOGRAPHIC_LIBRARIES = {
    "cryptography": "cryptography",
    "pycryptodome": "Crypto",
    "pycryptodomex": "Cryptodome",
    "pynacl": "nacl",
}
_REQUIREMENT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_INCLUDE = re.compile(r"(?:-r\s*|--requirement(?:\s+|=))(\S+)")
# Lista cerrada de excepciones de RF-010: añadir una es un cambio de la spec.
ALLOWED_USES = {("apps/accounts/password_validation.py", "hashlib.sha1")}


def _read_requirements(path: Path, declared: set[str], visited: set[Path]) -> None:
    if path in visited or not path.is_file():
        return
    visited.add(path)
    for raw_line in path.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        include = _INCLUDE.match(line)
        if include:
            _read_requirements(path.parent / include.group(1), declared, visited)
        elif line and not line.startswith("-"):
            match = _REQUIREMENT_NAME.match(line)
            if match:
                declared.add(match.group().lower().replace("_", "-"))


def declared_requirements(root: Path) -> set[str]:
    declared: set[str] = set()
    visited: set[Path] = set()
    for path in sorted(root.glob("requirements*.txt")):
        _read_requirements(path, declared, visited)
    return declared


def _forbidden_modules(root: Path) -> tuple[str, ...]:
    declared = declared_requirements(root)
    return FORBIDDEN_MODULES + tuple(
        module for name, module in KNOWN_CRYPTOGRAPHIC_LIBRARIES.items() if name in declared
    )


def _is_forbidden(name: str, forbidden: tuple[str, ...]) -> bool:
    return any(name == module or name.startswith(f"{module}.") for module in forbidden)


def _is_ancestor(name: str, forbidden: tuple[str, ...]) -> bool:
    return any(module.startswith(f"{name}.") for module in forbidden)


def _dotted(node: ast.Attribute) -> tuple[ast.Name, str] | None:
    attributes: list[str] = []
    current: ast.expr = node
    while isinstance(current, ast.Attribute):
        attributes.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    return current, ".".join(reversed(attributes))


def forbidden_uses(source: str, forbidden: tuple[str, ...] = FORBIDDEN_MODULES) -> list[str]:
    tree = ast.parse(source)
    # Nombre local -> ruta completa, para imports vigilados o antepasados de uno vigilado (D-09).
    aliases: dict[str, str] = {}
    uses: set[str] = set()

    def bind(local: str, full_name: str) -> None:
        if _is_forbidden(full_name, forbidden) or _is_ancestor(full_name, forbidden):
            aliases[local] = full_name

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname is not None:
                    bind(alias.asname, alias.name)
                    continue
                if "." in alias.name and _is_forbidden(alias.name, forbidden):
                    uses.add(alias.name)
                top_level = alias.name.split(".", 1)[0]
                bind(top_level, top_level)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                if _is_forbidden(node.module, forbidden):
                    uses.add(full_name)
                else:
                    bind(alias.asname or alias.name, full_name)
    inner_attributes: set[int] = set()
    chain_bases: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute):
            inner_attributes.add(id(node.value))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in inner_attributes:
            continue
        chain = _dotted(node)
        if chain is None or chain[0].id not in aliases:
            continue
        base, attributes = chain
        chain_bases.add(id(base))
        resolved = f"{aliases[base.id]}.{attributes}"
        if _is_forbidden(resolved, forbidden):
            uses.add(_watched_prefix(resolved, forbidden))
    for node in ast.walk(tree):
        # Un uso sin atributo (por ejemplo, getattr(hashlib, ...)) cuenta como el módulo entero.
        if isinstance(node, ast.Name) and node.id in aliases and id(node) not in chain_bases:
            if _is_forbidden(aliases[node.id], forbidden):
                uses.add(aliases[node.id])
    return sorted(uses)


def _watched_prefix(resolved: str, forbidden: tuple[str, ...]) -> str:
    # Se informa del módulo vigilado más el primer nombre usado: `hashlib.sha256`, no la cadena
    # entera (`hashlib.sha256().hexdigest`).
    module = max((name for name in forbidden if _is_forbidden(resolved, (name,))), key=len)
    rest = resolved[len(module) + 1 :]
    return f"{module}.{rest.split('.', 1)[0]}" if rest else module


def _is_scanned(relative: Path) -> bool:
    if "tests" in relative.parts or relative.name in ("conftest.py", "tests.py"):
        return False
    if relative.name.startswith("test_"):
        return False
    if any(part.startswith(".") for part in relative.parts):
        return False
    return relative.as_posix() != SINGLE_POINT


def scan(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    forbidden = _forbidden_modules(root)
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if not _is_scanned(relative):
            continue
        uses = [
            use
            for use in forbidden_uses(path.read_text(), forbidden)
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
        (
            "apps/x/h.py",
            "from django.core import signing\nsigning.dumps(1)\n",
            "django.core.signing.dumps",
        ),
        (
            "apps/x/i.py",
            "import django.core.signing\n",
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


_CRYPTOGRAPHY_USE = "from cryptography.hazmat.primitives import hashes\nhashes.SHA256()\n"


def test_scan_ignores_cryptographic_libraries_that_are_not_declared(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "Django>=5.0\n# cryptography is only transitive\n")
    _write(tmp_path, "apps/x/c.py", _CRYPTOGRAPHY_USE)

    assert scan(tmp_path) == {}


def test_scan_reports_a_declared_cryptographic_library(tmp_path: Path) -> None:
    _write(tmp_path, "requirements.txt", "Django>=5.0\ncryptography>=42\n")
    _write(tmp_path, "apps/x/c.py", _CRYPTOGRAPHY_USE)

    assert scan(tmp_path) == {"apps/x/c.py": ["cryptography.hazmat.primitives.hashes"]}


def test_scan_follows_included_requirement_files(tmp_path: Path) -> None:
    _write(tmp_path, "requirements-dev.txt", "-r requirements/base.txt  # shared\npytest>=8\n")
    _write(tmp_path, "requirements/base.txt", "PyCryptodome==3.20  # hashes\n")
    _write(tmp_path, "apps/x/d.py", "from Crypto.Hash import SHA256\n")

    assert scan(tmp_path) == {"apps/x/d.py": ["Crypto.Hash.SHA256"]}


def test_real_requirements_are_read_including_included_files() -> None:
    declared = declared_requirements(BACKEND_DIR)

    assert {"django", "django-allauth", "pytest"} <= declared


@pytest.mark.parametrize(
    ("source", "use"),
    [
        ("import django.core\ndjango.core.signing.dumps(1)\n", "django.core.signing.dumps"),
        ("import django\ndjango.core.signing.dumps(1)\n", "django.core.signing.dumps"),
        (
            "from django import utils\nutils.crypto.salted_hmac('s', 'v')\n",
            "django.utils.crypto.salted_hmac",
        ),
        ("import django.utils as du\ndu.crypto.salted_hmac\n", "django.utils.crypto.salted_hmac"),
    ],
)
def test_scan_reports_uses_through_any_ancestor_package(
    tmp_path: Path, source: str, use: str
) -> None:
    _write(tmp_path, "apps/x/a.py", source)

    assert scan(tmp_path) == {"apps/x/a.py": [use]}


def test_scan_ignores_ancestor_packages_used_for_something_else(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "apps/x/a.py",
        "import django\nimport django.core\ndjango.conf.settings\nprint(django)\n",
    )

    assert scan(tmp_path) == {}


@pytest.mark.parametrize(
    "include", ["-rbase.txt", "-r base.txt", "--requirement=base.txt", "--requirement base.txt"]
)
def test_scan_follows_every_form_of_included_requirements(tmp_path: Path, include: str) -> None:
    _write(tmp_path, "requirements.txt", f"{include}\n")
    _write(tmp_path, "base.txt", "cryptography>=42\n")
    _write(tmp_path, "apps/x/c.py", _CRYPTOGRAPHY_USE)

    assert scan(tmp_path) == {"apps/x/c.py": ["cryptography.hazmat.primitives.hashes"]}


PYTHON_INTERNAL_HASH_MODULES = ("_hashlib", "_sha1", "_sha2", "_sha3", "_md5", "_blake2", "_crypt")


@pytest.mark.parametrize("module", PYTHON_INTERNAL_HASH_MODULES)
def test_scan_reports_every_internal_hash_module(tmp_path: Path, module: str) -> None:
    _write(tmp_path, "apps/x/a.py", f"import {module}\n{module}.new\n")

    assert scan(tmp_path) == {"apps/x/a.py": [f"{module}.new"]}


def test_only_internal_hash_modules_of_python_3_12_are_watched() -> None:
    internal = tuple(name for name in FORBIDDEN_MODULES if name.startswith("_"))

    assert internal == PYTHON_INTERNAL_HASH_MODULES


@pytest.mark.parametrize(
    ("source", "use"),
    [
        ("import crypt\ncrypt.crypt('x')\n", "crypt.crypt"),
        (
            "from django.contrib.auth.tokens import default_token_generator\n",
            "django.contrib.auth.tokens.default_token_generator",
        ),
    ],
)
def test_scan_reports_crypt_and_the_framework_tokens(
    tmp_path: Path, source: str, use: str
) -> None:
    _write(tmp_path, "apps/x/a.py", source)

    assert scan(tmp_path) == {"apps/x/a.py": [use]}


def test_scan_skips_files_that_pytest_collects_as_tests(tmp_path: Path) -> None:
    _write(tmp_path, "apps/x/test_x.py", "import hmac\nhmac.new\n")
    _write(tmp_path, "apps/x/tests.py", "import hmac\nhmac.new\n")

    assert scan(tmp_path) == {}
