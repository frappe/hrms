from unittest.mock import patch

from frappe.tests import UnitTestCase

from hrms.api import get_holidays_for_employee


class TestApi(UnitTestCase):
	def test_holidays_for_employee_uses_current_holiday_list(self):
		with patch("hrms.api.get_holiday_list_for_employee", return_value=None) as get_holiday_list:
			get_holidays_for_employee("_Test Employee")

		get_holiday_list.assert_called_once_with("_Test Employee", raise_exception=False)
