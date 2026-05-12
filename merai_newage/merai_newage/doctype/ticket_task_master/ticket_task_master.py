# Copyright (c) 2026, Siddhant Hybrowlabs and contributors
# For license information, please see license.txt

import frappe , json
from frappe.model.document import Document


class TicketTaskMaster(Document):
    
    def on_update(self):
        if not self.workflow_state:
            return

        old_doc = self.get_doc_before_save()
        old_state = old_doc.workflow_state if old_doc else None

        # Trigger only if state changed
        if old_state == self.workflow_state:
            return

        if self.workflow_state == "Pending From Store Team" and self.issue_type == "Hardware + Clinical":
            self.notify_assigned_engineers()

        if self.workflow_state == "Pending From Store Team":
            self.notify_store_team()

        if self.workflow_state == "Approved" and self.issue_type=="Hardware":
            self.notify_ticket_rasied_by_user()
        if self.workflow_state == "Approved" and self.issue_type=="Software":
            self.notify_ticket_rasied_by_user_software()

    def notify_store_team(self):

        users = frappe.get_all(
            "Has Role",
            filters={"role": "Store Team"},
            pluck="parent"
        )

        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )

        # Build child table HTML
        items_html = """
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
            <tr style="background:#f2f2f2;">
                <th>Item Code</th>
                <th>Item Name</th>
                <th>Qty</th>
            </tr>
        """

        for row in self.robot_materials:
            items_html += f"""
            <tr>
                <td>{row.item}</td>
                <td>{row.item_name}</td>
                <td>{row.qty}</td>
            </tr>
            """

        items_html += "</table>"

        subject = f"Please Provide Required Materials for the Ticket {self.ticket_master_reference}"

        message = f"""
        <p>Dear Team,</p>

        <p>Please Provide the below materials.</p>
        <b>Ticket:</b> {self.ticket_master_reference}<br>
        <b>Robot:</b> {self.robot_serial_no}<br>
        <b>Issue Description:</b> {self.issue_reported}<br><br>

        <b>Requested Items:</b><br><br>
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


    def notify_assigned_engineers(self):

        engineers = []

        if self.clinical_engineer:
            engineers.append(self.clinical_engineer)

        if self.service_engineer:
            engineers.append(self.service_engineer)

        if not engineers:
            return

        # Get user IDs from Employee
        users = frappe.get_all(
            "Employee",
            filters={"name": ["in", engineers]},
            pluck="user_id"
        )

        if not users:
            return

        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )

        subject = f"New Ticket Assigned - {self.ticket_master_reference} | {self.issue_type}"

        for user in users:
            message = f"""
            <p>Dear,</p>
            <p>You have been assigned a new ticket.</p>

            <b>Ticket:</b> {self.ticket_master_reference}<br>
            <b>Robot:</b> {self.robot_serial_no}<br>
            <b>Issue:</b> {self.issue_reported}<br><br>

            <a href="{doc_url}" 
            style="background:#007bff;color:#fff;
            padding:10px 15px;
            text-decoration:none;
            border-radius:5px;">
            Open Ticket
            </a>
            """

            # Email
            frappe.sendmail(
                recipients=user,
                subject=subject,
                message=message
            )

            # Notification
            frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "for_user": user,
                "type": "Alert",
                "document_type": self.doctype,
                "document_name": self.name
            }).insert(ignore_permissions=True)

    def notify_ticket_rasied_by_user(self):

        if not self.issue_raised_by:
            return

        user = frappe.db.get_value(
            "Employee",
            self.issue_raised_by,
            "user_id"
        )

        if not user:
            return
        
        doctype = "Ticket Master"
        doc_url = frappe.utils.get_url_to_form(
            doctype,
            self.ticket_master_reference
        )

        items_html = """
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
            <tr style="background:#f2f2f2;">
                <th>Item Code</th>
                <th>Item Name</th>
                <th>Qty</th>
            </tr>
        """

        for row in self.robot_materials:
            items_html += f"""
            <tr>
                <td>{row.item}</td>
                <td>{row.item_name}</td>
                <td>{row.qty}</td>
            </tr>
            """

        items_html += "</table>"

        subject = f"Material for the below service ticket {self.ticket_master_reference} has been dispatched from the store."
        message = f"""
        <p>Dear Team,</p>
        <b>Ticket Details:</b>
        <b>Ticket ID:</b> {self.ticket_master_reference}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hosiptal Name:</b> {self.hospital_name}<br>
        <b>Dispatch Details:</b> <br>
        <b>Docket Number:</b> {self.docket_no}<br>
        <b>Courier Name:</b>{self.courier_name} <br>
        <b>Dispatch Date:<b>{self.dispatch_date}<br> <br>
        <b>Requested Items:</b><br><br>
        {items_html}<br><br>

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


    def notify_ticket_rasied_by_user_software(self):

        if not self.issue_raised_by:
            return

        user = frappe.db.get_value(
            "Employee",
            self.issue_raised_by,
            "user_id"
        )

        if not user:
            return
        
        doctype = "Ticket Master"
        doc_url = frappe.utils.get_url_to_form(
            doctype,
            self.ticket_master_reference
        )

        items_html = """
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse;width:100%;">
            <tr style="background:#f2f2f2;">
                <th>Item Code</th>
                <th>Item Name</th>
                <th>Qty</th>
            </tr>
        """

        for row in self.robot_materials:
            items_html += f"""
            <tr>
                <td>{row.item}</td>
                <td>{row.item_name}</td>
                <td>{row.qty}</td>
            </tr>
            """

        items_html += "</table>"

        subject = f"Issue for the below service ticket {self.ticket_master_reference} is resolved"
        message = f"""
        <p>Dear Team,</p>
        <b>Ticket Details:</b>
        <b>Ticket ID:</b> {self.ticket_master_reference}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hosiptal Name:</b> {self.hospital_name}<br>
       
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

    def validate(self):
        # Get the state from DB before this save
        previous_state = frappe.db.get_value("Ticket Task Master", self.name, "workflow_state")
        
        # Only enforce remarks if coming from Draft AND moving to Resolved state
        # (i.e., user clicked Resolve, not Send)
        if previous_state == "Draft" and self.workflow_state == "Approved" and not self.remarks:
            frappe.throw("Please fill in <b>Remarks</b> before proceeding.")
@frappe.whitelist()
def create_ticket_task(doc):

    doc = frappe.parse_json(doc)

    if doc.get("issue_type") == "Software + Service":

        ticket_ref = doc.get("name")

        # =====================================================
        # BACKEND / HARDWARE TASK  →  TASK-2026050070-HW
        # =====================================================

        backend_task = frappe.new_doc("Ticket Task Master")
        backend_task.robot_serial_no = doc.get("robot_serial_no")
        backend_task.issue_type = "Hardware"
        backend_task.hospital_name = doc.get("hospital_name")
        backend_task.issue_reported = doc.get("issue_reported")
        backend_task.system_admin_remarks = doc.get("system_admin_remarks")
        backend_task.ticket_master_reference = ticket_ref
        backend_task.issue_raised_by = doc.get("raised_by")
        backend_task.dispatch_type = "By Courier"

        for row in doc.get("backend_team_engineer") or []:
            backend_task.append("assign_engineer", {
                "software_engineer": row.get("software_engineer")
            })

        # ✅ This flag tells Frappe: DO NOT auto-generate name, use what I set
        backend_task.name = f"TASK-{ticket_ref}-HW"
        backend_task.flags.name_set = True

        backend_task.insert(ignore_permissions=True)
        frappe.db.commit()

        # =====================================================
        # SOFTWARE TASK  →  TASK-2026050070-SW
        # =====================================================

        software_task = frappe.new_doc("Ticket Task Master")
        software_task.robot_serial_no = doc.get("robot_serial_no")
        software_task.issue_type = "Software"
        software_task.hospital_name = doc.get("hospital_name")
        software_task.issue_reported = doc.get("issue_reported")
        software_task.system_admin_remarks = doc.get("system_admin_remarks")
        software_task.ticket_master_reference = ticket_ref
        software_task.issue_raised_by = doc.get("raised_by")

        for row in doc.get("software_team_engineer") or []:
            software_task.append("software_team", {
                "software_engineer": row.get("software_engineer")
            })

        # ✅ Same flag for software task
        software_task.name = f"TASK-{ticket_ref}-SW"
        software_task.flags.name_set = True

        software_task.insert(ignore_permissions=True)
        frappe.db.commit()
        print("backend_task=======",backend_task.name,"software_task_id=======",software_task.name)
        return {
            "backend_task_id": backend_task.name,   # TASK-2026050070-HW
            "software_task_id": software_task.name  # TASK-2026050070-SW
        }

    # =========================================================
    # EXISTING FLOW (unchanged)
    # =========================================================

    new_task = frappe.new_doc("Ticket Task Master")
    new_task.robot_serial_no = doc.get("robot_serial_no")
    new_task.issue_type = doc.get("issue_type")
    new_task.hospital_name = doc.get("hospital_name")
    new_task.issue_reported = doc.get("issue_reported")
    new_task.system_admin_remarks = doc.get("system_admin_remarks")
    new_task.ticket_master_reference = doc.get("name")
    new_task.issue_raised_by = doc.get("raised_by")

    if doc.get("issue_type") == "Hardware + Clinical":
        new_task.dispatch_type = "By Hand"
    elif doc.get("issue_type") == "Hardware":
        new_task.dispatch_type = "By Courier"

    if doc.get("issue_type") == "Software":
        for row in doc.get("software_team_engineer") or []:
            new_task.append("software_team", {
                "software_engineer": row.get("software_engineer")
            })
    else:
        for row in doc.get("backend_team_engineer") or []:
            new_task.append("assign_engineer", {
                "software_engineer": row.get("software_engineer")
            })

    new_task.insert(ignore_permissions=True)
    frappe.db.commit()

    return new_task.name

from frappe.utils import nowdate

def create_todo_for_engineer(task_doc, installation_name):
    # if not task_doc.engineer_name:
    #     frappe.throw("Assigned Engineer is not selected!")

    user_id = frappe.db.get_value(
        "Employee",
        task_doc.assign_engineer,
        "user_id"
    )

    if not user_id:
        frappe.throw("Selected Engineer is not linked to a User account!")

    todo = frappe.get_doc({
        "doctype": "ToDo",
        "description": f"New Ticket is Assigned : {installation_name}",
        "reference_type": "Ticket Master",
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
        "subject": "New Ticket Assigned",
        "email_content": f"You have been assigned a new Ticket task: {installation_name}",
        "for_user": user_id,
        "type": "Alert",
        "document_type": "Ticket Master",
        "document_name": installation_name,
    }).insert(ignore_permissions=True)


@frappe.whitelist()
def update_ticket_master(reference_name, task_doc, previous_state=None):
    print("reference_name-----", reference_name, "task_doc====", task_doc)
    if isinstance(task_doc, str):
        task_doc = json.loads(task_doc)

    if not reference_name:
        return

    if task_doc.get("workflow_state") != "Approved":
        return

    issue_type = task_doc.get("issue_type")

    print("previous_state from JS-----", previous_state)

    # Load the actual Ticket Master doc so hooks fire
    ticket_doc = frappe.get_doc("Ticket Master", reference_name)

    # Set docket number
    ticket_doc.docket_number = task_doc.get("docket_no")
    ticket_doc.remarks = task_doc.get('remarks')
    # Set workflow state based on conditions
    if previous_state == "Draft":
        ticket_doc.workflow_state = "Resolved"
        print("Ticket Master closed → Resolved (was Draft)")

    elif issue_type == "Hardware" or issue_type=="Software + Service":
        ticket_doc.workflow_state = "Pending To Close"
        print("Ticket Master → Pending To Close")

    else:
        ticket_doc.workflow_state = "Resolved"
        print("Ticket Master closed → Resolved")

    # Clear and re-insert received_materials
    ticket_doc.received_materials = []

    for row in task_doc.get("robot_materials", []):
        ticket_doc.append("received_materials", {
            "item": row.get("item"),
            "item_name": row.get("item_name"),
            "qty": row.get("qty")
        })

    # Save with ignore_permissions so hooks fire properly
    ticket_doc.flags.ignore_permissions = True
    ticket_doc.save()
    frappe.db.commit()

    # Publish realtime event to refresh Ticket Master on all open tabs
    frappe.publish_realtime(
        event="doc_update",
        message={
            "doctype": "Ticket Master",
            "name": reference_name
        },
        doctype="Ticket Master",
        docname=reference_name
    )

    return reference_name


@frappe.whitelist()
def close_related_ticket(ticket_name, issue_type):
    print("close_related_ticket============534===========")
    if not ticket_name:
        return

    if issue_type == "Hardware":
        return

    # Load doc so hooks fire
    ticket_doc = frappe.get_doc("Ticket Master", ticket_name)
    ticket_doc.workflow_state = "Resolved"
    ticket_doc.flags.ignore_permissions = True
    ticket_doc.save()
    frappe.db.commit()

    return ticket_name