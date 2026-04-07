# from merai_newage.merai_newage.utils.sync_workflow_attachments_from_source import sync_workflow_attachments_from_source

# # 🔹 Global mapping (recommended)
# SOURCE_MAP = {
#     "custom_pickup_request": "Pickup Request",
#     "custom_supplier_quotation": "Supplier Quotation",
#     "custom_pre_alert": "Pre Alert",
#     "custom_pre_alert_check_list": "Pre-Alert Check List",
#     "custom_boe_entry": "BOE Entry",
# }


# def sync_workflow_attachments_for_logistics(doc, method):

#     if doc.custom_type != "Logistics":
#         return

#     for field, doctype in SOURCE_MAP.items():
#         source_name = getattr(doc, field, None)

#         if source_name:
#             sync_workflow_attachments_from_source(
#                 doc, doctype, source_name
#             )

import frappe
from merai_newage.merai_newage.utils.sync_workflow_attachments_from_source import sync_workflow_attachments_from_source
from merai_newage.overrides.workflow_attachment import sync_workflow_attachment

# 🔹 Doctype-wise mapping (FLOW BASED)
DOCTYPE_SOURCE_MAP = {
    "Request for Quotation": {
        "custom_pickup_request": "Pickup Request",
    },
    "Supplier Quotation": {
        "custom_request_for_quotation": "Request for Quotation",
    },
    "Pre Alert": {
        "custom_supplier_quotation": "Supplier Quotation",
        "rfq_number": "Request for Quotation",
        "pickup_request": "Pickup Request",
    },
}


def sync_workflow_attachments_for_logistics(doc, method):
    frappe.logger().info(f"RUNNING SYNC FOR {doc.doctype} - {doc.name}")
    
    if getattr(doc, "custom_type", None) != "Logistics":
        return

    # Get mapping based on current doctype
    source_map = DOCTYPE_SOURCE_MAP.get(doc.doctype, {})

    for field, source_doctype in source_map.items():
        source_name = getattr(doc, field, None)
        
        if source_name:
            sync_workflow_attachments_from_source(
                target_doc=doc,
                source_doctype=source_doctype,
                source_name=source_name,
            )
# copy from supplier quotation to pre alert
def copy_attachments_from_supplier_quotation(doc, method=None):

    if not doc.custom_supplier_quotation:
        return

    source_doc = frappe.get_doc("Supplier Quotation", doc.custom_supplier_quotation)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })
        
# copy from pre alert to pre alert check list        
def copy_attachments_from_pre_alert(doc, method=None):

    if not doc.pre_alert:
        return

    source_doc = frappe.get_doc("Pre Alert", doc.pre_alert)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })

# copy from pre alert check list to BoE entry
def copy_attachments_from_pre_alert_checklist(doc, method=None):

    if not doc.per_alert_check:
        return

    source_doc = frappe.get_doc("Pre-Alert Check List", doc.per_alert_check)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })
        
# copy from BOe entry to po coinditiuon change
def copy_attachments_from_boe(doc, method=None):

    if not doc.boe_entry_reference:
        return

    source_doc = frappe.get_doc("BOE Entry", doc.boe_entry_reference)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })
        
# copy from po condition change to e way bill
def copy_attachments_from_po_condition_change(doc, method=None):

    if not doc.doctype_id:
        return

    source_doc = frappe.get_doc("PO Condition Change", doc.doctype_id)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })

# copy from EWAY chnage to GATENETRY
def copy_attachments_from_eway_bill(doc, method=None):
    frappe.msgprint("GATE ENTRY SYNC RUNNING")

    if not doc.e_waybill_no:
        return

    source_doc = frappe.get_doc("E-way Bill", doc.e_waybill_no)

    source_rows = source_doc.get("custom_workflow_attachment") or []
    target_rows = doc.get("custom_workflow_attachment") or []

    existing_paths = {row.path for row in target_rows}

    for row in source_rows:
        if not row.path:
            continue

        if row.path in existing_paths:
            continue

        doc.append("custom_workflow_attachment", {
            "path": row.path,
            "file_name": row.file_name,
            "doctype_name": row.doctype_name,
            "doctype_id": row.doctype_id,
        })
        
def safe_sync_workflow_attachment(doc, method=None):
    if doc.is_new():
        return
    
    from merai_newage.overrides.workflow_attachment import sync_workflow_attachment
    sync_workflow_attachment(doc.doctype, doc.name)