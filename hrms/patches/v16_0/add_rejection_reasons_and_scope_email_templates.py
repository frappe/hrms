from hrms.hr.doctype.rejection_reason.rejection_reason import create_default_reasons
from hrms.setup import create_hiring_email_templates, setup_email_template_scopes


def execute():
	create_default_reasons()
	setup_email_template_scopes()
	create_hiring_email_templates()
