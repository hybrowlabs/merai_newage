# ---------------------------------------------------------------------------------------
# import frappe


# def copy_workflow_attachments_from_pickup_request(doc, method):

#     if doc.custom_type != "Logistics":
#         return

#     if not doc.custom_pickup_request:
#         return

#     pickup = frappe.get_doc("Pickup Request", doc.custom_pickup_request)

#     table_field = "custom_workflow_attachment"

#     source_rows = pickup.get(table_field) or []

#     # Existing pickup-origin rows in RFQ
#     existing_pickup_rows = [
#         row for row in (doc.get(table_field) or [])
#         if row.doctype_name == "Pickup Request"
#         and row.doctype_id == pickup.name
#     ]

#     existing_pickup_paths = {row.path for row in existing_pickup_rows}

#     # Remove deleted pickup files
#     source_paths = {row.path for row in source_rows}

#     for row in existing_pickup_rows:
#         if row.path not in source_paths:
#             doc.remove(row)

#     # Add new pickup files (ignore RFQ-origin rows)
#     for row in source_rows:
#         if not row.path:
#             continue

#         if row.path in existing_pickup_paths:
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


# ---------------------------------------------------------------------------------------

# from merai_newage.overrides.workflow_attachment import sync_workflow_attachment

# def sync_rfq_workflow_attachments(doc, method):
#     if doc.custom_type != "Logistics":
#         return

#     # RFQ ke apne attachments
#     sync_workflow_attachment(doc.doctype, doc.name)

#     # Pickup ke attachments
#     if doc.custom_pickup_request:
#         sync_workflow_attachment(
#             doc.doctype,
#             doc.name,
#             "Pickup Request",
#             doc.custom_pickup_request
#         )