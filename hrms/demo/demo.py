import frappe

from hrms.demo.setup import Setup


def make():
	Setup.prerequisites()
	# frappe.db.commit()
