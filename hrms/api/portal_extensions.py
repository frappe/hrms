import frappe
from frappe import _

from hrms.api import get_current_employee

HOOK = "employee_portal_screens"


def _definitions() -> dict:
	"""slug -> definition, collected from every installed app that declares the hook."""
	out = {}
	for path in frappe.get_hooks(HOOK) or []:
		try:
			screens = frappe.get_attr(path)() or []
		except Exception:
			# a broken regional app must not take the whole portal down
			frappe.log_error(title="Employee portal extension failed", message=frappe.get_traceback())
			continue
		for screen in screens:
			if screen.get("slug"):
				out[screen["slug"]] = screen
	return out


def nav_items() -> list[dict]:
	"""Sidebar entries contributed by other apps. Rendered like any other item."""
	items = []
	for slug, screen in _definitions().items():
		items.append(
			{
				"label": screen.get("label") or slug,
				"icon": screen.get("icon") or "lucide-puzzle",
				"to": f"/x/{slug}",
				"group": screen.get("group") or "My Work",
				"order": screen.get("order") or 0,
			}
		)
	items.sort(key=lambda i: (i["order"], i["label"]))
	return items


def _screen_or_throw(slug: str) -> dict:
	screen = _definitions().get(slug)
	if not screen:
		raise frappe.DoesNotExistError(_("No such page."))
	return screen


@frappe.whitelist()
def get_screen(slug: str) -> dict:
	"""Render-ready spec for an extension screen, from the app that owns it."""
	employee = get_current_employee()
	screen = _screen_or_throw(slug)
	spec = frappe.get_attr(screen["get"])(employee) or {}
	spec.setdefault("title", screen.get("label") or slug)
	spec["slug"] = slug
	return spec


@frappe.whitelist(methods=["POST"])
def run_action(slug: str, action: str, values: str | dict | None = None) -> dict:
	"""Invoke an action the owning screen declared. Unlisted names are refused."""
	employee = get_current_employee()
	screen = _screen_or_throw(slug)

	handler = (screen.get("actions") or {}).get(action)
	if not handler:
		raise frappe.PermissionError(_("This action is not available."))

	if isinstance(values, str):
		values = frappe.parse_json(values)

	result = frappe.get_attr(handler)(employee, values or {}) or {}
	# the screen almost always wants to re-render itself afterwards
	if result.get("reload", True):
		result["spec"] = get_screen(slug)
	return result
