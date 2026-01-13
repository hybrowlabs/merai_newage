# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TicketTaskMaster(Document):
	pass

@frappe.whitelist()
def create_ticket_task(doc):
    doc = frappe.parse_json(doc)
    new_task = frappe.new_doc("Ticket Task Master")
    new_task.robot_serial_no = doc.get("robot_serial_no")
    new_task.issue_type = doc.get("issue_type")
    new_task.hospital_name = doc.get("hospital_name")
    new_task.issue_reported = doc.get("issue_reported")
    new_task.system_admin_remarks = doc.get("system_admin_remarks")
    new_task.ticket_master_reference = doc.get("name")
   
    new_task.insert(ignore_permissions=True)  

    return new_task.name
