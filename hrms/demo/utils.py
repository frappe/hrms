import logging
import random
import threading

import frappe


class Batch:
	def __init__(
		self,
		no_of_records: int = 0,
		batch_size: int = 25000,
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
		threads = []

		while self.no_of_records > 0:

			if self.no_of_records < self.batch_size:
				self.batch_end = self.no_of_records
			else:
				self.batch_end = self.batch_start + self.batch_size

			try:
				batch_id = self.get_batch_id()
				thread = Thread(
					*[self.batch_start, self.batch_end],
					**{
						"method": self.method_to_enqueue,
						"batch_id": batch_id,
						"site": frappe.local.site,
						"on_success": self.on_success,
						"on_failure": self.on_failure,
					},
				)
				thread.start()
				threads.append(thread)

			except Exception as e:
				Log(e)

			self.batch_start = self.batch_end
			self.no_of_records -= self.batch_size

		for thread in threads:
			thread.join()

	def get_batch_id(self):
		return f"{self.method_to_enqueue}-{self.batch_start}-{self.batch_end}"


class Thread(threading.Thread):
	def __init__(self, *args, **kwargs):
		super().__init__(
			target=kwargs["method"], args=args, kwargs=kwargs, daemon=True, name=kwargs["batch_id"]
		)

		self.on_sucess = kwargs["on_success"]
		self.on_failure = kwargs["on_failure"]
		self.exc = None

	def run(self):
		try:
			self.ret = self._target(*self._args, **self._kwargs)
		except Exception as e:
			self.exc = e

	def join(self, timeout=None):
		super(Thread, self).join(timeout)
		if self.exc:
			if self.on_failure:
				self.on_failure(*self._args, **self._kwargs)
			raise self.exc

		if self.on_sucess:
			self._kwargs["result"] = self.ret
			self.on_sucess(*self._args, **self._kwargs)


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


# decorator
def initialize(func):
	"""
	decorator to initiate env in thread
	"""

	def _func(*args, **kwargs):
		frappe.init(site=kwargs["site"])
		frappe.connect()

		return func(*args)

	return _func
