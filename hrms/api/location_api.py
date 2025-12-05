import frappe

@frappe.whitelist()
def get_all_locations():
    try:
        docs = frappe.get_all(
            "Location",
            fields=["name", "reference_name", "latitude", "longitude", "radius", "parent_location"],
            ignore_permissions=True,   # ✅ optional: avoids "No Permission" error
        )
        return {"data": docs, "success": True}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Location - GetAll Error")
        frappe.local.response["http_status_code"] = 500
        return {"message": str(e), "success": False}