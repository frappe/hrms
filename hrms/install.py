import click

from hrms.setup import after_install as setup


def before_install():
	from frappe.utils.connections import check_connection

	service_status = check_connection(redis_services=["redis_cache"])
	are_services_running = all(service_status.values())

	if not are_services_running:
		for service in service_status:
			if not service_status.get(service, True):
				click.secho(f"Service {service} is not running.", fg="red")

		click.secho("Please ensure that the server is running before installing HRMS.", fg="red")
		click.secho("See: https://github.com/frappe/hrms/issues/369#issuecomment-1463632514", fg="red")
		raise click.Abort()


def after_install():
	try:
		print("Setting up Frappe HR...")
		setup()

		click.secho("Thank you for installing Frappe HR!", fg="green")

	except Exception as e:
		BUG_REPORT_URL = "https://github.com/frappe/hrms/issues/new"
		click.secho(
			"Installation for Frappe HR app failed due to an error."
			" Please try re-installing the app or"
			f" report the issue on {BUG_REPORT_URL} if not resolved.",
			fg="bright_red",
		)
		raise e
