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

    def before_submit(self):
        if self.task_id:
            task_status = frappe.db.get_value("Ticket Task Master",self.task_id,"docstatus")
            if task_status==0:
                frappe.throw(f"Please Resolve Ticket Task {self.task_id}")

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
                
                self.notify_backend_team()
                self._notified_backend_engineer = True
    def before_save(self):
        prev_doc = self.get_doc_before_save()
        prev_state = prev_doc.workflow_state if prev_doc else None

        if prev_state == "Pending From Master Admin":
            if self.workflow_state == "Resolved":
                # Bypass all mandatory — only remarks will be checked in validate
                self.flags.ignore_mandatory = True
            
            # If Assign Engineer — do nothing, let normal mandatory checks run

    def validate(self):
        prev_doc = self.get_doc_before_save()
        prev_state = prev_doc.workflow_state if prev_doc else None

        if prev_state == "Pending From Master Admin":
            if self.workflow_state == "Resolved":
                # Only remarks is mandatory
                if not self.system_admin_remarks:
                    frappe.throw("System Admin Remarks is mandatory when closing the ticket.")
        
        # If Assign Engineer — Frappe handles mandatory normally (ignore_mandatory not set)
    def notify_master_admins(self):
        doc_url = frappe.utils.get_url_to_form(self.doctype, self.name)

        # ─── Employee details ──────────────────────────────────────────────────
        raised_by_data = frappe.db.get_value(
            "Employee", self.raised_by,
            ["employee_name", "reports_to", "department", "user_id"],
            as_dict=True
        ) or {}

        raised_by = raised_by_data.get("employee_name") or self.raised_by
        manager_of_raiser = raised_by_data.get("reports_to")
        department = raised_by_data.get("department")
        raised_by_user_id = raised_by_data.get("user_id")
        print("rasied by ---",raised_by_user_id,"manager_of_raiser=======",manager_of_raiser)
        # ─── Collect all recipients ────────────────────────────────────────────
        recipients = []
        notify_users = []  # for notification logs

        # Master Admins
        admin_users = frappe.get_all(
            "Has Role",
            filters={"role": "Master Admin"},
            pluck="parent"
        )
        for user in admin_users:
            email = frappe.db.get_value("User", user, "email")
            if email:
                recipients.append(email.strip())
                notify_users.append(user)

        # Raised By
        if raised_by_user_id:
            email = frappe.db.get_value("User", raised_by_user_id, "email")
            if email:
                recipients.append(email.strip())
                notify_users.append(raised_by_user_id)

        # Manager
        manager_name = None
        if manager_of_raiser:
            manager_data = frappe.db.get_value(
                "Employee", manager_of_raiser,
                ["employee_name", "user_id"],
                as_dict=True
            ) or {}
            manager_name = manager_data.get("employee_name") or manager_of_raiser
            if manager_data.get("user_id"):
                email = frappe.db.get_value("User", manager_data.get("user_id"), "email")
                if email:
                    recipients.append(email.strip())
                    notify_users.append(manager_data.get("user_id"))

        # Remove duplicates
        recipients = list(set(recipients))
        notify_users = list(set(notify_users))

        if not recipients:
            frappe.logger().warning(f"No recipients found for {self.name}")
            return

        # ─── Single email to all ───────────────────────────────────────────────
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
            <b>Department:</b> {department or 'N/A'}<br>
            <b>Date & Time:</b> {self.ticket_date_and_time}<br>
            <p>Kindly review the ticket and proceed further.</p>
            <a href="{doc_url}"
            style="background:#007bff;color:#fff;
                    padding:10px 15px;
                    text-decoration:none;
                    border-radius:5px;">
                Open Ticket
            </a>
        """

        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )

        # ─── Notification logs for all users ──────────────────────────────────
        for user in notify_users:
            if user == "Administrator":
                continue
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
        raised_by_user = frappe.db.get_value(
            "Employee",
            self.raised_by,
            "user_id"
        )

        if raised_by_user and raised_by_user not in users:
            users.append(raised_by_user)
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
        <b>Priorty:</b> {self.priorty} <br>

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
            if user == "Administrator":
                continue
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
            if user == "Administrator":
                continue
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

    def notify_backend_team(self):
        # employee_list = self.software_team_engineer
        users = []

        for row in self.backend_team_engineer:
            user = frappe.db.get_value(
                "Employee",
                row.software_engineer,
                "user_id"
            )
            if user:
                users.append(user)
        raised_by_user = frappe.db.get_value(
            "Employee",
            self.raised_by,
            "user_id"
        )

        if raised_by_user and raised_by_user not in users:
            users.append(raised_by_user)


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
        <b>Priorty:</b> {self.priorty} <br>

        <b>Issue:</b> {self.ticket_subject}<br>
        <b>Issue Reported:</b> {self.issue_reported}<br>
        <b>Issue Type:</b> {self.issue_type}<br>
        <b>Raised By:</b> {raised_by} ({self.raised_by})<br>
        <b>Department:</b> {department}<br>

        <b>Date & Time:</b> {self.ticket_date_and_time}<br>
        <p>Please initiate the required actions at the earliest and update the ticket status accordingly.</p>

        <a href="{doc_url}" 
        style="background:#007bff;color:#fff;
        padding:10px 15px;
        text-decoration:none;
        border-radius:5px;">
        Open Ticket
        </a>
        """

        for user in users:
            if user == "Administrator":
                continue
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
            if user == "Administrator":
                continue
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
            if self.issue_type=="Software" or self.issue_type=="Software + Service":
                    self.notify_software_team()
            self.notify_backend_team()
            return {"success": True}
        
        return {"success": False, "message": "Task ID not set or wrong workflow state"}
    
    def notify_on_field_engineer_after_resolve(self):
        if not self.raised_by:
            return

        doc_url = frappe.utils.get_url_to_form(self.doctype, self.name)

        # ─── Employee details ──────────────────────────────────────────────────
        raised_by_data = frappe.db.get_value(
            "Employee", self.raised_by,
            ["employee_name", "reports_to", "department", "user_id"],
            as_dict=True
        ) or {}

        raised_by = raised_by_data.get("employee_name") or self.raised_by
        manager_of_raiser = raised_by_data.get("reports_to")
        department = raised_by_data.get("department")
        raised_by_user_id = raised_by_data.get("user_id")

        # ─── Collect all recipients ────────────────────────────────────────────
        recipients = []
        notify_users = []

        # 1. Master Admins
        admin_users = frappe.get_all(
            "Has Role",
            filters={"role": "Master Admin"},
            pluck="parent"
        )
        for user in admin_users:
            email = frappe.db.get_value("User", user, "email")
            if email:
                recipients.append(email.strip())
                notify_users.append(user)

        # 2. Backend Team — from child table only (selected people)
        for row in self.backend_team_engineer:
            user = frappe.db.get_value("Employee", row.software_engineer, "user_id")
            if user:
                email = frappe.db.get_value("User", user, "email")
                if email:
                    recipients.append(email.strip())
                    notify_users.append(user)

        # 3. Raised By
        if raised_by_user_id:
            email = frappe.db.get_value("User", raised_by_user_id, "email")
            if email:
                recipients.append(email.strip())
                notify_users.append(raised_by_user_id)

        # 4. Manager
        manager_name = None
        if manager_of_raiser:
            manager_data = frappe.db.get_value(
                "Employee", manager_of_raiser,
                ["employee_name", "user_id"],
                as_dict=True
            ) or {}
            manager_name = manager_data.get("employee_name") or manager_of_raiser
            if manager_data.get("user_id"):
                email = frappe.db.get_value("User", manager_data.get("user_id"), "email")
                if email:
                    recipients.append(email.strip())
                    notify_users.append(manager_data.get("user_id"))

        # Remove duplicates
        recipients = list(set(recipients))
        notify_users = list(set(notify_users))

        if not recipients:
            frappe.logger().warning(f"No recipients found for {self.name}")
            return

        # ─── Email ────────────────────────────────────────────────────────────
        subject = f"Ticket - {self.name} has been Resolved"
        message = f"""
            <p>Dear Team,</p>
            <p>The following service ticket has been resolved and closed.</p>
            <b>Ticket Details:</b> <br>
            <b>Ticket ID:</b> {self.name}<br>
            <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
            <b>Hospital Name:</b> {self.hospital_name} <br>
            <b>Issue Type:</b> {self.issue_type}<br>
            <b>Raised By:</b> {raised_by} ({self.raised_by})<br>
            <b>Department:</b> {department or 'N/A'}<br>
            <b>Remarks:</b> {self.system_admin_remarks}<br>
            <b>Docket No:</b> {self.docket_number}<br>
            <b>Date Of Receipt:</b> {self.date_of_receipt}<br>
            <b>Courier Name:</b> {self.courier_name}<br>
            <b>Closed Reason:</b> {self.remarks}<br>
            <p>Kindly review the ticket for your reference.</p>
            <a href="{doc_url}"
            style="background:#007bff;color:#fff;
                    padding:10px 15px;
                    text-decoration:none;
                    border-radius:5px;">
                Open Ticket
            </a>
        """

        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message
        )

        # ─── Notification logs ────────────────────────────────────────────────
        for user in notify_users:
            if user == "Administrator":
                continue
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)

@frappe.whitelist()
def create_ticket_again(old_doc):

    old_doc = frappe.get_doc("Ticket Master", old_doc)

    # decide base ticket
    base_ticket = old_doc.original_ticket_id if old_doc.original_ticket_id else old_doc.name

    naming_series = f"{base_ticket}.-.##"

    return {
        "robot_serial_no": old_doc.robot_serial_no,
        "issue_reported": old_doc.issue_reported,
        "ticket_subject": old_doc.ticket_subject,
        "old_ticket_reference": old_doc.name,
        "surgery_no": old_doc.surgery_no,
        "original_ticket_id": base_ticket,
        "naming_series": naming_series
    }


import frappe


def is_restriction_enabled():
    """Check if restriction is enabled in Meril Manufacturing Settings."""
    return frappe.db.get_single_value("Meril Manufacturing Settings", "engineers_cant_see_other_records")


def get_permission_query_conditions(user=None):
    """
    If restriction enabled AND user has 'Engineers' role → only their own Ticket Master records.
    All other roles or restriction disabled → see everything.
    """
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if user == "Administrator":
        return ""

    if "System Manager" in roles:
        return ""

    # Engineer role + restriction enabled → only their own tickets
    if is_restriction_enabled() and "Field Engineer" in roles:
        return f"`tabTicket Master`.owner = '{user}'"

    # All other roles or restriction disabled → no restriction
    return ""


def has_permission(doc, ptype="read", user=None):
    """
    If restriction enabled AND user has 'Engineers' role → only their own Ticket Master records.
    All other roles or restriction disabled → full access.
    """
    if not user:
        user = frappe.session.user

    roles = frappe.get_roles(user)

    if user == "Administrator":
        return True

    if "System Manager" in roles:
        return True

    # Engineer role + restriction enabled → only their own tickets
    if is_restriction_enabled() and "Field Engineer" in roles:
        return doc.owner == user

    # All other roles or restriction disabled → allow
    return True