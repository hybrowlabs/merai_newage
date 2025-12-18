# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RobotTracker(Document):
	pass


import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def create_robot_tracker(doc, method=None):
    # Convert Document → dict safely
    if not isinstance(doc, dict):
        doc = doc.as_dict()

    wo_name = doc.get("name")
    print("-----is full dhr",doc.get("custom_is_full_dhr"))
    if doc.get("custom_is_full_dhr"):
        existing_rt = frappe.db.get_value(
            "Robot Tracker",
            {"work_order": wo_name},
            "name"
        )

        if existing_rt:
            rt = frappe.get_doc("Robot Tracker", existing_rt)
            print("batch====",doc.get("custom_batch"))
            rt.batch_number = doc.get("custom_batch")
            rt.batch_no = doc.get("custom_batch_number")
            rt.date = doc.get("planned_start_date")
            rt.item_code = doc.get("production_item")
            rt.document_no = doc.get("name")
            rt.batch_no= doc.get('custom_batch_number')


            rt.robot_tracker_details = []

            # Add 1 updated row
            row = rt.append("robot_tracker_details", {})
            row.document_no = doc.get("name")
            row.location = doc.get("company")
            row.date = nowdate()
            row.robot_status = "Manufactured"
            row.doctype_name="Work Order"
            rt.robot_status = "Manufactured"
            rt.save(ignore_permissions=True)
            frappe.db.commit()

            return rt.name

        rt = frappe.new_doc("Robot Tracker")
        rt.work_order = wo_name
        rt.batch_number = doc.get("custom_batch")
        rt.date = doc.get("planned_start_date")
        rt.item_code = doc.get("production_item")
        rt.document_no = doc.get("name")
        rt.batch_no= doc.get('custom_batch_number')
        if doc.custom_manual_batch_no==1:
            rt.batch_number = frappe.db.get_value("Batch",{"item":doc.production_item,"custom_batch_number":doc.custom_batch_number},"name")

             

        row = rt.append("robot_tracker_details", {})
        row.document_no = doc.get("name")
        row.location = doc.get("company")
        row.date = doc.get("planned_start_date")
        row.robot_status = "Manufactured"
        row.doctype_name="Work Order"
        rt.robot_status = "Manufactured"

        rt.save(ignore_permissions=True)
        frappe.db.commit()

        return rt.name
