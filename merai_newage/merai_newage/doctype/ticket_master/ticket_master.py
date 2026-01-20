# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate

class TicketMaster(Document):
    def before_save(self):
        if self.workflow_state == "Issue Resolved":
            if not self.date_of_issue_resolved:
                self.date_of_issue_resolved = nowdate()

    def on_update(self):
        if not self.workflow_state:
            return

        old_doc = self.get_doc_before_save()
        old_state = old_doc.workflow_state if old_doc else None

        if old_state != self.workflow_state:
            if self.workflow_state == "Pending From Master Admin":
                if not self.get("_notified_master_admin"):
                    self.notify_master_admins()
                    self._notified_master_admin = True

            if self.workflow_state=="Received Material":
                if not self.get("_notified_store_team"):
                    self.notify_store_team_material()
                    self._notified_store_team = True
            if self.workflow_state=="Resolved":
                if not self.get("_notified_on_field_engineer_after_issue_resolved"):
                    self._notified_on_field_engineer_after_issue_resolved=True
                    self.notify_on_field_engineer_after_resolve()
        if self.workflow_state=="Issue Resolved":
            print("----date of issue re")
            if not self.get("_notified_admin_after_issue_resolved"):
                self._notified_admin_after_issue_resolved = True
                self.notify_master_admins_after_issue_resolved()

    def after_save(self):

        if self.workflow_state == "Pending From Backend Team":

            if not self.get("_notified_backend_engineer"):
                
                self.notify_assigned_engineer()
                self._notified_backend_engineer = True
            


    def notify_master_admins(self):
        users = frappe.get_all(
            "Has Role",
            filters={"role": "Master Admin"},
            pluck="parent"
        )

        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )
        raised_by = frappe.db.get_value("Employee",self.raised_by,"employee_name")
        department = frappe.db.get_value("Employee",self.raised_by,"department")

        subject = f"Ticket Pending for Review - {self.name}"
        message = f"""
        <p>Dear Team,</p>
        <p>A new service ticket has been raised.</p>
        <b>Ticket Details:</b> <br>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hospital Name:</b> {self.hospital_name} <br>
        <b>Issue:</b> {self.ticket_subject}<br>
        <b>Issue Reported:</b> {self.issue_reported}<br>
        <b>Raised By:</b> {raised_by} ({self.raised_by})<br>
        <b>Department:</b> {department}<br>

        <b>Date & Time:</b> {self.ticket_date_and_time}<br>
        <p>Kindly review the ticket and proceed further.</p> <br>

        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """

        for user in users:
            frappe.sendmail(
                recipients=user,
                subject=subject,
                message=message
            )

            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)
    
    def notify_software_team(self):
        # employee_list = self.software_team_engineer
        users = []

        for row in self.software_team_engineer:
            user = frappe.db.get_value(
                "Employee",
                row.software_engineer,
                "user_id"
            )
            if user:
                users.append(user)

        ticket_task = "Ticket Task Master"
        doc_url = frappe.utils.get_url_to_form(
            ticket_task,
            self.task_id
        )
        raised_by = frappe.db.get_value("Employee",self.raised_by,"employee_name")
        department = frappe.db.get_value("Employee",self.raised_by,"department")

        subject = f"Service Ticket Assigned - {self.name}"
        message = f"""
        <p>Dear Team,</p>
        <p>The following service ticket has been reviewed and assigned</p>
        <b>Ticket Details:</b> <br>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hospital Name:</b> {self.hospital_name} <br>
        <b>Issue:</b> {self.ticket_subject}<br>
        <b>Issue Reported:</b> {self.issue_reported}<br>
        <b>Issue Type:</b> {self.issue_type}<br>
        <b>Raised By:</b> {raised_by} ({self.raised_by})<br>
        <b>Department:</b> {department}<br>

        <b>Date & Time:</b> {self.ticket_date_and_time}<br>
        <p>Kindly review the ticket and proceed further.</p> <br>

        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """

        for user in users:
            frappe.sendmail(
                recipients=user,
                subject=subject,
                message=message
            )

            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)

    def notify_master_admins_after_issue_resolved(self):
        users = frappe.get_all(
            "Has Role",
            filters={"role": "Master Admin"},
            pluck="parent"
        )

        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )
        raised_by = frappe.db.get_value("Employee",self.raised_by,"employee_name")
        department = frappe.db.get_value("Employee",self.raised_by,"department")
        subject = f"Ticket Resolved - {self.name}"
        message = f"""
        <p>Dear Team,</p>
        <p>Ticket with Id {self.name} was resolved Thank You for your Co-operation.</p>
        <b>Ticket Details:</b> <br>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hospital Name:</b> {self.hospital_name} <br>
        <b>Issue:</b> {self.ticket_subject}<br>
        <b>Issue Reported:</b> {self.issue_reported}<br>
        <b>Raised By:</b> {raised_by} ({self.raised_by})<br>
        <b>Department:</b> {department}<br>

        <b>Date & Time:</b> {self.ticket_date_and_time}<br> <br>
        
        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """

        for user in users:
            frappe.sendmail(
                recipients=user,
                subject=subject,
                message=message
            )

            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)

    def notify_assigned_engineer(self):

        if not self.assign_engineer:
            return

        user = frappe.db.get_value(
            "Employee",
            self.assign_engineer,
            "user_id"
        )

        if not user:
            return
        ticket_task = "Ticket Task Master"
        doc_url = frappe.utils.get_url_to_form(
            ticket_task,
            self.task_id
        )

        subject = f"Service Ticket Assigned - {self.name}"
        message = f"""
        <p>Dear Team,</p>
        <p>The following service ticket has been reviewed and assigned.</p>
        <b>Ticket Details:</b> <br>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hospital Name:</b> {self.hospital_name} <br>

        <b>Issue Type:</b> {self.issue_type}<br>
        <b>Remarks:</b> {self.system_admin_remarks}<br>
        <p>Please initiate the required actions at the earliest and update the ticket status accordingly.</p>
        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """
        
        frappe.sendmail(
            recipients=user,
            subject=subject,
            message=message
        )

        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "for_user": user,
            "type": "Alert",
            "document_type": self.doctype,
            "document_name": self.name
        }).insert(ignore_permissions=True)

    def notify_store_team_material(self):

        users = frappe.get_all(
            "Has Role",
            filters={"role": "Store Team"},
            pluck="parent"
        )

        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )

        items_html = """
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
            <tr style="background:#f2f2f2;">
                <th>Item Code</th>
                <th>Item Name</th>
                <th>Qty</th>
            </tr>
        """

        for row in self.received_materials:
            items_html += f"""
            <tr>
                <td>{row.item}</td>
                <td>{row.item_name}</td>
                <td>{row.qty}</td>
            </tr>
            """

        items_html += "</table>"

        subject = f"Received Materials from Store Team for Ticket - {self.name}"

        message = f"""
        <p>Dear Team,</p>
        <p>This is to confirm that the material for the below service ticket has been received</p>
        <b>Ticket Details:</b>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial Number:</b> {self.robot_serial_no}<br>
        <b>Hosiptal Name:</b> {self.hospital_name}<br>
        <b>Docket Number:</b> {self.docket_number}<br>
        <b>Date of Receipt:</b> {self.date_of_receipt}<br>


        <b>Received Items:</b><br><br>
        {items_html}<br><br>

        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """

        for user in users:
            frappe.sendmail(
                recipients=user,
                subject=subject,
                message=message
            )

            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)

    @frappe.whitelist()
    def send_backend_notification(self):
        """Send notification to backend engineer after task_id is set"""
        if self.workflow_state == "Pending From Backend Team" and self.task_id:
            if self.issue_type=="Software":
                    self.notify_software_team()
            self.notify_assigned_engineer()
            return {"success": True}
        
        return {"success": False, "message": "Task ID not set or wrong workflow state"}
    
    def notify_on_field_engineer_after_resolve(self):

        if not self.raised_by:
            return

        user = frappe.db.get_value(
            "Employee",
            self.raised_by,
            "user_id"
        )

        if not user:
            return
        ticket_task = "Ticket Master"
        doc_url = frappe.utils.get_url_to_form(
            ticket_task,
            self.task_id
        )

        subject = f"Ticket - {self.name} has been  Resolved"
        message = f"""
        <p>Dear Team,</p>
        <p>The following service ticket has been resolved and closed.</p>
        <b>Ticket Details:</b> <br>
        <b>Ticket ID:</b> {self.name}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hospital Name:</b> {self.hospital_name} <br>
        <b>Issue Type:</b> {self.issue_type}<br>
        <b>Remarks:</b> {self.system_admin_remarks}<br>
        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """
        
        frappe.sendmail(
            recipients=user,
            subject=subject,
            message=message
        )

        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": subject,
            "for_user": user,
            "type": "Alert",
            "document_type": self.doctype,
            "document_name": self.name
        }).insert(ignore_permissions=True)


