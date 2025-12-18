# create accounting_dimension_section and dimension_col_break
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_accounting_dimension_section():
    fields = {
        "Employee" : [
            {
                "fieldname" : "accounting_dimensions_section",
                "fieldtype" : "Section Break",
                "label" : "Accounting Dimensions",
                "insert_after" : "iban"
            },
            {
                "fieldname": "dimension_col_break",
                "fieldtype": "Column Break",
                "insert_after" : "accounting_dimensions_section"
            },
           ]
    }
    create_custom_fields(fields)

def execute():
    create_accounting_dimension_section()