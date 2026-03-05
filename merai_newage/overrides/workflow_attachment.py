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


# import frappe

# @frappe.whitelist()
# def sync_workflow_attachment(doctype, docname):
#     doc = frappe.get_doc(doctype, docname)

#     table_field = "custom_workflow_attachment"

#     # 🔹 Current sidebar attachments
#     files = frappe.get_all(
#         "File",
#         filters={
#             "attached_to_doctype": doctype,
#             "attached_to_name": docname,
#             "is_folder": 0
#         },
#         fields=["file_url", "file_name"]
#     )

#     file_urls = {f.file_url for f in files}

#     # 🔹 Existing table rows
#     existing_rows = doc.get(table_field) or []
#     existing_paths = {row.path for row in existing_rows}

#     added = False
#     removed = False

#     for row in list(existing_rows):
#         if row.path not in file_urls:
#             doc.remove(row)
#             removed = True

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

#     return {"added": added, "removed": removed}

# import frappe

# @frappe.whitelist()
# def sync_workflow_attachment(doctype, docname):
    
#     parentfield = "custom_workflow_attachment"

#     # Dynamically get child table doctype
#     child_doctype = frappe.get_meta(doctype).get_field(parentfield).options

#     # Sidebar attachments
#     files = frappe.get_all(
#         "File",
#         filters={
#             "attached_to_doctype": doctype,
#             "attached_to_name": docname,
#             "is_folder": 0
#         },
#         fields=["file_url", "file_name"]
#     )

#     file_urls = {f.file_url for f in files}

#     # Existing child rows
#     existing = frappe.get_all(
#         child_doctype,
#         filters={
#             "parent": docname,
#             "parenttype": doctype,
#             "parentfield": parentfield
#         },
#         fields=["name", "path"]
#     )

#     existing_paths = {row.path for row in existing}

#     added = False
#     removed = False

#     # Remove deleted attachments
#     for row in existing:
#     # Skip rows that originated from Pickup Request
#         child_row = frappe.get_doc(child_doctype, row.name)

#         if child_row.doctype_name == "Pickup Request":
#             continue

#     if row.path not in file_urls:
#         frappe.delete_doc(child_doctype, row.name, ignore_permissions=True)
#         removed = True

#     # Add new attachments
#     for f in files:
#         if f.file_url in existing_paths:
#             continue

#         frappe.get_doc({
#             "doctype": child_doctype,
#             "parent": docname,
#             "parenttype": doctype,
#             "parentfield": parentfield,
#             "path": f.file_url,
#             "file_name": f.file_name,
#             "doctype_name": doctype,
#             "doctype_id": docname
#         }).insert(ignore_permissions=True)

#         added = True

#     return {"added": added, "removed": removed}

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

    # ✅ Remove only CURRENT-doc RFQ rows (doctype_name + doctype_id match current doc)
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

    # ✅ Add new current-doc RFQ attachments
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
