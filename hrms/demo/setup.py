import frappe
from frappe.utils import now_datetime, cint, get_year_ending, get_year_start, getdate


class DemoSetup:
	def __init__(self):
		self.holiday_list = None
		self.payroll_period = None
		self.income_tax_slab = None

	@classmethod
	def prerequisites(cls):
		year = now_datetime().year

		cls.complete_setup_wizard(year)
		cls.create_holiday_list(year)
		cls.create_payroll_period()
		cls.create_tax_slab()

		frappe.db.commit()  # nosemgrep

	@classmethod
	def complete_setup_wizard(self, year):
		from frappe.desk.page.setup_wizard.setup_wizard import setup_complete

		if not cint(frappe.db.get_single_value("System Settings", "setup_complete")):
			setup_complete(
				{
					"currency": "INR",
					"full_name": "Test User",
					"company_name": "Wind Power LLC",
					"timezone": "Asia/Kolkata",
					"company_abbr": "WP",
					"industry": "Manufacturing",
					"country": "India",
					"fy_start_date": f"{year}-01-01",
					"fy_end_date": f"{year}-12-31",
					"language": "english",
					"company_tagline": "Testing",
					"email": "test@erpnext.com",
					"password": "test",
					"chart_of_accounts": "Standard",
				}
			)

			frappe.db.commit()  # nosemgrep

		print("Setup Wizard Completed")

	@classmethod
	def create_holiday_list(cls, year):
		hl = DemoHolidayList()
		cls.holiday_list = hl.create_holiday_list(year)
		DemoHolidayList.update_holiday_list_on_company(cls.holiday_list)

		print(f"Holiday List {cls.holiday_list} Created")

	@classmethod
	def create_payroll_period(cls):
		pp = DemoPayrollPeriod()
		cls.payroll_period = pp.create_payroll_period()

		print(f"Payroll Period {cls.payroll_period.name} Created")

	@classmethod
	def create_tax_slab(cls):
		ts = DemoIncomeTaxSlab()
		cls.income_tax_slab = ts.create_income_tax_slab()
		print(f"Income Tax Slab {cls.income_tax_slab.name} Created")


class DemoHolidayList:
	def __init__(
		self,
		start_date: str = None,
		end_date: str = None,
		holidays: list = None,
		weekly_off: list = None,
	):
		self._holiday_list = None
		self.start_date = start_date or get_year_start(getdate())
		self.end_date = end_date or get_year_ending(getdate())
		self.weekly_off = "Sunday"
		self.holidays = holidays
		self.weekly_off = weekly_off or ["Sunday", "Saturday"]

	def create_holiday_list(self, holiday_list_name: str = None):
		_holiday_list = frappe.db.get_value("Holiday List", holiday_list_name, "name")

		if not _holiday_list:
			_holiday_list_doc = frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": holiday_list_name,
					"from_date": self.start_date,
					"to_date": self.end_date,
					"holidays": self.get_holidays(),
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
				}
			).insert()
			_holiday_list = _holiday_list_doc.name

		self._holiday_list = _holiday_list

		return _holiday_list

	def get_holidays(self):
		import calendar
		from dateutil import relativedelta

		holidays = []

		for day in self.weekly_off:
			weekday = getattr(calendar, day.upper())
			first_day = self.start_date + relativedelta.relativedelta(weekday=weekday)

			while first_day <= self.end_date:
				holidays.append({"holiday_date": first_day, "description": day, "is_weekly_off": 1})
				first_day += relativedelta.relativedelta(weeks=1)

		return holidays

	@staticmethod
	def update_holiday_list_on_company(holiday_list_name: str = None):
		company = frappe.db.get_single_value("Global Defaults", "default_company")
		frappe.db.set_value("Company", company, "default_holiday_list", holiday_list_name)
		frappe.db.commit()  # nosemgrep


class DemoPayrollPeriod:
	def __init__(self, start_date: str = None, end_date: str = None):
		self.start_date = start_date or get_year_start(getdate())
		self.end_date = end_date or get_year_ending(getdate())

	def create_payroll_period(self):
		try:
			payroll_period = frappe.get_doc(
				{
					"doctype": "Payroll Period",
					"__newname": f"{self.start_date} - {self.end_date}",
					"start_date": self.start_date,
					"end_date": self.end_date,
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
				}
			).insert()
		except frappe.DuplicateEntryError:
			payroll_period = frappe.get_doc("Payroll Period", f"{self.start_date} - {self.end_date}")

		return payroll_period


class DemoIncomeTaxSlab:
	def __init__(self, tax_slab_name: str = None, tax_slabs: list = None):
		self.tax_slab_name = tax_slab_name or "Demo Income Tax Slab"
		self.tax_slabs = tax_slabs or [
			{
				"from_amount": 250000,
				"to_amount": 500000,
				"percent_deduction": 5,
				"condition": "annual_taxable_earning > 500000",
			},
			{"from_amount": 500001, "to_amount": 1000000, "percent_deduction": 20},
			{"from_amount": 1000001, "percent_deduction": 30},
		]

	def create_income_tax_slab(self):
		try:
			tax_slab = frappe.get_doc(
				{
					"doctype": "Income Tax Slab",
					"__newname": self.tax_slab_name,
					"slabs": self.tax_slabs,
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
					"currency": "INR",
					"effective_from": get_year_start(getdate()),
					"standard_tax_exemption_amount": 50000,
				}
			).insert()
			tax_slab.submit()

		except frappe.DuplicateEntryError:
			tax_slab = frappe.get_doc("Income Tax Slab", self.tax_slab_name)

		return tax_slab
