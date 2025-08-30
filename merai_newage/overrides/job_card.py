import frappe
from erpnext.manufacturing.doctype.job_card.job_card import JobCard

class CustomJobCard(JobCard):
    def before_submit(self):
        # is_qi_reqd = frappe.db.get_value("Opeartion",self.operation,"custom_quality_inspection_required")
        is_qi_reqd = frappe.db.get_value(
            "Operation", 
            self.operation,  # assuming self.operation stores Operation name
            "custom_quality_inspection_required"
        )

        # print("is_qi_reqd========7===",is_qi_reqd)
        if is_qi_reqd:
            if not self.quality_inspection:
                frappe.throw("Please create and submit a Quality Inspection before submitting the Job Card.")

            qi_doc = frappe.get_doc("Quality Inspection", self.quality_inspection)

            if qi_doc.docstatus != 1:
                frappe.throw(f"Quality Inspection {qi_doc.name} must be submitted before submitting the Job Card.")

        # super().before_submit()