import frappe


def execute():
	FnF = frappe.qb.DocType("Full and Final Asset")
	frappe.qb.update(FnF).set(FnF.action, "Return").where((FnF.action.isnull()) | (FnF.action == "")).run()
