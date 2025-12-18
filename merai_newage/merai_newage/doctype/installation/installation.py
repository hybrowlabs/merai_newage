# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class Installation(Document):

    def validate(self):
        self.set_print_format_from_item_group()
   
    def set_print_format_from_item_group(self):
        if self.item_group:
            installation_print_format = frappe.db.get_value(
                "Item Group",
                self.item_group,
                "custom_installation_print_format"
            )

            if installation_print_format:
                self.custom_print_format = installation_print_format
            else:
                self.custom_print_format = None     
	
    def on_submit(self):
            update_robot_tracker(self)


def update_robot_tracker(self):
        robot_tracker_name = frappe.db.get_value(
            "Robot Tracker",
            {
                "document_no": self.get("work_order"),
                # "batch_number": self.batch_no
            },
            "name"
        )

        if not robot_tracker_name:
            frappe.msgprint("Robot Tracker not found for this Work Order & Batch No.")
            return
        

        tracker = frappe.get_doc("Robot Tracker", robot_tracker_name)

        new_row = tracker.append("robot_tracker_details", {})
        new_row.document_no = self.name
        new_row.date = nowdate()
        new_row.location = self.hospital_name
        new_row.robot_status = "Installed"
        new_row.doctype_name="Installation"
        tracker.robot_status = "Installed"

        tracker.save(ignore_permissions=True)
        frappe.db.commit()

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
