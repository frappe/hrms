import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeFrappe(types.ModuleType):
	def __getattr__(self, name):
		if name in {"session", "form_dict", "db"}:
			return getattr(self.local, name)
		raise AttributeError(name)


frappe = FakeFrappe("frappe")
frappe._ = lambda value: value
frappe.Redirect = type("Redirect", (Exception,), {})
frappe.local = types.SimpleNamespace(
	flags=types.SimpleNamespace(),
	session_obj=None,
	session=types.SimpleNamespace(user="Guest", data=types.SimpleNamespace()),
	form_dict={},
	db=types.SimpleNamespace(exists=lambda *args, **kwargs: False),
)
frappe.throw = lambda message: (_ for _ in ()).throw(RuntimeError(message))
frappe.get_doc = lambda *args, **kwargs: None
frappe.new_doc = lambda *args, **kwargs: None

frappe_utils = types.ModuleType("frappe.utils")
frappe_utils.get_url = lambda path="/": f"https://example.test{path}"

frappe_utils_oauth = types.ModuleType("frappe.utils.oauth")
frappe_utils_oauth.get_email = lambda userinfo: userinfo.get("email")
frappe_utils_oauth.get_oauth2_authorize_url = (
	lambda provider, redirect_to: f"https://auth.example/{provider}?redirect={redirect_to}"
)
frappe_utils_oauth.get_oauth2_flow = lambda provider: None
frappe_utils_oauth.get_oauth2_providers = lambda: {}
frappe_utils_oauth.get_redirect_uri = lambda provider: f"https://example.test/auth/{provider}/redirect"
frappe_utils_oauth.login_oauth_user = lambda *args, **kwargs: None

social_login_key = types.ModuleType("frappe.integrations.doctype.social_login_key.social_login_key")
social_login_key.SocialLoginKey = type(
	"SocialLoginKey",
	(),
	{"get_social_login_provider": staticmethod(lambda doc, provider, initialize=True: None)},
)

oauth2_logins = types.ModuleType("frappe.integrations.oauth2_logins")
oauth2_logins.decoder_compat = object()

sys.modules.setdefault("frappe", frappe)
sys.modules.setdefault("frappe.utils", frappe_utils)
sys.modules.setdefault("frappe.utils.oauth", frappe_utils_oauth)
sys.modules.setdefault(
	"frappe.integrations.doctype.social_login_key.social_login_key",
	social_login_key,
)
sys.modules.setdefault("frappe.integrations.oauth2_logins", oauth2_logins)

module_path = Path(__file__).resolve().parents[1] / "ameide_oidc.py"
module_spec = importlib.util.spec_from_file_location("hr_ameide_oidc_under_test", module_path)
ameide_oidc = importlib.util.module_from_spec(module_spec)
assert module_spec and module_spec.loader
module_spec.loader.exec_module(ameide_oidc)


class TestAmeideOidc(unittest.TestCase):
	def test_normalize_redirect_to_defaults_to_app_base(self):
		self.assertEqual(ameide_oidc.normalize_redirect_to(None), "/hrms")
		self.assertEqual(ameide_oidc.normalize_redirect_to(""), "/hrms")

	def test_normalize_redirect_to_rejects_external_targets(self):
		self.assertEqual(ameide_oidc.normalize_redirect_to("https://evil.example"), "/hrms")
		self.assertEqual(ameide_oidc.normalize_redirect_to("//evil.example"), "/hrms")

	def test_normalize_redirect_to_normalizes_relative_targets(self):
		self.assertEqual(ameide_oidc.normalize_redirect_to("home"), "/home")
		self.assertEqual(ameide_oidc.normalize_redirect_to("/home"), "/home")

	def test_build_login_redirect_location_encodes_redirect_target(self):
		location = ameide_oidc.build_login_redirect_location("/hrms/team space")
		self.assertEqual(location, "/auth/ameide-oidc?redirect-to=/hrms/team%20space")

	def test_build_logout_redirect_location_uses_explicit_end_session_endpoint(self):
		env = {
			"AMEIDE_OIDC_END_SESSION_ENDPOINT": "https://auth.example/realms/ameide/protocol/openid-connect/logout",
			"AMEIDE_OIDC_CLIENT_ID": "io-ameide-hr",
			"AMEIDE_OIDC_POST_LOGOUT_REDIRECT_URI": "https://hr.example/",
		}
		with patch.dict("os.environ", env, clear=True):
			location = ameide_oidc.build_logout_redirect_location("token-123")
		self.assertIn("client_id=io-ameide-hr", location)
		self.assertIn("post_logout_redirect_uri=https%3A%2F%2Fhr.example%2F", location)
		self.assertIn("id_token_hint=token-123", location)
		self.assertTrue(location.startswith(env["AMEIDE_OIDC_END_SESSION_ENDPOINT"]))

	def test_build_logout_redirect_location_falls_back_to_issuer(self):
		env = {
			"AMEIDE_OIDC_ISSUER_URL": "https://auth.example/realms/ameide",
			"AMEIDE_OIDC_CLIENT_ID": "io-ameide-hr",
			"AMEIDE_OIDC_POST_LOGOUT_REDIRECT_URI": "https://hr.example/",
		}
		with patch.dict("os.environ", env, clear=True):
			location = ameide_oidc.build_logout_redirect_location()
		self.assertTrue(
			location.startswith("https://auth.example/realms/ameide/protocol/openid-connect/logout?")
		)


if __name__ == "__main__":
	unittest.main()
