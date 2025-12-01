# Copyright (c) 2025, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class AssignInstallation(Document):
    def on_submit(self):

        new_installation = frappe.new_doc("Installation")

        new_installation.robot_classification = self.robot_classification
        new_installation.item_code = self.item_code
        new_installation.dispatch_no = self.name
        new_installation.hospital_name = self.hospital_name
        new_installation.date = nowdate()
        new_installation.status = "Assigned"

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

        for row in template_doc.instllation_steps:
            new_installation.append("installation_step_details", {
                "installation_steps": row.installation_steps
            })
            
        for row in template_doc.safety_check_and_precautions:
            new_installation.append("installation_step_details", {
                "safety_check_description": row.safety_check_description
            })

        new_installation.insert(ignore_permissions=True)

        return new_installation.name








@frappe.whitelist()
def create_assign_installation(doc):
    doc = frappe.parse_json(doc)

    new_assign_installation = frappe.new_doc("Assign Installation")
    new_assign_installation.robot_classification = doc.get("robot_classifcation")
    new_assign_installation.item_code = doc.get("item_code")
    new_assign_installation.dispatch_no = doc.get("name")
    new_assign_installation.hospital_name = doc.get("hospital_name")

    new_assign_installation.insert(ignore_permissions=True)  # Save the doc

    return new_assign_installation.name
