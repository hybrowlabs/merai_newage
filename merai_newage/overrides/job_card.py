import frappe
from erpnext.manufacturing.doctype.job_card.job_card import JobCard

class CustomJobCard(JobCard):
    def before_submit(self):
        if not self.quality_inspection:
            frappe.throw("Please create and submit a Quality Inspection before submitting the Job Card.")

        qi_doc = frappe.get_doc("Quality Inspection", self.quality_inspection)

        if qi_doc.docstatus != 1:
            frappe.throw(f"Quality Inspection {qi_doc.name} must be submitted before submitting the Job Card.")

        super().before_submit()