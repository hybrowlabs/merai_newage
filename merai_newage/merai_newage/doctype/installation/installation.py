# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Installation(Document):
	pass


@frappe.whitelist()
def get_safety_check_items(safety_steps):
    # Get master record
    doc = frappe.get_doc("Safety Check List Master", safety_steps)

    items = []
    for d in doc.safety_check_details:
        items.append({
            "check_name": d.check_name,   # adjust fieldnames if different
            "options": d.options if hasattr(d, "options") else "Yes\nNo"
        })

    return items



# @frappe.whitelist()
# def get_performance_items(performance_check):
#     # Get master record
#     doc = frappe.get_doc("Safety Check List Master", performance_check)

#     items = []
#     for d in doc.safety_check_details:
#         items.append({
#             "check_name": d.check_name,   # adjust fieldnames if different
#             "options": d.options if hasattr(d, "options") else "Yes\nNo"
#         })

#     return items
