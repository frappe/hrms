import frappe

# -------------------- GET ALL --------------------
@frappe.whitelist()
def get_all_lead():
    try:
        docs = frappe.get_all("Lead", fields=["*"], ignore_permissions=True)
        return {"success": True, "data": docs}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Lead - GetAll Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to fetch Lead records"}

# -------------------- CREATE --------------------
@frappe.whitelist()
def create_lead(**kwargs):
    try:
        doc = frappe.new_doc("Lead")
        for key, value in kwargs.items():
            doc.set(key, value)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "data": doc}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Lead - Create Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to create Lead"}

@frappe.whitelist()
def get_all_hospital():
    try:
        docs = frappe.get_all("Hospital", fields=["*"], ignore_permissions=True)
        return {"success": True, "data": docs}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Hospital - GetAll Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to fetch Hospital records"}

@frappe.whitelist()
def create_hospital(**kwargs):
    try:
        doc = frappe.new_doc("Hospital")
        for k, v in kwargs.items():
            doc.set(k, v)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "data": doc}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Hospital - Create Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to create Hospital"}

@frappe.whitelist()
def get_all_opportunity():
    try:
        docs = frappe.get_all("Opportunity", fields=["*"], ignore_permissions=True)
        return {"success": True, "data": docs}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Opportunity - GetAll Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to fetch Opportunity records"}

@frappe.whitelist()
def create_opportunity(**kwargs):
    try:
        doc = frappe.new_doc("Opportunity")
        for k, v in kwargs.items():
            doc.set(k, v)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "data": doc}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Opportunity - Create Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to create Opportunity"}

@frappe.whitelist()
def get_all_car():
    try:
        docs = frappe.get_all("CAR", fields=["*"], ignore_permissions=True)
        return {"success": True, "data": docs}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "CAR - GetAll Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to fetch CAR records"}

@frappe.whitelist()
def create_car(**kwargs):
    try:
        doc = frappe.new_doc("CAR")
        for k, v in kwargs.items():
            doc.set(k, v)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "data": doc}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "CAR - Create Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to create CAR"}


@frappe.whitelist()
def create_checkin_joureny(**kwargs):
    try:
        doc = frappe.new_doc("CheckIn Journey")
        for k, v in kwargs.items():
            doc.set(k, v)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {"success": True, "data": doc}
    except Exception:
        frappe.log_error(frappe.get_traceback(), "CheckIn Journey - Create Error")
        frappe.local.response["http_status_code"] = 500
        return {"success": False, "message": "Failed to create CheckIn Journey"}
