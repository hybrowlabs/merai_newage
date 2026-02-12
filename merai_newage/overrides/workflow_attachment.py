# import frappe

# @frappe.whitelist()
# def sync_workflow_attachment(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)

#     files = frappe.get_all(
#         "File",
#         filters={
#             "attached_to_doctype": doctype,
#             "attached_to_name": docname,
#             "is_folder": 0
#         },
#         fields=["file_url", "file_name"]
#     )

#     # 🔥 USE ACTUAL TABLE FIELDNAME
#     table_field = "custom_workflow_attachment"

#     existing_paths = {
#         row.path for row in doc.get(table_field) or []
#     }

#     added = False
#     for f in files:
#         if f.file_url in existing_paths:
#             continue

#         doc.append(table_field, {
#             "path": f.file_url,
#             "file_name": f.file_name,
#             "doctype_name": doctype,
#             "doctype_id": docname
#         })
#         added = True

#     if added:
#         doc.save(ignore_permissions=True)

#     return {"added": added}


import frappe

@frappe.whitelist()
def sync_workflow_attachment(doctype, docname):
    doc = frappe.get_doc(doctype, docname)

    table_field = "custom_workflow_attachment"

    # 🔹 Current sidebar attachments
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_folder": 0
        },
        fields=["file_url", "file_name"]
    )

    file_urls = {f.file_url for f in files}

    # 🔹 Existing table rows
    existing_rows = doc.get(table_field) or []
    existing_paths = {row.path for row in existing_rows}

    added = False
    removed = False

    for row in list(existing_rows):
        if row.path not in file_urls:
            doc.remove(row)
            removed = True

    for f in files:
        if f.file_url in existing_paths:
            continue

        doc.append(table_field, {
            "path": f.file_url,
            "file_name": f.file_name,
            "doctype_name": doctype,
            "doctype_id": docname
        })
        added = True

    return {"added": added, "removed": removed}
