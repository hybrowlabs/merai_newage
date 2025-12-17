import frappe, json

@frappe.whitelist()
def set_repoter_for_approval(doc):
    doc = frappe.get_doc(json.loads(doc))

    if doc.workflow_state == "Pending From Manager":
        reports_to = frappe.db.get_value(
            "Employee",
            doc.custom_requisitioner,
            "reports_to"
        )
        doc.custom_approval_manager = reports_to

    elif doc.workflow_state == "Pending From Head":
        reports_to = frappe.db.get_value(
            "Employee",
            doc.custom_approval_manager,
            "reports_to"
        )
        doc.custom_approval_head = reports_to

    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate_update_after_submit = True
    doc.save()
