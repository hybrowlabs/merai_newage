# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class Dispatch(Document):
    def on_submit(self):
        robot_tracker_name = frappe.db.get_value(
            "Robot Tracker",
            {
                "document_no": self.get("work_order"),
            },
            "name"
        )

        if not robot_tracker_name:
            frappe.msgprint("Robot Tracker not found for this Work Order")
            return
        

        tracker = frappe.get_doc("Robot Tracker", robot_tracker_name)
        tracker.robot_classification = self.robot_classifcation
        new_row = tracker.append("robot_tracker_details", {})
        new_row.document_no = self.name
        new_row.date = nowdate()
        new_row.location = self.hospital_name
        new_row.robot_status = "Dispatched"
        new_row.doctype_name="Dispatch"
        tracker.robot_status = "Dispatched"
        tracker.save(ignore_permissions=True)
        frappe.db.commit()

        
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
        print("=======================")
        new_row.product_description = frappe.db.get_value("Item",row.product_name,"description")
    

    dispatch_doc.save(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def update_dispatch_details(doc):
    doc = frappe.parse_json(doc)
    batch_no = doc.get("batch_no")

    std_batch_no = frappe.db.get_value("Batch", {"name": batch_no}, "custom_batch_number")

    wo = None

    batch_wo = frappe.db.get_value("Batch", {"name": batch_no}, "custom_work_order")
    if batch_wo:
        wo = batch_wo
    else:
        wo = frappe.db.get_value("Work Order", {"custom_batch": batch_no}, "name")

        if not wo:
            wo = frappe.db.get_value("Work Order", {"custom_batch_number": std_batch_no}, "name")

    if not wo:
        return {
            "work_order": None,
            "items": []
        }

    job_cards = frappe.db.sql("""
        SELECT opd.item_code, opd.batch_number
        FROM `tabJob Card Opeartion Deatils` opd
        LEFT JOIN `tabJob Card` jc ON opd.parent = jc.name
        WHERE jc.work_order = %s
    """, (wo,), as_dict=True)
    updated_rows = [{
        "product_code": jc.item_code,
        "batch_no": jc.batch_number,
        "description":frappe.db.get_value("Item",jc.item_code,"description"),
        "qty":frappe.db.get_value("Work Order",jc.work_order,"qty")
    } for jc in job_cards]

    return {
        "work_order": wo,
        "items": updated_rows,
        "std_batch_no": std_batch_no
    }


@frappe.whitelist()
def get_used_batch_numbers():
    return [row[0] for row in frappe.db.sql("""
        SELECT batch_no 
        FROM `tabDispatch` 
        WHERE batch_no IS NOT NULL AND batch_no != ''
    """, as_list=1)]

@frappe.whitelist()
def get_available_batches(doctype, txt, searchfield, start, page_len, filters):
    filters = frappe.parse_json(filters)
    item_code = filters.get("item_code")
    exclude = tuple(filters.get("exclude_batches") or [""])

    return frappe.db.sql("""
        SELECT name, name
        FROM `tabBatch`
        WHERE item = %(item)s
        AND name NOT IN %(exclude)s
        AND name LIKE %(txt)s
        ORDER BY creation DESC
        LIMIT %(start)s, %(page_len)s
    """, {
        "item": item_code,
        "exclude": exclude,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })
