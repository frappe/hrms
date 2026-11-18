from pathlib import Path

import frappe

# Custom HTML Block isn't an exportable standard doctype, so the source of each block lives in
# this folder and is copied into a Custom HTML Block record after every migrate.
BLOCKS = {
	"Upcoming interviews": "upcoming_interviews",
	"Open roles": "open_roles",
}
FIELDS = {"html": "html", "script": "js", "style": "css"}


def sync_blocks():
	for name, slug in BLOCKS.items():
		values = {field: read_source(slug, extension) for field, extension in FIELDS.items()}
		if frappe.db.exists("Custom HTML Block", name):
			block = frappe.get_doc("Custom HTML Block", name)
			if all(block.get(field) == value for field, value in values.items()):
				continue
			block.update(values)
			block.save(ignore_permissions=True)
		else:
			frappe.get_doc({"doctype": "Custom HTML Block", "name": name, "private": 0, **values}).insert(
				ignore_permissions=True
			)


def read_source(slug, extension):
	return (Path(__file__).parent / slug / f"{slug}.{extension}").read_text().strip("\n")
