# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class AssignInstallation(Document):
    def on_submit(self):
        dispatch_doc=frappe.get_doc("Dispatch",self.dispatch_no)
        new_installation = frappe.new_doc("Installation")

        new_installation.robot_classification = self.robot_classification
        new_installation.item_code = self.item_code
        new_installation.dispatch_no = self.name
        new_installation.hospital_name = self.hospital_name
        new_installation.date = nowdate()
        new_installation.installation_status = "Assigned"
        new_installation.assign_installation = self.name
        new_installation.work_order = self.work_order
        new_installation.hospital_address = frappe.db.get_value("Account Master",dispatch_doc.hospital_name,"address")


        item_group = frappe.db.get_value("Item", self.item_code, "item_group")
        template_name = frappe.db.get_value(
            "Item Group",
            item_group,
            "custom_installtion_procedure__verification_template"
        )

        if not template_name:
            frappe.throw("No Installation Template linked to Item Group")

        template_doc = frappe.get_doc(
            "Installation Procedure And Verification Template",
            template_name
        )
        new_installation.description=template_doc.system_electrical_ratings

        for row in template_doc.instllation_steps:
            new_installation.append("installation_step_details", {
                "installation_steps": row.installation_steps
            })
            
        for row in template_doc.safety_check_and_precautions:
            new_installation.append("safety_check_and_precautions", {
                "safety_steps":row.safety_check
            })
        
        for row in template_doc.performance_checks:
            new_installation.append("performance_check_details", {
                "performance_check":row.performance_check
            })
        
        for row in dispatch_doc.dispatch_standard_checklist:
            new_installation.append('system_packaging_list',{
                "item":row.product_code,
                "qty":row.std_qty
            })
            new_installation.append('instrument_tray_list',{
                "product_code":row.product_code,
                "product_description":frappe.db.get_value("Item",row.product_code,"description"),
                "stdqty":row.std_qty,
                "batch_no":row.batch_no
            })

        

        new_installation.insert(ignore_permissions=True)
        update_robot_tracker(self)
        create_todo_for_engineer(self, new_installation.name)

        return new_installation.name




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
        new_row.doctype_name="Assign Installation"
        new_row.robot_status = "Engineer Assigned"
        tracker.robot_status = "Engineer Assigned"

        tracker.save(ignore_permissions=True)
        frappe.db.commit()
import frappe
from frappe.utils import nowdate

def create_todo_for_engineer(assign_doc, installation_name):
    if not assign_doc.engineer_name:
        frappe.throw("Assigned Engineer is not selected!")

    user_id = frappe.db.get_value(
        "Employee",
        assign_doc.engineer_name,
        "user_id"
    )

    if not user_id:
        frappe.throw("Selected Engineer is not linked to a User account!")

    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": f"Complete Installation: {installation_name}",
        "reference_type": "Installation",
        "reference_name": installation_name,
        "assigned_by": frappe.session.user,
        "owner": user_id,
        "allocated_to": user_id,
        "status": "Open",
        "date": nowdate()
    })
    todo.insert(ignore_permissions=True)
    frappe.db.commit()

    frappe.get_doc({
        "doctype": "Notification Log",
        "subject": "New Installation Assigned",
        "email_content": f"You have been assigned a new Installation task: {installation_name}",
        "for_user": user_id,
        "type": "Alert",
        "document_type": "Installation",
        "document_name": installation_name,
    }).insert(ignore_permissions=True)



@frappe.whitelist()
def create_assign_installation(doc):
    doc = frappe.parse_json(doc)

    new_assign_installation = frappe.new_doc("Assign Installation")
    new_assign_installation.robot_classification = doc.get("robot_classifcation")
    new_assign_installation.item_code = doc.get("item_code")
    new_assign_installation.dispatch_no = doc.get("name")
    new_assign_installation.hospital_name = doc.get("hospital_name")
    new_assign_installation.work_order = doc.get("work_order")
    new_assign_installation.hospital_address = frappe.db.get_value("Account Master",doc.hospital_name,"address")
    new_assign_installation.city = frappe.db.get_value("Account Master",doc.hospital_name,"city")
    new_assign_installation.state = frappe.db.get_value("Account Master",doc.hospital_name,"state")

    new_assign_installation.insert(ignore_permissions=True)  # Save the doc

    return new_assign_installation.name
