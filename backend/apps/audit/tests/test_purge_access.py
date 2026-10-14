import ast
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[3]
AUDIT_MODELS = "apps.audit.models"
PURGE_FUNCTION = f"{AUDIT_MODELS}.purge_expired"
PRIVATE_NAMES = frozenset({"_purge_allowed", "_purge_context"})
# Únicos usos permitidos (D-07, T-040): el permiso interno vive en el modelo y la purga solo la
# llama su comando.
ALLOWED_USES = {
    "apps/audit/models.py": PRIVATE_NAMES,
    "apps/audit/management/commands/purge_security_events.py": frozenset({PURGE_FUNCTION}),
}


def _absolute_module(relative: Path, node: ast.ImportFrom) -> str:
    if node.level == 0:
        return node.module or ""
    package = list(relative.parent.parts)
    base = package[: len(package) - (node.level - 1)]
    return ".".join([*base, node.module] if node.module else base)


def _dotted(node: ast.expr, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id)
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value, aliases)
        return f"{base}.{node.attr}" if base else None
    return None


def purge_uses(source: str, relative: Path) -> list[str]:
    tree = ast.parse(source)
    aliases: dict[str, str] = {}
    uses: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    top_level = alias.name.split(".", 1)[0]
                    aliases[top_level] = top_level
        elif isinstance(node, ast.ImportFrom):
            module = _absolute_module(relative, node)
            for alias in node.names:
                full_name = f"{module}.{alias.name}"
                if alias.name in PRIVATE_NAMES:
                    uses.add(alias.name)
                elif full_name == PURGE_FUNCTION:
                    uses.add(PURGE_FUNCTION)
                aliases[alias.asname or alias.name] = full_name
        elif isinstance(node, ast.Name) and node.id in PRIVATE_NAMES:
            uses.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in PRIVATE_NAMES:
            uses.add(node.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in PRIVATE_NAMES:
                uses.add(node.value)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "purge_expired":
            if _dotted(node.value, aliases) == AUDIT_MODELS:
                uses.add(PURGE_FUNCTION)
    return sorted(uses)


def _is_scanned(relative: Path) -> bool:
    if "tests" in relative.parts or relative.name in ("conftest.py", "tests.py"):
        return False
    if relative.name.startswith("test_"):
        return False
    return not any(part.startswith(".") for part in relative.parts)


def scan(root: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root)
        if not _is_scanned(relative):
            continue
        allowed = ALLOWED_USES.get(relative.as_posix(), frozenset())
        uses = [use for use in purge_uses(path.read_text(), relative) if use not in allowed]
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
        ("apps/audit/admin.py", "from apps.audit.models import _purge_allowed\n", "_purge_allowed"),
        (
            "apps/x/a.py",
            "from apps.audit import models\nwith models._purge_allowed():\n    pass\n",
            "_purge_allowed",
        ),
        (
            "apps/x/b.py",
            "from apps.audit.models import _purge_context as c\nc.set(True)\n",
            "_purge_context",
        ),
        (
            "apps/x/c.py",
            "import apps.audit.models as m\ngetattr(m, '_purge_allowed')\n",
            "_purge_allowed",
        ),
        ("apps/x/d.py", "from apps.audit.models import purge_expired\n", PURGE_FUNCTION),
        ("apps/audit/admin.py", "from .models import purge_expired\n", PURGE_FUNCTION),
        (
            "apps/audit/management/commands/other.py",
            "from ...models import purge_expired\n",
            PURGE_FUNCTION,
        ),
        (
            "apps/x/e.py",
            "import apps.audit.models\napps.audit.models.purge_expired()\n",
            PURGE_FUNCTION,
        ),
        (
            "apps/x/f.py",
            "from apps.audit import models as m\nm.purge_expired()\n",
            PURGE_FUNCTION,
        ),
    ],
)
def test_scan_reports_purge_access_outside_its_allowed_files(
    tmp_path: Path, relative: str, source: str, use: str
) -> None:
    _write(tmp_path, relative, source)

    assert scan(tmp_path) == {relative: [use]}


def test_scan_allows_the_model_the_command_tests_and_other_purges(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "apps/audit/models.py",
        "_purge_context = None\ndef _purge_allowed():\n    return _purge_context\n",
    )
    _write(
        tmp_path,
        "apps/audit/management/commands/purge_security_events.py",
        "from apps.audit.models import purge_expired\npurge_expired()\n",
    )
    _write(tmp_path, "apps/audit/tests/test_x.py", "from apps.audit.models import _purge_allowed\n")
    _write(
        tmp_path,
        "apps/accounts/management/commands/registration.py",
        "from apps.accounts import registration\nregistration.purge_expired()\n",
    )

    assert scan(tmp_path) == {}


def test_purge_access_stays_in_the_model_and_its_command() -> None:
    found = scan(BACKEND_DIR)

    assert found == {}, "Purge access outside its allowed files (RF-012, D-07): " + "; ".join(
        f"{path}: {', '.join(uses)}" for path, uses in sorted(found.items())
    )
