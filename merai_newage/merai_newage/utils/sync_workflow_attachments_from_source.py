import frappe

def sync_workflow_attachments_from_source(
    target_doc,
    source_doctype,
    source_name,
    table_field="custom_workflow_attachment",
):
    if not source_name:
        return

    source_doc = frappe.get_doc(source_doctype, source_name)

    source_rows = source_doc.get(table_field) or []

    existing_rows = [
        row
        for row in (target_doc.get(table_field) or [])
        if row.doctype_name == source_doctype
        and row.doctype_id == source_name
    ]

    existing_paths = {row.path for row in existing_rows}
    source_paths = {row.path for row in source_rows}

    # Remove deleted files
    for row in existing_rows:
        if row.path not in source_paths:
            target_doc.remove(row)

    # Add new files
    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        target_doc.append(
            table_field,
            {
                "path": row.path,
                "file_name": row.file_name,
                "doctype_name": row.doctype_name or source_doctype,
                "doctype_id": row.doctype_id or source_name,
            },
        )