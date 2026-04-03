import frappe

def execute():
    if not frappe.db.exists(
        "Custom Field",
        {
            "dt": "Manufacturing Settings",
            "fieldname": "custom_auto_create_mr"
        }
    ):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Manufacturing Settings",
            "label": "Auto Create MR",
            "fieldname": "custom_auto_create_mr",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "material_request_type"
        }).insert(ignore_permissions=True)

    frappe.db.commit()
