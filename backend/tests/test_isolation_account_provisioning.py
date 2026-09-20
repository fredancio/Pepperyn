from copy import deepcopy
from types import SimpleNamespace as NS

import unittest

from sandbox.provision_isolation_accounts import EMAILS, URL, provision


def bundle():
    return {"project_url": URL, "purpose": "A24_TECHNICAL_ISOLATION_ONLY", "dpapi_roundtrip_verified": True,
            "accounts": [{"email": email, "password": str(i) * 64} for i, email in enumerate(EMAILS)]}


class Factory:
    def __init__(self, failure=None):
        self.created = []
        self.failure = failure

    def __call__(self, url, key):
        assert url == URL
        owner = self
        client = NS()
        if key == "service-test":
            def create(attrs):
                assert attrs["email_confirm"] is True
                assert attrs["app_metadata"]["pepperyn_test_purpose"] == "A24_TECHNICAL_ISOLATION_ONLY"
                if owner.failure == "timeout" and len(owner.created) == 1:
                    raise RuntimeError("sensitive response never printed")
                owner.created.append(attrs)
                return NS(user=user(len(owner.created)))
            client.auth = NS(admin=NS(create_user=create))
            return client
        assert key == "anon-test"
        i = len(owner.created)
        client.auth = NS(sign_in_with_password=lambda data: NS(session=NS(access_token="secret-test-token")),
                         get_user=lambda token: NS(user=user(1 if owner.failure == "foreign-auth" else i)))

        class Query:
            def __init__(self, table): self.name = table
            def select(self, fields): return self
            def eq(self, *args): return self
            def limit(self, value): assert value == 2; return self
            def execute(self):
                uid = uuid(i)
                company = uuid(i + 10)
                if self.name == "profiles":
                    rows = [{"id": uid, "company_id": company}]
                elif self.name == "companies":
                    rows = [{"id": company, "admin_user_id": uid, "name": f"Pepperyn A24 Isolation Synthetic {i}"}]
                else:
                    rows = [{"id": uuid(i + 20), "company_id": company, "name": f"Pepperyn A24 Isolation Synthetic {i}", "is_primary": True}]
                if owner.failure == "foreign-owner" and self.name == "companies": rows[0]["admin_user_id"] = uuid(99)
                if owner.failure == "missing-trigger": rows = []
                return NS(data=rows)
        client.table = Query
        return client


def uuid(i): return f"00000000-0000-4000-8000-{i:012d}"
def user(i): return NS(id=uuid(i), email=EMAILS[i-1], role="authenticated")


def check_success_does_not_claim_adversarial_proof_or_disclose_credentials():
    f = Factory()
    result = provision(bundle(), "service-test", "anon-test", f)
    assert result["status"] == "ACCOUNTS_CREATED_SCOPE_VERIFIED"
    assert result["adversarial_isolation_proven"] is False
    assert len(f.created) == 2
    assert "secret-test-token" not in str(result)
    assert all(a["password"] not in str(result) for a in f.created)


def check_invalid_authority_refuses_before_write(field, value):
    data = deepcopy(bundle()); data[field] = value
    f = Factory()
    assert provision(data, "service-test", "anon-test", f)["status"] == "REFUSED"
    assert not f.created


def check_partial_failure_never_retries_or_prints_response(failure):
    f = Factory(failure)
    result = provision(bundle(), "service-test", "anon-test", f)
    assert result["status"] == "REFUSED"
    assert result["automatic_retry_permitted"] is False
    assert len(f.created) <= 2
    assert "sensitive response" not in str(result)


class ProvisioningTests(unittest.TestCase):
    def test_success(self):
        check_success_does_not_claim_adversarial_proof_or_disclose_credentials()

    def test_bad_authority(self):
        for field, value in [("project_url", "https://other.invalid"), ("purpose", "production"), ("dpapi_roundtrip_verified", False)]:
            with self.subTest(field=field):
                check_invalid_authority_refuses_before_write(field, value)

    def test_partial_failures(self):
        for failure in ["timeout", "foreign-auth", "foreign-owner", "missing-trigger"]:
            with self.subTest(failure=failure):
                check_partial_failure_never_retries_or_prints_response(failure)
