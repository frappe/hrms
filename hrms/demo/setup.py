import frappe
from frappe.utils import now_datetime


class Setup:
	def __init__(self):
		pass

	@classmethod
	def complete_setup_wizard(self):
		from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

		year = now_datetime().year
		print("year", year)

	@classmethod
	def prerequisites(cls):
		cls.complete_setup_wizard()
