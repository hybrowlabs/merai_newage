# your_app/controllers/supplier_quotation.py

import frappe
from frappe import _

def before_save_supplier_quotation(doc, method):
    """Populate ACR from Material Request"""
    
    # Check if created from Material Request
    for item in doc.items:
        if item.material_request:
            mr = frappe.get_doc("Material Request", item.material_request)
            if mr.custom_asset_creation_request:
                doc.custom_asset_creation_request = mr.custom_asset_creation_request
                break


def validate_supplier_quotation(doc, method):
    """Validate Supplier Quotation for Asset items"""
    
    if doc.custom_asset_creation_request:
        acr = frappe.get_doc("Asset Creation Request", doc.custom_asset_creation_request)
        
        # Validate items
        for item in doc.items:
            if item.item_code != acr.item:
                frappe.throw(_("Row {0}: Item {1} does not match Asset Creation Request").format(
                    item.idx, item.item_code))