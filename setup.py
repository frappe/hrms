from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in hrms/__init__.py
from hrms import __version__ as version

setup(
	name="hrms",
	version=version,
	description="Modern HR and Payroll Software",
	author="Frappe",
	author_email="contact@frappe.io",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires,
)
