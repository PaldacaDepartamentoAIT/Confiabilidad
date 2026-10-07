from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.tests.factories import make_user
from apps.consents.models import Terms, UserTerms
from apps.consents.tests.factories import make_document, publish_version

pytestmark = pytest.mark.django_db


def _call(*args: str) -> tuple[dict[str, str], str]:
    out = StringIO()
    call_command("consents", *args, stdout=out)
    output = out.getvalue()
    fields = dict(line.split(": ", 1) for line in output.splitlines() if ": " in line)
    return fields, output


def test_current_shows_the_current_document_in_a_locale() -> None:
    documents = publish_version(version="2", content="# Términos\n\nTexto legal.")

    fields, output = _call("current", "--kind", "terms", "--locale", "pt-BR")

    assert fields["kind"] == "terms"
    assert fields["version"] == "2"
    assert fields["locale"] == "pt-BR"
    assert fields["published_at"] == documents["pt-BR"].published_at.isoformat()  # type: ignore[union-attr]
    assert output.endswith("# Términos\n\nTexto legal.\n")


def test_current_without_a_current_version_fails() -> None:
    make_document(kind=Terms.Kind.MARKETING, version="draft")

    with pytest.raises(CommandError, match="There is no current version"):
        _call("current", "--kind", "marketing", "--locale", "es")


def test_accept_terms_registers_the_acceptance() -> None:
    publish_version(version="1")
    user = make_user(email="ana@x.com")

    fields, _ = _call("accept-terms", "Ana@X.com", "--version", "1", "--locale", "en")

    acceptance = UserTerms.objects.get()
    assert acceptance.user == user
    assert acceptance.terms.locale == "en"
    assert fields["accepted"] == "terms 1 (en)"
    assert fields["accepted_at"] == acceptance.terms_accepted_at.isoformat()


def test_accept_terms_shows_the_refusal() -> None:
    publish_version(version="1")
    make_document(version="draft")
    make_user(email="ana@x.com")

    with pytest.raises(CommandError, match="The document is not the current version"):
        _call("accept-terms", "ana@x.com", "--version", "draft", "--locale", "es")
    assert not UserTerms.objects.exists()


def test_accept_terms_with_an_unknown_email_fails() -> None:
    publish_version(version="1")

    with pytest.raises(CommandError, match="Unknown user"):
        _call("accept-terms", "nobody@x.com", "--version", "1", "--locale", "es")
