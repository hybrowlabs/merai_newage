import frappe

@frappe.whitelist()
def sync_workflow_attachment(doctype, docname):
    parentfield = "custom_workflow_attachment"
    child_doctype = frappe.get_meta(doctype).get_field(parentfield).options

    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_folder": 0
        },
        fields=["file_url", "file_name"]
    )
    file_map = {f.file_url: f.file_name for f in files}

    existing_rows = frappe.get_all(
        child_doctype,
        filters={
            "parent": docname,
            "parenttype": doctype,
            "parentfield": parentfield
        },
        fields=["name", "path", "doctype_name", "doctype_id"]
    )

    added = False
    removed = False

    # Remove only CURRENT-doc RFQ rows (doctype_name + doctype_id match current doc)
    for row in existing_rows:
        if not (row.doctype_name == doctype and row.doctype_id == docname):
            continue  # Skip Pickup rows + old revision RFQ rows

        if row.path not in file_map:
            frappe.delete_doc(child_doctype, row.name, ignore_permissions=True)
            removed = True

    # refresh list after deletes
    existing_rows = frappe.get_all(
        child_doctype,
        filters={
            "parent": docname,
            "parenttype": doctype,
            "parentfield": parentfield
        },
        fields=["path", "doctype_name", "doctype_id"]
    )

    existing_current_rfq_paths = {
        r.path for r in existing_rows
        if r.doctype_name == doctype and r.doctype_id == docname
    }

    # Add new current-doc RFQ attachments
    for file_url, file_name in file_map.items():
        if file_url in existing_current_rfq_paths:
            continue

        frappe.get_doc({
            "doctype": child_doctype,
            "parent": docname,
            "parenttype": doctype,
            "parentfield": parentfield,
            "path": file_url,
            "file_name": file_name,
            "doctype_name": doctype,
            "doctype_id": docname
        }).insert(ignore_permissions=True)

        added = True

    return {"added": added, "removed": removed}


# import frappe

# @frappe.whitelist()
# def sync_workflow_attachment(
#     doctype,
#     docname,
#     source_doctype=None,
#     source_name=None
# ):
#     parentfield = "custom_workflow_attachment"
#     child_doctype = frappe.get_meta(doctype).get_field(parentfield).options

#     # 🔹 Decide source
#     source_doctype = source_doctype or doctype
#     source_name = source_name or docname

#     # 🔹 Get files from source doc
#     files = frappe.get_all(
#         "File",
#         filters={
#             "attached_to_doctype": source_doctype,
#             "attached_to_name": source_name,
#             "is_folder": 0
#         },
#         fields=["file_url", "file_name"]
#     )
#     # 🔹 If no File attachments → fallback to child table
#     if not files:
#         source_doc = frappe.get_doc(source_doctype, source_name)
#         child_rows = source_doc.get("custom_workflow_attachment") or []

#         files = [
#             {
#                 "file_url": row.path,
#                 "file_name": row.file_name
#             }
#             for row in child_rows
#             if row.path
#         ]

#     file_map = {f.file_url: f.file_name for f in files}

#     # 🔹 Existing rows
#     existing_rows = frappe.get_all(
#         child_doctype,
#         filters={
#             "parent": docname,
#             "parenttype": doctype,
#             "parentfield": parentfield
#         },
#         fields=["name", "path", "doctype_name", "doctype_id"]
#     )

#     added = False
#     removed = False

#     # =========================
#     # 🔹 REMOVE LOGIC
#     # =========================
#     for row in existing_rows:
#         if not (
#             row.doctype_name == source_doctype
#             and row.doctype_id == source_name
#         ):
#             continue

#         if row.path not in file_map:
#             frappe.delete_doc(child_doctype, row.name, ignore_permissions=True)
#             removed = True

#     # refresh
#     existing_rows = frappe.get_all(
#         child_doctype,
#         filters={
#             "parent": docname,
#             "parenttype": doctype,
#             "parentfield": parentfield
#         },
#         fields=["path", "doctype_name", "doctype_id"]
#     )

#     existing_paths = {
#         r.path for r in existing_rows
#         if r.doctype_name == source_doctype
#         and r.doctype_id == source_name
#     }

#     # =========================
#     # 🔹 ADD LOGIC
#     # =========================
#     for file_url, file_name in file_map.items():
#         if file_url in existing_paths:
#             continue

#         frappe.get_doc({
#             "doctype": child_doctype,
#             "parent": docname,
#             "parenttype": doctype,
#             "parentfield": parentfield,
#             "path": file_url,
#             "file_name": file_name,
#             "doctype_name": source_doctype,
#             "doctype_id": source_name
#         }).insert(ignore_permissions=True)

#         added = True

#     return {
#         "added": added,
#         "removed": removed,
#         "source_doctype": source_doctype,
#         "source_name": source_name
#     }