

import frappe
from frappe import _
from frappe.model.workflow import apply_workflow
from frappe.model.document import Document

def before_save_purchase_invoice(doc, method):
    populate_asset_codes(doc)

def on_submit_purchase_invoice(doc, method):
    populate_asset_codes(doc)


def populate_asset_codes(doc):
    """
    For each PI Item:
    - pr_detail = PR Item row name
    - Asset.purchase_receipt_item = PR Item row name
    """

    parent_creation_request = None  # to set in parent

    for item in doc.items:

        if not item.get("pr_detail"):
            continue

        # Fetch complete Asset document
        asset = frappe.get_doc("Asset", {
            "purchase_receipt_item": item.pr_detail,
            "docstatus": ["<", 2]
        }) if frappe.db.exists("Asset", {
            "purchase_receipt_item": item.pr_detail,
            "docstatus": ["<", 2]
        }) else None

        if not asset:
            continue

        # -----------------------------
        # CHILD TABLE UPDATES
        # -----------------------------

        # 1️⃣ Set Asset Name
        if not item.get("custom_asset"):
            item.custom_asset = asset.name

        # 2️⃣ Set Asset Master (field from Asset doctype)
        if not item.get("custom_asset_master"):
            item.custom_asset_master = asset.get("custom_asset_master")

        # -----------------------------
        # PARENT FIELD UPDATE
        # -----------------------------

        if not parent_creation_request:
            parent_creation_request = asset.get("custom_asset_creation_request"
            "")

    # Set parent field once
    if parent_creation_request:
        doc.custom_asset_creation_request = parent_creation_request


def create_todo_for_user(doctype, name, assign_to, description, custom_document_number=None):
    todo = frappe.get_doc({
        "doctype": "ToDo",
        "owner": assign_to,
        "allocated_to": assign_to,
        "reference_type": doctype,
        "reference_name": name,
        "description": description,
        "custom_document_number": custom_document_number or 0,
        "status": "Open",
        "priority": "High"
    })
    todo.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"assigned to {assign_to} successfully.")


def create_notification_log(subject, message, for_user, doc):
    """Create a Notification Log entry so it appears in the bell icon."""
    notification = frappe.get_doc({
        "doctype": "Notification Log",
        "subject": subject,
        "email_content": message,
        "for_user": for_user,
        "type": "Alert",
        "document_type": doc.doctype,
        "document_name": doc.name
    })
    notification.insert(ignore_permissions=True)


@frappe.whitelist()
def raise_query(docname, query_text, related_field, raised_by=None, assigned_to=None):
    doc = frappe.get_doc("Purchase Invoice", docname)

    current_user = raised_by or frappe.session.user

    # Auto-determine assigned_to if not passed from frontend
    if not assigned_to:
        if frappe.db.exists("Has Role", {"parent": current_user, "role": "Booking Approver"}):
            # Checker -> assign to Maker
            assigned_to = doc.custom_approved_by_maker or doc.owner
        elif frappe.db.exists("Has Role", {"parent": current_user, "role": "Booking User"}):
            # Maker -> assign to GRN creator
            if doc.custom_purchase_receipt:
                assigned_to = frappe.db.get_value("Purchase Receipt", doc.custom_purchase_receipt, "owner")
            else:
                assigned_to = doc.owner
        else:
            frappe.throw("You do not have permission to raise a query")

    if not assigned_to:
        frappe.throw("Unable to determine who to assign the query to")

    # Append query to child table
    doc.append("custom_purchase_invoice_query", {
        "query": query_text,
        "related_field": related_field,
        "raised_by": current_user,
        "assigned_to": assigned_to,
        "status": "Open",
        "priority": "High",
        "raised_on": frappe.utils.now()
    })

    doc.save(ignore_permissions=True)
    print("doc.workflow_state=============117",doc.workflow_state)
    # Workflow transitions
    if doc.workflow_state == "Pending From Checker":
        apply_workflow(doc, "Revert")   # action name

    elif doc.workflow_state == "Pending From Accountant":
        apply_workflow(doc, "Revert")   # action name
    # Create ToDo for assigned user
    create_todo_for_user(
        doctype=doc.doctype,
        name=doc.name,
        assign_to=assigned_to,
        description=f"Query Raised on {related_field}: {query_text}"
    )
    create_notification_log(
        subject=_("New Query Assigned"),
        message=f"A new query <b>{doc.name}</b> has been assigned to you.",
        for_user=assigned_to,
        doc=doc
    )
    # frappe.sendmail(
    #     recipients=[assigned_to],
    #     subject=f"Query Raised on Invoice {docname}",
    #     message=f"""
    #     <p>A query has been raised on <b>{docname}</b></p>
    #     <p><b>Field:</b> {related_field}</p>
    #     <p><b>Query:</b> {query_text}</p>
    #     <p><b>Raised By:</b> {current_user}</p>
    #     <p>Please login and resolve the query.</p>
    #     """
    # )

    return True



@frappe.whitelist()
def resolve_all_queries(docname):

    doc = frappe.get_doc("Purchase Invoice", docname)
    current_user = frappe.session.user

    # -----------------------------------
    # 1️⃣ Close Child Queries
    # -----------------------------------
    raised_by_users = set()

    for row in doc.custom_purchase_invoice_query:
        if row.status == "Open":
            row.status = "Closed"
            row.resolved_on = frappe.utils.now()

        if row.raised_by:
            raised_by_users.add(row.raised_by)

    doc.save(ignore_permissions=True)

    # -----------------------------------
    # 2️⃣ Close Current User ToDos
    # -----------------------------------
    open_todos = frappe.get_all(
        "ToDo",
        filters={
            "reference_type": "Purchase Invoice",
            "reference_name": doc.name,
            "status": "Open",
            "allocated_to": current_user
        },
        fields=["name"]
    )

    for todo in open_todos:
        frappe.db.set_value("ToDo", todo.name, "status", "Closed")

    # -----------------------------------
    # 3️⃣ Move Workflow
    # -----------------------------------
    if doc.workflow_state != "Pending From Checker":
        apply_workflow(doc, "Send To Checker")  # ensure correct action name

    # -----------------------------------
    # 4️⃣ Notify All Raised By Users
    # -----------------------------------
    for user in raised_by_users:

        # Skip current user (optional)
        if user == current_user:
            continue

        create_todo_for_user(
            doctype=doc.doctype,
            name=doc.name,
            assign_to=user,
            description=f"Your query has been resolved for Invoice {doc.name}."
        )

        frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"Query Resolved - {doc.name}",
            "email_content": f"Your query has been resolved for Purchase Invoice {doc.name}.",
            "document_type": doc.doctype,
            "document_name": doc.name,
            "for_user": user,
            "type": "Alert"
        }).insert(ignore_permissions=True)
        frappe.publish_realtime(
            event="notification",
            message={
                "type": "Alert",
                "subject": f"Query Resolved - {doc.name}",
                "message": f"Your query has been resolved for Invoice {doc.name}.",
                "doctype": doc.doctype,
                "docname": doc.name
            },
            user=user
        )

    # -----------------------------------
    # 5️⃣ Also Notify Checker (Optional)
    # -----------------------------------
    checker = doc.custom_approved_by_checker

    if checker and checker not in raised_by_users:

        create_todo_for_user(
            doctype=doc.doctype,
            name=doc.name,
            assign_to=checker,
            description=f"Queries resolved for Invoice {doc.name}. Please review again."
        )

        frappe.publish_realtime(
            event="notification",
            message={
                "type": "Alert",
                "subject": f"Queries Resolved - {doc.name}",
                "message": f"Queries resolved. Please review invoice {doc.name}",
                "doctype": doc.doctype,
                "docname": doc.name
            },
            user=checker
        )

    return True
@frappe.whitelist()
def capture_workflow_user(docname, workflow_state):
    current_user = frappe.session.user
    
    print(f"====CAPTURE WORKFLOW USER==== Doc: {docname} | State: {workflow_state} | User: {current_user}")
    frappe.log_error(f"Doc: {docname} | State: {workflow_state} | User: {current_user}", "Workflow Capture")

    if workflow_state == "Pending From Checker":
        frappe.db.set_value("Purchase Invoice", docname, {
            "custom_approved_by_maker": current_user,
            "custom_approved_on_maker": frappe.utils.now()
        })

    elif workflow_state in ("Approved"):
        frappe.db.set_value("Purchase Invoice", docname, {
            "custom_approved_by_checker": current_user,
            "custom_approved_on_checker": frappe.utils.now()
        })

    return True