# Copyright (c) 2026, Frappe Technologies and Contributors
# License: MIT. See LICENSE

"""hrms ships its navigation as `Sidebar` fixtures, one per semantic module.

The framework renamed `Module Sidebar` to `Sidebar` and moved an app's fixtures from
`<module>/module_sidebar/` to `<module>/sidebar/`. An app that has not followed is not broken --
its folder is simply never walked, and each of its modules falls back to a base computed from
its own contents -- so nothing here fails loudly if the conversion is half done. That is exactly
why it is asserted: the failure mode is hrms's curated navigation quietly reverting to generated.

Two facts, and they are different questions:

- `TestTheFixturesAreWhereMigrateLooks` is about the *files*. Import finds them, and orphan
  removal derives the same record name from the path that the file declares -- a mismatch there
  makes migrate delete the very rows it just imported.
- `TestTheModulesResolveToTheirShippedArrangement` is about *navigation*, asked through the
  resolver seam rather than through any payload key. It is what says the files actually took.
"""

import json
import os

import frappe
from frappe.desk.doctype.sidebar.convert_fixtures import export_path
from frappe.desk.doctype.sidebar.sidebar import resolve_sidebar
from frappe.model.sync import create_entity_file_map, get_doc_files
from frappe.tests import IntegrationTestCase

#: The semantic modules that own hrms's navigation, as declared in `modules.txt`, each mapped to
#: the shell its sidebar is called by. `HR` and `Payroll` are code modules and ship no sidebar of
#: their own, so they are deliberately absent. Their `Module Def` rows arrive from the framework's
#: `sync_module_defs`, which runs on every migrate -- an app adding a module no longer needs a
#: patch of its own to register it.
#:
#: The two are the same string for seven of the nine. They part where a module wants an `&` in
#: its name and cannot have one, because a module folder is an imported Python package: the
#: module is `Shift and Attendance` and the sidebar is `Shift & Attendance`. A `Sidebar` is
#: `autoname: field:title`, so a fixture cannot hold a title apart from its name -- the name is
#: the ampersand or nothing is. The framework calls this a renamed shell and carries it: a
#: sidebar says which module it belongs to in its own column, and `sidebar_for_module` walks to
#: it. Naming these two after their modules instead is what the `&` gets quietly eaten by.
SIDEBAR_SHELLS = {
	"Expenses": "Expenses",
	"HR Setup": "HR Setup",
	"Leaves": "Leaves",
	"Payroll": "Payroll",
	"Performance": "Performance",
	"Recruitment": "Recruitment",
	"Shift and Attendance": "Shift & Attendance",
	"Tax and Benefits": "Tax & Benefits",
	"Tenure": "Tenure",
}


def fixture_path(module: str) -> str:
	"""Where the module's fixture sits, which a `Sidebar` derives from its title, not its module."""
	return export_path(module, SIDEBAR_SHELLS[module])


def shipped(module: str) -> dict:
	"""The fixture as it sits in the app folder, before any site has seen it."""
	with open(fixture_path(module)) as f:
		return json.load(f)


class TestTheFixturesAreWhereMigrateLooks(IntegrationTestCase):
	def test_every_semantic_module_ships_one(self):
		"""Named individually rather than globbed: a fixture that stopped being exported would
		pass a test that only checks the files it can find."""
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				self.assertTrue(os.path.exists(fixture_path(module)))

	def test_they_declare_the_renamed_doctype(self):
		"""A fixture still naming `Module Sidebar` would import against a doctype the site no
		longer has -- which is why the walk skips the old folder rather than failing on it."""
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				self.assertEqual(shipped(module)["doctype"], "Sidebar")

	def test_the_module_walk_picks_them_up(self):
		"""`get_doc_files` is what migrate imports from. It only opens folders named by
		`IMPORTABLE_DOCTYPES`, so this is the fact that the folder rename landed."""
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				module_path = frappe.get_module_path(module)
				self.assertIn(fixture_path(module), get_doc_files(files=[], start_path=module_path))

	def test_record_name_and_filename_agree(self):
		"""Orphan removal maps a file to a record by reading the `name` out of it and looking
		for that record. Standard rows whose file it cannot find are deleted, so a fixture whose
		name and path disagree is imported and then reaped on the same migrate."""
		known = create_entity_file_map(["Sidebar"])["Sidebar"]

		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				shell = SIDEBAR_SHELLS[module]
				self.assertEqual(shipped(module)["name"], shell)
				self.assertEqual(known.get(shell), fixture_path(module))


class TestTheModulesResolveToTheirShippedArrangement(IntegrationTestCase):
	"""The point of the whole exercise: what a person's navigation resolves to.

	Asserted as Administrator, who is filtered out of nothing and carries no customization, so
	the resolution is the shipped arrangement itself rather than one reader's view of it. That a
	*restricted* reader sees less is the framework's fact and is asserted there.
	"""

	def test_a_module_resolves_to_the_items_its_fixture_ships(self):
		"""Labels in order, which is the whole of what the fixture authored. A Computed base
		would still resolve to something -- these modules have workspaces -- so "resolves to
		anything at all" is not the fact worth asserting."""
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				resolved = resolve_sidebar(SIDEBAR_SHELLS[module], "Administrator")

				self.assertIsNotNone(resolved)
				self.assertEqual(
					[item["label"] for item in resolved.items],
					[item["label"] for item in shipped(module)["items"]],
				)

	def test_the_label_and_icon_are_the_fixture_s(self):
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				resolved = resolve_sidebar(SIDEBAR_SHELLS[module], "Administrator")
				fixture = shipped(module)

				self.assertEqual(resolved.label, fixture["title"])
				self.assertEqual(resolved.header_icon, fixture["header_icon"])

	def test_a_module_opens_on_its_own_navigation(self):
		"""Landing is derived from the resolved entries, so a module falling back to a computed
		base would land somewhere the fixture never named."""
		for module in SIDEBAR_SHELLS:
			with self.subTest(module=module):
				self.assertIsNotNone(resolve_sidebar(SIDEBAR_SHELLS[module], "Administrator").landing)
