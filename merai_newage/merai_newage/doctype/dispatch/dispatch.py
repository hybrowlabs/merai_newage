# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Dispatch(Document):
	pass
@frappe.whitelist()
def set_values_in_checklist(name):
    dispatch_doc = frappe.get_doc("Dispatch", name)

    if not dispatch_doc.item_code:
        frappe.throw("Item Code is not set in Dispatch document.")

    item_doc = frappe.get_doc("Item", dispatch_doc.item_code)

    dispatch_doc.dispatch_standard_checklist = []

    for row in item_doc.custom_dispatch_checklist_details:
        new_row = dispatch_doc.append("dispatch_standard_checklist", {})
        new_row.product_name = row.product_name
        new_row.product_description = row.product_description

    dispatch_doc.save(ignore_permissions=True)
    frappe.db.commit()

    # return f"Copied {len(item_doc.custom_dispatch_checklist_details)} checklist rows from Item {item_doc.name}."
