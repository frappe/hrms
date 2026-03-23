import importlib.util
import sys
import types
import unittest
from pathlib import Path


class FakeFrappe(types.ModuleType):
	def __getattr__(self, name):
		if name in {"session", "form_dict"}:
			return getattr(self.local, name)
		raise AttributeError(name)


class TestAmeideOidcPages(unittest.TestCase):
	def _restore_module(self, name, module):
		if module is None:
			sys.modules.pop(name, None)
			return
		sys.modules[name] = module

	def _load_module(self, relative_path):
		original_frappe = sys.modules.get("frappe")
		original_helper = sys.modules.get("hrms.ameide_oidc")
		frappe = FakeFrappe("frappe")
		frappe.Redirect = type("Redirect", (Exception,), {})
		frappe.local = types.SimpleNamespace(
			flags=types.SimpleNamespace(),
			login_manager=types.SimpleNamespace(logout=lambda: setattr(self, "logout_called", True)),
			form_dict={},
			session=types.SimpleNamespace(data={}),
		)

		helper = types.ModuleType("hrms.ameide_oidc")
		helper.begin_login = lambda redirect_to: setattr(self, "begin_login_target", redirect_to)
		helper.normalize_redirect_to = lambda value: f"normalized:{value}"
		helper.complete_login = lambda code, state: setattr(self, "completed_login", (code, state))
		helper.build_logout_redirect_location = (
			lambda id_token_hint=None: f"https://auth.example/logout?id_token_hint={id_token_hint}"
		)

		self.addCleanup(self._restore_module, "frappe", original_frappe)
		self.addCleanup(self._restore_module, "hrms.ameide_oidc", original_helper)
		sys.modules["frappe"] = frappe
		sys.modules["hrms.ameide_oidc"] = helper

		module_path = Path(__file__).resolve().parents[1] / relative_path
		spec = importlib.util.spec_from_file_location(f"hrms_{relative_path.replace('/', '_')}", module_path)
		module = importlib.util.module_from_spec(spec)
		assert spec and spec.loader
		spec.loader.exec_module(module)
		return module, frappe

	def _load_hooks(self):
		module_path = Path(__file__).resolve().parents[1] / "hooks.py"
		spec = importlib.util.spec_from_file_location("hrms_hooks_under_test", module_path)
		module = importlib.util.module_from_spec(spec)
		assert spec and spec.loader
		spec.loader.exec_module(module)
		return module

	def test_login_page_redirects_to_oidc(self):
		module, frappe = self._load_module("www/login.py")
		context = types.SimpleNamespace()
		frappe.local.form_dict = {"redirect_to": "/hrms/team"}
		module.get_context(context)
		self.assertEqual(context.no_cache, 1)
		self.assertEqual(self.begin_login_target, "normalized:/hrms/team")

	def test_auth_entrypoint_redirects_to_oidc(self):
		module, frappe = self._load_module("www/auth/ameide_oidc.py")
		context = types.SimpleNamespace()
		frappe.local.form_dict = {"redirect-to": "/hrms"}
		module.get_context(context)
		self.assertEqual(context.no_cache, 1)
		self.assertEqual(self.begin_login_target, "normalized:/hrms")

	def test_auth_redirect_page_completes_login(self):
		module, frappe = self._load_module("www/auth/ameide_oidc_redirect.py")
		context = types.SimpleNamespace()
		frappe.local.form_dict = {"code": "code-123", "state": "state-456"}
		module.get_context(context)
		self.assertEqual(context.no_cache, 1)
		self.assertEqual(self.completed_login, ("code-123", "state-456"))

	def test_logout_page_uses_keycloak_logout(self):
		module, frappe = self._load_module("www/logout.py")
		context = types.SimpleNamespace()
		frappe.local.session.data["ameide_oidc_id_token"] = "token-123"
		with self.assertRaises(frappe.Redirect):
			module.get_context(context)
		self.assertEqual(context.no_cache, 1)
		self.assertTrue(self.logout_called)
		self.assertEqual(
			frappe.local.flags.redirect_location,
			"https://auth.example/logout?id_token_hint=token-123",
		)

	def test_hooks_expose_sales_equivalent_ameide_routes(self):
		hooks = self._load_hooks()
		self.assertIn(
			{"from_route": "/auth/ameide-oidc", "to_route": "auth/ameide_oidc"},
			hooks.website_route_rules,
		)
		self.assertIn(
			{"from_route": "/auth/ameide-oidc/redirect", "to_route": "auth/ameide_oidc_redirect"},
			hooks.website_route_rules,
		)
		self.assertIn(
			{"from_route": "/auth/ameide-oidc/logout", "to_route": "auth/ameide_oidc_logout"},
			hooks.website_route_rules,
		)
		self.assertIn(
			{"source": "/login", "target": "/auth/ameide-oidc"},
			hooks.website_redirects,
		)
		self.assertIn(
			{"source": "/logout", "target": "/auth/ameide-oidc/logout"},
			hooks.website_redirects,
		)


if __name__ == "__main__":
	unittest.main()
