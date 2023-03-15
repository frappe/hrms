import logging
import random

import frappe


class Batch:
	def __init__(
		self,
		no_of_records: int = 0,
		batch_size: int = 100,
		method: str = None,
		on_success: str = None,
		on_failure: str = None,
	):
		self.batch_size = batch_size
		self.no_of_records = no_of_records
		self.method_to_enqueue = method
		self.batch_start = 0
		self.batch_end = 0
		self.on_success = on_success
		self.on_failure = on_failure

	def set_batch(self):
		while self.no_of_records > 0:

			if self.no_of_records < self.batch_size:
				self.batch_end = self.no_of_records
			else:
				self.batch_end = self.batch_start + self.batch_size

			try:

				batch_id = self.get_batch_id()
				frappe.call(self.method_to_enqueue, *[self.batch_start, self.batch_end])
				frappe.call(self.on_success, *[batch_id])

			except Exception as e:
				Log(e)
				frappe.call(self.on_failure, *[batch_id])

			self.batch_start = self.batch_end
			self.no_of_records -= self.batch_size

	def get_batch_id(self):
		return f"{self.method_to_enqueue}-{self.batch_start}-{self.batch_end}"


class Date:
	@staticmethod
	def get_random_date():
		start_date = "1980-01-01"
		random_no = random.randint(0, 15)

		return frappe.utils.add_to_date(start_date, years=random_no, months=random_no, days=random_no)

	@staticmethod
	def add_years(date, years):
		return frappe.utils.add_to_date(date, years=years)


# logging
format = "%(asctime)s: %(message)s"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")


class Log:
	def __init__(self, message) -> None:
		logging.info(message)
