import frappe
from frappe.utils import now_datetime, cint, get_year_ending, get_year_start, getdate


class Setup:
	def __init__(self):
		self.holiday_list = None
		self.payroll_period = None

	@classmethod
	def prerequisites(cls):
		year = now_datetime().year

		cls.complete_setup_wizard(year)
		cls.holiday_list(year)
		cls.create_payroll_period()

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
	def holiday_list(cls, year):
		hl = HolidayList()
		cls.holiday_list = hl.create_holiday_list(year)
		HolidayList.update_holiday_list_on_company(cls.holiday_list)

	@classmethod
	def create_payroll_period(cls):
		pp = PayrollPeriod()
		cls.payroll_period = pp.create_payroll_period()


class HolidayList:
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

	def create_holiday_list(cls, holiday_list_name: str = None):
		_holiday_list = frappe.db.get_value("Holiday List", holiday_list_name, "name")

		if not _holiday_list:
			_holiday_list_doc = frappe.get_doc(
				{
					"doctype": "Holiday List",
					"holiday_list_name": holiday_list_name,
					"from_date": cls().start_date,
					"to_date": cls().end_date,
					"holidays": cls().get_holidays(),
					"company": frappe.db.get_single_value("Global Defaults", "default_company"),
				}
			).insert()
			_holiday_list = _holiday_list_doc.name

		cls._holiday_list = _holiday_list

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
		frappe.db.commit()


class PayrollPeriod:
	def __init__(self, start_date: str = None, end_date: str = None):
		self.start_date = start_date or get_year_start(getdate())
		self.end_date = end_date or get_year_ending(getdate())

	def create_payroll_period(self):
		payroll_period = frappe.get_doc(
			{
				"doctype": "Payroll Period",
				"__newname": f"{self.start_date} - {self.end_date}",
				"start_date": self.start_date,
				"end_date": self.end_date,
				"company": frappe.db.get_single_value("Global Defaults", "default_company"),
			}
		).insert()

		return payroll_period
