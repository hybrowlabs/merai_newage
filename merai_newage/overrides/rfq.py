import frappe
from frappe import _

def validate_request_for_quotation(doc, method):
    """Validate RFQ for asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Validate items match ACR
        for item in doc.items:
            if item.material_request:
                mr_item_code = frappe.db.get_value("Material Request Item", 
                    {"parent": item.material_request}, "item_code")
                if mr_item_code != acr.item:
                    frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
                        item.idx, item.item_code))

def before_save_request_for_quotation(doc, method):
    """Populate ACR from Material Request"""
    
    # Get ACR from linked Material Requests
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break


def validate_request_for_quotation(doc, method):
    """Validate RFQ for asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Validate items match ACR
        for item in doc.items:
            if item.material_request:
                mr_item_code = frappe.db.get_value("Material Request Item", 
                    {"parent": item.material_request}, "item_code")
                if mr_item_code != acr.item:
                    frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
                        item.idx, item.item_code))

    from merai_newage.overrides.request_for_quotation import (
            copy_workflow_attachments_from_pickup_request
        )
    copy_workflow_attachments_from_pickup_request(doc, method)
    

@frappe.whitelist()
def revise_rfq(rfq_name: str):

    rfq = frappe.get_doc("Request for Quotation", rfq_name)

    if rfq.docstatus != 1:
        frappe.throw("Only Submitted RFQ can be revised.")

    original_rfq = rfq.custom_original_rfq or rfq.name

    last_revision = frappe.db.sql("""
        SELECT COALESCE(MAX(custom_revision_no), 0)
        FROM `tabRequest for Quotation`
        WHERE custom_original_rfq = %s
           OR name = %s
    """, (original_rfq, original_rfq))[0][0]

    new_revision_no = int(last_revision) + 1
    rfq_number_part = original_rfq.split("-")[-1]
    revision_code = f"PUR-RFQ-REV-{rfq_number_part}-{new_revision_no:03d}"

    new_rfq = frappe.copy_doc(rfq)
    new_rfq.docstatus = 0
    new_rfq.status = "Draft"

    new_rfq.custom_original_rfq = original_rfq
    new_rfq.custom_revision_no = new_revision_no
    new_rfq.custom_revision_code = revision_code
    new_rfq.custom_is_latest_revision = 1

    frappe.db.set_value(
        "Request for Quotation",
        rfq.name,
        "custom_is_latest_revision",
        0
    )

    new_rfq.insert(ignore_permissions=True)

    return new_rfq.name


@frappe.whitelist()
def get_rfq_revisions(rfq_name):

    rfq = frappe.get_doc("Request for Quotation", rfq_name)

    original = rfq.custom_original_rfq or rfq.name

    revisions = frappe.get_all(
        "Request for Quotation",
        filters={
            "custom_original_rfq": original
        },
        fields=[
            "name",
            "custom_revision_no",
            "custom_revision_code",
            "creation"
        ],
        order_by="custom_revision_no asc"
    )

    return {
        "original_rfq": original,
        "revisions": revisions
    }