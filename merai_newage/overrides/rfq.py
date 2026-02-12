import frappe
from frappe import _

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