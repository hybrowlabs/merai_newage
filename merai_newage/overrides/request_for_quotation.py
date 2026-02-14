# import frappe

# def copy_workflow_attachments_from_pickup_request(doc, method):
#     # Guards
#     if doc.custom_type != "Logistics":
#         return

#     if not doc.custom_pickup_request:
#         return

#     # Fetch Pickup Request
#     try:
#         pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)
#     except frappe.DoesNotExistError:
#         return

#     source_rows = pickup.get("custom_workflow_attachment") or []
#     if not source_rows:
#         return

#     # Avoid duplicates
#     existing_paths = {
#         row.path for row in (doc.get("custom_workflow_attachment") or [])
#     }

#     for row in source_rows:
#         if row.path in existing_paths:
#             continue

#         doc.append("custom_workflow_attachment", {
#             "path": row.path,
#             "file_name": row.file_name,
#             "doctype_name": "Pickup Request",
#             "doctype_id": pickup.name
#         })

# import frappe

# def copy_workflow_attachments_from_pickup_request(doc, method):

#     # Guards
#     if doc.custom_type != "Logistics":
#         return

#     if not doc.custom_pickup_request:
#         return

#     try:
#         pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)
#     except frappe.DoesNotExistError:
#         return

#     table_field = "custom_workflow_attachment"

#     source_rows = pickup.get(table_field) or []
#     source_paths = {row.path for row in source_rows}

#     target_rows = doc.get(table_field) or []

#     added = False
#     removed = False

#     for row in list(target_rows):
#         if row.doctype_name == "Pickup Request" and row.path not in source_paths:
#             doc.remove(row)
#             removed = True

#     existing_paths = {row.path for row in doc.get(table_field) or []}

#     for row in source_rows:
#         if row.path in existing_paths:
#             continue

#         doc.append(table_field, {
#             "path": row.path,
#             "file_name": row.file_name,
#             "doctype_name": "Pickup Request",
#             "doctype_id": pickup.name
#         })
#         added = True

#     return added or removed


import frappe


# def copy_workflow_attachments_from_pickup_request(doc, method):
#     frappe.msgprint("Pickup Copy Function Running")

#     # Guards
#     if doc.custom_type != "Logistics":
#         return

#     if not doc.custom_pickup_request:
#         return

#     try:
#         pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)
#     except frappe.DoesNotExistError:
#         return

#     table_field = "custom_workflow_attachment"

#     # Source (Pickup) attachments
#     source_rows = pickup.get(table_field) or []
#     source_paths = {row.path for row in source_rows if row.path}

#     # Target (RFQ) attachments
#     target_rows = doc.get(table_field) or []

#     added = False
#     removed = False

#     # -----------------------------
#     # 1️⃣ Remove deleted pickup files
#     # -----------------------------
#     for row in list(target_rows):
#         if (
#             row.doctype_name == "Pickup Request"
#             and row.doctype_id == pickup.name
#             and row.path not in source_paths
#         ):
#             doc.remove(row)
#             removed = True

#     # -----------------------------
#     # 2️⃣ Get existing pickup-origin paths in RFQ
#     # -----------------------------
#     existing_pickup_paths = {
#         row.path
#         for row in (doc.get(table_field) or [])
#         if row.path
#         and row.doctype_name == "Pickup Request"
#         and row.doctype_id == pickup.name
#     }

#     # -----------------------------
#     # 3️⃣ Add new pickup files
#     # -----------------------------
#     for row in source_rows:
#         if not row.path or row.path in existing_pickup_paths:
#             continue

#         doc.append(
#             table_field,
#             {
#                 "path": row.path,
#                 "file_name": row.file_name,
#                 "doctype_name": "Pickup Request",
#                 "doctype_id": pickup.name,
#             },
#         )
#         added = True

#     return added or removed

import frappe


def copy_workflow_attachments_from_pickup_request(doc, method):

    if doc.custom_type != "Logistics":
        return

    if not doc.custom_pickup_request:
        return

    pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)

    table_field = "custom_workflow_attachment"

    source_rows = pickup.get(table_field) or []

    # Existing pickup-origin rows in RFQ
    existing_pickup_rows = [
        row for row in (doc.get(table_field) or [])
        if row.doctype_name == "Pickup Request"
        and row.doctype_id == pickup.name
    ]

    existing_pickup_paths = {row.path for row in existing_pickup_rows}

    # 1️⃣ Remove deleted pickup files
    source_paths = {row.path for row in source_rows}

    for row in existing_pickup_rows:
        if row.path not in source_paths:
            doc.remove(row)

    # 2️⃣ Add new pickup files (ignore RFQ-origin rows)
    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_pickup_paths:
            continue

        doc.append(
            table_field,
            {
                "path": row.path,
                "file_name": row.file_name,
                "doctype_name": "Pickup Request",
                "doctype_id": pickup.name,
            },
        )