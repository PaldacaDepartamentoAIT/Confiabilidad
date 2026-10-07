from datetime import timedelta
from typing import Any

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth.models import Group, Permission
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import User
from apps.accounts.tests.factories import make_user
from apps.consents.hashing import email_fingerprint
from apps.consents.models import MarketingConsent, Terms, UserTerms
from apps.consents.tests.factories import make_document

pytestmark = pytest.mark.django_db

SUPPORT_GROUP = "Soporte técnico"
MODELS = ["userterms", "marketingconsent"]


def _support_member() -> User:
    user = make_user(is_staff=True)
    user.groups.add(Group.objects.get(name=SUPPORT_GROUP))
    return user


def _client(user: User) -> Client:
    client = Client()
    client.force_login(user)
    return client


@pytest.fixture
def support_client() -> Client:
    return _client(_support_member())


def _url(model: str, name: str, *args: object) -> str:
    return reverse(f"admin:consents_{model}_{name}", args=args)


def _acceptance_form(user: User, document: Terms, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "user": user.pk,
        "terms": document.pk,
        "terms_accepted_at_0": "2026-01-01",
        "terms_accepted_at_1": "10:00:00",
        "revoked_at_0": "",
        "revoked_at_1": "",
    }
    data.update(overrides)
    return data


def _consent_form(user: User, document: Terms, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "user": user.pk,
        "terms": document.pk,
        "granted": "on",
        "granted_at_0": "2026-01-01",
        "granted_at_1": "10:00:00",
        "revoked_at_0": "",
        "revoked_at_1": "",
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize("model", MODELS)
def test_support_member_sees_the_lists(support_client: Client, model: str) -> None:
    assert support_client.get(_url(model, "changelist")).status_code == 200


def test_support_creates_an_acceptance_of_a_non_current_document_for_an_inactive_account(
    support_client: Client,
) -> None:
    user = make_user(email="ana@x.com", is_active=False)
    draft = make_document(version="draft")

    response = support_client.post(
        _url("userterms", "add"), _acceptance_form(user, draft, user_email_hash="typed")
    )

    assert response.status_code == 302
    acceptance = UserTerms.objects.get()
    assert (acceptance.user, acceptance.terms) == (user, draft)
    assert acceptance.user_email_hash == email_fingerprint("ana@x.com")


def test_support_creates_a_marketing_consent(support_client: Client) -> None:
    user, document = make_user(), make_document(kind=Terms.Kind.MARKETING)

    response = support_client.post(_url("marketingconsent", "add"), _consent_form(user, document))

    assert response.status_code == 302
    assert MarketingConsent.objects.get().granted is True


@pytest.mark.parametrize(
    ("model", "form"), [("userterms", _acceptance_form), ("marketingconsent", _consent_form)]
)
def test_creating_a_record_without_user_shows_a_form_error(
    support_client: Client, model: str, form: Any
) -> None:
    kind = Terms.Kind.TERMS if model == "userterms" else Terms.Kind.MARKETING
    data = form(make_user(), make_document(kind=kind))
    data["user"] = ""

    response = support_client.post(_url(model, "add"), data)

    assert response.status_code == 200
    assert "user" in response.context["adminform"].form.errors


def test_duplicate_active_consent_shows_a_form_error(support_client: Client) -> None:
    user, document = make_user(), make_document(kind=Terms.Kind.MARKETING)
    MarketingConsent(user=user, terms=document).save()

    response = support_client.post(_url("marketingconsent", "add"), _consent_form(user, document))

    assert response.status_code == 200
    assert MarketingConsent.objects.count() == 1


def test_support_edits_and_deletes_an_acceptance(support_client: Client) -> None:
    user, document = make_user(), make_document()
    acceptance = UserTerms(user=user, terms=document)
    acceptance.save()

    edited = support_client.post(
        _url("userterms", "change", acceptance.pk),
        _acceptance_form(user, document, revoked_at_0="2026-02-01", revoked_at_1="09:00:00"),
    )
    acceptance.refresh_from_db()
    deleted = support_client.post(_url("userterms", "delete", acceptance.pk), {"post": "yes"})

    assert edited.status_code == 302
    assert acceptance.revoked_at is not None
    assert deleted.status_code == 302
    assert not UserTerms.objects.exists()


def test_support_deletes_a_marketing_consent(support_client: Client) -> None:
    consent = MarketingConsent(user=make_user(), terms=make_document(kind=Terms.Kind.MARKETING))
    consent.save()

    response = support_client.post(_url("marketingconsent", "delete", consent.pk), {"post": "yes"})

    assert response.status_code == 302
    assert not MarketingConsent.objects.exists()


@pytest.mark.parametrize("model", [UserTerms, MarketingConsent])
def test_email_hash_is_read_only(model: type[UserTerms | MarketingConsent]) -> None:
    model_admin = site.get_model_admin(model)

    assert "user_email_hash" in model_admin.get_readonly_fields(RequestFactory().get("/"), None)


def test_revoke_action_revokes_the_selected_acceptances(support_client: Client) -> None:
    active = UserTerms(user=make_user(), terms=make_document())
    active.save()
    already = UserTerms(
        user=make_user(), terms=make_document(), revoked_at=timezone.now() - timedelta(days=1)
    )
    already.save()
    first_revocation = already.revoked_at

    response = support_client.post(
        _url("userterms", "changelist"),
        {"action": "revoke_selected", "_selected_action": [active.pk, already.pk]},
    )
    active.refresh_from_db()
    already.refresh_from_db()

    assert response.status_code == 302
    assert active.revoked_at is not None
    assert already.revoked_at == first_revocation


def test_revoke_action_revokes_the_selected_marketing_consents(support_client: Client) -> None:
    consent = MarketingConsent(user=make_user(), terms=make_document(kind=Terms.Kind.MARKETING))
    consent.save()

    support_client.post(
        _url("marketingconsent", "changelist"),
        {"action": "revoke_selected", "_selected_action": [consent.pk]},
    )
    consent.refresh_from_db()

    assert consent.granted is False
    assert consent.revoked_at is not None


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("name", ["changelist", "add"])
def test_staff_outside_the_group_is_forbidden_even_with_permissions(model: str, name: str) -> None:
    user = make_user(is_staff=True)
    user.user_permissions.set(
        Permission.objects.filter(
            content_type__app_label="consents",
            codename__in=[f"{action}_{model}" for action in ("view", "add", "change", "delete")],
        )
    )

    assert _client(user).get(_url(model, name)).status_code == 403


@pytest.mark.parametrize("model", MODELS)
def test_superuser_can_manage_records(model: str) -> None:
    superuser = make_user(is_staff=True, is_superuser=True)

    assert _client(superuser).get(_url(model, "add")).status_code == 200


def test_inactive_support_member_cannot_access() -> None:
    member = _support_member()
    member.is_active = False
    member.save()
    request = RequestFactory().get("/")
    request.user = member

    assert site.get_model_admin(UserTerms).has_view_permission(request) is False


def _all_model_permissions(user: User) -> User:
    user.user_permissions.set(Permission.objects.filter(content_type__app_label="consents"))
    return User.objects.get(pk=user.pk)


def _permissions(user: User, model: type[UserTerms | MarketingConsent]) -> list[bool]:
    request = RequestFactory().get("/")
    request.user = user
    model_admin = site.get_model_admin(model)
    return [
        model_admin.has_module_permission(request),
        model_admin.has_view_permission(request),
        model_admin.has_add_permission(request),
        model_admin.has_change_permission(request),
        model_admin.has_delete_permission(request),
    ]


@pytest.mark.parametrize("model", [UserTerms, MarketingConsent])
def test_only_active_staff_in_the_group_gets_every_permission(
    model: type[UserTerms | MarketingConsent],
) -> None:
    member = _support_member()
    outsider = _all_model_permissions(make_user(is_staff=True))
    not_staff = make_user()
    not_staff.groups.add(Group.objects.get(name=SUPPORT_GROUP))

    assert _permissions(member, model) == [True] * 5
    assert _permissions(outsider, model) == [False] * 5
    assert _permissions(not_staff, model) == [False] * 5
