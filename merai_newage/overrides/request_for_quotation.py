import frappe

def copy_workflow_attachments_from_pickup_request(doc, method):
    # Guards
    if doc.custom_type != "Logistics":
        return

    if not doc.custom_pickup_request:
        return

    # Fetch Pickup Request
    try:
        pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)
    except frappe.DoesNotExistError:
        return

    source_rows = pickup.get("custom_workflow_attachment") or []
    if not source_rows:
        return

    # Avoid duplicates
    existing_paths = {
        row.path for row in (doc.get("custom_workflow_attachment") or [])
    }

    for row in source_rows:
        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": "Pickup Request",
            "doctype_id": pickup.name
        })
