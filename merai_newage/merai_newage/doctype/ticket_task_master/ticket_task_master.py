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
        # if old_state == self.workflow_state:
        #     return

        if self.workflow_state == "Pending From Store Team" and self.issue_type == "Hardware + Clinical":
            self.notify_assigned_engineers()

        if self.workflow_state == "Pending From Store Team":
            self.notify_store_team()

        if self.workflow_state == "Approved":
            self.notify_ticket_rasied_by_user()

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
        <b>Ticket:</b> {self.name}<br>
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

            <b>Ticket:</b> {self.name}<br>
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
        doc_url = frappe.utils.get_url_to_form(
            self.doctype,
            self.name
        )

        subject = f"Material for the below service ticket {self.ticket_master_reference} has been dispatched from the store."
        message = f"""
        <p>Dear Team,</p>
        <b>Ticket Details:</b>
        <b>Ticket ID:</b> {self.ticket_master_reference}<br>
        <b>Robot Serial & Batch Number:</b> {self.robot_serial_no}<br>
        <b>Hosiptal Name:</b> {self.hospital_name}<br>
        <b>Dispatch Details:</b>
        <b>Docket Number:</b> {self.docket_no}<br>
        <b>Courier Name:</b>{self.courier_name} <br>
        <b>Dispatch Date:<b>{self.dispatch_date}<br> <br>
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
    new_task.assign_engineer = doc.get("assign_engineer")
    new_task.issue_raised_by = doc.get("raised_by")

    new_task.insert(ignore_permissions=True)  
    # if new_task.assign_engineer:
    #     create_todo_for_engineer(
    #         new_task,
    #         new_task.name
    #     )

    return new_task.name



@frappe.whitelist()
def update_ticket_master(reference_name, task_doc):
    print("reference_name-----",reference_name,"task_doc====",task_doc)
    if isinstance(task_doc, str):
        task_doc = json.loads(task_doc)

    if not reference_name:
        return

    if task_doc.get("workflow_state") != "Approved":
        return

    doc = frappe.get_doc("Ticket Master", reference_name)

    doc.workflow_state = "Pending To Receive Material"
    doc.docket_number = task_doc.get('docket_no')

    doc.set("received_materials", [])

    for row in task_doc.get("robot_materials", []):
        doc.append("received_materials", {
            "item": row.get("item"),
            "item_name": row.get("item_name"),
            "qty": row.get("qty")
        })

    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return doc.name


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

