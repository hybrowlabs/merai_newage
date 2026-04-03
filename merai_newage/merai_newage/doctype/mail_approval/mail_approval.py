# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


# class MailApproval(Document):
# 	pass






import frappe
from frappe.model.document import Document
import base64
import requests

class MailApproval(Document):
    def validate(self):
        if self.workflow_state == "Approved":
            if not self.company or not self.year:
                frappe.throw("Please select Company and Year before approving.")

            files = frappe.get_all(
                "File",
                filters={
                    "attached_to_doctype": "Mail Approval",
                    "attached_to_name": self.name
                },
                fields=["file_url"]
            )

            # Filter PDF files with None check
            pdf_files = [f["file_url"] for f in files if f.get("file_url") and f["file_url"].lower().endswith(".pdf")]

            if not pdf_files:
                frappe.throw("No PDF file found in attachments. Please attach a PDF invoice before approving.")

            try:
                invoice = frappe.new_doc("Purchase Booking Request")
                invoice.company = self.company
                invoice.year = self.year
                invoice.mail_approval_reference = self.name
                invoice.upload_file = pdf_files[0]

                # Using ignore_permissions as this is a system-triggered workflow action
                invoice.insert(ignore_permissions=True)
            except Exception as e:
                frappe.throw(f"Failed to create Purchase Booking Entry: {str(e)}")


def create_mail_approval_from_email(doc, method=None):
    if doc.sent_or_received != "Received":
        return

    # Check if Mail Approvals already exist for this communication
    if frappe.db.exists("Mail Approval", {"communication_link": doc.name}):
        return

    try:
        enqueue_create_mail_approval(doc.name)
    except Exception as e:
        frappe.log_error(f"Failed to create Mail Approval from email: {str(e)}", "Mail Approval Creation Error")

def enqueue_create_mail_approval(doc_name):
    """Create Mail Approval records - one for each PDF attachment from Communication."""
    doc = frappe.get_doc("Communication", doc_name)

    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Communication",
            "attached_to_name": doc.name
        },
        fields=["name", "file_url"]
    )

    pdf_files = [f for f in files if f.get("file_url") and f["file_url"].lower().endswith(".pdf")]

    if not pdf_files:
        return

    # Create a separate Mail Approval for each PDF attachment
    for pdf_file in pdf_files:
        mail_approval = frappe.new_doc("Mail Approval")
        mail_approval.email_subject = doc.subject
        mail_approval.from_email = doc.sender
        mail_approval.received_date = doc.creation
        mail_approval.message = doc.content
        mail_approval.communication_link = doc.name
        mail_approval.status = "Pending"
        mail_approval.attachment = pdf_file["file_url"]

        mail_approval.insert(ignore_permissions=True)

    frappe.db.commit()