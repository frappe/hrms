import frappe

def get_context(context):
	context.parents = [{"name": frappe._("My Account"), "route": "/"}]
